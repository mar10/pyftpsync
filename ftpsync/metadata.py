# -*- coding: utf-8 -*-
"""
(c) 2012-2020 Martin Wendt; see https://github.com/mar10/pyftpsync
Licensed under the MIT license: https://www.opensource.org/licenses/mit-license.php
"""

import json
import time

from ftpsync import __version__
from ftpsync.util import (
    get_option,
    pretty_stamp,
    str_to_bool,
    write,
    write_error,
    make_native_dict_keys,
)

PYFTPSYNC_VERBOSE_META = str_to_bool(
    get_option("PYFTPSYNC_VERBOSE_META", "debug", "verbose_meta", False)
)


class IncompatibleMetadataVersion(RuntimeError):
    """Raised when existing meta data file has an obsolete version number."""


# ===============================================================================
# DirMetadata
# ===============================================================================
class DirMetadata:
    """"""

    META_FILE_NAME = ".pyftpsync-meta.json"
    LOCK_FILE_NAME = ".pyftpsync-lock.json"
    # False: Reduce file size to 35% (like 3759 -> 1375 bytes)
    PRETTY = PYFTPSYNC_VERBOSE_META
    # Increment file version if format changes. Old files will be discarded then!
    # v1: Initial version
    # v2: Since v2.0: Change data structure
    # v3: Since v3.0: Use utf-8 with ensure_ascii=False
    VERSION = 3

    def __init__(self, target):
        self.target = target
        self.path = target.cur_dir
        self.list = {}
        self.peer_sync = {}
        self.dir = {"mtimes": self.list, "peer_sync": self.peer_sync}
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
        if self.target.server_time_ofs:
            # We add the estimated time offset, so the stored 'u' time stamp matches
            # better the mtime value that the server will generate for that file
            ut += self.target.server_time_ofs

        self.list[filename] = {"m": mtime, "s": size, "u": ut}
        if self.PRETTY:
            self.list[filename].update(
                {"mtime_str": pretty_stamp(mtime), "uploaded_str": pretty_stamp(ut)}
            )
        # print("set_mtime", self.list[filename])
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
        pse = ps[filename] = {"m": mtime, "s": size, "u": ut}
        if self.PRETTY:
            ps[":last_sync_str"] = pretty_stamp(
                ut
            )  # use an invalid file name to avoid conflicts
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
                    rid = remote_target.get_id()
                    self.modified_sync = bool(
                        self.dir["peer_sync"][rid].pop(filename, None)
                    )
        return

    def read(self):
        """Initialize self from .pyftpsync-meta.json file."""
        assert self.path == self.target.cur_dir
        try:
            self.modified_list = False
            self.modified_sync = False
            is_valid_file = False

            s = self.target.read_text(self.filename)
            # print("s", s)
            if self.target.synchronizer:
                self.target.synchronizer._inc_stat("meta_bytes_read", len(s))
            self.was_read = True  # True if a file exists (even invalid)
            self.dir = json.loads(s)
            # import pprint
            # print("dir")
            # print(pprint.pformat(self.dir))
            self.dir = make_native_dict_keys(self.dir)
            # print(pprint.pformat(self.dir))
            self.list = self.dir["mtimes"]
            self.peer_sync = self.dir["peer_sync"]
            is_valid_file = True
            # write"DirMetadata: read(%s)" % (self.filename, ), self.dir)
        # except IncompatibleMetadataVersion:
        #     raise  # We want version errors to terminate the app
        except Exception as e:
            write_error("Could not read meta info {}: {!r}".format(self, e))

        # If the version is incompatible, we stop, unless:
        # if --migrate is set, we simply ignore this file (and probably replace it
        # with a current version)
        if is_valid_file and self.dir.get("_file_version", 0) != self.VERSION:
            if not self.target or not self.target.get_option("migrate"):
                raise IncompatibleMetadataVersion(
                    "Invalid meta data version: {} (expected {}).\n"
                    "Consider passing --migrate to discard old data.".format(
                        self.dir.get("_file_version"), self.VERSION
                    )
                )
            #
            write(
                "Migrating meta data version from {} to {} (discarding old): {}".format(
                    self.dir.get("_file_version"), self.VERSION, self.filename
                )
            )
            self.list = {}
            self.peer_sync = {}

        return

    def flush(self):
        """Write self to .pyftpsync-meta.json."""
        # We DO write meta files even on read-only targets, but not in dry-run mode
        # if self.target.readonly:
        #     write("DirMetadata.flush(%s): read-only; nothing to do" % self.target)
        #     return
        assert self.path == self.target.cur_dir
        if self.target.dry_run:
            # write("DirMetadata.flush(%s): dry-run; nothing to do" % self.target)
            pass

        elif self.was_read and len(self.list) == 0 and len(self.peer_sync) == 0:
            write("Remove empty meta data file: {}".format(self.target))
            self.target.remove_file(self.filename)

        elif not self.modified_list and not self.modified_sync:
            # write("DirMetadata.flush(%s): unmodified; nothing to do" % self.target)
            pass

        else:
            self.dir["_disclaimer"] = "Generated by https://github.com/mar10/pyftpsync"
            self.dir["_time_str"] = pretty_stamp(time.time())
            self.dir["_file_version"] = self.VERSION
            self.dir["_version"] = __version__
            self.dir["_time"] = time.mktime(time.gmtime())

            # We always save utf-8 encoded.
            # `ensure_ascii` would escape all bytes >127 as `\x12` or `\u1234`,
            # which makes it hard to read, so we set it to false.
            # `sort_keys` converts binary keys to unicode using utf-8, so we
            # must make sure that we don't pass cp1225 or other encoded data.
            data = self.dir
            opts = {"indent": 4, "sort_keys": True, "ensure_ascii": False}

            # if compat.PY2:
            #     # The `encoding` arg defaults to utf-8 on Py2 and was removed in Py3
            #     # opts["encoding"] = "utf-8"
            #     # Python 2 has problems with mixed keys (str/unicode)
            #     data = decode_dict_keys(data, "utf-8")

            if not self.PRETTY:
                opts["indent"] = None
                opts["separators"] = (",", ":")

            s = json.dumps(data, **opts)

            self.target.write_text(self.filename, s)
            if self.target.synchronizer:
                self.target.synchronizer._inc_stat("meta_bytes_written", len(s))

        self.modified_list = False
        self.modified_sync = False
