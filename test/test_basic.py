# -*- coding: UTF-8 -*-
"""
Tests for pyftpsync
"""
from __future__ import print_function

import datetime
import os
from pprint import pprint
import sys

import unittest
from unittest.case import SkipTest  # @UnusedImport

from ftpsync.targets import FsTarget, DirMetadata
from ftpsync.synchronizers import DownloadSynchronizer, UploadSynchronizer, \
    BiDirSynchronizer
from test.fixture_tools import PYFTPSYNC_TEST_FOLDER, \
    _get_test_file_date, STAMP_20140101_120000, _touch_test_file, \
    _write_test_file, _remove_test_file, _is_test_file, _get_test_folder,\
    _remove_test_folder, _sync_test_folders, _delete_metadata, \
    _SyncTestBase


#===============================================================================
# FixtureTest
#===============================================================================

class FixtureTest(_SyncTestBase):
    """Test the preconditions of the _SyncTestBase."""

    def setUp(self):
        # Call self._prepare_initial_synced_fixture():
        super(FixtureTest, self).setUp()

    def tearDown(self):
        super(FixtureTest, self).tearDown()

    def test_prepare_initial_synced_fixture(self):
        # """Test that fixture set up code worked."""
        # Fixtures are initialized to 9 top-level files and 7 folders, all 12:00:00
        self.assertDictEqual(_get_test_folder("local"), _SyncTestBase.local_fixture_unmodified)

        # setUp() should have created a copy of /local in /remote
        self.assertDictEqual(_get_test_folder("remote"), _SyncTestBase.local_fixture_unmodified)

        # Metadata files are created on local only
        self.assertTrue(_is_test_file("local/" + DirMetadata.META_FILE_NAME))
        self.assertTrue(not _is_test_file("remote/" + DirMetadata.META_FILE_NAME))

    def test_prepare_modified_fixture(self):
        # """Test that fixture set up code worked."""
        #
        self._prepare_modified_fixture()

        self.assertDictEqual(_get_test_folder("local"), _SyncTestBase.local_fixture_modified)

        self.assertDictEqual(_get_test_folder("remote"), _SyncTestBase.remote_fixture_modified)

        # No Metadata files are created yet
        self.assertTrue(_is_test_file("local/" + DirMetadata.META_FILE_NAME))
        self.assertTrue(not _is_test_file("remote/" + DirMetadata.META_FILE_NAME))


#===============================================================================
# Main
#===============================================================================
if __name__ == "__main__":
    unittest.main()
