# -*- coding: UTF-8 -*-
"""
Tests for pyftpsync
"""
from __future__ import print_function

import os
import unittest
from unittest.case import SkipTest  # @UnusedImport

from ftpsync.targets import DirMetadata, make_target
from test.fixture_tools import is_test_file, get_test_folder,\
    _SyncTestBase, read_test_file, get_metadata, PYFTPSYNC_TEST_FOLDER
from ftpsync.ftp_target import FtpTarget


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
        self.assertDictEqual(get_test_folder("local"), _SyncTestBase.local_fixture_unmodified)

        # setUp() should have created a copy of /local in /remote
        self.assertDictEqual(get_test_folder("remote"), _SyncTestBase.local_fixture_unmodified)

        # Metadata files are created on local target only
        self.assertTrue(is_test_file("local/" + DirMetadata.META_FILE_NAME))
        self.assertTrue(not is_test_file("remote/" + DirMetadata.META_FILE_NAME))

        # Local meta data file contains peer sync info
        meta = get_metadata("local")
        remote_path = os.path.join(PYFTPSYNC_TEST_FOLDER, "remote")
        assert "peer_sync" in meta
        meta = meta["peer_sync"]
        assert remote_path in meta
        meta = meta[remote_path]
        assert "file1.txt" in meta
        assert "folder7" in meta
        # Subfolders also contain peer_sync info
        meta = get_metadata("local/folder7")
        assert "file7_1.txt" in meta["peer_sync"][remote_path]

    def test_prepare_modified_fixture(self):
        # """Test that fixture set up code worked."""
        #
        self._prepare_modified_fixture()

        self.assertDictEqual(get_test_folder("local"), _SyncTestBase.local_fixture_modified)

        self.assertDictEqual(get_test_folder("remote"), _SyncTestBase.remote_fixture_modified)

        # Metadata files are created on local target only
        self.assertTrue(is_test_file("local/" + DirMetadata.META_FILE_NAME))
        self.assertTrue(not is_test_file("remote/" + DirMetadata.META_FILE_NAME))


#===============================================================================
# PlainTest
#===============================================================================
class PlainTest(unittest.TestCase):
    """Tests that don't connect."""
    def setUp(self):
#        user, passwd = get_stored_credentials("pyftpsync.pw", self.HOST)
        pass

    def tearDown(self):
        pass

    def test_make_target(self):
        for scheme in ['ftp', 'ftps']:
            tls = True if scheme == 'ftps' else False

            t = make_target(scheme + "://ftp.example.com/target/folder")
            self.assertTrue(isinstance(t, FtpTarget))
            self.assertEqual(t.host, "ftp.example.com")
            self.assertEqual(t.root_dir, "/target/folder")
            self.assertEqual(t.username, None)
            self.assertEqual(t.tls, tls)

            # scheme is case-insensitive
            t = make_target(scheme.upper() + "://ftp.example.com/target/folder")
            self.assertTrue(isinstance(t, FtpTarget))
            self.assertEqual(t.host, "ftp.example.com")
            self.assertEqual(t.root_dir, "/target/folder")
            self.assertEqual(t.username, None)
            self.assertEqual(t.tls, tls)

            # pass credentials with URL
            url = 'user:secret@ftp.example.com/target/folder'
            t = make_target(scheme + "://" + url)
            self.assertTrue(isinstance(t, FtpTarget))
            self.assertEqual(t.host, "ftp.example.com")
            self.assertEqual(t.username, "user")
            self.assertEqual(t.password, "secret")
            self.assertEqual(t.root_dir, "/target/folder")
            self.assertEqual(t.tls, tls)

            url = 'user@example.com:secret@ftp.example.com/target/folder'
            t = make_target(scheme + "://" + url)
            self.assertTrue(isinstance(t, FtpTarget))
            self.assertEqual(t.host, "ftp.example.com")
            self.assertEqual(t.username, "user@example.com")
            self.assertEqual(t.password, "secret")
            self.assertEqual(t.root_dir, "/target/folder")
            self.assertEqual(t.tls, tls)

        # unsupported schemes
        self.assertRaises(ValueError, make_target, "ftpa://ftp.example.com/test")
        self.assertRaises(ValueError, make_target, "http://example.com/test")
        self.assertRaises(ValueError, make_target, "https://example.com/test")


#===============================================================================
# Main
#===============================================================================
if __name__ == "__main__":
    unittest.main()
