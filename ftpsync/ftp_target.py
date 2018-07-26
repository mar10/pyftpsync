# -*- coding: utf-8 -*-
"""
(c) 2012-2018 Martin Wendt; see https://github.com/mar10/pyftpsync
Licensed under the MIT license: http://www.opensource.org/licenses/mit-license.php
"""
import calendar
import ftplib
import json
import os
import time
from posixpath import join as join_url, normpath as normpath_url, relpath as relpath_url
from tempfile import SpooledTemporaryFile

from ftpsync.compat import CompatConnectionError
from ftpsync.metadata import DirMetadata, IncompatibleMetadataVersion
from ftpsync.resources import DirectoryEntry, FileEntry
from ftpsync.targets import _Target
from ftpsync.util import (
    get_credentials_for_url,
    prompt_for_password,
    save_password,
    write,
    write_error,
)


# ===============================================================================
# FtpTarget
# ===============================================================================
class FtpTarget(_Target):
    """Represents a synchronization target on an FTP server.

    Attributes:
        path (str): Current working directory on FTP server.
        ftp (FTP): Instance of ftplib.FTP.
        host (str): hostname of FTP server
        port (int): FTP port (defaults to 21)
        username (str):
        password (str):
    """

    DEFAULT_BLOCKSIZE = 8 * 1024  # ftplib uses 8k chunks by default
    MAX_SPOOL_MEM = (
        100 * 1024
    )  # keep open_readable() buffer in memory if smaller than 100kB

    def __init__(
        self,
        path,
        host,
        port=0,
        username=None,
        password=None,
        tls=False,
        timeout=None,
        extra_opts=None,
    ):
        """Create FTP target with host, initial path, optional credentials and options.

        Args:
            path (str): root path on FTP server, relative to *host*
            host (str): hostname of FTP server
            port (int): FTP port (defaults to 21)
            username (str):
            password (str):
            tls (bool): encrypt the connection using TLS (Python 2.7/3.2+)
            timeout (int): the timeout to set against the ftp socket (seconds)
            extra_opts (dict):
        """
        path = path or "/"
        super(FtpTarget, self).__init__(path, extra_opts)
        if tls:
            try:
                self.ftp = ftplib.FTP_TLS()
            except AttributeError:
                write("Python 2.7/3.2+ required for FTPS (TLS).")
                raise
        else:
            self.ftp = ftplib.FTP()
        self.ftp.set_debuglevel(self.get_option("ftp_debug", 0))
        self.host = host
        self.port = port or 0
        self.username = username
        self.password = password
        self.tls = tls
        self.timeout = timeout
        #: dict: written to ftp target root folder before synchronization starts.
        #: set to False, if write failed. Default: None
        self.lock_data = None
        self.is_unix = None
        self.time_zone_ofs = None
        self.clock_ofs = None
        self.ftp_socket_connected = False
        self.support_set_time = False

    def __str__(self):
        return "<{} + {}>".format(
            self.get_base_name(), relpath_url(self.cur_dir or "/", self.root_dir)
        )

    def get_base_name(self):
        scheme = "ftps" if self.tls else "ftp"
        return "{}://{}{}".format(scheme, self.host, self.root_dir)

    def open(self):
        assert not self.ftp_socket_connected

        super(FtpTarget, self).open()

        options = self.get_options_dict()
        no_prompt = self.get_option("no_prompt", True)
        store_password = self.get_option("store_password", False)

        self.ftp.set_debuglevel(self.get_option("ftp_debug", 0))

        # Optionally use FTP active mode (default: PASV) (issue #21)
        force_active = self.get_option("ftp_active", False)
        self.ftp.set_pasv(not force_active)

        if self.timeout:
            self.ftp.connect(self.host, self.port, self.timeout)
        else:
            # Py2.7 uses -999 as default for `timeout`, Py3 uses None
            self.ftp.connect(self.host, self.port)

        self.ftp_socket_connected = True

        if self.username is None or self.password is None:
            creds = get_credentials_for_url(
                self.host, options, force_user=self.username
            )
            if creds:
                self.username, self.password = creds

        while True:
            try:
                # Login (as 'anonymous' if self.username is undefined):
                self.ftp.login(self.username, self.password)
                if self.get_option("verbose", 3) >= 4:
                    write(
                        "Login as '{}'.".format(
                            self.username if self.username else "anonymous"
                        )
                    )
                break
            except ftplib.error_perm as e:
                # If credentials were passed, but authentication fails, prompt
                # for new password
                if not e.args[0].startswith("530"):
                    raise  # error other then '530 Login incorrect'
                write_error(
                    "Could not login to {}@{}: {}".format(self.username, self.host, e)
                )
                if no_prompt or not self.username:
                    raise
                creds = prompt_for_password(self.host, self.username)
                self.username, self.password = creds
                # Continue while-loop

        if self.tls:
            # Upgrade data connection to TLS.
            self.ftp.prot_p()

        try:
            self.ftp.cwd(self.root_dir)
        except ftplib.error_perm as e:
            # If credentials were passed, but authentication fails, prompt
            # for new password
            if not e.args[0].startswith("550"):
                raise  # error other then 550 No such directory'
            write_error(
                "Could not change directory to {} ({}): missing permissions?".format(
                    self.root_dir, e
                )
            )

        pwd = self.ftp.pwd()
        if pwd != self.root_dir:
            raise RuntimeError(
                "Unable to navigate to working directory {!r} (now at {!r})".format(
                    self.root_dir, pwd
                )
            )

        self.cur_dir = pwd

        # self.ftp_initialized = True
        # Successfully authenticated: store password
        if store_password:
            save_password(self.host, self.username, self.password)

        # TODO: case sensitivity?
        # self.is_unix = "unix" in resp.lower() # not necessarily true, better check with r/w tests
        if self.get_option("verbose", 3) >= 5:
            try:
                resp = self.ftp.sendcmd("SYST")
                write("SYST: '{}'.".format(resp))
            except Exception as e:
                write("SYST command failed: '{}'.".format(e))

            try:
                resp = self.ftp.sendcmd("FEAT")
                write("FEAT: '{}'.".format(resp))
            except Exception as e:
                write("FEAT command failed: '{}'.".format(e))

        self._lock()

        return

    def close(self):
        if self.lock_data:
            self._unlock(closing=True)

        if self.ftp_socket_connected:
            try:
                self.ftp.quit()
            except (CompatConnectionError, EOFError) as e:
                write_error("ftp.quit() failed: {}".format(e))
            self.ftp_socket_connected = False

        super(FtpTarget, self).close()

    def _lock(self, break_existing=False):
        """Write a special file to the target root folder."""
        # write("_lock")
        data = {"lock_time": time.time(), "lock_holder": None}

        try:
            assert self.cur_dir == self.root_dir
            self.write_text(DirMetadata.LOCK_FILE_NAME, json.dumps(data))
            self.lock_data = data
        except Exception as e:
            errmsg = "{}".format(e)
            write_error("Could not write lock file: {}".format(errmsg))
            if errmsg.startswith("550") and self.ftp.passiveserver:
                try:
                    self.ftp.makepasv()
                except Exception:
                    write_error(
                        "The server probably requires FTP Active mode. "
                        "Try passing the --ftp-active option."
                    )

            # Set to False, so we don't try to remove later
            self.lock_data = False

    def _unlock(self, closing=False):
        """Remove lock file to the target root folder.

        """
        # write("_unlock", closing)
        try:
            if self.cur_dir != self.root_dir:
                if closing:
                    write(
                        "Changing to ftp root folder to remove lock file: {}".format(
                            self.root_dir
                        )
                    )
                    self.cwd(self.root_dir)
                else:
                    write_error(
                        "Could not remove lock file, because CWD != ftp root: {}".format(
                            self.cur_dir
                        )
                    )
                    return

            if self.lock_data is False:
                if self.get_option("verbose", 3) >= 4:
                    write("Skip remove lock file (was not written).")
            else:
                # direct delete, without updating metadata or checking for target access:
                self.ftp.delete(DirMetadata.LOCK_FILE_NAME)
                # self.remove_file(DirMetadata.LOCK_FILE_NAME)

            self.lock_data = None
        except Exception as e:
            write_error("Could not remove lock file: {}".format(e))
            raise

    def _probe_lock_file(self, reported_mtime):
        """Called by get_dir"""
        delta = reported_mtime - self.lock_data["lock_time"]
        if self.get_option("verbose", 3) >= 4:
            write("Server time offset: {0:.2f} seconds".format(delta))

    def get_id(self):
        return self.host + self.root_dir

    def cwd(self, dir_name):
        path = normpath_url(join_url(self.cur_dir, dir_name))
        if not path.startswith(self.root_dir):
            # paranoic check to prevent that our sync tool goes berserk
            raise RuntimeError(
                "Tried to navigate outside root %r: %r" % (self.root_dir, path)
            )
        self.ftp.cwd(dir_name)
        self.cur_dir = path
        self.cur_dir_meta = None
        return self.cur_dir

    def pwd(self):
        return self.ftp.pwd()

    def mkdir(self, dir_name):
        self.check_write(dir_name)
        self.ftp.mkd(dir_name)

    def _rmdir_impl(self, dir_name, keep_root_folder=False, predicate=None):
        # FTP does not support deletion of non-empty directories.
        self.check_write(dir_name)
        names = []
        nlst_res = self.ftp.nlst(dir_name)
        # write("rmdir(%s): %s" % (dir_name, nlst_res))
        for name in nlst_res:
            if "/" in name:
                name = os.path.basename(name)
            if name in (".", ".."):
                continue
            if predicate and not predicate(name):
                continue
            names.append(name)

        if len(names) > 0:
            self.ftp.cwd(dir_name)
            try:
                for name in names:
                    try:
                        # try to delete this as a file
                        self.ftp.delete(name)
                    except ftplib.all_errors as _e:
                        write(
                            "    ftp.delete({}) failed: {}, trying rmdir()...".format(
                                name, _e
                            )
                        )
                        # assume <name> is a folder
                        self.rmdir(name)
            finally:
                if dir_name != ".":
                    self.ftp.cwd("..")
        #        write("ftp.rmd(%s)..." % (dir_name, ))
        if not keep_root_folder:
            self.ftp.rmd(dir_name)
        return

    def rmdir(self, dir_name):
        return self._rmdir_impl(dir_name)

    def get_dir(self):
        entry_list = []
        entry_map = {}
        local_res = {"has_meta": False}  # pass local variables outside func scope

        def _addline(line):
            data, _, name = line.partition("; ")
            res_type = size = mtime = unique = None
            fields = data.split(";")
            # http://tools.ietf.org/html/rfc3659#page-23
            # "Size" / "Modify" / "Create" / "Type" / "Unique" / "Perm" / "Lang"
            #   / "Media-Type" / "CharSet" / os-depend-fact / local-fact
            for field in fields:
                field_name, _, field_value = field.partition("=")
                field_name = field_name.lower()
                if field_name == "type":
                    res_type = field_value
                elif field_name in ("sizd", "size"):
                    size = int(field_value)
                elif field_name == "modify":
                    # Use calendar.timegm() instead of time.mktime(), because
                    # the date was returned as UTC
                    if "." in field_value:
                        mtime = calendar.timegm(
                            time.strptime(field_value, "%Y%m%d%H%M%S.%f")
                        )
                    else:
                        mtime = calendar.timegm(
                            time.strptime(field_value, "%Y%m%d%H%M%S")
                        )
                elif field_name == "unique":
                    unique = field_value

            entry = None
            if res_type == "dir":
                entry = DirectoryEntry(self, self.cur_dir, name, size, mtime, unique)
            elif res_type == "file":
                if name == DirMetadata.META_FILE_NAME:
                    # the meta-data file is silently ignored
                    local_res["has_meta"] = True
                elif (
                    name == DirMetadata.LOCK_FILE_NAME and self.cur_dir == self.root_dir
                ):
                    # this is the root lock file. compare reported mtime with
                    # local upload time
                    self._probe_lock_file(mtime)
                else:
                    entry = FileEntry(self, self.cur_dir, name, size, mtime, unique)
            elif res_type in ("cdir", "pdir"):
                pass
            else:
                raise NotImplementedError(
                    "MLSD returned unsupported type: {!r}".format(res_type)
                )

            if entry:
                entry_map[name] = entry
                entry_list.append(entry)

        try:
            self.ftp.retrlines("MLSD", _addline)
        except ftplib.error_perm as e:
            # write_error("The FTP server responded with {}".format(e))
            # raises error_perm "500 Unknown command" if command is not supported
            if "500" in str(e.args):
                raise RuntimeError(
                    "The FTP server does not support the 'MLSD' command."
                )
            raise

        # load stored meta data if present
        self.cur_dir_meta = DirMetadata(self)

        if local_res["has_meta"]:
            try:
                self.cur_dir_meta.read()
            except IncompatibleMetadataVersion:
                raise  # this should end the script (user should pass --migrate)
            except Exception as e:
                write_error(
                    "Could not read meta info {}: {}".format(self.cur_dir_meta, e)
                )

            meta_files = self.cur_dir_meta.list

            # Adjust file mtime from meta-data if present
            missing = []
            for n in meta_files:
                meta = meta_files[n]
                if n in entry_map:
                    # We have a meta-data entry for this resource
                    upload_time = meta.get("u", 0)
                    if (
                        entry_map[n].size == meta.get("s")
                        and FileEntry._eps_compare(entry_map[n].mtime, upload_time) <= 0
                    ):
                        # Use meta-data mtime instead of the one reported by FTP server
                        entry_map[n].meta = meta
                        entry_map[n].mtime = meta["m"]
                        # entry_map[n].dt_modified = datetime.fromtimestamp(meta["m"])
                    else:
                        # Discard stored meta-data if
                        #   1. the the mtime reported by the FTP server is later
                        #      than the stored upload time (which indicates
                        #      that the file was modified directly on the server)
                        #      or
                        #   2. the reported files size is different than the
                        #      size we stored in the meta-data
                        if self.get_option("verbose", 3) >= 5:
                            write(
                                (
                                    "META: Removing outdated meta entry {}\n"
                                    + "      modified after upload ({} > {}), or\n"
                                    "      cur. size ({}) != meta size ({})"
                                ).format(
                                    n,
                                    time.ctime(entry_map[n].mtime),
                                    time.ctime(upload_time),
                                    entry_map[n].size,
                                    meta.get("s"),
                                )
                            )
                        missing.append(n)
                else:
                    # File is stored in meta-data, but no longer exists on FTP server
                    # write("META: Removing missing meta entry %s" % n)
                    missing.append(n)
            # Remove missing or invalid files from cur_dir_meta
            for n in missing:
                self.cur_dir_meta.remove(n)

        return entry_list

    def open_readable(self, name):
        """Open cur_dir/name for reading.

        Note: we read everything into a buffer that supports .read().

        Args:
            name (str): file name, located in self.curdir
        Returns:
            file-like (must support read() method)
        """
        # print("FTP open_readable({})".format(name))
        out = SpooledTemporaryFile(max_size=self.MAX_SPOOL_MEM, mode="w+b")
        self.ftp.retrbinary(
            "RETR {}".format(name), out.write, FtpTarget.DEFAULT_BLOCKSIZE
        )
        out.seek(0)
        return out

    def write_file(self, name, fp_src, blocksize=DEFAULT_BLOCKSIZE, callback=None):
        """Write file-like `fp_src` to cur_dir/name.

        Args:
            name (str): file name, located in self.curdir
            fp_src (file-like): must support read() method
            blocksize (int, optional):
            callback (function, optional):
                Called like `func(buf)` for every written chunk
        """
        self.check_write(name)
        # print("FTP write_file({})".format(name), blocksize)
        self.ftp.storbinary("STOR {}".format(name), fp_src, blocksize, callback)
        # TODO: check result

    def copy_to_file(self, name, fp_dest, callback=None):
        """Write cur_dir/name to file-like `fp_dest`.

        Args:
            name (str): file name, located in self.curdir
            fp_dest (file-like): must support write() method
            callback (function, optional):
                Called like `func(buf)` for every written chunk
        """

        def _write_to_file(data):
            # print("_write_to_file() {} bytes.".format(len(data)))
            fp_dest.write(data)
            if callback:
                callback(data)

        self.ftp.retrbinary(
            "RETR {}".format(name), _write_to_file, FtpTarget.DEFAULT_BLOCKSIZE
        )

    def remove_file(self, name):
        """Remove cur_dir/name."""
        self.check_write(name)
        # self.cur_dir_meta.remove(name)
        self.ftp.delete(name)
        self.remove_sync_info(name)

    def set_mtime(self, name, mtime, size):
        self.check_write(name)
        # write("META set_mtime(%s): %s" % (name, time.ctime(mtime)))
        # We cannot set the mtime on FTP servers, so we store this as additional
        # meta data in the same directory
        # TODO: try "SITE UTIME", "MDTM (set version)", or "SRFT" command
        self.cur_dir_meta.set_mtime(name, mtime, size)
