# -*- coding: iso-8859-1 -*-
"""
(c) 2012 Martin Wendt; see http://pyftpsync.googlecode.com/
Licensed under the MIT license: http://www.opensource.org/licenses/mit-license.php
"""

from __future__ import print_function

import os
from posixpath import join as join_url, normpath as normurl
from datetime import datetime
import sys
import io
import time
import fnmatch
try:
    from urllib.parse import urlparse
except ImportError:
    # Python 2
    from urlparse import urlparse


DEFAULT_CREDENTIAL_STORE = "pyftpsync.pw"
DRY_RUN_PREFIX = "(DRY-RUN) "
IS_REDIRECTED = (os.fstat(0) != os.fstat(1))


def get_stored_credentials(filename, url):
    """Parse a file in the user's home directory, formatted like:
    
    URL = user:password
    """
    home_path = os.path.expanduser("~")
    file_path = os.path.join(home_path, filename)
    if os.path.isfile(file_path):
        with open(file_path, "rt") as f:
            for line in f:
                line = line.strip()
                if not "=" in line or line.startswith("#") or line.startswith(";"):
                    continue
                u, creds = line.split("=", 1)
                if not creds or u.strip().lower() != url:
                    continue
                creds = creds.strip()
                return creds.split(":", 1)
    return None




#===============================================================================
# make_target
#===============================================================================
def make_target(url, connect=True, debug=1, allow_stored_credentials=True):
    """Factory that creates _Target obejcts from URLs."""
    parts = urlparse(url, allow_fragments=False)
    # scheme is case-insensitive according to http://tools.ietf.org/html/rfc3986
    if parts.scheme.lower() == "ftp":
        creds = parts.username, parts.password
        if not parts.username and allow_stored_credentials:
            sc = get_stored_credentials(DEFAULT_CREDENTIAL_STORE, parts.netloc)
            if sc:
                creds = sc
        from ftpsync import ftp_target
        target = ftp_target.FtpTarget(parts.path, parts.hostname, 
                                      creds[0], creds[1], connect, debug)
    else:
        target = FsTarget(url)

    return target


def to_binary(s):
    """Convert unicode (text strings) to binary data on Python 2 and 3."""
    if sys.version_info[0] < 3:
        # Python 2
        if type(s) is not str:
            s = s.encode("utf8") 
    elif type(s) is str:
        # Python 3
        s = bytes(s, "utf8")
    return s 
    
#def to_text(s):
#    """Convert binary data to unicode (text strings) on Python 2 and 3."""
#    if sys.version_info[0] < 3:
#        # Python 2
#        if type(s) is not str:
#            s = s.encode("utf8") 
#    elif type(s) is str:
#        # Python 3
#        s = bytes(s, "utf8")
#    return s 
    
#===============================================================================
# LogginFileWrapper
# Wrapper around a file for writing to write a hash sign every block.
#===============================================================================
#class LoggingFileWrapper(object):
#    def __init__(self, fp, callback=None):
#        self.fp = fp
#        self.callback = callback or self.default_callback
#        self.bytes = 0
#    
#    def __enter__(self):
#        return self
#
#    def __exit__(self, type, value, tb):
#        self.close()
#
#    @staticmethod
#    def default_callback(wrapper, data):
#        print("#", end="")
#        sys.stdout.flush()
#        
#    def write(self, data):
#        self.bytes += len(data)
#        self.fp.write(data)
#        self.callback(self, data)
#    
#    def close(self):
#        self.fp.close()


#===============================================================================
# _Resource
#===============================================================================
class _Resource(object):
    def __init__(self, target, rel_path, name, size, mtime, unique):
        """
        
        @param target
        @param rel_path
        @param name base name
        @param size file size in bytes
        @param mtime modification time as UTC stamp
        @param uniqe string
        """
        self.target = target
        self.rel_path = rel_path
        self.name = name
        self.size = size
        self.mtime = mtime 
        self.dt_modified = datetime.fromtimestamp(self.mtime)
        self.unique = unique
        self.meta = None

    def __str__(self):
        return "%s('%s', size:%s, modified:%s)" % (self.__class__.__name__, 
                                                   os.path.join(self.rel_path, self.name), 
                                                   self.size, self.dt_modified) #+ " ## %s, %s" % (self.mtime, time.asctime(time.gmtime(self.mtime)))

    def __eq__(self, other):
        raise NotImplementedError

    def get_rel_path(self):
        return normurl(join_url(self.rel_path, self.name))
    
    def is_file(self):
        return False
    
    def is_dir(self):
        return False


#===============================================================================
# FileEntry
#===============================================================================
class FileEntry(_Resource):
    EPS_TIME = 0.1 # 2 seconds difference is considered equal
    
    def __init__(self, target, rel_path, name, size, mtime, unique):
        super(FileEntry, self).__init__(target, rel_path, name, size, mtime, unique)

    @staticmethod
    def _eps_compare(date_1, date_2):
        res = date_1 - date_2
        if abs(res) <= FileEntry.EPS_TIME: # '<=',so eps == 0 works as expected
#             print("DTC: %s, %s => %s" % (date_1, date_2, res))
            return 0
        elif res < 0:
            return -1
        return 1
        
    def __eq__(self, other):
#        if other.get_adjusted_mtime() == self.get_adjusted_mtime() and other.mtime != self.mtime:
#            print("*** Adjusted time match", self, other)
        same_time = self._eps_compare(self.get_adjusted_mtime(), other.get_adjusted_mtime()) == 0
        return (other and other.__class__ == self.__class__ 
                and other.name == self.name and other.size == self.size 
                and same_time)

    def __gt__(self, other):
        time_greater = self._eps_compare(self.get_adjusted_mtime(), other.get_adjusted_mtime()) > 0
        return (other and other.__class__ == self.__class__ 
                and other.name == self.name 
                and time_greater)

    def get_adjusted_mtime(self):
        try:
            res = self.meta["mtime"]
#            print("META: %s reporting %s instead of %s" % (self.name, time.ctime(res), time.ctime(self.mtime)))
            return res
        except:
            return self.mtime
        
    def is_file(self):
        return True


#===============================================================================
# DirectoryEntry
#===============================================================================
class DirectoryEntry(_Resource):
    def __init__(self, target, rel_path, name, size, mtime, unique):
        super(DirectoryEntry, self).__init__(target, rel_path, name, size, mtime, unique)

    def is_dir(self):
        return True


#===============================================================================
# _Target
#===============================================================================
class _Target(object):
    META_FILE_NAME = "_pyftpsync-meta.json"

    def __init__(self, root_dir):
        self.readonly = False
        self.dry_run = False
        self.root_dir = root_dir.rstrip("/")
        self.cur_dir = None
        self.connected = False
        self.save_mode = True
        self.case_sensitive = None # don't know yet
        
    def __del__(self):
        self.close()
        
    def open(self):
        self.connected = True
    
    def close(self):
        self.connected = False
    
    def check_write(self, name):
        """Raise exception if writing cur_dir/name is not allowed."""
        if self.readonly:
            raise RuntimeError("target is read-only: %s + %s / " % (self, name))

    def cwd(self, dir_name):
        raise NotImplementedError
    
    def pwd(self, dir_name):
        raise NotImplementedError
    
    def mkdir(self, dir_name):
        raise NotImplementedError

    def rmdir(self, name):
        """Remove cur_dir/name."""
        raise NotImplementedError

    def flush_meta(self):
        """Write additional meta information for current directory."""
        pass

    def get_dir(self):
        """Return a list of _Resource entries."""
        raise NotImplementedError

    def open_readable(self, name):
        """Return file-like object opened in binary mode for cur_dir/name."""
        raise NotImplementedError

    def read_text(self, name):
        """Read text string from cur_dir/name using open_readable()."""
        with self.open_readable(name) as fp:
            res = fp.getvalue()
            res = res.decode("utf8")
            return res

    def write_file(self, name, fp_src, blocksize=8192, callback=None):
        """Write binary data from file-like to cur_dir/name."""
        raise NotImplementedError

    def write_text(self, name, s):
        """Write string data to cur_dir/name using write_file()."""
        buf = io.BytesIO(to_binary(s))
        self.write_file(name, buf)

    def remove_file(self, name):
        """Remove cur_dir/name."""
        raise NotImplementedError

    def set_mtime(self, name, mtime, size):
        raise NotImplementedError


#===============================================================================
# FsTarget
#===============================================================================
class FsTarget(_Target):
    def __init__(self, root_dir):
        root_dir = os.path.expanduser(root_dir)
        root_dir = os.path.abspath(root_dir)
        if not os.path.isdir(root_dir):
            raise ValueError("%s is not a directory" % root_dir)
        super(FsTarget, self).__init__(root_dir)
        self.open()

    def __str__(self):
        return "<FS:%s + %s>" % (self.root_dir, os.path.relpath(self.cur_dir, self.root_dir))

    def open(self):
        self.connected = True
        self.cur_dir = self.root_dir

    def close(self):
        self.connected = False
        
    def cwd(self, dir_name):
        path = normurl(join_url(self.cur_dir, dir_name))
        if not path.startswith(self.root_dir):
            raise RuntimeError("Tried to navigate outside root %r: %r" % (self.root_dir, path))
        self.cur_dir = path
        return self.cur_dir

    def pwd(self):
        return self.cur_dir

    def mkdir(self, dir_name):
        self.check_write(dir_name)
        path = normurl(join_url(self.cur_dir, dir_name))
        os.mkdir(path)

    def get_dir(self):
        res = []
        for name in os.listdir(self.cur_dir):
            path = os.path.join(self.cur_dir, name)
            stat = os.lstat(path)
#            print(name)
#            print("    mt : %s" % stat.st_mtime)
#            print("    lc : %s" % (time.localtime(stat.st_mtime),))
#            print("       : %s" % time.asctime(time.localtime(stat.st_mtime)))
#            print("    gmt: %s" % (time.gmtime(stat.st_mtime),))
#            print("       : %s" % time.asctime(time.gmtime(stat.st_mtime)))
#
#            utc_stamp = st_mtime_to_utc(stat.st_mtime)
#            print("    utc: %s" % utc_stamp)
#            print("    diff: %s" % ((utc_stamp - stat.st_mtime) / (60*60)))
            # stat.st_mtime is returned as UTC
            mtime = stat.st_mtime
            if os.path.isdir(path):
                res.append(DirectoryEntry(self, self.cur_dir, name, stat.st_size, 
                                          mtime, 
                                          str(stat.st_ino)))
            elif os.path.isfile(path):
                res.append(FileEntry(self, self.cur_dir, name, stat.st_size, 
                                     mtime, 
                                     str(stat.st_ino)))
        return res

    def open_readable(self, name):
        fp = open(os.path.join(self.cur_dir, name), "rb")
        return fp
        
    def write_file(self, name, fp_src, blocksize=8192, callback=None):
        self.check_write(name)
        with open(os.path.join(self.cur_dir, name), "wb") as fp_dst:
            while True:
                data = fp_src.read(blocksize)
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
        self.check_write(name)
        os.utime(os.path.join(self.cur_dir, name), (-1, mtime))


#===============================================================================
# BaseSynchronizer
#===============================================================================
class BaseSynchronizer(object):
    """Synchronizes two target instances in dry_run mode (also base class for other synchonizers)."""
    DEFAULT_EXCLUDES = [".DS_Store",
                        ".git",
                        ".hg",
                        ".svn",
                        _Target.META_FILE_NAME,
                        ]

    def __init__(self, local, remote, options):
        self.local = local
        self.remote = remote
        #TODO: check for self-including paths
        self.options = options or {}
        self.verbose = self.options.get("verbose", 3) 
        self.dry_run = self.options.get("dry_run", True)

        self.include_files = self.options.get("include_files")
        if self.include_files:
            self.include_files = [ pat.strip() for pat in self.include_files.split(",") ]

        self.omit = self.options.get("omit")
        if self.omit:
            self.omit = [ pat.strip() for pat in self.omit.split(",") ]
        
        if self.dry_run:
            self.local.readonly = True
            self.remote.readonly = True
        
        self._stats = {"local_files": 0,
                       "local_dirs": 0,
                       "remote_files": 0,
                       "remote_dirs": 0,
                       "files_created": 0,
                       "files_deleted": 0,
                       "files_written": 0,
                       "dirs_written": 0,
                       "dirs_deleted": 0,
                       "bytes_written": 0,
                       "entries_seen": 0,
                       "entries_touched": 0,
                       "elap": None,
                       "elap_secs": None,
                       }
    
    def get_stats(self):
        return self._stats
    
    def _inc_stat(self, name, ofs=1):
        self._stats[name] = self._stats.get(name, 0) + ofs

    def _match(self, entry):
        name = entry.name
        if name == _Target.META_FILE_NAME:
            return False
#        if name in self.DEFAULT_EXCLUDES:
#            return False
        ok = True
        if entry.is_file() and self.include_files:
            ok = False
            for pat in self.include_files:
                if fnmatch.fnmatch(name, pat):
                    ok = True
                    break
        if ok and self.omit:
            for pat in self.omit:
                if fnmatch.fnmatch(name, pat):
                    ok = False
                    break
        return ok
    
    def run(self):
        start = time.time()
        res = self._sync_dir()
        self._stats["elap_secs"] = time.time() - start
        self._stats["elap"] = "%0.2f sec" % self._stats["elap_secs"]
        return res
    
    def _copy_file(self, src, dest, file_entry):
        # TODO: save replace:
        # 1. remove temp file
        # 2. copy to target.temp
        # 3. use loggingFile for feedback
        # 4. rename target.temp
#        print("_copy_file(%s, %s --> %s)" % (file_entry, src, dest))
        assert isinstance(file_entry, FileEntry)
        self._inc_stat("files_written")
        self._inc_stat("entries_touched")
        self._tick()
        if self.dry_run:
            return self._dry_run_action("copy file (%s, %s --> %s)" % (file_entry, src, dest))
        elif dest.readonly:
            raise RuntimeError("target is read-only: %s" % dest)

        def __block_written(data):
#            print(">(%s), " % len(data))
            self._inc_stat("bytes_written", len(data))

        with src.open_readable(file_entry.name) as fp_src:
            dest.write_file(file_entry.name, fp_src, callback=__block_written)

        dest.set_mtime(file_entry.name, file_entry.mtime, file_entry.size)
    
    def _copy_recursive(self, src, dest, dir_entry):
#        print("_copy_recursive(%s, %s --> %s)" % (dir_entry, src, dest))
        assert isinstance(dir_entry, DirectoryEntry)
        self._inc_stat("entries_touched")
        self._inc_stat("dirs_written")
        self._tick()
        if self.dry_run:
            return self._dry_run_action("copy directory (%s, %s --> %s)" % (dir_entry, src, dest))
        elif dest.readonly:
            raise RuntimeError("target is read-only: %s" % dest)
        src.cwd(dir_entry.name)
        dest.mkdir(dir_entry.name)
        dest.cwd(dir_entry.name)
        for entry in src.get_dir():
            # the outer call was already accompanied by an increment, but not recursions
            self._inc_stat("entries_seen")
            if entry.is_dir():
                self._copy_recursive(src, dest, entry)
            else:
                self._copy_file(src, dest, entry)
        src.cwd("..")
        dest.cwd("..")

    def _remove_file(self, file_entry):
        # TODO: honor backup
#        print("_remove_file(%s)" % (file_entry, ))
        assert isinstance(file_entry, FileEntry)
        self._inc_stat("entries_touched")
        self._inc_stat("files_deleted")
        if self.dry_run:
            return self._dry_run_action("delete file (%s)" % (file_entry,))
        elif file_entry.target.readonly:
            raise RuntimeError("target is read-only: %s" % file_entry.target)
        file_entry.target.remove_file(file_entry.name)

    def _remove_dir(self, dir_entry):
        # TODO: honor backup
        assert isinstance(dir_entry, DirectoryEntry)
        self._inc_stat("entries_touched")
        self._inc_stat("dirs_deleted")
        if self.dry_run:
            return self._dry_run_action("delete directory (%s)" % (dir_entry,))
        elif dir_entry.target.readonly:
            raise RuntimeError("target is read-only: %s" % dir_entry.target)
        dir_entry.target.rmdir(dir_entry.name)

    def _log_call(self, msg, min_level=5):
        if self.verbose >= min_level: 
            print(msg)
        
    def _log_action(self, action, status, symbol, entry, min_level=3):
        if self.verbose < min_level:
            return
        prefix = "" 
        if self.dry_run:
            prefix = DRY_RUN_PREFIX
        if action and status:
            tag = ("%s %s" % (action, status)).upper()
        else:
            tag = ("%s%s" % (action, status)).upper()
        name = entry.get_rel_path()
        if entry.is_dir():
            name = "[%s]" % name
        print("%s%-16s %-2s %s" % (prefix, tag, symbol, name))
        
    def _dry_run_action(self, action):
        """"Called in dry-run mode after call to _log_action() and before exiting function."""
#        print("dry-run", action)
        return
    
    def _test_match_or_print(self, entry):
        """Return True if entry matches filter. Otherwise print 'skip' and return False ."""
        if not self._match(entry):
            self._log_action("skip", "unmatched", "-", entry, min_level=4)
            return False
        return True
    
    def _tick(self):
        """Write progress info and move cursor to beginning of line."""
        if (self.verbose >= 3 and not IS_REDIRECTED) or self.options.get("progress"):
            stats = self.get_stats()
            prefix = DRY_RUN_PREFIX if self.dry_run else ""
            sys.stdout.write("%sTouched %s/%s entries in %s dirs...\r" 
                % (prefix,
                   stats["entries_touched"], stats["entries_seen"], 
                   stats["local_dirs"]))
        sys.stdout.flush()
        return
    
    def _before_sync(self, entry):
        """Called by the synchronizer for each entry. 
        Return False to prevent the synchronizer's default action.
        """
        self._inc_stat("entries_seen")
        self._tick()
        return True
    
    def _sync_dir(self):
        """Traverse the local folder structure and remote peers.
        
        This is the core algorithm that generates calls to self.sync_XXX() 
        handler methods.
        _sync_dir() is called by self.run().
        """
        local_entries = self.local.get_dir()
        local_entry_map = dict(map(lambda e: (e.name, e), local_entries))
        local_files = [e for e in local_entries if isinstance(e, FileEntry)]
        local_directories = [e for e in local_entries if isinstance(e, DirectoryEntry)]
        
        remote_entries = self.remote.get_dir()
        # convert into a dict {name: FileEntry, ...}
        remote_entry_map = dict(map(lambda e: (e.name, e), remote_entries))
        
        # 1. Loop over all local files and classify the relationship to the
        #    peer entries.
        for local_file in local_files:
            self._inc_stat("local_files")
            if not self._before_sync(local_file):
                # TODO: currently, if a file is skipped, it will not be
                # considered for deletion on the peer target
                continue
            # TODO: case insensitive?
            # We should use os.path.normcase() to convert to lowercase on windows
            # (i.e. if the FTP server is based on Windows)
            remote_file = remote_entry_map.get(local_file.name)

            if remote_file is None:
                self.sync_missing_remote_file(local_file)
            elif local_file == remote_file:
                self.sync_equal_file(local_file, remote_file)
            # TODO: renaming could be triggered, if we find an existing
            # entry.unique with a different entry.name
#            elif local_file.key in remote_keys:
#                self._rename_file(local_file, remote_file)
            elif local_file > remote_file:
                self.sync_newer_local_file(local_file, remote_file)
            elif local_file < remote_file:
                self.sync_older_local_file(local_file, remote_file)
            else:
                self._sync_error("file with identical date but different otherwise", 
                                 local_file, remote_file)

        # 2. Handle all local directories that do NOT exist on remote target.
        for local_dir in local_directories:
            self._inc_stat("local_dirs")
            if not self._before_sync(local_dir):
                continue
            remote_dir = remote_entry_map.get(local_dir.name)
            if not remote_dir:
                self.sync_missing_remote_dir(local_dir)

        # 3. Handle all remote entries that do NOT exist on the local target.
        for remote_entry in remote_entries:
            if isinstance(remote_entry, DirectoryEntry):
                self._inc_stat("remote_dirs")
            else:
                self._inc_stat("remote_files")
                
            if not self._before_sync(remote_entry):
                continue
            if not remote_entry.name in local_entry_map:
                if isinstance(remote_entry, DirectoryEntry):
                    self.sync_missing_local_dir(remote_entry)
                else:  
                    self.sync_missing_local_file(remote_entry)
        
        # 4. Let the target provider write it's meta data for the files in the 
        #    current directory.
        self.local.flush_meta()
        self.remote.flush_meta()

        # 5. Finally visit all local sub-directories recursively that also 
        #    exist on the remote target.
        for local_dir in local_directories:
            if not self._before_sync(local_dir):
                continue
            remote_dir = remote_entry_map.get(local_dir.name)
            if remote_dir:
                res = self.sync_equal_dir(local_dir, remote_dir)
                if res is not False:
                    self.local.cwd(local_dir.name)
                    self.remote.cwd(local_dir.name)
                    self._sync_dir()
                    self.local.cwd("..")
                    self.remote.cwd("..")
        
    def _sync_error(self, msg, local_file, remote_file):
        print(msg, local_file, remote_file, file=sys.stderr)
    
    def sync_equal_file(self, local_file, remote_file):
        self._log_call("sync_equal_file(%s, %s)" % (local_file, remote_file))
        self._log_action("", "equal", "=", local_file, min_level=4)
    
    def sync_equal_dir(self, local_dir, remote_dir):
        """Return False to prevent visiting of children"""
        self._log_call("sync_equal_dir(%s, %s)" % (local_dir, remote_dir))
        self._log_action("", "equal", "=", local_dir, min_level=4)
        return True
    
    def sync_newer_local_file(self, local_file, remote_file):
        self._log_call("sync_newer_local_file(%s, %s)" % (local_file, remote_file))
        self._log_action("", "modified", ">", local_file)
    
    def sync_older_local_file(self, local_file, remote_file):
        self._log_call("sync_older_local_file(%s, %s)" % (local_file, remote_file))
        self._log_action("", "modified", "<", local_file)
    
    def sync_missing_local_file(self, remote_file):
        self._log_call("sync_missing_local_file(%s)" % remote_file)
        self._log_action("", "missing", "<", remote_file)
    
    def sync_missing_local_dir(self, remote_dir):
        """Return False to prevent visiting of children"""
        self._log_call("sync_missing_local_dir(%s)" % remote_dir)
        self._log_action("", "missing", "<", remote_dir)
    
    def sync_missing_remote_file(self, local_file):
        self._log_call("sync_missing_remote_file(%s)" % local_file)
        self._log_action("", "new", ">", local_file)
    
    def sync_missing_remote_dir(self, local_dir):
        self._log_call("sync_missing_remote_dir(%s)" % local_dir)
        self._log_action("", "new", ">", local_dir)


#===============================================================================
# UploadSynchronizer
#===============================================================================
class UploadSynchronizer(BaseSynchronizer):
    def __init__(self, local, remote, options):
        super(UploadSynchronizer, self).__init__(local, remote, options)
        local.readonly = True
        # don't set target.readonly to True, because it might have been set to
        # False by a caller to enforce security
#        remote.readonly = False

    def _check_del_unmatched(self, remote_entry):
        """Return True if entry is NOT matched (i.e. excluded by filter).
        
        If --delete-unmatched is on, remove the remote resource. 
        is on.
        
        """
        if not self._match(remote_entry):
            if self.options.get("delete_unmatched"):
                self._log_action("delete", "unmatched", ">", remote_entry)
                if remote_entry.is_dir():
                    self._remove_dir(remote_entry)
                else:
                    self._remove_file(remote_entry)
            else:
                self._log_action("skip", "unmatched", "-", remote_entry, min_level=4)
            return True
        return False

    def sync_equal_file(self, local_file, remote_file):
        self._log_call("sync_equal_file(%s, %s)" % (local_file, remote_file))
        self._log_action("", "equal", "=", local_file, min_level=4)
        self._check_del_unmatched(remote_file)
    
    def sync_equal_dir(self, local_dir, remote_dir):
        """Return False to prevent visiting of children"""
        self._log_call("sync_equal_dir(%s, %s)" % (local_dir, remote_dir))
        if self._check_del_unmatched(remote_dir):
            return False
        self._log_action("", "equal", "=", local_dir, min_level=4)
        return True

    def sync_newer_local_file(self, local_file, remote_file):
        self._log_call("sync_newer_local_file(%s, %s)" % (local_file, remote_file))
        if self._check_del_unmatched(remote_file):
            return False
        self._log_action("copy", "modified", ">", local_file)
        self._copy_file(self.local, self.remote, local_file)
#        if not self._match(remote_file) and self.options.get("delete_unmatched"):
#            self._log_action("delete", "unmatched", ">", remote_file)
#            self._remove_file(remote_file)
#        elif self._test_match_or_print(local_file):
#            self._log_action("copy", "modified", ">", local_file)
#            self._copy_file(self.local, self.remote, local_file)

    def sync_older_local_file(self, local_file, remote_file):
        self._log_call("sync_older_local_file(%s, %s)" % (local_file, remote_file))
        if self._check_del_unmatched(remote_file):
            return False
        elif self.options.get("force"):
            self._log_action("restore", "older", ">", local_file)
            self._copy_file(self.local, self.remote, remote_file)
        else:
            self._log_action("skip", "older", "?", local_file, 4)
#        if not self._match(remote_file) and self.options.get("delete_unmatched"):
#            self._log_action("delete", "unmatched", ">", remote_file)
#            self._remove_file(remote_file)
#        elif self.options.get("force"):
#            self._log_action("restore", "older", ">", local_file)
#            self._copy_file(self.local, self.remote, remote_file)
#        else:
#            self._log_action("skip", "older", "?", local_file, 4)

    def sync_missing_local_file(self, remote_file):
        self._log_call("sync_missing_local_file(%s)" % remote_file)
        # If a file exists locally, but does not match the filter, this will be
        # handled by sync_newer_file()/sync_older_file()
        if self._check_del_unmatched(remote_file):
            return False
        elif not self._test_match_or_print(remote_file):
            return
        elif self.options.get("delete"):
            self._log_action("delete", "missing", ">", remote_file)
            self._remove_file(remote_file)
        else:
            self._log_action("skip", "missing", "?", remote_file, 4)
#        if not self._test_match_or_print(remote_file):
#            return
#        elif self.options.get("delete"):
#            self._log_action("delete", "missing", ">", remote_file)
#            self._remove_file(remote_file)
#        else:
#            self._log_action("skip", "missing", "?", remote_file, 4)

    def sync_missing_local_dir(self, remote_dir):
        self._log_call("sync_missing_local_dir(%s)" % remote_dir)
        if self._check_del_unmatched(remote_dir):
            return False
        elif not self._test_match_or_print(remote_dir):
            return False
        elif self.options.get("delete"):
            self._log_action("delete", "missing", ">", remote_dir)
            self._remove_dir(remote_dir)
        else:
            self._log_action("skip", "missing", "?", remote_dir, 4)
    
    def sync_missing_remote_file(self, local_file):
        self._log_call("sync_missing_remote_file(%s)" % local_file)
        if self._test_match_or_print(local_file):
            self._log_action("copy", "new", ">", local_file)
            self._copy_file(self.local, self.remote, local_file)
    
    def sync_missing_remote_dir(self, local_dir):
        self._log_call("sync_missing_remote_dir(%s)" % local_dir)
        if self._test_match_or_print(local_dir):
            self._log_action("copy", "new", ">", local_dir)
            self._copy_recursive(self.local, self.remote, local_dir)
    

#===============================================================================
# DownloadSynchronizer
#===============================================================================
class DownloadSynchronizer(UploadSynchronizer):
    """
    This download syncronize is implemented as an UploadSynchronizer with
    swapped local and remote targets. 
    """
    def __init__(self, local, remote, options):
        # swap local and remote target
        temp = local
        local = remote
        remote = temp
        # behave like an UploadSynchronizer otherwise
        super(DownloadSynchronizer, self).__init__(local, remote, options)

    def _log_action(self, action, status, symbol, entry, min_level=3):
        if symbol == "<":
            symbol = ">"
        elif symbol == ">":
            symbol = "<"
        super(DownloadSynchronizer, self)._log_action(action, status, symbol, entry, min_level)
