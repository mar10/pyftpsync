# -*- coding: iso-8859-1 -*-
"""
(c) 2012-2015 Martin Wendt; see https://github.com/mar10/pyftpsync
Licensed under the MIT license: http://www.opensource.org/licenses/mit-license.php
"""

from __future__ import print_function

from datetime import datetime
import os
from posixpath import join as join_url, normpath as normpath_url, relpath as relpath_url


try:
    from urllib.parse import urlparse
except ImportError:
    # Python 2
    from urlparse import urlparse  # @UnusedImport

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
        self.mtime = mtime  # possibly adjusted using metadata information
        self.dt_modified = datetime.fromtimestamp(self.mtime)
        self.mtime_org = mtime  # as reported by source server
        self.unique = unique
        self.meta = None # Set by target.get_dir()

    def __str__(self):
        return "%s('%s', size:%s, modified:%s)" % (self.__class__.__name__,
                                                   os.path.join(self.rel_path, self.name),
                                                   self.size, self.dt_modified) #+ " ## %s, %s" % (self.mtime, time.asctime(time.gmtime(self.mtime)))

    def as_string(self):
#         dt = datetime.fromtimestamp(self.get_adjusted_mtime())
        dt = datetime.fromtimestamp(self.mtime)
        return "%s, %8s bytes" % (dt.strftime("%Y-%m-%d %H:%M:%S"), self.size)

    def __eq__(self, other):
        raise NotImplementedError

    def get_rel_path(self):
        path = relpath_url(self.target.cur_dir, self.target.root_dir)
        return normpath_url(join_url(path, self.name))

    def is_file(self):
        return False

    def is_dir(self):
        return False

    def is_local(self):
        return self.target.is_local()

    def get_sync_info(self):
        raise NotImplementedError

    def set_sync_info(self, local_file):
        raise NotImplementedError


#===============================================================================
# FileEntry
#===============================================================================
class FileEntry(_Resource):

    # 2 seconds difference is considered equal.
    # mtime stamp resolution depends on filesystem: FAT32. 2 seconds, NTFS ms, OSX. 1 sec.
    EPS_TIME = 2.01
#     EPS_TIME = 0.1

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

    def is_file(self):
        return True

    def __eq__(self, other):
        same_time = self._eps_compare(self.mtime, other.mtime) == 0
        return (other and other.__class__ == self.__class__
                and other.name == self.name and other.size == self.size
                and same_time)

    def __gt__(self, other):
        time_greater = self._eps_compare(self.mtime, other.mtime) > 0
        return (other and other.__class__ == self.__class__
                and other.name == self.name
                and time_greater)

    def get_sync_info(self):
        """Get mtime/size when this resource was last synchronized with remote."""
        return self.target.get_sync_info(self.name)

    def was_modified_since_last_sync(self):
        """Return True if this resource was modified since last sync.

        None is returned if we don't know (because of missing meta data).
        """
        info = self.get_sync_info()
        if not info:
            return None
        if self.size != info["s"]:
            return True
        if self.mtime > info["m"]:
            return True
#         if res:
#             print("%s was_modified_since_last_sync: %s" % (self, (self.get_adjusted_mtime() - self.target.cur_dir_meta.get_last_sync_with(peer_target))))
        return False


#===============================================================================
# DirectoryEntry
#===============================================================================
class DirectoryEntry(_Resource):
    def __init__(self, target, rel_path, name, size, mtime, unique):
        super(DirectoryEntry, self).__init__(target, rel_path, name, size, mtime, unique)

    def is_dir(self):
        return True
