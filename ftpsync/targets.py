# -*- coding: utf-8 -*-
"""
(c) 2012-2020 Martin Wendt; see https://github.com/mar10/pyftpsync
Licensed under the MIT license: https://www.opensource.org/licenses/mit-license.php
"""

import codecs
import contextlib
import io
import os
import shutil
import sys
import threading
from posixpath import join as join_url, normpath as normpath_url
from urllib.parse import urlparse

from ftpsync.metadata import DirMetadata
from ftpsync.resources import DirectoryEntry, FileEntry
from ftpsync.util import is_native, to_bytes, to_native, to_unicode, write


# ===============================================================================
# make_target
# ===============================================================================
def make_target(url, extra_opts=None):
    """Factory that creates `_Target` objects from URLs.

    FTP targets must begin with the scheme ``ftp://``,  ``ftps://`` for TLS,
    or ``sftp://`` for SFTP.

    Args:
        url (str):
        extra_opts (dict, optional): Passed to Target constructor. Default: None.
    Returns:
        :class:`_Target`
    """
    # debug = extra_opts.get("debug", 1)
    parts = urlparse(url, allow_fragments=False)
    # scheme is case-insensitive according to https://tools.ietf.org/html/rfc3986
    scheme = parts.scheme.lower()
    if scheme in ("ftp", "ftps"):
        from ftpsync.ftp_target import FTPTarget

        target = FTPTarget(
            parts.path,
            parts.hostname,
            parts.port,
            username=parts.username,
            password=parts.password,
            tls=(scheme == "ftps"),
            timeout=None,
            extra_opts=extra_opts,
        )
    elif scheme == "sftp":
        from ftpsync.sftp_target import SFTPTarget

        target = SFTPTarget(
            parts.path,
            parts.hostname,
            parts.port,
            username=parts.username,
            password=parts.password,
            timeout=None,
            extra_opts=extra_opts,
        )
    else:
        target = FsTarget(url, extra_opts)

    return target


def _get_encoding_opt(synchronizer, extra_opts, default):
    """Helper to figure out encoding setting inside constructors."""
    encoding = default
    # if synchronizer and "encoding" in synchronizer.options:
    #     encoding = synchronizer.options.get("encoding")
    if extra_opts and "encoding" in extra_opts:
        encoding = extra_opts.get("encoding")
    if encoding:
        # Normalize name (e.g. 'UTF8' => 'utf-8')
        encoding = codecs.lookup(encoding).name
    # print("_get_encoding_opt", encoding)
    return encoding or None


# ===============================================================================
# _Target
# ===============================================================================
class _Target:
    """Base class for :class:`FsTarget`, :class:`FTPTarget`, etc."""

    DEFAULT_BLOCKSIZE = 16 * 1024  # shutil.copyobj() uses 16k blocks by default

    def __init__(self, root_dir, extra_opts):
        # All internal paths should use unicode.
        # (We cannot convert here, since we don't know the target encoding.)
        assert is_native(root_dir)
        if root_dir != "/":
            root_dir = root_dir.rstrip("/")
        # This target is not thread safe
        self._rlock = threading.RLock()
        #: The target's top-level folder
        self.root_dir = root_dir
        self.extra_opts = extra_opts or {}
        self.readonly = False
        self.dry_run = False
        self.host = None
        self.synchronizer = None  # Set by BaseSynchronizer.__init__()
        self.peer = None
        self.cur_dir = None
        self.connected = False
        self.save_mode = True
        self.case_sensitive = None  # TODO: don't know yet
        #: Time difference between <local upload time> and the mtime that the server reports afterwards.
        #: The value is added to the 'u' time stored in meta data.
        #: (This is only a rough estimation, derived from the lock-file.)
        self.server_time_ofs = None
        #: Maximum allowed difference between a reported mtime and the last known update time,
        #: before we classify the entry as 'modified externally'
        self.mtime_compare_eps = FileEntry.EPS_TIME
        self.cur_dir_meta = DirMetadata(self)
        self.meta_stack = []
        # Optionally define an encoding for this target, but don't override
        # derived class's setting
        if not hasattr(self, "encoding"):
            #: Assumed encoding for this target. Used to decode binary paths.
            self.encoding = _get_encoding_opt(None, extra_opts, None)
        return

    def __del__(self):
        # TODO: http://pydev.blogspot.de/2015/01/creating-safe-cyclic-reference.html
        if self.connected:
            self.close()

    # def __enter__(self):
    #     self.open()
    #     return self

    # def __exit__(self, exc_type, exc_value, traceback):
    #     self.close()

    def get_base_name(self):
        return "{}".format(self.root_dir)

    def is_local(self):
        return self.synchronizer.local is self

    def is_unbound(self):
        return self.synchronizer is None

    def get_options_dict(self):
        """Return options from synchronizer (possibly overridden by own extra_opts)."""
        d = self.synchronizer.options if self.synchronizer else {}
        d.update(self.extra_opts)
        return d

    def get_option(self, key, default=None):
        """Return option from synchronizer (possibly overridden by target extra_opts)."""
        if self.synchronizer:
            return self.extra_opts.get(key, self.synchronizer.options.get(key, default))
        return self.extra_opts.get(key, default)

    def open(self):
        if self.connected:
            raise RuntimeError("Target already open: {}.  ".format(self))
        # Not thread safe (issue #20)
        if not self._rlock.acquire(False):
            raise RuntimeError("Could not acquire _Target lock on open")
        self.connected = True

    def close(self):
        if not self.connected:
            return
        if self.get_option("verbose", 3) >= 5:
            write("Closing target {}.".format(self))
        self.connected = False
        self.readonly = False  # issue #20
        self._rlock.release()

    def check_write(self, name):
        """Raise exception if writing cur_dir/name is not allowed."""
        assert is_native(name)
        if self.readonly and name not in (
            DirMetadata.META_FILE_NAME,
            DirMetadata.LOCK_FILE_NAME,
        ):
            raise RuntimeError("Target is read-only: {} + {} / ".format(self, name))

    def get_id(self):
        return self.root_dir

    def get_sync_info(self, name, key=None):
        """Get mtime/size when this target's current dir was last synchronized with remote."""
        peer_target = self.peer
        if self.is_local():
            info = self.cur_dir_meta.dir["peer_sync"].get(peer_target.get_id())
        else:
            info = peer_target.cur_dir_meta.dir["peer_sync"].get(self.get_id())
        if name is not None:
            info = info.get(name) if info else None
        if info and key:
            info = info.get(key)
        return info

    def cwd(self, dir_name):
        raise NotImplementedError

    @contextlib.contextmanager
    def enter_subdir(self, name):
        """Temporarily changes the working directory to `name`.

        Examples:
            with target.enter_subdir(folder):
                ...
        """
        self.cwd(name)
        yield
        self.cwd("..")

    def push_meta(self):
        self.meta_stack.append(self.cur_dir_meta)
        self.cur_dir_meta = None

    def pop_meta(self):
        self.cur_dir_meta = self.meta_stack.pop()

    def flush_meta(self):
        """Write additional meta information for current directory."""
        if self.cur_dir_meta:
            self.cur_dir_meta.flush()

    def pwd(self, dir_name):
        raise NotImplementedError

    def mkdir(self, dir_name):
        raise NotImplementedError

    def rmdir(self, dir_name):
        """Remove cur_dir/name."""
        raise NotImplementedError

    def get_dir(self):
        """Return a list of _Resource entries."""
        raise NotImplementedError

    def walk(self, pred=None, recursive=True):
        """Iterate over all target entries recursively.

        Args:
            pred (function, optional):
                Callback(:class:`ftpsync.resources._Resource`) should return `False` to
                ignore entry. Default: `None`.
            recursive (bool, optional):
                Pass `False` to generate top level entries only. Default: `True`.
        Yields:
            :class:`ftpsync.resources._Resource`
        """
        for entry in self.get_dir():
            if pred and pred(entry) is False:
                continue

            yield entry

            if recursive:
                if isinstance(entry, DirectoryEntry):
                    self.cwd(entry.name)
                    for e in self.walk(pred):
                        yield e
                    self.cwd("..")
        return

    def walk_tree(self, pred=None, _prefixes=None):
        """Iterate over target hierarchy, depth-first, adding a connector prefix.

            This iterator walks the tree nodes, but slightly delays the output, in
            order to add information if a node is the *last* sibling.
            This information is then used to create pretty tree connector prefixes.

            Args:
                pred (function, optional):
                    Callback(:class:`ftpsync.resources._Resource`) should return `False` to
                    ignore entry. Default: `None`.
            Yields:
                3-tuple (
                    :class:`ftpsync.resources._Resource`,
                    is_last_sibling,
                    prefix,
                )

        A
         +- a
         |   +- 1
         |   |   `- 1.1
         |   `- 2
         |       `- 2.1
         `- b
             +- 1
             |   `-  1.1
              ` 2
        """
        # List of parent's `is_last` flags:
        if _prefixes is None:
            _prefixes = []

        def _yield_entry(entry, is_last):
            path = "".join(["    " if last else " |  " for last in _prefixes])
            path += " `- " if is_last else " +- "
            yield path, entry
            if entry.is_dir():
                with self.enter_subdir(entry.name):
                    _prefixes.append(is_last)
                    yield from self.walk_tree(pred, _prefixes)
                    _prefixes.pop()
            return

        prev_entry = None
        for next_entry in self.get_dir():
            if pred and pred(next_entry) is False:
                continue
            # Skip first entry
            if prev_entry is None:
                prev_entry = next_entry
                continue
            # Yield entry (this is never the last sibling)
            yield from _yield_entry(prev_entry, False)
            prev_entry = next_entry

        # Finally yield the last sibling
        if prev_entry:
            yield from _yield_entry(prev_entry, True)
        return

    def open_readable(self, name):
        """Return file-like object opened in binary mode for cur_dir/name."""
        raise NotImplementedError

    def open_writable(self, name):
        """Return file-like object opened in binary mode for cur_dir/name."""
        raise NotImplementedError

    def read_text(self, name):
        """Read text string from cur_dir/name using open_readable()."""
        with self.open_readable(name) as fp:
            res = fp.read()  # StringIO or file object
            # try:
            #     res = fp.getvalue()  # StringIO returned by FTPTarget
            # except AttributeError:
            #     res = fp.read()  # file object returned by FsTarget
            res = res.decode("utf-8")
            return res

    def copy_to_file(self, name, fp_dest, callback=None):
        """Write cur_dir/name to file-like `fp_dest`.

        Args:
            name (str): file name, located in self.curdir
            fp_dest (file-like): must support write() method
            callback (function, optional):
                Called like `func(buf)` for every written chunk
        """
        raise NotImplementedError

    def write_file(self, name, fp_src, blocksize=DEFAULT_BLOCKSIZE, callback=None):
        """Write binary data from file-like to cur_dir/name."""
        raise NotImplementedError

    def write_text(self, name, s):
        """Write string data to cur_dir/name using write_file()."""
        buf = io.BytesIO(to_bytes(s))
        self.write_file(name, buf)

    def remove_file(self, name):
        """Remove cur_dir/name."""
        raise NotImplementedError

    def set_mtime(self, name, mtime, size):
        raise NotImplementedError

    def set_sync_info(self, name, mtime, size):
        """Store mtime/size when this resource was last synchronized with remote."""
        if not self.is_local():
            return self.peer.set_sync_info(name, mtime, size)
        return self.cur_dir_meta.set_sync_info(name, mtime, size)

    def remove_sync_info(self, name):
        if not self.is_local():
            return self.peer.remove_sync_info(name)
        if self.cur_dir_meta:
            return self.cur_dir_meta.remove(name)
        # write("%s.remove_sync_info(%s): nothing to do" % (self, name))
        return


# ===============================================================================
# FsTarget
# ===============================================================================


class FsTarget(_Target):

    DEFAULT_BLOCKSIZE = 16 * 1024  # shutil.copyobj() uses 16k blocks by default

    def __init__(self, root_dir, extra_opts=None):
        def_enc = sys.getfilesystemencoding()
        if not def_enc:
            def_enc = "utf-8"
        self.encoding = _get_encoding_opt(None, extra_opts, def_enc)
        # root_dir = self.to_unicode(root_dir)
        root_dir = os.path.expanduser(root_dir)
        root_dir = os.path.abspath(root_dir)
        super(FsTarget, self).__init__(root_dir, extra_opts)
        if not os.path.isdir(root_dir):
            raise ValueError("{} is not a directory.".format(root_dir))
        self.support_set_time = True

    def __str__(self):
        return "<FS:{} + {}>".format(
            self.root_dir, os.path.relpath(self.cur_dir, self.root_dir)
        )

    def open(self):
        super(FsTarget, self).open()
        self.cur_dir = self.root_dir

    def close(self):
        super(FsTarget, self).close()

    def cwd(self, dir_name):
        path = normpath_url(join_url(self.cur_dir, dir_name))
        if not path.startswith(self.root_dir):
            raise RuntimeError(
                "Tried to navigate outside root %r: %r" % (self.root_dir, path)
            )
        self.cur_dir_meta = None
        self.cur_dir = path
        return self.cur_dir

    def pwd(self):
        return self.cur_dir

    def mkdir(self, dir_name):
        self.check_write(dir_name)
        path = normpath_url(join_url(self.cur_dir, dir_name))
        os.mkdir(path)

    def rmdir(self, dir_name):
        """Remove cur_dir/name."""
        self.check_write(dir_name)
        path = normpath_url(join_url(self.cur_dir, dir_name))
        # write("REMOVE %r" % path)
        shutil.rmtree(path)

    def flush_meta(self):
        """Write additional meta information for current directory."""
        if self.cur_dir_meta:
            self.cur_dir_meta.flush()

    def get_dir(self):
        res = []
        # self.cur_dir_meta = None
        self.cur_dir_meta = DirMetadata(self)
        # List directory. Pass in unicode on Py2, so we get unicode in return
        unicode_cur_dir = to_unicode(self.cur_dir)
        for name in os.listdir(unicode_cur_dir):
            name = to_native(name)
            path = os.path.join(self.cur_dir, name)
            stat = os.lstat(path)
            # write(name)
            # write("    mt : %s" % stat.st_mtime)
            # write("    lc : %s" % (time.localtime(stat.st_mtime),))
            # write("       : %s" % time.asctime(time.localtime(stat.st_mtime)))
            # write("    gmt: %s" % (time.gmtime(stat.st_mtime),))
            # write("       : %s" % time.asctime(time.gmtime(stat.st_mtime)))

            # utc_stamp = st_mtime_to_utc(stat.st_mtime)
            # write("    utc: %s" % utc_stamp)
            # write("    diff: %s" % ((utc_stamp - stat.st_mtime) / (60*60)))
            # stat.st_mtime is returned as UTC
            mtime = stat.st_mtime
            if os.path.isdir(path):
                res.append(
                    DirectoryEntry(
                        self, self.cur_dir, name, stat.st_size, mtime, str(stat.st_ino)
                    )
                )
            elif os.path.isfile(path):
                if name == DirMetadata.META_FILE_NAME:
                    self.cur_dir_meta.read()
                # elif not name in (DirMetadata.DEBUG_META_FILE_NAME, ):
                else:
                    res.append(
                        FileEntry(
                            self,
                            self.cur_dir,
                            name,
                            stat.st_size,
                            mtime,
                            str(stat.st_ino),
                        )
                    )
        return res

    def open_readable(self, name):
        fp = open(os.path.join(self.cur_dir, name), "rb")
        # print("open_readable({})".format(name))
        return fp

    def open_writable(self, name):
        fp = open(os.path.join(self.cur_dir, name), "wb")
        # print("open_readable({})".format(name))
        return fp

    def write_file(self, name, fp_src, blocksize=DEFAULT_BLOCKSIZE, callback=None):
        self.check_write(name)
        with open(os.path.join(self.cur_dir, name), "wb") as fp_dst:
            while True:
                data = fp_src.read(blocksize)
                # print("write_file({})".format(name), len(data))
                if data is None or not len(data):
                    break
                fp_dst.write(data)
                if callback:
                    callback(data)
        return

    def remove_file(self, name):
        """Remove cur_dir/name."""
        self.check_write(name)
        path = os.path.join(self.cur_dir, name)
        os.remove(path)

    def set_mtime(self, name, mtime, size):
        """Set modification time on file."""
        self.check_write(name)
        os.utime(os.path.join(self.cur_dir, name), (-1, mtime))
