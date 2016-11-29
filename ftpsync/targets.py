# -*- coding: iso-8859-1 -*-
"""
(c) 2012-2016 Martin Wendt; see https://github.com/mar10/pyftpsync
Licensed under the MIT license: http://www.opensource.org/licenses/mit-license.php
"""

from __future__ import print_function

import io
import os
from posixpath import join as join_url, normpath as normpath_url
import shutil
from ftpsync.resources import DirectoryEntry, FileEntry
from ftpsync.util import to_binary, urlparse, DEFAULT_BLOCKSIZE
from ftpsync.metadata import DirMetadata

#===============================================================================
# make_target
#===============================================================================
def make_target(url, extra_opts=None):
    """Factory that creates _Target objects from URLs.

    FTP targets must begin with the scheme ftp:// or ftps:// for TLS.
    TLS is only supported on Python 2.7/3.2+.
    """
#    debug = extra_opts.get("debug", 1)
    parts = urlparse(url, allow_fragments=False)
    # scheme is case-insensitive according to http://tools.ietf.org/html/rfc3986
    scheme = parts.scheme.lower()
    if scheme in ["ftp", "ftps"]:
        creds = parts.username, parts.password
        tls = scheme == "ftps"
        from ftpsync import ftp_target
        target = ftp_target.FtpTarget(parts.path, parts.hostname, parts.port,
                                      username=creds[0], password=creds[1],
                                      tls=tls, timeout=None,
                                      extra_opts=extra_opts)
    else:
        target = FsTarget(url, extra_opts)

    return target


#===============================================================================
# _Target
#===============================================================================
class _Target(object):

    def __init__(self, root_dir, extra_opts):
        if root_dir != "/":
            root_dir = root_dir.rstrip("/")
        self.root_dir = root_dir
        self.extra_opts = extra_opts or {}
        self.readonly = False
        self.dry_run = False
        self.host = None
        self.synchronizer = None # Set by BaseSynchronizer.__init__()
        self.peer = None
        self.cur_dir = None
        self.connected = False
        self.save_mode = True
        self.case_sensitive = None # TODO: don't know yet
        self.time_ofs = None # TODO: don't know yet
        self.support_set_time = None # TODO: don't know yet
        self.cur_dir_meta = DirMetadata(self)
        self.meta_stack = []

    def __del__(self):
        # TODO: http://pydev.blogspot.de/2015/01/creating-safe-cyclic-reference.html
        self.close()

    def get_base_name(self):
        return "%s" % self.root_dir

    def is_local(self):
        return self.synchronizer.local is self

    def get_option(self, key, default=None):
        """Return option from synchronizer (possibly overridden by target extra_opts)."""
        if self.synchronizer:
            return self.extra_opts.get(key, self.synchronizer.options.get(key, default))
        return self.extra_opts.get(key, default)

    def open(self):
        self.connected = True

    def close(self):
        self.connected = False

    def check_write(self, name):
        """Raise exception if writing cur_dir/name is not allowed."""
        if self.readonly and name not in (DirMetadata.META_FILE_NAME, DirMetadata.LOCK_FILE_NAME):
            raise RuntimeError("target is read-only: %s + %s / " % (self, name))

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

    def push_meta(self):
        self.meta_stack.append( self.cur_dir_meta)
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

    def open_readable(self, name):
        """Return file-like object opened in binary mode for cur_dir/name."""
        raise NotImplementedError

    def read_text(self, name):
        """Read text string from cur_dir/name using open_readable()."""
        with self.open_readable(name) as fp:
            res = fp.read()  # StringIO or file object
#             try:
#                 res = fp.getvalue()  # StringIO returned by FtpTarget
#             except AttributeError:
#                 res = fp.read()  # file object returned by FsTarget
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
        # print("%s.remove_sync_info(%s): nothing to do" % (self, name))
        return


#===============================================================================
# FsTarget
#===============================================================================

class FsTarget(_Target):
    def __init__(self, root_dir, extra_opts=None):
        root_dir = os.path.expanduser(root_dir)
        root_dir = os.path.abspath(root_dir)
        if not os.path.isdir(root_dir):
            raise ValueError("%s is not a directory" % root_dir)
        super(FsTarget, self).__init__(root_dir, extra_opts)
        self.open()

    def __str__(self):
        return "<FS:%s + %s>" % (self.root_dir, os.path.relpath(self.cur_dir, self.root_dir))

    def open(self):
        self.connected = True
        self.cur_dir = self.root_dir

    def close(self):
        self.connected = False

    def cwd(self, dir_name):
        path = normpath_url(join_url(self.cur_dir, dir_name))
        if not path.startswith(self.root_dir):
            raise RuntimeError("Tried to navigate outside root %r: %r" % (self.root_dir, path))
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
#         print("REMOVE %r" % path)
        shutil.rmtree(path)

    def flush_meta(self):
        """Write additional meta information for current directory."""
        if self.cur_dir_meta:
            self.cur_dir_meta.flush()

    def get_dir(self):
        res = []
#        self.cur_dir_meta = None
        self.cur_dir_meta = DirMetadata(self)
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
                if name == DirMetadata.META_FILE_NAME:
                    self.cur_dir_meta.read()
                elif not name in (DirMetadata.DEBUG_META_FILE_NAME, ):
                    res.append(FileEntry(self, self.cur_dir, name, stat.st_size,
                                         mtime,
                                         str(stat.st_ino)))
        return res

    def open_readable(self, name):
        fp = open(os.path.join(self.cur_dir, name), "rb")
        return fp

    def write_file(self, name, fp_src, blocksize=DEFAULT_BLOCKSIZE, callback=None):
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
        """Set modification time on file."""
        self.check_write(name)
        os.utime(os.path.join(self.cur_dir, name), (-1, mtime))
