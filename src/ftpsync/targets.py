# -*- coding: iso-8859-1 -*-
'''
Created on 14.09.2012

@author: Wendt
'''
import os
from posixpath import join as join_url
import time
#import collections
from ftplib import FTP
from datetime import datetime
import calendar
from io import StringIO
import sys
import json
#import StringIO

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


#def concat_path(root, rel_path):
#    """Append rel_path to root.
#    
#    I rel_path startswith
#    """
#    if rel_path.startswith("/"):
#        path = rel_path.rtrip("/") + "/"
#    else:
#        assert root.endswith("/")
#        path = root + rel_path.rtrip("/") + "/"
#    if not path.startswith(root):
#        raise RuntimeError("Tried to navigate outside root %r: %r" % (root, path))
#    return path


#def st_mtime_to_utc(t):
#    """Convert a stat.st_mtime stamp to UTC.
#    
#    os.lstat().st_mtime is returned  
#    """
#    assert isinstance(t, float)
#    lc_tuple = time.localtime(t)
#    gt_tuple = time.gmtime(t)
#    gt = time.mktime(gt_tuple)
#    print("t: %s, gt: %s" % (t, gt))
#    return gt


#def utc_stamp_to_local(t):
#    assert isinstance(t, float)
#    gts = time.localtime(t)
#    gt = time.mktime(gts)
#    print("t: %s, gt: %s" % (t, gt))
#    return gt


#===============================================================================
# LogginFileWrapper
# Wrapper around a file for writing to write a hash sign every block.
#===============================================================================
class LogginFileWrapper(object):
    def __init__(self, fp, callback=None):
        self.fp = fp
        self.callback = callback or self.default_callback
        self.bytes = 0
    
    def __enter__(self):
        return self

    def __exit__(self, type, value, tb):
        self.fp.close()

    @staticmethod
    def default_callback(wrapper, data):
        print("#", end="")
        sys.stdout.flush()
        
    def write(self, data):
        self.bytes += len(data)
        self.fp.write(data)
        self.callback(self, data)
    
    def close(self):
        self.fp.close()


#===============================================================================
# FTPDirectory
# @see http://stackoverflow.com/questions/2867217/how-to-delete-files-with-a-python-script-from-a-ftp-server-which-are-older-than/3114477#3114477
#===============================================================================
#FTPDir = collections.namedtuple("FTPDir", "name size mtime tree")
#FTPFile = collections.namedtuple("FTPFile", "name size mtime")
#
#class FTPDirectory(object):
#    def __init__(self, path="."):
#        self.dirs = []
#        self.files = []
#        self.path = path
#
#    def getdata(self, ftpobj):
#        def _addline(line):
#            data, _, name = line.partition("; ")
#            target = size = mtime = None
#            fields = data.split(";")
#            # http://tools.ietf.org/html/rfc3659#page-23
#            # "Size" / "Modify" / "Create" / "Type" / "Unique" / "Perm" / "Lang" / "Media-Type" / "CharSet" / os-depend-fact / local-fact
#            for field in fields:
#                field_name, _, field_value = field.partition("=")
#                field_name = field_name.lower()
#                if field_name == "type":
#                    target = self.dirs if field_value == "dir" else self.files
#                elif field_name in ("sizd", "size"):
#                    size = int(field_value)
#                elif field_name == "modify":
#                    mtime = time.mktime(time.strptime(field_value, "%Y%m%d%H%M%S"))
#            if target is self.files:
#                target.append(FTPFile(name, size, mtime))
#            else:
#                target.append(FTPDir(name, size, mtime, self.__class__(os.path.join(self.path, name))))
#        # raises error_perm, if command is not supported
#        ftpobj.retrlines("MLSD", _addline)
#
#
#    def walk(self):
#        for ftpfile in self.files:
#            yield self.path, ftpfile
#        for ftpdir in self.dirs:
#            for path, ftpfile in ftpdir.tree.walk():
#                yield path, ftpfile
#
#
#class FTPTree(FTPDirectory):
#    def getdata(self, ftpobj):
#        super(FTPTree, self).getdata(ftpobj)
#        for dirname in self.dirs:
#            ftpobj.cwd(dirname.name)
#            dirname.tree.getdata(ftpobj)
#            ftpobj.cwd("..")


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

    def __str__(self):
        return "%s('%s', size:%s, modified:%s)" % (self.__class__.__name__, 
                                                   os.path.join(self.rel_path, self.name), 
                                                   self.size, self.dt_modified) #+ " ## %s, %s" % (self.mtime, time.asctime(time.gmtime(self.mtime)))

#    def __repr__(self):
#        return "%s(%s)" % (self.__class__.__name__, self.name)
    
    def __eq__(self, other):
        raise NotImplementedError

    def get_rel_path(self):
        return join_url(self.rel_path, self.name)
    
    def is_file(self):
        return False
    
    def is_dir(self):
        return False


class FileEntry(_Resource):
    def __init__(self, target, rel_path, name, size, mtime, unique):
        super(FileEntry, self).__init__(target, rel_path, name, size, mtime, unique)

    def __eq__(self, other):
        return other and other.__class__ == self.__class__ and other.name == self.name and other.size == self.size and other.mtime == self.mtime

    def __gt__(self, other):
        return other and other.__class__ == self.__class__ and other.name == self.name and self.mtime > other.mtime

    def is_file(self):
        return True


class DirectoryEntry(_Resource):
    def __init__(self, target, rel_path, name, size, mtime, unique):
        super(DirectoryEntry, self).__init__(target, rel_path, name, size, mtime, unique)

    def is_dir(self):
        return True


#===============================================================================
# _CwdTarget
#===============================================================================
class _CwdTarget(object):
    def __init__(self, target, dir_name):
        self.target = target
        self.dir_name = dir_name
    def __enter__(self):
        self.target.cwd(self.dir_name)
    def __exit__(self):
        self.target.cwd("..")
        
#===============================================================================
# _Target
#===============================================================================
class _Target(object):
    def __init__(self, root_dir):
        self.readonly = True
        self.root_dir = root_dir.rstrip("/")
        self.cur_dir = None
        self.connected = False
        self.save_mode = True
        self.dry_run = True
        self.case_sensitive = None # don't know yet
        
    def __del__(self):
        self.close()
        
    def open(self):
        self.connected = True
    
    def close(self):
        self.connected = False
    
    def check_write(self, name):
        """Raise exception, if writing cur_dir/name is not allowed."""
        if self.readonly:
            raise RuntimeError("target is read-only: %s" % self)

    def cwd(self, dir_name):
        raise NotImplementedError
    
#    def dip(self, dir_name):
#        return _CwdTarget(dir_name)
#    
#    def walk(self):
#        raise NotImplementedError
    
    def flush_meta(self):
        """Write additional meta information for current directory."""
        pass

    def get_dir(self):
        """Return a list of _Resource entries."""
        raise NotImplementedError

    def write_file(self, name, fp):
        """Write data cur_dir/name."""
        raise NotImplementedError

    def open_file(self, name):
        """Open cur_dir/name for reading."""
        raise NotImplementedError

    def remove_file(self, name):
        """Remove cur_dir/name."""
        raise NotImplementedError

    def set_mtime(self, name, mtime):
        raise NotImplementedError


#===============================================================================
# FsTarget
#===============================================================================
class FsTarget(_Target):
    def __init__(self, root_dir):
        root_dir = os.path.abspath(root_dir)
        if not os.path.isdir(root_dir):
            raise ValueError("%s is not a directory" % root_dir)
        super(FsTarget, self).__init__(root_dir)
        self.open()

    def __str__(self):
        return "FS:%s + %s" % (self.root_dir, os.path.relpath(self.cur_dir, self.root_dir))

    def open(self):
        self.connected = True
        self.cur_dir = self.root_dir

    def close(self):
        self.connected = False
        
    def cwd(self, dir_name):
        path = join_url(self.cur_dir, dir_name)
        if not path.startswith(self.root_dir):
            raise RuntimeError("Tried to navigate outside root %r: %r" % (self.root_dir, path))
        self.cur_dir = path
        return self.cur_dir

    def pwd(self):
        return self.cur_dir

    def mkdir(self, dir_name):
        path = join_url(self.cur_dir, dir_name)
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

#    def write_file(self, name, src):
#        """Write data cur_dir/name."""
#        with open(os.path.join(self.cur_dir, name), "wb") as dst:
#            src.write(dst)

    def open_file(self, name):
        """Open cur_dir/name for reading."""
        raise NotImplementedError

    def remove_file(self, name):
        """Remove cur_dir/name."""
        raise NotImplementedError

    def open_writable(self, name):
        fp = open(os.path.join(self.cur_dir, name), "wb")
        return LogginFileWrapper(fp)
        
    def retrbinary(self, name, callback, blocksize=8192):
        """Open cur_dir/name for reading."""
        # TODO: this mimic the FTP interface, but yield seems better
        with open(os.path.join(self.cur_dir, name), "rb") as fp:
            while True:
                data = fp.read(blocksize)
                if not data:
                    break
                callback(data)
        return

    def storefile(self, name, src, blocksize=8192):
        with open(os.path.join(self.cur_dir, name), "wb") as fp:
            while True:
                buf = src.read(blocksize)
                if not buf: 
                    break
                fp.write(buf)
#                if callback: callback(buf)
#        self.ftp.storbinary('STOR %s' % name, fh)
#        fh.close()

    def set_mtime(self, name, mtime):
        os.utime(os.path.join(self.cur_dir, name), (-1, mtime))


#===============================================================================
# FtpTarget
#===============================================================================
class FtpTarget(_Target):
    META_FILE_NAME = ".pyftpsync"
    
    def __init__(self, path, host, username=None, password=None, connect=True, debug=1):
        path = path or "/"
        super(FtpTarget, self).__init__(path)
        self.ftp = FTP()
        self.ftp.debug(debug)
        self.host = host
        self.username = username
        self.password = password
        self.cwd_meta = None
        self.cwd_meta_modified = False
        self.has_old_cwd_meta = None
        if connect:
            self.open()

    def __str__(self):
        return "ftp:%s%s" % (self.host, self.cur_dir)

    def open(self):
        self.ftp.connect(self.host)
        if self.username:
            self.ftp.login(self.username, self.password)
        # TODO: case senstivity?
#        resp = self.ftp.sendcmd("system")
#        self.is_unix = "unix" in resp.lower()
        self.ftp.cwd(self.root_dir)
        pwd = self.ftp.pwd()
        if pwd != self.root_dir:
            raise RuntimeError("Unable to navigate to working directory %r" % self.root_dir)
        self.cur_dir = pwd
        self.connected = True

    def close(self):
        self.ftp.quit()
        self.connected = False
        
    def cwd(self, dir_name):
        path = join_url(self.cur_dir, dir_name)
        if not path.startswith(self.root_dir):
            raise RuntimeError("Tried to navigate outside root %r: %r" % (self.root_dir, path))
        self.ftp.cwd(dir_name)
        self.cur_dir = path
        self.has_old_cwd_meta = None
        self.cwd_meta = None
        return self.cur_dir

    def pwd(self):
        return self.ftp.pwd()

    def flush_meta(self):
        if self.readonly:
            return
        if not self.cwd_meta:
            if self.has_old_cwd_meta:
                self.ftp.delete(self.META_FILE_NAME)
                self.has_old_cwd_meta = False
            return
        fp = json.dump(self.cwd_meta)
        self.ftp.storlines("STOR " + self.META_FILE_NAME, fp)

    def get_dir(self):
        res = []
        self.has_old_cwd_meta = False
        def _addline(line):
            data, _, name = line.partition("; ")
            res_type = size = mtime = unique = None
            fields = data.split(";")
            # http://tools.ietf.org/html/rfc3659#page-23
            # "Size" / "Modify" / "Create" / "Type" / "Unique" / "Perm" / "Lang" / "Media-Type" / "CharSet" / os-depend-fact / local-fact
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
                    mtime = calendar.timegm(time.strptime(field_value, "%Y%m%d%H%M%S"))
                elif field_name == "unique":
                    unique = field_value

            if res_type == "dir":
                res.append(DirectoryEntry(self, self.cur_dir, name, size, mtime, unique))
            elif res_type == "file":
                if name == self.META_FILE_NAME:
                    self.has_old_cwd_meta = True
                else:
                    res.append(FileEntry(self, self.cur_dir, name, size, mtime, unique))
            elif res_type in ("cdir", "pdir"):
                pass
            else:
                raise NotImplementedError
                
        # raises error_perm, if command is not supported
        self.ftp.retrlines("MLSD", _addline)
        
        self.cwd_meta = {}
        if self.has_old_cwd_meta:
            try:
                m = self.ftp.retrlines("RETR " + self.META_FILE_NAME)
                self.cwd_meta = json.loads(m)
                # TODO: remove missing files from cwd_meta, and set cwd_meta_modified in this case 
            except Exception as e:
                print("Could not read meta info: %s" % e)

        return res

#    def write_file(self, name, src):
#        """Write data cur_dir/name."""
#        with open(os.path.join(self.cur_dir, name), "wb") as dst:
#            src.write(dst)

    def open_file(self, name):
        """Open cur_dir/name for reading."""
        out = StringIO()
        self.ftp.retrbinary('RETR %s' % name, out.write)
#        fh.close()
        return out

    def retrbinary(self, name, callback, blocksize=8192):
        """Open cur_dir/name for reading."""
        self.ftp.retrbinary('RETR %s' % name, callback)

    def remove_file(self, name):
        """Remove cur_dir/name."""
        if self.cwd_meta.pop(name, None):
            self.cwd_meta_modified = True
        raise NotImplementedError

    def set_mtime(self, name, mtime):
        # We cannot set the mtime on FTP servers, so we store this as additional
        # meta data in the directory
        self.cwd_meta[name] = {"touch": time.gmtime(), "mtime": mtime}
        self.cwd_meta_modified = True


#===============================================================================
# Synchronizer
#===============================================================================
class Synchronizer(object):
    def __init__(self, local, remote):
        self.local = local
        self.remote = remote
        self._stats = {"source_files": 0,
                       "target_files": 0,
                       "created_files": 0,
                       "files_written": 0,
                       "bytes_written": 0,
                       }
    
    def get_stats(self):
        return self._stats
    
    def _copy_file(self, src, dest, file_entry):
        # 1.remove temp file
        # 2. copy to target.temp
        # 3. use loggingFile for feedback
        # 4. rename target.temp
        print("_copy_file(%s, %s --> %s)" % (file_entry, src, dest))
        assert isinstance(file_entry, FileEntry)
        if dest.readonly:
            raise RuntimeError("target is read-only: %s" % dest)
        with dest.open_writable(file_entry.name) as dst:
            src.retrbinary(file_entry.name, dst.write)
        self._stats["files_written"] += 1
        self._stats["bytes_written"] += src.size
        dest.set_mtime(file_entry.name, file_entry.mtime)
    
    def _copy_recursive(self, src, dest, dir_entry):
        print("_copy_recursive(%s, %s --> %s)" % (dir_entry, src, dest))
        assert isinstance(dir_entry, DirectoryEntry)
        if dest.readonly:
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

    def _log_action(self, status, action, entry):
        print("%-8s %-2s %s" % (status, action, entry.get_rel_path()))
        
    def _sync_equal_file(self, local_file, remote_file):
        print("_sync_equal_file(%s, %s)" % (local_file, remote_file))
        self._log_action("EQUAL", "=", local_file)
    
    def _sync_equal_dir(self, local_dir, remote_dir):
        print("_sync_equal_dir(%s, %s)" % (local_dir, remote_dir))
        self._log_action("EQUAL", "=", local_dir)
    
    def _sync_newer_local(self, local_file, remote_file):
        print("_sync_newer_local(%s, %s)" % (local_file, remote_file))
        self._log_action("MODIFIED", ">", local_file)
    
    def _sync_missing_local_file(self, remote_file):
        print("_sync_missing_local_file(%s)" % remote_file)
        self._log_action("MISSING", "<", remote_file)
        self._copy_file(self.remote, self.local, remote_file)
    
    def _sync_missing_local_dir(self, remote_dir):
        print("_sync_missing_local_dir(%s)" % remote_dir)
        self._log_action("MISSING", "<", remote_dir)
        self._copy_recursive(self.remote, self.local, remote_dir)
    
    def _sync_missing_remote_file(self, local_file):
        print("_sync_missing_remote_file(%s)" % local_file)
        self._log_action("NEW", ">", local_file)
        self._copy_file(self.local, self.remote, local_file)
    
    def _sync_missing_remote_dir(self, local_dir):
        print("_sync_missing_remote_dir(%s)" % local_dir)
        self._log_action("NEW", ">", local_dir)
        self._copy_recursive(self.local, self.remote, local_dir)
    
    def _sync_older_local(self, local_file, remote_file):
        print("_sync_older_local(%s, %s)" % (local_file, remote_file))
        self._log_action("MODIFIED", "<", local_file)
        self._copy_file(self.remote, self.local, remote_file)
    
    def _sync_dir(self):
        local_entries = self.local.get_dir()
        local_entry_map = dict(map(lambda e: (e.name, e), local_entries))
        local_files = [e for e in local_entries if isinstance(e, FileEntry)]
        local_directories = [e for e in local_entries if isinstance(e, DirectoryEntry)]
        
        remote_entries = self.remote.get_dir()
        # convert into a dict {name: FileEntry, ...}
        remote_entry_map = dict(map(lambda e: (e.name, e), remote_entries))
        
        for local_file in local_files:
            # TODO: case insensitive?
            remote_file = remote_entry_map.get(local_file.name)

            if remote_file is None:
                self._sync_missing_remote_file(local_file)
            elif local_file == remote_file:
                self._sync_equal_file(local_file, remote_file)
#            elif local_file.key in remote_keys:
#                self._rename_file(local_file, remote_file)
            elif local_file > remote_file:
                self._sync_newer_local(local_file, remote_file)
            else:
                assert local_file < remote_file
                self._sync_older_local(local_file, remote_file)

        for local_dir in local_directories:
            remote_dir = remote_entry_map.get(local_dir.name)
            if not remote_dir:
                remote_dir = self._sync_missing_remote_dir(local_dir)
            if remote_dir:
                self._sync_equal_dir(local_dir, remote_dir)
                self.local.cwd(local_dir.name)
                self.remote.cwd(local_dir.name)
                self._sync_dir()
                self.local.cwd("..")
                self.remote.cwd("..")
                # TODO: check if cwd is still correct
        
        for remote_entry in remote_entries:
            if not remote_entry.name in local_entry_map:
                if isinstance(remote_entry, DirectoryEntry):
                    self._sync_missing_local_dir(remote_entry)
                else:  
                    self._sync_missing_local_file(remote_entry)
        
        self.local.flush_meta()
        self.remote.flush_meta()

    def upload(self, overwrite=True, backups=False, dry_run=False):
        self._sync_dir()

    def download(self, overwrite=True, backups=False, dry_run=False):
        raise NotImplementedError
