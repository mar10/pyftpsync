# -*- coding: UTF-8 -*-
"""
Tests for pyftpsync
"""
from __future__ import print_function

import datetime
import os
import sys

# Python 2.7+
import unittest
from unittest.case import SkipTest  # @UnusedImport


from ftpsync.targets import FsTarget, DirMetadata

from ftpsync.synchronizers import DownloadSynchronizer, UploadSynchronizer, \
    BiDirSynchronizer
from test.tools import prepare_fixtures_1, PYFTPSYNC_TEST_FOLDER, \
    _get_test_file_date, STAMP_20140101_120000, _touch_test_file, \
    _write_test_file, _remove_test_file, _is_test_file, _get_test_folder,\
    _remove_test_folder, prepare_fixtures_2, _sync_test_folders


#===============================================================================
# Module setUp / tearDown
#===============================================================================

def setUpModule():
#    prepare_fixtures_1()
    pass

def tearDownModule():
#    _empty_folder(PYFTPSYNC_TEST_FOLDER)
    pass


#===============================================================================
# FilesystemTest
#===============================================================================

class FilesystemTest(unittest.TestCase):
    """Test different synchronizers on file system targets."""
    def setUp(self):
#         raise SkipTest
        self.verbose = 3  # 4
        prepare_fixtures_1()

    def tearDown(self):
        pass

    def test_download_fs_fs(self):
        # Download files from local to remote (which is empty)
        local = FsTarget(os.path.join(PYFTPSYNC_TEST_FOLDER, "remote"))
        remote = FsTarget(os.path.join(PYFTPSYNC_TEST_FOLDER, "local"))
        opts = {"force": False, "delete": False, "dry_run": False, "verbose": self.verbose}
        s = DownloadSynchronizer(local, remote, opts)
        s.run()
        stats = s.get_stats()
#        pprint(stats)
        self.assertEqual(stats["local_dirs"], 0)
        self.assertEqual(stats["local_files"], 0)
        self.assertEqual(stats["remote_dirs"], 2)
        self.assertEqual(stats["remote_files"], 4) # currently files are not counted, when inside a *new* folder
        self.assertEqual(stats["files_written"], 6)
        self.assertEqual(stats["dirs_created"], 2)
        self.assertEqual(stats["bytes_written"], 16403)
        # Again: nothing to do
        s = DownloadSynchronizer(local, remote, opts)
        s.run()
        stats = s.get_stats()
#        pprint(stats)
        self.assertEqual(stats["local_dirs"], 2)
        self.assertEqual(stats["local_files"], 6)
        self.assertEqual(stats["remote_dirs"], 2)
        self.assertEqual(stats["remote_files"], 6)
        self.assertEqual(stats["files_written"], 0)
        self.assertEqual(stats["dirs_created"], 0)
        self.assertEqual(stats["bytes_written"], 0)
        # file times are preserved
        self.assertEqual(_get_test_file_date("local/file1.txt"), STAMP_20140101_120000)
        self.assertEqual(_get_test_file_date("remote/file1.txt"), STAMP_20140101_120000)


    def test_upload_fs_fs(self):
        local = FsTarget(os.path.join(PYFTPSYNC_TEST_FOLDER, "local"))
        remote = FsTarget(os.path.join(PYFTPSYNC_TEST_FOLDER, "remote"))
        opts = {"force": False, "delete": False, "dry_run": False, "verbose": self.verbose}
        s = UploadSynchronizer(local, remote, opts)
        s.run()
        stats = s.get_stats()
#        pprint(stats)
        self.assertEqual(stats["local_dirs"], 2)
        self.assertEqual(stats["local_files"], 4) # currently files are not counted, when inside a *new* folder
        self.assertEqual(stats["remote_dirs"], 0)
        self.assertEqual(stats["remote_files"], 0)
        self.assertEqual(stats["files_written"], 6)
        self.assertEqual(stats["dirs_created"], 2)
        self.assertEqual(stats["bytes_written"], 16403)
        # file times are preserved
        self.assertEqual(_get_test_file_date("local/file1.txt"), STAMP_20140101_120000)
        self.assertEqual(_get_test_file_date("remote/file1.txt"), STAMP_20140101_120000)


    def test_sync_fs_fs(self):
        local = FsTarget(os.path.join(PYFTPSYNC_TEST_FOLDER, "local"))
        remote = FsTarget(os.path.join(PYFTPSYNC_TEST_FOLDER, "remote"))
        opts = {"dry_run": False, "verbose": self.verbose}  # , "resolve": "ask"}
        s = BiDirSynchronizer(local, remote, opts)
        s.run()
        stats = s.get_stats()
#        pprint(stats)
        self.assertEqual(stats["local_dirs"], 2)
        self.assertEqual(stats["local_files"], 4) # currently files are not counted, when inside a *new* folder
        self.assertEqual(stats["remote_dirs"], 0)
        self.assertEqual(stats["remote_files"], 0)
        self.assertEqual(stats["files_written"], 6)
        self.assertEqual(stats["dirs_created"], 2)
        self.assertEqual(stats["bytes_written"], 16403)
        # file times are preserved
        self.assertEqual(_get_test_file_date("local/file1.txt"), STAMP_20140101_120000)
        self.assertEqual(_get_test_file_date("remote/file1.txt"), STAMP_20140101_120000)

        # Again: nothing to do
        s = BiDirSynchronizer(local, remote, opts)
        s.run()
        stats = s.get_stats()
#        pprint(stats)
        self.assertEqual(stats["local_dirs"], 2)
        self.assertEqual(stats["local_files"], 6)
        self.assertEqual(stats["remote_dirs"], 2)
        self.assertEqual(stats["remote_files"], 6)
        self.assertEqual(stats["files_created"], 0)
        self.assertEqual(stats["files_deleted"], 0)
        self.assertEqual(stats["files_written"], 0)
        self.assertEqual(stats["dirs_created"], 0)
        self.assertEqual(stats["bytes_written"], 0)

        # Modify remote and/or remote
        _touch_test_file("local/file1.txt")
        _touch_test_file("remote/file2.txt")
        # file3.txt will cause a conflict:
        _touch_test_file("local/file3.txt")
        dt = datetime.datetime.utcnow() - datetime.timedelta(seconds=10)
        _touch_test_file("remote/file3.txt", dt=dt)

        s = BiDirSynchronizer(local, remote, opts)
        s.run()
        stats = s.get_stats()
#        pprint(stats)
        self.assertEqual(stats["entries_seen"], 18)
        self.assertEqual(stats["entries_touched"], 2)
        self.assertEqual(stats["files_created"], 0)
        self.assertEqual(stats["files_deleted"], 0)
        self.assertEqual(stats["files_written"], 2)
        self.assertEqual(stats["dirs_created"], 0)
        self.assertEqual(stats["download_files_written"], 1)
        self.assertEqual(stats["upload_files_written"], 1)
        self.assertEqual(stats["conflict_files"], 1)
        self.assertEqual(stats["bytes_written"], 6)

    def test_sync_conflicts(self):
        local = FsTarget(os.path.join(PYFTPSYNC_TEST_FOLDER, "local"))
        remote = FsTarget(os.path.join(PYFTPSYNC_TEST_FOLDER, "remote"))
        opts = {"dry_run": False, "verbose": self.verbose}  # , "resolve": "ask"}

        # Copy local -> remote

        s = BiDirSynchronizer(local, remote, opts)
        s.run()
        stats = s.get_stats()
        self.assertEqual(stats["files_written"], 6)
        self.assertEqual(stats["dirs_created"], 2)

        # Modify local and remote

        # conflict 1: local is newer
        dt = datetime.datetime.utcnow()
        _touch_test_file("local/file1.txt", dt)
        dt = datetime.datetime.utcnow() - datetime.timedelta(seconds=10)
        _touch_test_file("remote/file1.txt", dt=dt)
#         path = os.path.join(PYFTPSYNC_TEST_FOLDER, "remote/file1.txt")
#         stamp = time.time() - 10
#         os.utime(path, (stamp, stamp))

        # conflict 2: remote is newer
        _touch_test_file("remote/file2.txt")
        dt = datetime.datetime.utcnow() - datetime.timedelta(seconds=10)
        _touch_test_file("local/file2.txt", dt=dt)


        s = BiDirSynchronizer(local, remote, opts)
        s.run()
        stats = s.get_stats()
#         pprint(stats)
        self.assertEqual(stats["entries_seen"], 18)
        self.assertEqual(stats["entries_touched"], 0)
        self.assertEqual(stats["bytes_written"], 0)
        self.assertEqual(stats["conflict_files"], 2)


#===============================================================================
# BidirSyncTest
#===============================================================================

class BidirResolveTest(unittest.TestCase):
    """Test BiDirSynchronizer on file system targets with different resolve modes."""
    def setUp(self):
        prepare_fixtures_2()
        self.maxDiff = None # do not trunkate Dict diffs

    def tearDown(self):
        pass

    def _do_run_suite(self, opts):
        """Modify both folders and run sync with specific options.

                                  Local           Remote
          file1.txt               13:00           12:00
          file2.txt                 x             12:00
          file3.txt               12:00           13:00
          file4.txt               12:00             x
          file5.txt               13:00           13:00:05     CONFLICT!
          file6.txt               13:00:05        13:00        CONFLICT!
          file7.txt                 x             13:00        CONFLICT!
          file8.txt               13:00             x          CONFLICT!
          folder1/file1_1.txt     13.00
          folder2/file2_1.txt       x             12:00        CONFLICT (folder deleted)
          folder3/file3_1.txt     12:00           13:00        CONFLICT
          folder4/file4_1.txt     12:00             x          CONFLICT (folder deleted)
          new_file1.txt           13:00             -
          new_file2.txt             -             13:00
        """
        # Change, remove, and add local only
        _write_test_file("local/file1.txt", dt="2014-01-01 13:00:00", content="local 13:00")
        _remove_test_file("local/file2.txt")
        _write_test_file("local/new_file1.txt", dt="2014-01-01 13:00:00", content="local 13:00")
        _write_test_file("local/folder1/file1_1.txt", dt="2014-01-01 13:00:00", content="local 13:00")
        _remove_test_folder("local/folder2")
        # Change, remove, and add remote only
        _write_test_file("remote/file3.txt", dt="2014-01-01 13:00:00", content="remote 13:00")
        _remove_test_file("remote/file4.txt")
        _write_test_file("remote/new_file2.txt", dt="2014-01-01 13:00:00", content="remote 13:00")
        _write_test_file("remote/folder3/file3_1.txt", dt="2014-01-01 13:00:00", content="remote 13:00")
        _remove_test_folder("remote/folder4")
        # Conflict: changed local and remote, remote is newer
        _write_test_file("local/file5.txt", dt="2014-01-01 13:00:00", content="local 13:00")
        _write_test_file("remote/file5.txt", dt="2014-01-01 13:00:05", content="remote 13:00:05")
        # Conflict: changed local and remote, local is newer
        _write_test_file("local/file6.txt", dt="2014-01-01 13:00:05", content="local 13:00:05")
        _write_test_file("remote/file6.txt", dt="2014-01-01 13:00:00", content="remote 13:00")
        # Conflict: removed local, but modified remote
        _remove_test_file("local/file7.txt")
        _write_test_file("remote/file7.txt", dt="2014-01-01 13:00:00", content="remote 13:00")
        # Conflict: removed remote, but modified local
        _write_test_file("local/file8.txt", dt="2014-01-01 13:00:00", content="local 13:00")
        _remove_test_file("remote/file8.txt")

        # Synchronize folders
#         stats = self._do_sync(opts)
        stats = _sync_test_folders(opts)
        return stats

    def test_setUp(self):
        # Test that setUp code worked
#         raise SkipTest
        # Set should have created a copy of /local in /remote...
        self.assertTrue(_is_test_file("local/" + DirMetadata.META_FILE_NAME))
        self.assertTrue(not _is_test_file("remote/" + DirMetadata.META_FILE_NAME))
#         self.assertEqual(stats["files_written"], 8)
        self.assertDictEqual(_get_test_folder("local"), _get_test_folder("remote"))

    def test_default(self):
#         raise SkipTest
        opts = {} # default options, i.e. 'skip' conflicts
        # Default options: expect 4 unresolved conflicts
        stats = self._do_run_suite(opts)
#         pprint(stats)
#         pprint(_get_test_folder("local"))
#         pprint(_get_test_folder("remote"))

        self.assertEqual(stats["files_written"], 6)
        self.assertEqual(stats["download_files_written"], 3)
        self.assertEqual(stats["upload_files_written"], 3)
        self.assertEqual(stats["files_deleted"], 2)
        self.assertEqual(stats["dirs_deleted"], 2)
        self.assertEqual(stats["conflict_files"], 4)

        expect_local = {
            'file1.txt': {'content': 'local 13:00', 'date': '2014-01-01 13:00:00'},
            'file3.txt': {'content': 'remote 13:00', 'date': '2014-01-01 13:00:00'},
            'file5.txt': {'content': 'local 13:00', 'date': '2014-01-01 13:00:00'}, # unresolved conflict
            'file6.txt': {'content': 'local 13:00:05', 'date': '2014-01-01 13:00:05'}, # unresolved conflict
            'file8.txt': {'content': 'local 13:00', 'date': '2014-01-01 13:00:00'}, # unresolved conflict
            'folder1/file1_1.txt': {'content': 'local 13:00', 'date': '2014-01-01 13:00:00'},
            'folder3/file3_1.txt': {'content': 'remote 13:00', 'date': '2014-01-01 13:00:00'},
            'new_file1.txt': {'content': 'local 13:00', 'date': '2014-01-01 13:00:00'},
            'new_file2.txt': {'content': 'remote 13:00', 'date': '2014-01-01 13:00:00'},
            }
        expect_remote = {
            'file1.txt': {'content': 'local 13:00', 'date': '2014-01-01 13:00:00'},
            'file3.txt': {'content': 'remote 13:00', 'date': '2014-01-01 13:00:00'},
            'file5.txt': {'content': 'remote 13:00:05', 'date': '2014-01-01 13:00:05'}, # unresolved conflict
            'file6.txt': {'content': 'remote 13:00', 'date': '2014-01-01 13:00:00'}, # unresolved conflict
            'file7.txt': {'content': 'remote 13:00', 'date': '2014-01-01 13:00:00'}, # unresolved conflict
            'folder1/file1_1.txt': {'content': 'local 13:00', 'date': '2014-01-01 13:00:00'},
            'folder3/file3_1.txt': {'content': 'remote 13:00', 'date': '2014-01-01 13:00:00'},
            'new_file1.txt': {'content': 'local 13:00', 'date': '2014-01-01 13:00:00'},
            'new_file2.txt': {'content': 'remote 13:00', 'date': '2014-01-01 13:00:00'},
            }
        self.assertDictEqual(_get_test_folder("local"), expect_local)
        self.assertDictEqual(_get_test_folder("remote"), expect_remote)


    def test_resolve_local(self):
#         raise SkipTest
        opts = {"resolve": "local"}
        stats = self._do_run_suite(opts)

        self.assertEqual(stats["files_written"], 9)
        self.assertEqual(stats["download_files_written"], 3)
        self.assertEqual(stats["upload_files_written"], 6)
        self.assertEqual(stats["files_deleted"], 3)
        self.assertEqual(stats["dirs_deleted"], 2)
        self.assertEqual(stats["conflict_files"], 4)

        expect_local = {
            'file1.txt': {'content': 'local 13:00', 'date': '2014-01-01 13:00:00'},
            'file3.txt': {'content': 'remote 13:00', 'date': '2014-01-01 13:00:00'},
            'file5.txt': {'content': 'local 13:00', 'date': '2014-01-01 13:00:00'}, # resolved conflict
            'file6.txt': {'content': 'local 13:00:05', 'date': '2014-01-01 13:00:05'}, # resolved conflict
            'file8.txt': {'content': 'local 13:00', 'date': '2014-01-01 13:00:00'}, # resolved conflict
            'folder1/file1_1.txt': {'content': 'local 13:00', 'date': '2014-01-01 13:00:00'},
            'folder3/file3_1.txt': {'content': 'remote 13:00', 'date': '2014-01-01 13:00:00'},
            'new_file1.txt': {'content': 'local 13:00', 'date': '2014-01-01 13:00:00'},
            'new_file2.txt': {'content': 'remote 13:00', 'date': '2014-01-01 13:00:00'},
            }
        self.assertDictEqual(_get_test_folder("local"), expect_local)
        self.assertDictEqual(_get_test_folder("remote"), expect_local)


    def test_resolve_remote(self):
#         raise SkipTest
        opts = {"resolve": "remote"}
        stats = self._do_run_suite(opts)
        self.assertEqual(stats["files_written"], 9)
        self.assertEqual(stats["download_files_written"], 6)
        self.assertEqual(stats["upload_files_written"], 3)
        self.assertEqual(stats["files_deleted"], 3)
        self.assertEqual(stats["dirs_deleted"], 2)
        self.assertEqual(stats["conflict_files"], 4)

        expect_local = {
            'file1.txt': {'content': 'local 13:00', 'date': '2014-01-01 13:00:00'},
            'file3.txt': {'content': 'remote 13:00', 'date': '2014-01-01 13:00:00'},
            'file5.txt': {'content': 'remote 13:00:05', 'date': '2014-01-01 13:00:05'}, # resolved conflict
            'file6.txt': {'content': 'remote 13:00', 'date': '2014-01-01 13:00:00'}, # resolved conflict
            'file7.txt': {'content': 'remote 13:00', 'date': '2014-01-01 13:00:00'}, # resolved conflict
            'folder1/file1_1.txt': {'content': 'local 13:00', 'date': '2014-01-01 13:00:00'},
            'folder3/file3_1.txt': {'content': 'remote 13:00', 'date': '2014-01-01 13:00:00'},
            'new_file1.txt': {'content': 'local 13:00', 'date': '2014-01-01 13:00:00'},
            'new_file2.txt': {'content': 'remote 13:00', 'date': '2014-01-01 13:00:00'},
            }
        self.assertDictEqual(_get_test_folder("local"), expect_local)
        self.assertDictEqual(_get_test_folder("remote"), expect_local)

#===============================================================================
# BidirSpecialTest
#===============================================================================
class BidirSpecialTest(unittest.TestCase):
    """Test BiDirSynchronizer on file system targets."""
    def setUp(self):
        prepare_fixtures_2()
        self.maxDiff = None # do not trunkate Dict diffs

    def tearDown(self):
        pass

    def test_folder_conflict(self):
        # delete a folder on one side, but change content on other side
        # Note: currently
#         raise SkipTest
        _write_test_file("local/folder1/file1_1.txt", dt="2014-01-01 13:00:00", content="local 13:00")
        _remove_test_folder("remote/folder1")

        opts = {}
        stats = _sync_test_folders(opts)
#         pprint(stats)
        self.assertEqual(stats["files_written"], 0)
        self.assertEqual(stats["download_files_written"], 0)
        self.assertEqual(stats["upload_files_written"], 0)
        self.assertEqual(stats["files_deleted"], 0)
        self.assertEqual(stats["dirs_deleted"], 1)
        self.assertEqual(stats["conflict_files"], 0)

        expect_local = {
            'file1.txt': {'content': 'local1', 'date': '2014-01-01 12:00:00'},
            'file2.txt': {'content': 'local2', 'date': '2014-01-01 12:00:00'},
            'file3.txt': {'content': 'local3', 'date': '2014-01-01 12:00:00'},
            'file4.txt': {'content': 'local4', 'date': '2014-01-01 12:00:00'},
            'file5.txt': {'content': 'local5', 'date': '2014-01-01 12:00:00'},
            'file6.txt': {'content': 'local6', 'date': '2014-01-01 12:00:00'},
            'file7.txt': {'content': 'local7', 'date': '2014-01-01 12:00:00'},
            'file8.txt': {'content': 'local8', 'date': '2014-01-01 12:00:00'},
#             'folder1/file1_1.txt': {'content': 'local1_1', 'date': '2014-01-01 12:00:00'},
            'folder2/file2_1.txt': {'content': 'local2_1', 'date': '2014-01-01 12:00:00'},
            'folder3/file3_1.txt': {'content': 'local3_1', 'date': '2014-01-01 12:00:00'},
            'folder4/file4_1.txt': {'content': 'local4_1', 'date': '2014-01-01 12:00:00'},
            }
        self.assertDictEqual(_get_test_folder("local"), expect_local)
        self.assertDictEqual(_get_test_folder("remote"), expect_local)

#===============================================================================
# Main
#===============================================================================
if __name__ == "__main__":
    print(sys.version)
    unittest.main()
