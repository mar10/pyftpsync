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

from ftpsync.synchronizers import UploadSynchronizer
from test.fixture_tools import PYFTPSYNC_TEST_FOLDER, \
    _get_test_file_date, STAMP_20140101_120000, _touch_test_file, \
    _write_test_file, _remove_test_file, _is_test_file, _get_test_folder,\
    _remove_test_folder, _sync_test_folders, _delete_metadata, \
    _SyncTestBase
from pprint import pprint


#===============================================================================
# BidirSyncTest
#===============================================================================

class UploadResolveTest(_SyncTestBase):
    """Test BiDirSynchronizer on file system targets with different resolve modes."""

    def setUp(self):
        # Call self._prepare_initial_synced_fixture():
        super(UploadResolveTest, self).setUp()

    def tearDown(self):
        super(UploadResolveTest, self).tearDown()

    def test_default(self):
        opts = {"verbose": 4} # default options, i.e. 'skip' conflicts
        # Default options: expect 4 unresolved conflicts
        stats = self._do_run_suite(UploadSynchronizer, opts)
        # self._dump_de_facto_results(stats)

        # We expect 7 conflicts, and leave them unresolved (i.e. skip them all)

        self.assertEqual(stats["files_written"], 3)
        self.assertEqual(stats["download_files_written"], 0)
        self.assertEqual(stats["upload_files_written"], 3)
        self.assertEqual(stats["files_deleted"], 1)
        self.assertEqual(stats["dirs_deleted"], 2)
        self.assertEqual(stats["conflict_files"], 7)

        # We expect that local remains unmodified
        self.assertDictEqual(_get_test_folder("local"), _SyncTestBase.local_fixture_modified)

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
            'new_file6.txt': {'content': 'remote 13:00', 'date': '2014-01-01 13:00:00'},
            }
        self.assertDictEqual(_get_test_folder("remote"), expect_remote)


#===============================================================================
# Main
#===============================================================================
if __name__ == "__main__":
    unittest.main()
