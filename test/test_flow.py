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
    _remove_test_folder, prepare_fixtures_2, _sync_test_folders, _delete_metadata
from pprint import pprint


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
          folder4/file4_1.txt       x             13:00        (*) CONFLICT!
          folder5/file5_1.txt     12:00           13:00
          folder6/file6_1.txt     12:00             x          (folder deleted)
          folder7/file7_1.txt     13:00             x          (*) CONFLICT!

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

        # Synchronize folders
        stats = _sync_test_folders(opts)
        return stats

    def test_setUp(self):
        # Test that setUp code worked
        # Set should have created a copy of /local in /remote...
        self.assertTrue(_is_test_file("local/" + DirMetadata.META_FILE_NAME))
        self.assertTrue(not _is_test_file("remote/" + DirMetadata.META_FILE_NAME))
#         self.assertEqual(stats["files_written"], 8)
        self.assertDictEqual(_get_test_folder("local"), _get_test_folder("remote"))

    def _dump_de_facto_results(self, stats):
        print("*** stats:")
        pprint(stats)
        print("*** local:")
        pprint(_get_test_folder("local"), width=128)
        print("*** remote:")
        pprint(_get_test_folder("remote"), width=128)

    def test_default(self):
        opts = {"verbose": 4} # default options, i.e. 'skip' conflicts
        # Default options: expect 4 unresolved conflicts
        stats = self._do_run_suite(opts)
#         self._dump_de_facto_results(stats)

        # We expect 7 conflicts, and leave them unresolved (i.e. skip them all)

        self.assertEqual(stats["files_written"], 6)
        self.assertEqual(stats["download_files_written"], 3)
        self.assertEqual(stats["upload_files_written"], 3)
        self.assertEqual(stats["files_deleted"], 2)
        self.assertEqual(stats["dirs_deleted"], 4)
        self.assertEqual(stats["conflict_files"], 7)

        expect_local = {
            'file1.txt': {'content': 'local1', 'date': '2014-01-01 12:00:00'},
            'file2.txt': {'content': 'local 13:00', 'date': '2014-01-01 13:00:00'},
            'file4.txt': {'content': 'remote 13:00', 'date': '2014-01-01 13:00:00'},
            'file6.txt': {'content': 'local 13:00', 'date': '2014-01-01 13:00:00'},
            'file7.txt': {'content': 'local 13:00:05', 'date': '2014-01-01 13:00:05'},
            'file9.txt': {'content': 'local 13:00', 'date': '2014-01-01 13:00:00'},
            'folder1/file1_1.txt': {'content': 'local1_1', 'date': '2014-01-01 12:00:00'},
            'folder2/file2_1.txt': {'content': 'local 13:00', 'date': '2014-01-01 13:00:00'},
            'folder5/file5_1.txt': {'content': 'remote 13:00', 'date': '2014-01-01 13:00:00'},
            'new_file1.txt': {'content': 'local 13:00', 'date': '2014-01-01 13:00:00'},
            'new_file2.txt': {'content': 'remote 13:00', 'date': '2014-01-01 13:00:00'},
            'new_file3.txt': {'content': 'local 13:00', 'date': '2014-01-01 13:00:00'},
            'new_file4.txt': {'content': 'local 13:00', 'date': '2014-01-01 13:00:00'},
            'new_file5.txt': {'content': 'local 13:00', 'date': '2014-01-01 13:00:00'},
            'new_file6.txt': {'content': 'local 13:00:05', 'date': '2014-01-01 13:00:05'}
            }
        expect_remote = {
            'file1.txt': {'content': 'local1', 'date': '2014-01-01 12:00:00'},
            'file2.txt': {'content': 'local 13:00', 'date': '2014-01-01 13:00:00'},
            'file4.txt': {'content': 'remote 13:00', 'date': '2014-01-01 13:00:00'},
            'file6.txt': {'content': 'remote 13:00:05', 'date': '2014-01-01 13:00:05'},
            'file7.txt': {'content': 'remote 13:00', 'date': '2014-01-01 13:00:00'},
            'file8.txt': {'content': 'remote 13:00', 'date': '2014-01-01 13:00:00'},
            'folder1/file1_1.txt': {'content': 'local1_1', 'date': '2014-01-01 12:00:00'},
            'folder2/file2_1.txt': {'content': 'local 13:00', 'date': '2014-01-01 13:00:00'},
            'folder5/file5_1.txt': {'content': 'remote 13:00', 'date': '2014-01-01 13:00:00'},
            'new_file1.txt': {'content': 'local 13:00', 'date': '2014-01-01 13:00:00'},
            'new_file2.txt': {'content': 'remote 13:00', 'date': '2014-01-01 13:00:00'},
            'new_file3.txt': {'content': 'local 13:00', 'date': '2014-01-01 13:00:00'},
            'new_file4.txt': {'content': 'remote 13:00 with other content', 'date': '2014-01-01 13:00:00'},
            'new_file5.txt': {'content': 'remote 13:00:05', 'date': '2014-01-01 13:00:05'},
            'new_file6.txt': {'content': 'remote 13:00', 'date': '2014-01-01 13:00:00'}
            }
        self.assertDictEqual(_get_test_folder("local"), expect_local)
        self.assertDictEqual(_get_test_folder("remote"), expect_remote)


    def test_resolve_local(self):
        opts = {"resolve": "local", "verbose": 4}

        stats = self._do_run_suite(opts)
        # self._dump_de_facto_results(stats)

        # We resolve all conflicts by using the local version.

        self.assertEqual(stats["files_written"], 12)
        self.assertEqual(stats["download_files_written"], 3)
        self.assertEqual(stats["upload_files_written"], 9)
        self.assertEqual(stats["files_deleted"], 3)
        self.assertEqual(stats["dirs_deleted"], 4)
        self.assertEqual(stats["conflict_files"], 7)

        expect_local = {
            'file1.txt': {'content': 'local1', 'date': '2014-01-01 12:00:00'},
            'file2.txt': {'content': 'local 13:00', 'date': '2014-01-01 13:00:00'},
            'file4.txt': {'content': 'remote 13:00', 'date': '2014-01-01 13:00:00'},
            'file6.txt': {'content': 'local 13:00', 'date': '2014-01-01 13:00:00'},
            'file7.txt': {'content': 'local 13:00:05', 'date': '2014-01-01 13:00:05'},
            'file9.txt': {'content': 'local 13:00', 'date': '2014-01-01 13:00:00'},
            'folder1/file1_1.txt': {'content': 'local1_1', 'date': '2014-01-01 12:00:00'},
            'folder2/file2_1.txt': {'content': 'local 13:00', 'date': '2014-01-01 13:00:00'},
            'folder5/file5_1.txt': {'content': 'remote 13:00', 'date': '2014-01-01 13:00:00'},
            'new_file1.txt': {'content': 'local 13:00', 'date': '2014-01-01 13:00:00'},
            'new_file2.txt': {'content': 'remote 13:00', 'date': '2014-01-01 13:00:00'},
            'new_file3.txt': {'content': 'local 13:00', 'date': '2014-01-01 13:00:00'},
            'new_file4.txt': {'content': 'local 13:00', 'date': '2014-01-01 13:00:00'},
            'new_file5.txt': {'content': 'local 13:00', 'date': '2014-01-01 13:00:00'},
            'new_file6.txt': {'content': 'local 13:00:05', 'date': '2014-01-01 13:00:05'},
            }
        self.assertDictEqual(_get_test_folder("local"), expect_local)
        self.assertDictEqual(_get_test_folder("remote"), expect_local)

    def test_resolve_remote(self):

        opts = {"resolve": "remote", "verbose": 4}

        stats = self._do_run_suite(opts)
        # self._dump_de_facto_results(stats)

        # We resolve all conflicts by using the remote version.

        self.assertEqual(stats["files_written"], 12)
        self.assertEqual(stats["download_files_written"], 9)
        self.assertEqual(stats["upload_files_written"], 3)
        self.assertEqual(stats["files_deleted"], 3)
        self.assertEqual(stats["dirs_deleted"], 4)
        self.assertEqual(stats["conflict_files"], 7)

        expect_local = {
            'file1.txt': {'content': 'local1', 'date': '2014-01-01 12:00:00'},
            'file2.txt': {'content': 'local 13:00', 'date': '2014-01-01 13:00:00'},
            'file4.txt': {'content': 'remote 13:00', 'date': '2014-01-01 13:00:00'},
            'file6.txt': {'content': 'remote 13:00:05', 'date': '2014-01-01 13:00:05'},
            'file7.txt': {'content': 'remote 13:00', 'date': '2014-01-01 13:00:00'},
            'file8.txt': {'content': 'remote 13:00', 'date': '2014-01-01 13:00:00'},
            'folder1/file1_1.txt': {'content': 'local1_1', 'date': '2014-01-01 12:00:00'},
            'folder2/file2_1.txt': {'content': 'local 13:00', 'date': '2014-01-01 13:00:00'},
            'folder5/file5_1.txt': {'content': 'remote 13:00', 'date': '2014-01-01 13:00:00'},
            'new_file1.txt': {'content': 'local 13:00', 'date': '2014-01-01 13:00:00'},
            'new_file2.txt': {'content': 'remote 13:00', 'date': '2014-01-01 13:00:00'},
            'new_file3.txt': {'content': 'local 13:00', 'date': '2014-01-01 13:00:00'},
            'new_file4.txt': {'content': 'remote 13:00 with other content', 'date': '2014-01-01 13:00:00'},
            'new_file5.txt': {'content': 'remote 13:00:05', 'date': '2014-01-01 13:00:05'},
            'new_file6.txt': {'content': 'remote 13:00', 'date': '2014-01-01 13:00:00'},
            }
        self.assertDictEqual(_get_test_folder("local"), expect_local)
        self.assertDictEqual(_get_test_folder("remote"), expect_local)

    def test_no_metadata(self):
        """Synchronize with absent .pyftpsync-meta.json."""
        opts = {"verbose": 4}

        # setUp already sync'd with remote. We want to check the results when metadata
        # is absent:
        _delete_metadata(PYFTPSYNC_TEST_FOLDER)

        stats = self._do_run_suite(opts)
#         self._dump_de_facto_results(stats)

        # NOTE:
        # Since we don't have meta data, the synchronizer treats missing files on
        # either side as 'new'.
        # Also modifications on both sides are not recognized as conflict. Instead the
        # newer file wins. (Only exception is new_file4.txt` which has identical time
        # but different size)
        # => So we basically get a union of both targets.

        self.assertEqual(stats["files_written"], 18)
        self.assertEqual(stats["download_files_written"], 9)
        self.assertEqual(stats["upload_files_written"], 9)
        self.assertEqual(stats["files_deleted"], 0)
        self.assertEqual(stats["dirs_deleted"], 0)
        self.assertEqual(stats["conflict_files"], 1)

        expect_local = {
            'file1.txt': {'content': 'local1', 'date': '2014-01-01 12:00:00'},
            'file2.txt': {'content': 'local 13:00', 'date': '2014-01-01 13:00:00'},
            'file3.txt': {'content': 'local3', 'date': '2014-01-01 12:00:00'},
            'file4.txt': {'content': 'remote 13:00', 'date': '2014-01-01 13:00:00'},
            'file5.txt': {'content': 'local5', 'date': '2014-01-01 12:00:00'},
            'file6.txt': {'content': 'remote 13:00:05', 'date': '2014-01-01 13:00:05'},
            'file7.txt': {'content': 'local 13:00:05', 'date': '2014-01-01 13:00:05'},
            'file8.txt': {'content': 'remote 13:00', 'date': '2014-01-01 13:00:00'},
            'file9.txt': {'content': 'local 13:00', 'date': '2014-01-01 13:00:00'},
            'folder1/file1_1.txt': {'content': 'local1_1', 'date': '2014-01-01 12:00:00'},
            'folder2/file2_1.txt': {'content': 'local 13:00', 'date': '2014-01-01 13:00:00'},
            'folder3/file3_1.txt': {'content': 'local3_1', 'date': '2014-01-01 12:00:00'},
            'folder4/file4_1.txt': {'content': 'remote 13:00', 'date': '2014-01-01 13:00:00'},
            'folder5/file5_1.txt': {'content': 'remote 13:00', 'date': '2014-01-01 13:00:00'},
            'folder6/file6_1.txt': {'content': 'local6_1', 'date': '2014-01-01 12:00:00'},
            'folder7/file7_1.txt': {'content': 'local 13:00', 'date': '2014-01-01 13:00:00'},
            'new_file1.txt': {'content': 'local 13:00', 'date': '2014-01-01 13:00:00'},
            'new_file2.txt': {'content': 'remote 13:00', 'date': '2014-01-01 13:00:00'},
            'new_file3.txt': {'content': 'local 13:00', 'date': '2014-01-01 13:00:00'},
            'new_file4.txt': {'content': 'local 13:00', 'date': '2014-01-01 13:00:00'},
            'new_file5.txt': {'content': 'remote 13:00:05', 'date': '2014-01-01 13:00:05'},
            'new_file6.txt': {'content': 'local 13:00:05', 'date': '2014-01-01 13:00:05'}
            }
        expect_remote = expect_local.copy()
        expect_remote.update({
            'new_file4.txt': {'content': 'remote 13:00 with other content', 'date': '2014-01-01 13:00:00'},
            })
        self.assertDictEqual(_get_test_folder("local"), expect_local)
        self.assertDictEqual(_get_test_folder("remote"), expect_remote)


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

        # Note: currently we do NOT detect this kind of conflicts!!!

        raise SkipTest("Currently we do NOT detect this kind of conflicts.")

        _write_test_file("local/folder1/file1_1.txt", dt="2014-01-01 13:00:00", content="local 13:00")
        _remove_test_folder("remote/folder1")

        opts = {}
        stats = _sync_test_folders(opts)

        self.assertEqual(stats["files_written"], 0)
        self.assertEqual(stats["download_files_written"], 0)
        self.assertEqual(stats["upload_files_written"], 0)
        self.assertEqual(stats["files_deleted"], 0)
        # self.assertEqual(stats["dirs_deleted"], 1)
        # self.assertEqual(stats["conflict_files"], 0)
        self.assertEqual(stats["dirs_deleted"], 0)
        self.assertEqual(stats["conflict_files"], 1)

        expect_local = {
            'file1.txt': {'content': 'local1', 'date': '2014-01-01 12:00:00'},
            'file2.txt': {'content': 'local2', 'date': '2014-01-01 12:00:00'},
            'file3.txt': {'content': 'local3', 'date': '2014-01-01 12:00:00'},
            'file4.txt': {'content': 'local4', 'date': '2014-01-01 12:00:00'},
            'file5.txt': {'content': 'local5', 'date': '2014-01-01 12:00:00'},
            'file6.txt': {'content': 'local6', 'date': '2014-01-01 12:00:00'},
            'file7.txt': {'content': 'local7', 'date': '2014-01-01 12:00:00'},
            'file8.txt': {'content': 'local8', 'date': '2014-01-01 12:00:00'},
            'file9.txt': {'content': 'local9', 'date': '2014-01-01 12:00:00'},
            'folder2/file2_1.txt': {'content': 'local2_1', 'date': '2014-01-01 12:00:00'},
            'folder3/file3_1.txt': {'content': 'local3_1', 'date': '2014-01-01 12:00:00'},
            'folder4/file4_1.txt': {'content': 'local4_1', 'date': '2014-01-01 12:00:00'},
            'folder5/file5_1.txt': {'content': 'local5_1', 'date': '2014-01-01 12:00:00'},
            'folder6/file6_1.txt': {'content': 'local6_1', 'date': '2014-01-01 12:00:00'},
            'folder7/file7_1.txt': {'content': 'local7_1', 'date': '2014-01-01 12:00:00'},
            }
        self.assertDictEqual(_get_test_folder("local"), expect_local)
        self.assertDictEqual(_get_test_folder("remote"), expect_local)

#===============================================================================
# Main
#===============================================================================
if __name__ == "__main__":
    print(sys.version)
    unittest.main()
