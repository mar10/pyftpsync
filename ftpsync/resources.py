# -*- coding: utf-8 -*-
"""
(c) 2012-2020 Martin Wendt; see https://github.com/mar10/pyftpsync
Licensed under the MIT license: https://www.opensource.org/licenses/mit-license.php
"""
import os
from datetime import datetime
from posixpath import join as join_url, normpath as normpath_url, relpath as relpath_url

from ftpsync.util import eps_compare, write

PRINT_CLASSIFICATIONS = False

ENTRY_CLASSIFICATIONS = frozenset(
    ["existing", "unmodified", "modified", "new", "deleted"]
)

# PAIR_CLASSIFICATIONS = frozenset([
#     "conflict", "equal", "other"
#     ])

PAIR_OPERATIONS = frozenset(
    [
        "conflict",
        "copy_local",
        "copy_remote",
        "delete_local",
        "delete_remote",
        "equal",
        "need_compare",
    ]
)

operation_map = {
    # (local, remote) => operation
    ("missing", "missing"): None,  # Not allowed
    ("missing", "new"): "copy_remote",
    ("missing", "unmodified"): "copy_remote",
    ("missing", "modified"): "copy_remote",
    ("missing", "deleted"): True,  # Nothing to do (only update metadata)
    ("new", "missing"): "copy_local",
    ("new", "new"): "need_compare",
    ("new", "unmodified"): "need_compare",
    ("new", "modified"): "need_compare",
    ("new", "deleted"): "conflict",
    ("unmodified", "missing"): "copy_local",
    ("unmodified", "new"): "need_compare",
    ("unmodified", "unmodified"): "equal",
    ("unmodified", "modified"): "copy_remote",
    ("unmodified", "deleted"): "delete_local",
    ("modified", "missing"): "copy_local",
    ("modified", "new"): "need_compare",
    ("modified", "unmodified"): "copy_local",
    ("modified", "modified"): "conflict",
    ("modified", "deleted"): "conflict",
    ("deleted", "missing"): True,  # Nothing to do (only update metadata)
    ("deleted", "new"): "conflict",
    ("deleted", "unmodified"): "delete_remote",
    ("deleted", "modified"): "conflict",
    ("deleted", "deleted"): True,  # Nothing to do (only update metadata)
    # No meta data available: treat as 'unmodified' in general:
    ("existing", "missing"): "copy_local",
    ("missing", "existing"): "copy_remote",
    ("existing", "existing"): "need_compare",
}


# ===============================================================================
# EntryPair
# ===============================================================================
class EntryPair:
    """"""

    def __init__(self, local, remote):
        self.local = local
        self.remote = remote
        any_entry = local or remote
        assert any_entry
        if local and remote:
            assert local.name == remote.name
            assert local.get_rel_path() == remote.get_rel_path()
            assert local.is_dir() == remote.is_dir()
        #: str:
        self.name = any_entry.name
        #: str:
        self.rel_path = any_entry.get_rel_path()
        #: bool:
        self.is_dir = any_entry.is_dir()
        #: str:
        self.local_classification = None
        #: str:
        self.remote_classification = None
        #: str:
        self.operation = None
        #: str:
        self.re_class_reason = None
        # #: bool:
        # self.was_skipped = None

    def __str__(self):
        s = "<EntryPair({})>: ({}, {}) => {}".format(
            "[{}]".format(self.rel_path) if self.is_dir else self.rel_path,
            self.local_classification,
            self.remote_classification,
            self.operation,
        )
        return s

    @property
    def any_entry(self):
        """Return the local entry (or the remote entry if it is None)."""
        return self.local or self.remote

    def is_conflict(self):
        assert self.operation
        return self.operation == "conflict"

    def is_same_time(self):
        """Return True if local.mtime == remote.mtime."""
        return (
            self.local
            and self.remote
            and FileEntry._eps_compare(self.local.mtime, self.remote.mtime) == 0
        )

    def override_operation(self, operation, reason):
        """Re-Classify entry pair."""
        prev_class = (self.local_classification, self.remote_classification)
        prev_op = self.operation
        assert operation != prev_op
        assert operation in PAIR_OPERATIONS
        if self.any_entry.target.synchronizer.verbose > 3:
            write(
                "override_operation({}, {}) -> {} ({})".format(
                    prev_class, prev_op, operation, reason
                ),
                debug=True,
            )
        self.operation = operation
        self.re_class_reason = reason

    def classify(self, peer_dir_meta):
        """Classify entry pair."""
        assert self.operation is None
        # write("CLASSIFIY", self, peer_dir_meta)
        # Note: We pass False if the entry is not listed in the metadata.
        #       We pass None if we don't have metadata all.
        peer_entry_meta = peer_dir_meta.get(self.name, False) if peer_dir_meta else None
        # write("=>", self, peer_entry_meta)
        if self.local:
            self.local.classify(peer_dir_meta)
            self.local_classification = self.local.classification
        elif peer_entry_meta:
            self.local_classification = "deleted"
        else:
            self.local_classification = "missing"

        if self.remote:
            self.remote.classify(peer_dir_meta)
            self.remote_classification = self.remote.classification
        elif peer_entry_meta:
            self.remote_classification = "deleted"
        else:
            self.remote_classification = "missing"

        c_pair = (self.local_classification, self.remote_classification)

        self.operation = operation_map.get(c_pair)
        if not self.operation:
            raise RuntimeError(
                "Undefined operation for pair classification {}".format(c_pair)
            )

        if PRINT_CLASSIFICATIONS:
            write("classify {}".format(self))
        # if not entry.meta:
        # assert self.classification in PAIR_CLASSIFICATIONS
        assert self.operation in PAIR_OPERATIONS
        return self.operation


# ===============================================================================
# _Resource
# ===============================================================================
class _Resource:
    """Common base class for files and directories."""

    def __init__(self, target, rel_path, name, size, mtime, unique):
        """

        Args:
            target:
            rel_path (str):
            name (str): base name
            size (int): file size in bytes
            mtime (float): modification time as UTC stamp
            uniqe (str): string
        """
        #: :class:`_Target`: Parent target object.
        self.target = target
        #: str: Path relative to :attr:`target`
        self.rel_path = rel_path
        #: str: File name.
        self.name = name
        #: int: Current file size
        self.size = size
        #: float: Current file modification time stamp
        #: (for FTP targets adjusted using metadata information).
        self.mtime = mtime
        # #: datetime: Converted version of :attr:`mtime`.
        # self.dt_modified = datetime.fromtimestamp(self.mtime)
        #: float: Modification time stamp (as reported by source FTP server).
        self.mtime_org = mtime
        # #: datetime: Converted version of :attr:`mtime_org`.
        # self.dt_modified_org = self.mtime_org
        #: str: Unique id of file/directory.
        self.unique = unique
        # #: dict: Additional metadata (set by target.get_dir()).
        # self.meta = None
        #: int: File size at the time of last sync operation
        self.ps_size = None
        #: float: File modification time stamp at the time of last sync operation
        self.ps_mtime = None
        #: float: Time stamp of last sync operation
        self.ps_utime = None
        #: str: (set by synchronizer._classify_entry()).
        self.classification = None

    def __str__(self):
        dt_modified = datetime.fromtimestamp(self.mtime)
        path = os.path.join(self.rel_path, self.name)
        if self.is_dir():
            res = "{}([{}])".format(self.__class__.__name__, path)
        else:
            res = "{}('{}', size:{}, modified:{})".format(
                self.__class__.__name__,
                path,
                "{:,}".format(self.size) if self.size is not None else self.size,
                dt_modified,
            )
            # + " ## %s, %s" % (self.mtime, time.asctime(time.gmtime(self.mtime)))
        if self.classification:
            res += " => {}".format(self.classification)
        return res

    def as_string(self, other_resource=None):
        # dt = datetime.fromtimestamp(self.get_adjusted_mtime())
        dt = datetime.fromtimestamp(self.mtime)
        res = "{}, {:>8,} bytes".format(dt.strftime("%Y-%m-%d %H:%M:%S"), self.size)
        if other_resource:
            comp = []
            if self.mtime < other_resource.mtime:
                comp.append("older")
            elif self.mtime > other_resource.mtime:
                comp.append("newer")

            if self.size < other_resource.size:
                comp.append("smaller")
            elif self.size > other_resource.size:
                comp.append("larger")

            if comp:
                res += " ({})".format(", ".join(comp))
        return res

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

    def get_sync_info(self, key=None):
        return None

    def set_sync_info(self, local_file):
        raise NotImplementedError

    def classify(self, peer_dir_meta):
        """Classify this entry as 'new', 'unmodified', or 'modified'."""
        assert self.classification is None
        peer_entry_meta = None
        if peer_dir_meta:
            # Metadata is generally available, so we can detect 'new' or 'modified'
            peer_entry_meta = peer_dir_meta.get(self.name, False)

            if self.is_dir():
                # Directories are considered 'unmodified' (would require deep traversal
                # to check otherwise)
                if peer_entry_meta:
                    self.classification = "unmodified"
                else:
                    self.classification = "new"
            elif peer_entry_meta:
                # File entries can be classified as modified/unmodified
                self.ps_size = peer_entry_meta.get("s")
                self.ps_mtime = peer_entry_meta.get("m")
                self.ps_utime = peer_entry_meta.get("u")
                if (
                    self.size == self.ps_size
                    and FileEntry._eps_compare(self.mtime, self.ps_mtime) == 0
                ):
                    self.classification = "unmodified"
                else:
                    self.classification = "modified"
            else:
                # A new file entry
                self.classification = "new"
        else:
            # No metadata available:
            if self.is_dir():
                # Directories are considered 'unmodified' (would require deep traversal
                # to check otherwise)
                self.classification = "unmodified"
            else:
                # That's all we know, but EntryPair.classify() may adjust this
                self.classification = "existing"

        if PRINT_CLASSIFICATIONS:
            write("classify {}".format(self))
        assert self.classification in ENTRY_CLASSIFICATIONS
        return self.classification


# ===============================================================================
# FileEntry
# ===============================================================================
class FileEntry(_Resource):

    # 2 seconds difference is considered equal.
    # mtime stamp resolution depends on filesystem: FAT32. 2 seconds, NTFS ms, OSX. 1 sec.
    EPS_TIME = 2.01
    #     EPS_TIME = 0.1

    def __init__(self, target, rel_path, name, size, mtime, unique):
        super(FileEntry, self).__init__(target, rel_path, name, size, mtime, unique)

    @staticmethod
    def _eps_compare(date_1, date_2):
        return eps_compare(date_1, date_2, FileEntry.EPS_TIME)

    def is_file(self):
        return True

    def __eq__(self, other):
        same_time = self._eps_compare(self.mtime, other.mtime) == 0
        return (
            other
            and other.__class__ == self.__class__
            and other.name == self.name
            and other.size == self.size
            and same_time
        )

    def __gt__(self, other):
        time_greater = self._eps_compare(self.mtime, other.mtime) > 0
        return (
            other
            and other.__class__ == self.__class__
            and other.name == self.name
            and time_greater
        )

    def get_sync_info(self, key=None):
        """Get mtime/size when this resource was last synchronized with remote."""
        return self.target.get_sync_info(self.name, key)

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
        return False


# ===============================================================================
# DirectoryEntry
# ===============================================================================
class DirectoryEntry(_Resource):
    def __init__(self, target, rel_path, name, size, mtime, unique):
        super(DirectoryEntry, self).__init__(
            target, rel_path, name, size, mtime, unique
        )
        # Directories don't have a size (that we could reasonably use for classification)
        self.size = 0

    def is_dir(self):
        return True
