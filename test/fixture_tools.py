# -*- coding: UTF-8 -*-
"""
Tests for pyftpsync
"""
from __future__ import print_function

import calendar
import datetime
import os
from pprint import pprint
import shutil
import tempfile
import unittest

from ftpsync.targets import FsTarget
from ftpsync.synchronizers import BiDirSynchronizer
from ftpsync.metadata import DirMetadata
from ftpsync.util import to_str


PYFTPSYNC_TEST_FOLDER = os.environ.get("PYFTPSYNC_TEST_FOLDER") or tempfile.mkdtemp()
PYFTPSYNC_TEST_FTP_URL = os.environ.get("PYFTPSYNC_TEST_FTP_URL")
STAMP_20140101_120000 = 1388577600.0  # Wed, 01 Jan 2014 12:00:00 GMT

# dt = datetime.datetime.strptime("2014-01-01 12:00:00", "%Y-%m-%d %H:%M:%S")
# stamp = calendar.timegm(dt.timetuple())
# print(stamp)  # --> 1388577600
# 1/0

def _write_test_file(name, size=None, content=None, dt=None, age=None):
    """Create a file inside the temporary folder, optionally creating subfolders.

    `name` must use '/' as path separator, even on Windows.
    """
    path = os.path.join(PYFTPSYNC_TEST_FOLDER, name.replace("/", os.sep))
    if "/" in name:
        parent_dir = os.path.dirname(path)
        if not os.path.isdir(parent_dir):
            os.makedirs(parent_dir)


    with open(path, "wt") as f:
        if content is None:
            if size is None:
                f.write(name)
            else:
                f.write("*" * size)
        else:
            assert size is None
            f.write(content)
    if age:
        assert dt is None
        dt = datetime.datetime.now() - datetime.timedelta(seconds=age)
    if dt:
        if isinstance(dt, str):
            dt = datetime.datetime.strptime(dt, "%Y-%m-%d %H:%M:%S")
        stamp = calendar.timegm(dt.timetuple())
        date = (stamp, stamp)
        os.utime(path, date)
    return

def _touch_test_file(name, dt=None, ofs_sec=None):
    """Set file access and modification time to `date` (default: now)."""
    path = os.path.join(PYFTPSYNC_TEST_FOLDER, name.replace("/", os.sep))
    if dt is not None:
        if isinstance(dt, str):
            dt = datetime.datetime.strptime(dt, "%Y-%m-%d %H:%M:%S")
        stamp = calendar.timegm(dt.timetuple())
        dt = (stamp, stamp)
    os.utime(path, dt)

def _get_test_file_date(name):
    path = os.path.join(PYFTPSYNC_TEST_FOLDER, name.replace("/", os.sep))
    stat = os.lstat(path)
    return stat.st_mtime

def _read_test_file(name):
    path = os.path.join(PYFTPSYNC_TEST_FOLDER, name.replace("/", os.sep))
    with open(path, "rb") as f:
        return f.readall()

def _is_test_file(name):
    path = os.path.join(PYFTPSYNC_TEST_FOLDER, name.replace("/", os.sep))
    return os.path.isfile(path)

def _remove_test_file(name):
    path = os.path.join(PYFTPSYNC_TEST_FOLDER, name.replace("/", os.sep))
    assert os.path.isfile(path)
    return os.remove(path)

def _remove_test_folder(name):
    path = os.path.join(PYFTPSYNC_TEST_FOLDER, name.replace("/", os.sep))
    assert os.path.isdir(path)
    shutil.rmtree(path)

def _empty_folder(folder_path):
    """Remove all files and subfolders, but leave the empty parent intact."""
    for file_object in os.listdir(folder_path):
        file_object_path = os.path.join(folder_path, file_object)
        if os.path.isfile(file_object_path):
            os.unlink(file_object_path)
        else:
            shutil.rmtree(file_object_path)

def _delete_metadata(folder_path, recursive=True):
    """Remove all .pyftpsync-meta.json files."""
    for file_object in os.listdir(folder_path):
        file_object_path = os.path.join(folder_path, file_object)
        if file_object == DirMetadata.META_FILE_NAME:
            print("Remove {}".format(file_object_path))
            os.unlink(file_object_path)
        elif recursive and os.path.isdir(file_object_path):
            _delete_metadata(file_object_path, recursive)
    return

def _get_test_folder(folder_name):
    """"Convert test folder content to dict for comparisons."""
#     root_path = os.path.join(PYFTPSYNC_TEST_FOLDER, folder_name.replace("/", os.sep))
    file_map = {}
    root_folder = os.path.join(PYFTPSYNC_TEST_FOLDER, folder_name)
    def __scan(rel_folder_path):
        abs_folder_path = os.path.join(root_folder, rel_folder_path)
        for fn in os.listdir(abs_folder_path):
            if fn.startswith("."):  # or fn == DirMetadata.DEBUG_META_FILE_NAME:
                continue
            abs_file_path = os.path.join(abs_folder_path, fn)
            if os.path.isdir(abs_file_path):
                __scan(os.path.join(rel_folder_path, fn))
                continue
            stat = os.lstat(abs_file_path)
            dt = datetime.datetime.utcfromtimestamp(stat.st_mtime)
            rel_file_path = os.path.join(rel_folder_path, fn).replace(os.sep, "/")
            file_map[rel_file_path] = {
                            "date": dt.strftime("%Y-%m-%d %H:%M:%S"),
                            #"size": stat.st_size,
                            }
            with open(abs_file_path, "rb") as fp:
                file_map[rel_file_path]["content"] = to_str(fp.read())
    __scan("")
    return file_map


# def prepare_test_folder(path, files):
#     _empty_folder(path)
#     for f in files:
#         pass

def _sync_test_folders(synchronizer_class, options):
    """Run bi-dir sync with fresh objects."""
    local = FsTarget(os.path.join(PYFTPSYNC_TEST_FOLDER, "local"))
    remote = FsTarget(os.path.join(PYFTPSYNC_TEST_FOLDER, "remote"))
    opts = {"dry_run": False, "verbose": 1}
    if options:
        opts.update(options)

    s = synchronizer_class(local, remote, opts)
    s.run()
    return s.get_stats()


#===============================================================================
# _SyncTestBase
#===============================================================================

class _SyncTestBase(unittest.TestCase):
    """Test BiDirSynchronizer on file system targets with different resolve modes."""
    
    local_fixture_unmodified = {
        'file1.txt': {'content': 'local1', 'date': '2014-01-01 12:00:00'},
        'file2.txt': {'content': 'local2', 'date': '2014-01-01 12:00:00'},
        'file3.txt': {'content': 'local3', 'date': '2014-01-01 12:00:00'},
        'file4.txt': {'content': 'local4', 'date': '2014-01-01 12:00:00'},
        'file5.txt': {'content': 'local5', 'date': '2014-01-01 12:00:00'},
        'file6.txt': {'content': 'local6', 'date': '2014-01-01 12:00:00'},
        'file7.txt': {'content': 'local7', 'date': '2014-01-01 12:00:00'},
        'file8.txt': {'content': 'local8', 'date': '2014-01-01 12:00:00'},
        'file9.txt': {'content': 'local9', 'date': '2014-01-01 12:00:00'},
        'folder1/file1_1.txt': {'content': 'local1_1', 'date': '2014-01-01 12:00:00'},
        'folder2/file2_1.txt': {'content': 'local2_1', 'date': '2014-01-01 12:00:00'},
        'folder3/file3_1.txt': {'content': 'local3_1', 'date': '2014-01-01 12:00:00'},
        'folder4/file4_1.txt': {'content': 'local4_1', 'date': '2014-01-01 12:00:00'},
        'folder5/file5_1.txt': {'content': 'local5_1', 'date': '2014-01-01 12:00:00'},
        'folder6/file6_1.txt': {'content': 'local6_1', 'date': '2014-01-01 12:00:00'},
        'folder7/file7_1.txt': {'content': 'local7_1', 'date': '2014-01-01 12:00:00'},
        }

    local_fixture_modified = {
        'file1.txt': {'content': 'local1', 'date': '2014-01-01 12:00:00'},
        'file2.txt': {'content': 'local 13:00', 'date': '2014-01-01 13:00:00'},
        'file4.txt': {'content': 'local4', 'date': '2014-01-01 12:00:00'},
        'file5.txt': {'content': 'local5', 'date': '2014-01-01 12:00:00'},
        'file6.txt': {'content': 'local 13:00', 'date': '2014-01-01 13:00:00'},
        'file7.txt': {'content': 'local 13:00:05', 'date': '2014-01-01 13:00:05'},
        'file9.txt': {'content': 'local 13:00', 'date': '2014-01-01 13:00:00'},
        'folder1/file1_1.txt': {'content': 'local1_1', 'date': '2014-01-01 12:00:00'},
        'folder2/file2_1.txt': {'content': 'local 13:00', 'date': '2014-01-01 13:00:00'},
        'folder5/file5_1.txt': {'content': 'local5_1', 'date': '2014-01-01 12:00:00'},
        'folder6/file6_1.txt': {'content': 'local6_1', 'date': '2014-01-01 12:00:00'},
        'folder7/file7_1.txt': {'content': 'local 13:00', 'date': '2014-01-01 13:00:00'},
        'new_file1.txt': {'content': 'local 13:00', 'date': '2014-01-01 13:00:00'},
        'new_file3.txt': {'content': 'local 13:00', 'date': '2014-01-01 13:00:00'},
        'new_file4.txt': {'content': 'local 13:00', 'date': '2014-01-01 13:00:00'},
        'new_file5.txt': {'content': 'local 13:00', 'date': '2014-01-01 13:00:00'},
        'new_file6.txt': {'content': 'local 13:00:05', 'date': '2014-01-01 13:00:05'},
        }

    remote_fixture_modified = {
        'file1.txt': {'content': 'local1', 'date': '2014-01-01 12:00:00'},
        'file2.txt': {'content': 'local2', 'date': '2014-01-01 12:00:00'},
        'file3.txt': {'content': 'local3', 'date': '2014-01-01 12:00:00'},
        'file4.txt': {'content': 'remote 13:00', 'date': '2014-01-01 13:00:00'},
        'file6.txt': {'content': 'remote 13:00:05', 'date': '2014-01-01 13:00:05'},
        'file7.txt': {'content': 'remote 13:00', 'date': '2014-01-01 13:00:00'},
        'file8.txt': {'content': 'remote 13:00', 'date': '2014-01-01 13:00:00'},
        'folder1/file1_1.txt': {'content': 'local1_1', 'date': '2014-01-01 12:00:00'},
        'folder2/file2_1.txt': {'content': 'local2_1', 'date': '2014-01-01 12:00:00'},
        'folder3/file3_1.txt': {'content': 'local3_1', 'date': '2014-01-01 12:00:00'},
        'folder4/file4_1.txt': {'content': 'remote 13:00', 'date': '2014-01-01 13:00:00'},
        'folder5/file5_1.txt': {'content': 'remote 13:00', 'date': '2014-01-01 13:00:00'},
        'new_file2.txt': {'content': 'remote 13:00', 'date': '2014-01-01 13:00:00'},
        'new_file3.txt': {'content': 'local 13:00', 'date': '2014-01-01 13:00:00'},
        'new_file4.txt': {'content': 'remote 13:00 with other content', 'date': '2014-01-01 13:00:00'},
        'new_file5.txt': {'content': 'remote 13:00:05', 'date': '2014-01-01 13:00:05'},
        'new_file6.txt': {'content': 'remote 13:00', 'date': '2014-01-01 13:00:00'},
        }

    def setUp(self):
        self._prepare_initial_synced_fixture()
        self.maxDiff = None # do not trunkate Dict diffs

    def tearDown(self):
        pass

    def _prepare_initial_local_fixture(self):
        """
        Create a local folder that has some files and folders with defined mtimes.

        The remote folder is empty. No meta data created yet.

                                  Local           Remote
          file1.txt               12:00           -
          file2.txt               12:00           -
          file3.txt               12:00           -
          file4.txt               12:00           -
          file5.txt               12:00           -
          file6.txt               12:00           -
          file7.txt               12:00           -
          file8.txt               12:00           -
          file9.txt               12:00           -
          folder1/file1_1.txt     12.00           -
          folder2/file2_1.txt     12:00           -
          folder3/file3_1.txt     12:00           -
          folder4/file4_1.txt     12:00           -
          folder5/file5_1.txt     12:00           -
          folder6/file6_1.txt     12:00           -
          folder7/file7_1.txt     12:00           -
        """
        assert os.path.isdir(PYFTPSYNC_TEST_FOLDER), "Invalid folder: {}".format(PYFTPSYNC_TEST_FOLDER)
        # Reset all
        _empty_folder(PYFTPSYNC_TEST_FOLDER)
        # Add some files to ../local/
        dt = "2014-01-01 12:00:00"
        for i in range(1, 10):
            _write_test_file("local/file{}.txt".format(i), dt=dt,
                             content="local{}".format(i))

        _write_test_file("local/folder1/file1_1.txt", dt=dt, content="local1_1")
        _write_test_file("local/folder2/file2_1.txt", dt=dt, content="local2_1")
        _write_test_file("local/folder3/file3_1.txt", dt=dt, content="local3_1")
        _write_test_file("local/folder4/file4_1.txt", dt=dt, content="local4_1")
        _write_test_file("local/folder5/file5_1.txt", dt=dt, content="local5_1")
        _write_test_file("local/folder6/file6_1.txt", dt=dt, content="local6_1")
        _write_test_file("local/folder7/file7_1.txt", dt=dt, content="local7_1")

        # Create empty ../remote/
        os.mkdir(os.path.join(PYFTPSYNC_TEST_FOLDER, "remote"))
        return

    def _prepare_initial_synced_fixture(self):
        """Create two folders that have already been sync'ed (so meta data is available).

                                  Local           Remote
          file1.txt               12:00           12:00
          file2.txt               12:00           12:00
          file3.txt               12:00           12:00
          file4.txt               12:00           12:00
          file5.txt               12:00           12:00
          file6.txt               12:00           12:00
          file7.txt               12:00           12:00
          file8.txt               12:00           12:00
          file9.txt               12:00           12:00
          folder1/file1_1.txt     12.00           12:00
          folder2/file2_1.txt     12:00           12:00
          folder3/file3_1.txt     12:00           12:00
          folder4/file4_1.txt     12:00           12:00
          folder5/file5_1.txt     12:00           12:00
          folder6/file6_1.txt     12:00           12:00
          folder7/file7_1.txt     12:00           12:00
        """
        self._prepare_initial_local_fixture()

        # Synchronize folders (also creates meta data files)
        opts = {"dry_run": False, "verbose": 0}
        stats = _sync_test_folders(BiDirSynchronizer, opts)

        assert stats["files_written"] == 16
        assert stats["dirs_created"] == 7
        return

    def _prepare_modified_fixture(self):
        """Modify both folders and run sync with specific options.

        1. The setUp() code initializes local & remote with 12 files in 5 folders:

                                  Local           Remote
          file?.txt               12:00           12:00
          ...

        2. Metadata was also created accordingly.

        3. Now we simulate user modifications on both targets:

                                  Local           Remote
          ------------------------------------------------------------------------------
          file1.txt               12:00           12:00        (unmodified)
          file2.txt               13:00           12:00
          file3.txt                 x             12:00
          file4.txt               12:00           13:00
          file5.txt               12:00             x
          file6.txt               13:00           13:00:05     CONFLICT!
          file7.txt               13:00:05        13:00        CONFLICT!
          file8.txt                 x             13:00        CONFLICT!
          file9.txt               13:00             x          CONFLICT!

          folder1/file1_1.txt     12.00           12:00        (unmodified)
          folder2/file2_1.txt     13.00           12:00
          folder3/file3_1.txt       x             12:00        (folder deleted)
          folder4/file4_1.txt       x             13:00        (*) undetected CONFLICT!
          folder5/file5_1.txt     12:00           13:00
          folder6/file6_1.txt     12:00             x          (folder deleted)
          folder7/file7_1.txt     13:00             x          (*) undetected CONFLICT!

          new_file1.txt           13:00             -
          new_file2.txt             -             13:00
          new_file3.txt           13:00           13:00        (same size)
          new_file4.txt           13:00           13:00        CONFLICT! (different size)
          new_file5.txt           13:00           13:00:05     CONFLICT!
          new_file6.txt           13:00:05        13:00        CONFLICT!

          NOTE: (*) currently conflicts are NOT detected, when a file is edited on one
                    target and the parent folder is removed on the peer target.
                    The folder will be removed on sync!

        4. Finally we call bi-dir sync with the custom options and return runtime stats.
        """
        # This method assumes that _prepare_initial_synced_fixture() was already run
        # (which is done by the setUp().)
        assert _get_test_file_date("remote/folder5/file5_1.txt") == STAMP_20140101_120000

        # Change, remove, and add local only
        _write_test_file("local/file2.txt", dt="2014-01-01 13:00:00", content="local 13:00")
        _remove_test_file("local/file3.txt")
        _write_test_file("remote/file4.txt", dt="2014-01-01 13:00:00", content="remote 13:00")
        _remove_test_file("remote/file5.txt")
        # Conflict: changed local and remote, remote is newer
        _write_test_file("local/file6.txt", dt="2014-01-01 13:00:00", content="local 13:00")
        _write_test_file("remote/file6.txt", dt="2014-01-01 13:00:05", content="remote 13:00:05")
        # Conflict: changed local and remote, local is newer
        _write_test_file("local/file7.txt", dt="2014-01-01 13:00:05", content="local 13:00:05")
        _write_test_file("remote/file7.txt", dt="2014-01-01 13:00:00", content="remote 13:00")
        # Conflict: removed local, but modified remote
        _remove_test_file("local/file8.txt")
        _write_test_file("remote/file8.txt", dt="2014-01-01 13:00:00", content="remote 13:00")
        # Conflict: removed remote, but modified local
        _write_test_file("local/file9.txt", dt="2014-01-01 13:00:00", content="local 13:00")
        _remove_test_file("remote/file9.txt")

        _write_test_file("local/folder2/file2_1.txt", dt="2014-01-01 13:00:00", content="local 13:00")
        _remove_test_folder("local/folder3")
        # Conflict: Modify sub-folder item on remote, but remove parent folder on local
        _remove_test_folder("local/folder4")
        _write_test_file("remote/folder4/file4_1.txt", dt="2014-01-01 13:00:00", content="remote 13:00")

        _write_test_file("remote/folder5/file5_1.txt", dt="2014-01-01 13:00:00", content="remote 13:00")
        _remove_test_folder("remote/folder6")
        # Conflict: Modify sub-folder item on local, but remove parent folder on remote
        _write_test_file("local/folder7/file7_1.txt", dt="2014-01-01 13:00:00", content="local 13:00")
        _remove_test_folder("remote/folder7")

        _write_test_file("local/new_file1.txt", dt="2014-01-01 13:00:00", content="local 13:00")
        _write_test_file("remote/new_file2.txt", dt="2014-01-01 13:00:00", content="remote 13:00")
        # Identical files on both sides (same time and size):
        _write_test_file("local/new_file3.txt", dt="2014-01-01 13:00:00", content="local 13:00")
        _write_test_file("remote/new_file3.txt", dt="2014-01-01 13:00:00", content="local 13:00")
        # Identical files on both sides (same time but different size):
        _write_test_file("local/new_file4.txt", dt="2014-01-01 13:00:00", content="local 13:00")
        _write_test_file("remote/new_file4.txt", dt="2014-01-01 13:00:00", content="remote 13:00 with other content")
        # Two new files on both sides with same name but different time
        _write_test_file("local/new_file5.txt", dt="2014-01-01 13:00:00", content="local 13:00")
        _write_test_file("remote/new_file5.txt", dt="2014-01-01 13:00:05", content="remote 13:00:05")
        # Two new files on both sides with same name but different time
        _write_test_file("local/new_file6.txt", dt="2014-01-01 13:00:05", content="local 13:00:05")
        _write_test_file("remote/new_file6.txt", dt="2014-01-01 13:00:00", content="remote 13:00")

    def _do_run_suite(self, synchronizer_class, opts):
        """Run a synchronizer with specific options against a defined scenario."""
        self._prepare_modified_fixture()
        # Synchronize folders
        stats = _sync_test_folders(synchronizer_class, opts)
        return stats

    def _dump_de_facto_results(self, stats):
        print("*** stats:")
        pprint(stats)
        print("*** local:")
        pprint(_get_test_folder("local"), width=128)
        print("*** remote:")
        pprint(_get_test_folder("remote"), width=128)
