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

from ftpsync.synchronizers import BiDirSynchronizer
from test.fixture_tools import PYFTPSYNC_TEST_FOLDER, \
    _get_test_file_date, STAMP_20140101_120000, _touch_test_file, \
    _write_test_file, _remove_test_file, _is_test_file, _get_test_folder,\
    _remove_test_folder, _sync_test_folders, _delete_metadata, \
    _SyncTestBase
from pprint import pprint


#===============================================================================
# BidirSyncTest
#===============================================================================

class BidirResolveTest(_SyncTestBase):
    """Test BiDirSynchronizer on file system targets with different resolve modes."""
    def setUp(self):
        # Call self._prepare_initial_synced_fixture():
        super(BidirResolveTest, self).setUp()

    def tearDown(self):
        super(BidirResolveTest, self).tearDown()

    def test_default(self):
        opts = {"verbose": 4} # default options, i.e. 'skip' conflicts
        # Default options: expect 4 unresolved conflicts
        stats = self._do_run_suite(BiDirSynchronizer, opts)
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

        stats = self._do_run_suite(BiDirSynchronizer, opts)
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

        stats = self._do_run_suite(BiDirSynchronizer, opts)
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

        stats = self._do_run_suite(BiDirSynchronizer, opts)
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
class BidirSpecialTest(_SyncTestBase):
    """Test BiDirSynchronizer on file system targets."""
    def setUp(self):
        # Call self._prepare_initial_synced_fixture():
        super(BidirSpecialTest, self).setUp()

    def tearDown(self):
        super(BidirSpecialTest, self).tearDown()

    def test_folder_conflict(self):
        """Delete a folder on one side, but change content on other side."""

        _write_test_file("local/folder1/file1_1.txt", dt="2014-01-01 13:00:00", content="local 13:00")
        _remove_test_folder("remote/folder1")

        opts = {}
        stats = _sync_test_folders(BiDirSynchronizer, opts)

        # Note: currently we do NOT detect this kind of conflicts!

        # This is what we can expect right now:
        self.assertEqual(stats["dirs_deleted"], 1)
        self.assertEqual(stats["conflict_files"], 0)

        raise SkipTest("Currently we do NOT detect this kind of conflicts.")

        self.assertEqual(stats["files_written"], 0)
        self.assertEqual(stats["download_files_written"], 0)
        self.assertEqual(stats["upload_files_written"], 0)
        self.assertEqual(stats["files_deleted"], 0)
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
