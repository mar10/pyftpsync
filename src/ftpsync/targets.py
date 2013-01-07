# -*- coding: iso-8859-1 -*-
"""
Created on 14.09.2012

@author: Martin Wendt
"""
from __future__ import print_function

import os
from posixpath import join as join_url, normpath as normurl
from datetime import datetime
import sys
import io
import time
try:
    from urllib.parse import urlparse
except ImportError:
    # Python 2
    from urlparse import urlparse


DEFAULT_CREDENTIAL_STORE = "pyftpsync.pw"


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
    def __init__(self, target, rel_path, name, size, mtime, unique):
        super(FileEntry, self).__init__(target, rel_path, name, size, mtime, unique)

    def __eq__(self, other):
#        if other.get_adjusted_mtime() == self.get_adjusted_mtime() and other.mtime != self.mtime:
#            print("*** Adjusted time match", self, other)
        return (other and other.__class__ == self.__class__ 
                and other.name == self.name and other.size == self.size 
                and other.get_adjusted_mtime() == self.get_adjusted_mtime())

    def __gt__(self, other):
        return (other and other.__class__ == self.__class__ 
                and other.name == self.name 
                and self.get_adjusted_mtime() > other.get_adjusted_mtime())

    def get_adjusted_mtime(self):
        try:
            return self.meta["mtime"]
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
        raise NotImplementedError

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

        if self.dry_run:
            self.local.readonly = True
            self.remote.readonly = True
        
        self._stats = {"source_files": 0,
                       "target_files": 0,
                       "created_files": 0,
                       "files_written": 0,
                       "bytes_written": 0,
                       "elap": None,
                       }
    
    def get_stats(self):
        return self._stats
    
    def _inc_stat(self, name, ofs=1):
        self._stats[name] = self._stats.get(name, 0) + ofs
    
    def run(self):
        start = time.time()
        res = self._sync_dir()
        self._stats["elap_secs"] = time.time() - start
        self._stats["elap"] = "%0.2f sec" % self._stats["elap_secs"]
        return res
    
    def _copy_file(self, src, dest, file_entry):
        # 1.remove temp file
        # 2. copy to target.temp
        # 3. use loggingFile for feedback
        # 4. rename target.temp
#        print("_copy_file(%s, %s --> %s)" % (file_entry, src, dest))
        assert isinstance(file_entry, FileEntry)
        if self.dry_run:
            return self._dry_run_action("copy file (%s, %s --> %s)" % (file_entry, src, dest))
        elif dest.readonly:
            raise RuntimeError("target is read-only: %s" % dest)

        def __block_written(data):
#            print(">(%s), " % len(data))
            self._inc_stat("bytes_written", len(data))

        with src.open_readable(file_entry.name) as fp_src:
            dest.write_file(file_entry.name, fp_src, callback=__block_written)

        self._inc_stat("files_written")
        dest.set_mtime(file_entry.name, file_entry.mtime, file_entry.size)
    
    def _copy_recursive(self, src, dest, dir_entry):
#        print("_copy_recursive(%s, %s --> %s)" % (dir_entry, src, dest))
        assert isinstance(dir_entry, DirectoryEntry)
        if self.dry_run:
            return self._dry_run_action("copy dir (%s, %s --> %s)" % (dir_entry, src, dest))
        elif dest.readonly:
            raise RuntimeError("target is read-only: %s" % dest)
        src.cwd(dir_entry.name)
        dest.mkdir(dir_entry.name)
        dest.cwd(dir_entry.name)
        for entry in src.get_dir():
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
        if self.dry_run:
            return self._dry_run_action("delete file (%s)" % (file_entry,))
        elif file_entry.target.readonly:
            raise RuntimeError("target is read-only: %s" % file_entry.target)
        self._inc_stat("removed_files")
        file_entry.target.remove_file(file_entry.name)

    def _remove_dir(self, dir_entry):
        # TODO: honor backup
        assert isinstance(dir_entry, DirectoryEntry)
        if self.dry_run:
            return self._dry_run_action("delete directory (%s)" % (dir_entry,))
        elif dir_entry.target.readonly:
            raise RuntimeError("target is read-only: %s" % dir_entry.target)
        self._inc_stat("removed_folders")
        dir_entry.target.remove_dir(dir_entry.name)

    def _log_call(self, msg, min_level=5):
        if self.verbose >= min_level: 
            print(msg)
        
    def _log_action(self, status, action, entry, min_level=3):
        if self.verbose >= min_level:
            prefix = "" 
            if self.dry_run:
                prefix = "(DRY-RUN) "
            print("%s%-8s %-2s %s" % (prefix, status, action, entry.get_rel_path()))
        
    def _dry_run_action(self, action):
        """"Called in dry-run mode after call to _log_action() and before exiting function."""
#        print("dry-run", action)
        return
    
    def _before_sync(self, entry):
        if entry.name in self.DEFAULT_EXCLUDES:
            self._sync_skip(entry)
            return False
        return True
    
    def _sync_dir(self):
        local_entries = self.local.get_dir()
        local_entry_map = dict(map(lambda e: (e.name, e), local_entries))
        local_files = [e for e in local_entries if isinstance(e, FileEntry)]
        local_directories = [e for e in local_entries if isinstance(e, DirectoryEntry)]
        
        remote_entries = self.remote.get_dir()
        # convert into a dict {name: FileEntry, ...}
        remote_entry_map = dict(map(lambda e: (e.name, e), remote_entries))
        
        self._inc_stat("local_dirs")
        for local_file in local_files:
            self._inc_stat("local_files")
            if not self._before_sync(local_file):
                continue
            # TODO: case insensitive?
            remote_file = remote_entry_map.get(local_file.name)

            if remote_file is None:
                self._sync_missing_remote_file(local_file)
            elif local_file == remote_file:
                self._sync_equal_file(local_file, remote_file)
#            elif local_file.key in remote_keys:
#                self._rename_file(local_file, remote_file)
            elif local_file > remote_file:
                self._sync_newer_local_file(local_file, remote_file)
            elif local_file < remote_file:
                self._sync_older_local_file(local_file, remote_file)
            else:
                self._sync_error("file with identical date but different otherwise", local_file, remote_file)

        for local_dir in local_directories:
            if not self._before_sync(local_dir):
                continue
            remote_dir = remote_entry_map.get(local_dir.name)
            if not remote_dir:
                remote_dir = self._sync_missing_remote_dir(local_dir)

        #
        for remote_entry in remote_entries:
            if not self._before_sync(remote_entry):
                continue
            if not remote_entry.name in local_entry_map:
                if isinstance(remote_entry, DirectoryEntry):
                    self._sync_missing_local_dir(remote_entry)
                else:  
                    self._sync_missing_local_file(remote_entry)
        
        self.local.flush_meta()
        self.remote.flush_meta()

        for local_dir in local_directories:
            if not self._before_sync(local_dir):
                continue
            remote_dir = remote_entry_map.get(local_dir.name)
            if remote_dir:
                self._sync_equal_dir(local_dir, remote_dir)
                self.local.cwd(local_dir.name)
                self.remote.cwd(local_dir.name)
                self._sync_dir()
                self.local.cwd("..")
                self.remote.cwd("..")
                # TODO: check if cwd is still correct
        
    def _sync_error(self, msg, local_file, remote_file):
        print(msg, local_file, remote_file, file=sys.stderr)
    
    def _sync_skip(self, entry):
        self._log_action("SKIP", "?", entry, min_level=4)
    
    def _sync_equal_file(self, local_file, remote_file):
        self._log_call("_sync_equal_file(%s, %s)" % (local_file, remote_file))
        self._log_action("EQUAL", "=", local_file, min_level=4)
    
    def _sync_equal_dir(self, local_dir, remote_dir):
        self._log_call("_sync_equal_dir(%s, %s)" % (local_dir, remote_dir))
        self._log_action("EQUAL", "=", local_dir, min_level=4)
    
    def _sync_newer_local_file(self, local_file, remote_file):
        self._log_call("_sync_newer_local_file(%s, %s)" % (local_file, remote_file))
        self._log_action("MODIFIED", ">", local_file)
    
    def _sync_older_local_file(self, local_file, remote_file):
        self._log_call("_sync_older_local_file(%s, %s)" % (local_file, remote_file))
        self._log_action("MODIFIED", "<", local_file)
    
    def _sync_missing_local_file(self, remote_file):
        self._log_call("_sync_missing_local_file(%s)" % remote_file)
        self._log_action("MISSING", "<", remote_file)
    
    def _sync_missing_local_dir(self, remote_dir):
        self._log_call("_sync_missing_local_dir(%s)" % remote_dir)
        self._log_action("MISSING", "<", remote_dir)
    
    def _sync_missing_remote_file(self, local_file):
        self._log_call("_sync_missing_remote_file(%s)" % local_file)
        self._log_action("NEW", ">", local_file)
    
    def _sync_missing_remote_dir(self, local_dir):
        self._log_call("_sync_missing_remote_dir(%s)" % local_dir)
        self._log_action("NEW", ">", local_dir)
    


#===============================================================================
# UploadSynchronizer
#===============================================================================
class UploadSynchronizer(BaseSynchronizer):
    def __init__(self, local, remote, options):
        super(UploadSynchronizer, self).__init__(local, remote, options)
        local.readonly = True
#        remote.readonly = False
        
    def _sync_newer_local_file(self, local_file, remote_file):
        self._log_call("_sync_newer_local_file(%s, %s)" % (local_file, remote_file))
        self._log_action("MODIFIED", ">", local_file)
        self._copy_file(self.local, self.remote, local_file)
    
    def _sync_older_local_file(self, local_file, remote_file):
        self._log_call("_sync_older_local_file(%s, %s)" % (local_file, remote_file))
        if self.options.get("force"):
            self._log_action("RESTORE", ">", local_file)
            self._copy_file(self.local, self.remote, remote_file)
        else:
            self._log_action("SKIP OLDER", "?", local_file)

    def _sync_missing_local_file(self, remote_file):
        self._log_call("_sync_missing_local_file(%s)" % remote_file)
        if self.options.get("delete"):
            self._log_action("DELETE", ">", remote_file)
            self._remove_file(remote_file)
        else:
            self._log_action("SKIP MISSING", "?", remote_file)
    
    def _sync_missing_local_dir(self, remote_dir):
        self._log_call("_sync_missing_local_dir(%s)" % remote_dir)
        if self.options.get("delete"):
            self._log_action("DELETE", ">", remote_dir)
            self._remove_dir(remote_dir)
        else:
            self._log_action("SKIP MISSING", "?", remote_dir)
    
    def _sync_missing_remote_file(self, local_file):
        self._log_call("_sync_missing_remote_file(%s)" % local_file)
        self._log_action("NEW", ">", local_file)
        self._copy_file(self.local, self.remote, local_file)
    
    def _sync_missing_remote_dir(self, local_dir):
        self._log_call("_sync_missing_remote_dir(%s)" % local_dir)
        self._log_action("NEW", ">", local_dir)
        self._copy_recursive(self.local, self.remote, local_dir)
    

#===============================================================================
# DownloadSynchronizer
#===============================================================================
class DownloadSynchronizer(BaseSynchronizer):
    def __init__(self, local, remote, options):
        super(DownloadSynchronizer, self).__init__(local, remote, options)
#        local.readonly = False
        remote.readonly = True
        
    def _sync_newer_local_file(self, local_file, remote_file):
        self._log_call("_sync_newer_local_file(%s, %s)" % (local_file, remote_file))
        if self.options.get("force"):
            self._log_action("RESTORE", "<", local_file)
            self._copy_file(self.remote, self.local, remote_file)
        else:
            self._log_action("SKIP OLDER", "?", local_file)
    
    def _sync_older_local_file(self, local_file, remote_file):
        self._log_call("_sync_older_local_file(%s, %s)" % (local_file, remote_file))
        self._log_action("MODIFIED", "<", local_file)
        self._copy_file(self.remote, self.local, remote_file)
    
    def _sync_missing_local_file(self, remote_file):
        self._log_call("_sync_missing_local_file(%s)" % remote_file)
        self._log_action("NEW", "<", remote_file)
        self._copy_file(self.remote, self.local, remote_file)
    
    def _sync_missing_local_dir(self, remote_dir):
        self._log_call("_sync_missing_local_dir(%s)" % remote_dir)
        self._log_action("NEW", "<", remote_dir)
        self._copy_recursive(self.remote, self.local, remote_dir)
    
    def _sync_missing_remote_file(self, local_file):
        self._log_call("_sync_missing_remote_file(%s)" % local_file)
        if self.options.get("delete"):
            self._log_action("MISSING", "X <", local_file)
            self._remove_file(local_file)
        else:
            self._log_action("SKIP MISSING", "?", local_file)
    
    def _sync_missing_remote_dir(self, local_dir):
        self._log_call("_sync_missing_remote_dir(%s)" % local_dir)
        if self.options.get("delete"):
            self._log_action("MISSING", "X <", local_dir)
            self._remove_file(local_dir)
        else:
            self._log_action("SKIP MISSING", "?", local_dir)
