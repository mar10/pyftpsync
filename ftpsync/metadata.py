# -*- coding: iso-8859-1 -*-
"""
(c) 2012-2017 Martin Wendt; see https://github.com/mar10/pyftpsync
Licensed under the MIT license: http://www.opensource.org/licenses/mit-license.php
"""

from __future__ import print_function

import json
import os
import sys
import time

from ftpsync import __version__
from ftpsync.util import pretty_stamp, str_to_bool


PYFTPSYNC_VERBOSE_META = str_to_bool(os.environ.get("PYFTPSYNC_VERBOSE_META", False))


class IncompatibleMetadataVersion(RuntimeError):
    """Raised when existing meta data file has an obsolete version number."""


#===============================================================================
# DirMetadata
#===============================================================================
class DirMetadata(object):
    """

    """
    META_FILE_NAME = ".pyftpsync-meta.json"
    LOCK_FILE_NAME = ".pyftpsync-lock.json"
    PRETTY = PYFTPSYNC_VERBOSE_META  # False: Reduce meta file size to 35% (like 3759 -> 1375 bytes)
    VERSION = 2    # Increment if format changes. Old files will be discarded then!

    def __init__(self, target):
        self.target = target
        self.path = target.cur_dir
        self.list = {}
        self.peer_sync = {}
        self.dir = {"mtimes": self.list,
                    "peer_sync": self.peer_sync,
                    }
        #: str: ".pyftpsync-meta.json"
        self.filename = self.META_FILE_NAME
        #: bool: True if a least one FTP file entry time was changed since last read/write
        self.modified_list = False
        #: bool: True if a least one peer data entry was changed since last read/write
        self.modified_sync = False
        #: bool: True if a meta data file was read (valid or not)
        self.was_read = False

    def __str__(self):
        return "DirMetadata<{}>".format(self.get_full_path())

    def get_full_path(self):
        return "/".join((self.path, self.filename))

    def set_mtime(self, filename, mtime, size):
        """Store real file mtime in meta data.

        This is needed on FTP targets, because FTP servers don't allow to set
        file mtime, but use to the upload time instead.
        We also record size and upload time, so we can detect if the file was
        changed by other means and we have to discard our meta data.
        """
        ut = time.time()  # UTC time stamp
        self.list[filename] = {"m": mtime,
                               "s": size,
                               "u": ut,
                               }
        if self.PRETTY:
            self.list[filename].update({
                "mtime_str": pretty_stamp(mtime),
                "uploaded_str": pretty_stamp(ut),
                })
        self.modified_list = True

    def set_sync_info(self, filename, mtime, size):
        """Store mtime/size when local and remote file was last synchronized.

        This is stored in the local file's folder as meta data.
        The information is used to detect conflicts, i.e. if both source and
        remote had been modified by other means since last synchronization.
        """
        assert self.target.is_local()
        remote_target = self.target.peer
        ps = self.dir["peer_sync"].setdefault(remote_target.get_id(), {})
        ut = time.time()  # UTC time stamp
        ps[":last_sync"] = ut  # this is an invalid file name to avoid conflicts
        pse = ps[filename] = {"m": mtime,
                              "s": size,
                              "u": ut,
                              }
        if self.PRETTY:
            ps[":last_sync_str"] = pretty_stamp(ut)  # this is an invalid file name to avoid conflicts
            pse["mtime_str"] = pretty_stamp(mtime) if mtime else "(directory)"
            pse["uploaded_str"] = pretty_stamp(ut)
        self.modified_sync = True

    def remove(self, filename):
        """Remove any data for the given file name."""
        if self.list.pop(filename, None):
            self.modified_list = True
        if self.target.peer:  # otherwise `scan` command
            if self.target.is_local():
                remote_target = self.target.peer
                if remote_target.get_id() in self.dir["peer_sync"]:
                    self.modified_sync = bool(self.dir["peer_sync"][remote_target.get_id()].pop(filename, None))
        return

    def read(self):
        """Initialize self from .pyftpsync-meta.json file."""
        assert self.path == self.target.cur_dir
        try:
            self.modified_list = False
            self.modified_sync = False
            is_valid_file = False

            s = self.target.read_text(self.filename)
            if self.target.synchronizer:
                self.target.synchronizer._inc_stat("meta_bytes_read", len(s))
            self.was_read = True  # True if a file exists (even invalid)
            self.dir = json.loads(s)
            self.list = self.dir["mtimes"]
            self.peer_sync = self.dir["peer_sync"]
            is_valid_file = True
#             print("DirMetadata: read(%s)" % (self.filename, ), self.dir)
        # except IncompatibleMetadataVersion:
        #     raise  # We want version errors to terminate the app
        except Exception as e:
            print("Could not read meta info {}: {!r}".format(self, e), file=sys.stderr)

        # If the version is incompatible, we stop, unless:
        # if --migrate is set, we simply ignore this file (and probably replace it
        # with a current version)
        if is_valid_file and self.dir.get("_file_version", 0) != self.VERSION:
            if not self.target or not self.target.get_option("migrate"):
                raise IncompatibleMetadataVersion(
                    "Invalid meta data version: {} (expected {}).\n"
                    "Consider passing --migrate to discard old data."
                    .format(self.dir.get("_file_version"), self.VERSION))
            #
            print("Migrating meta data version from {} to {} (discarding old): {}"
                .format(self.dir.get("_file_version"), self.VERSION, self.filename))
            self.list = {}
            self.peer_sync = {}

        return

    def flush(self):
        """Write self to .pyftpsync-meta.json."""
        # We DO write meta files even on read-only targets, but not in dry-run mode
#         if self.target.readonly:
#             print("DirMetadata.flush(%s): read-only; nothing to do" % self.target)
#             return
        assert self.path == self.target.cur_dir
        if self.target.dry_run:
#             print("DirMetadata.flush(%s): dry-run; nothing to do" % self.target)
            pass

        elif self.was_read and len(self.list) == 0 and len(self.peer_sync) == 0:
#             print("DirMetadata.flush(%s): DELETE" % self.target)
            self.target.remove_file(self.filename)

        elif not self.modified_list and not self.modified_sync:
#             print("DirMetadata.flush(%s): unmodified; nothing to do" % self.target)
            pass

        else:
            self.dir["_disclaimer"] = "Generated by https://github.com/mar10/pyftpsync"
            self.dir["_time_str"] = pretty_stamp(time.time())
            self.dir["_file_version"] = self.VERSION
            self.dir["_version"] = __version__
            self.dir["_time"] = time.mktime(time.gmtime())
            if self.PRETTY:
                s = json.dumps(self.dir, indent=4, sort_keys=True)
            else:
                s = json.dumps(self.dir, sort_keys=True)
#             print("DirMetadata.flush(%s)" % (self.target, ))#, s)
            self.target.write_text(self.filename, s)
            if self.target.synchronizer:
                self.target.synchronizer._inc_stat("meta_bytes_written", len(s))

        self.modified_list = False
        self.modified_sync = False
