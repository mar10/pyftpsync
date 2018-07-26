# -*- coding: utf-8 -*-
"""
Tests for pyftpsync
"""
from __future__ import print_function

import os
import unittest
from test.fixture_tools import (
    PYFTPSYNC_TEST_FOLDER,
    _SyncTestBase,
    get_metadata,
    get_test_folder,
    is_test_file,
    read_test_file,
)

from ftpsync.ftp_target import FtpTarget
from ftpsync.targets import DirMetadata, make_target
from ftpsync.util import set_pyftpsync_logger, write, write_error

# ===============================================================================
# FixtureTest
# ===============================================================================


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
        self.assert_test_folder_equal(
            get_test_folder("local"), _SyncTestBase.local_fixture_unmodified
        )

        # setUp() should have created a copy of /local in /remote
        self.assert_test_folder_equal(
            get_test_folder("remote"), _SyncTestBase.local_fixture_unmodified
        )

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

        self.assert_test_folder_equal(
            get_test_folder("local"), _SyncTestBase.local_fixture_modified
        )

        self.assert_test_folder_equal(
            get_test_folder("remote"), _SyncTestBase.remote_fixture_modified
        )

        # Metadata files are created on local target only
        self.assertTrue(is_test_file("local/" + DirMetadata.META_FILE_NAME))
        self.assertTrue(not is_test_file("remote/" + DirMetadata.META_FILE_NAME))


# ===============================================================================
# PlainTest
# ===============================================================================
class PlainTest(unittest.TestCase):
    """Tests that don't connect."""

    def setUp(self):
        # user, passwd = get_stored_credentials("pyftpsync.pw", self.HOST)
        pass

    def tearDown(self):
        pass

    def test_make_target(self):
        for scheme in ["ftp", "ftps"]:
            tls = True if scheme == "ftps" else False

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
            url = "user:secret@ftp.example.com/target/folder"
            t = make_target(scheme + "://" + url)
            self.assertTrue(isinstance(t, FtpTarget))
            self.assertEqual(t.host, "ftp.example.com")
            self.assertEqual(t.username, "user")
            self.assertEqual(t.password, "secret")
            self.assertEqual(t.root_dir, "/target/folder")
            self.assertEqual(t.tls, tls)

            url = "user@example.com:secret@ftp.example.com/target/folder"
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

    def test_logging(self):
        import logging
        import logging.handlers
        import os

        # Create and use a custom logger
        custom_logger = logging.getLogger("pyftpsync_test")
        log_path = os.path.join(PYFTPSYNC_TEST_FOLDER, "pyftpsync.log")
        handler = logging.handlers.WatchedFileHandler(log_path)
        # formatter = logging.Formatter(logging.BASIC_FORMAT)
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        custom_logger.addHandler(handler)
        set_pyftpsync_logger(custom_logger)

        custom_logger.setLevel(logging.DEBUG)
        print("print 1")
        write("write info 1")
        write_error("write error 1")

        custom_logger.setLevel(logging.WARNING)
        write("write info 2")
        write_error("write error 2")

        handler.flush()
        log_data = read_test_file("pyftpsync.log")
        assert "print 1" not in log_data
        assert "write info 1" in log_data
        assert "write error 1" in log_data
        assert "write info 2" not in log_data, "Loglevel honored"
        assert "write error 2" in log_data
        # Cleanup properly (log file would be locked otherwise)
        custom_logger.removeHandler(handler)
        handler.close()


# ===============================================================================
# Main
# ===============================================================================
if __name__ == "__main__":
    unittest.main()
