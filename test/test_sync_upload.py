# -*- coding: utf-8 -*-
"""
Tests for pyftpsync
"""
# Allow long lines for readabilty
# flake8: noqa: E501

from __future__ import print_function

import unittest
from test.fixture_tools import _SyncTestBase, get_test_folder

from ftpsync.synchronizers import UploadSynchronizer

# ===============================================================================
# UploadResolveTest
# ===============================================================================


class UploadResolveTest(_SyncTestBase):
    """Test UploadSynchronizer on file system targets with different resolve modes."""

    def setUp(self):
        # Call self._prepare_initial_synced_fixture():
        super(UploadResolveTest, self).setUp()

    def tearDown(self):
        super(UploadResolveTest, self).tearDown()

    def test_default(self):
        opts = {"verbose": self.verbose}  # default options, i.e. 'skip' conflicts
        # Default options: expect 4 unresolved conflicts
        stats = self.do_run_suite(UploadSynchronizer, opts)
        self._dump_de_facto_results(stats)

        # We expect 7 conflicts, and leave them unresolved (i.e. skip them all)

        self.assertEqual(stats["files_written"], 3)
        self.assertEqual(stats["download_files_written"], 0)
        self.assertEqual(stats["upload_files_written"], 3)
        self.assertEqual(stats["files_deleted"], 0)
        self.assertEqual(stats["dirs_deleted"], 0)
        self.assertEqual(stats["conflict_files"], 7)
        self.assertEqual(stats["conflict_files_skipped"], 7)

        # We expect that local remains unmodified
        self.assert_test_folder_equal(
            get_test_folder("local"), _SyncTestBase.local_fixture_modified
        )

        expect_remote = {
            "file1.txt": {"content": "local1", "date": "2014-01-01 12:00:00"},
            "file2.txt": {"content": "local 13:00", "date": "2014-01-01 13:00:00"},
            "file3.txt": {"content": "local3", "date": "2014-01-01 12:00:00"},
            "file4.txt": {"content": "remote 13:00", "date": "2014-01-01 13:00:00"},
            "file6.txt": {"content": "remote 13:00:05", "date": "2014-01-01 13:00:05"},
            "file7.txt": {"content": "remote 13:00", "date": "2014-01-01 13:00:00"},
            "file8.txt": {"content": "remote 13:00", "date": "2014-01-01 13:00:00"},
            "folder1/file1_1.txt": {
                "content": "local1_1",
                "date": "2014-01-01 12:00:00",
            },
            "folder2/file2_1.txt": {
                "content": "local 13:00",
                "date": "2014-01-01 13:00:00",
            },
            "folder3/file3_1.txt": {
                "content": "local3_1",
                "date": "2014-01-01 12:00:00",
            },
            "folder4/file4_1.txt": {
                "content": "remote 13:00",
                "date": "2014-01-01 13:00:00",
            },
            "folder5/file5_1.txt": {
                "content": "remote 13:00",
                "date": "2014-01-01 13:00:00",
            },
            "new_file1.txt": {"content": "local 13:00", "date": "2014-01-01 13:00:00"},
            "new_file2.txt": {"content": "remote 13:00", "date": "2014-01-01 13:00:00"},
            "new_file3.txt": {"content": "local 13:00", "date": "2014-01-01 13:00:00"},
            "new_file4.txt": {
                "content": "remote 13:00 with other content",
                "date": "2014-01-01 13:00:00",
            },
            "new_file5.txt": {
                "content": "remote 13:00:05",
                "date": "2014-01-01 13:00:05",
            },
            "new_file6.txt": {"content": "remote 13:00", "date": "2014-01-01 13:00:00"},
        }
        self.assert_test_folder_equal(get_test_folder("remote"), expect_remote)

    def test_mirror(self):
        opts = {
            "verbose": self.verbose,
            "resolve": "local",
            "delete": True,
            "force": True,
        }

        self.do_run_suite(UploadSynchronizer, opts)

        # We expect that local is mirrored 1:1 to remote
        self.assert_test_folder_equal(
            get_test_folder("local"), _SyncTestBase.local_fixture_modified
        )
        self.assert_test_folder_equal(
            get_test_folder("remote"), _SyncTestBase.local_fixture_modified
        )

    def test_dry_run(self):
        opts = {
            "verbose": self.verbose,
            "resolve": "local",
            "delete": True,
            "force": True,
            "dry_run": True,
        }

        stats = self.do_run_suite(UploadSynchronizer, opts)

        # DRY-RUN: We expect no changes

        self.assertEqual(stats["bytes_written"], 0)
        self.assert_test_folder_equal(
            get_test_folder("local"), _SyncTestBase.local_fixture_modified
        )
        self.assert_test_folder_equal(
            get_test_folder("remote"), _SyncTestBase.remote_fixture_modified
        )

    def test_delete_unmatched(self):
        opts = {
            "verbose": self.verbose,
            "resolve": "local",
            "delete": True,
            "delete_unmatched": True,
            "force": True,
            "match": "*1.txt",
        }

        stats = self.do_run_suite(UploadSynchronizer, opts)
        self._dump_de_facto_results(stats)

        # We expect 7 conflicts, and leave them unresolved (i.e. skip them all)

        # self.assertEqual(stats["files_written"], 3)
        # self.assertEqual(stats["download_files_written"], 0)
        # self.assertEqual(stats["upload_files_written"], 3)
        # self.assertEqual(stats["files_deleted"], 1)
        # self.assertEqual(stats["dirs_deleted"], 2)
        # self.assertEqual(stats["conflict_files"], 7)
        # self.assertEqual(stats["conflict_files_skipped"], 7)

        self.assert_test_folder_equal(
            get_test_folder("local"), _SyncTestBase.local_fixture_modified
        )

        # We expect that remote only contains files that match '*1.txt'
        expect_remote = {
            "file1.txt": {"content": "local1", "date": "2014-01-01 12:00:00"},
            "folder1/file1_1.txt": {
                "content": "local1_1",
                "date": "2014-01-01 12:00:00",
            },
            "folder2/file2_1.txt": {
                "content": "local 13:00",
                "date": "2014-01-01 13:00:00",
            },
            "folder5/file5_1.txt": {
                "content": "local5_1",
                "date": "2014-01-01 12:00:00",
            },
            "folder6/file6_1.txt": {
                "content": "local6_1",
                "date": "2014-01-01 12:00:00",
            },
            "folder7/file7_1.txt": {
                "content": "local 13:00",
                "date": "2014-01-01 13:00:00",
            },
            "new_file1.txt": {"content": "local 13:00", "date": "2014-01-01 13:00:00"},
        }
        self.assert_test_folder_equal(get_test_folder("remote"), expect_remote)

    def test_delete(self):
        opts = {"verbose": self.verbose, "resolve": "skip", "delete": True}

        stats = self.do_run_suite(UploadSynchronizer, opts)
        self._dump_de_facto_results(stats)

        # We expect 7 conflicts, and leave them unresolved (i.e. skip them all)

        self.assertEqual(stats["files_written"], 3)
        self.assertEqual(stats["download_files_written"], 0)
        self.assertEqual(stats["upload_files_written"], 3)
        self.assertEqual(stats["files_deleted"], 2)
        self.assertEqual(stats["dirs_deleted"], 2)
        self.assertEqual(stats["conflict_files"], 7)
        self.assertEqual(stats["conflict_files_skipped"], 7)

        self.assert_test_folder_equal(
            get_test_folder("local"), _SyncTestBase.local_fixture_modified
        )

        # We expect that remote only contains files that match '*1.txt'
        expect_remote = {
            "file1.txt": {"content": "local1", "date": "2014-01-01 12:00:00"},
            "file2.txt": {"content": "local 13:00", "date": "2014-01-01 13:00:00"},
            "file4.txt": {"content": "remote 13:00", "date": "2014-01-01 13:00:00"},
            "file6.txt": {"content": "remote 13:00:05", "date": "2014-01-01 13:00:05"},
            "file7.txt": {"content": "remote 13:00", "date": "2014-01-01 13:00:00"},
            "file8.txt": {"content": "remote 13:00", "date": "2014-01-01 13:00:00"},
            "folder1/file1_1.txt": {
                "content": "local1_1",
                "date": "2014-01-01 12:00:00",
            },
            "folder2/file2_1.txt": {
                "content": "local 13:00",
                "date": "2014-01-01 13:00:00",
            },
            "folder5/file5_1.txt": {
                "content": "remote 13:00",
                "date": "2014-01-01 13:00:00",
            },
            "new_file1.txt": {"content": "local 13:00", "date": "2014-01-01 13:00:00"},
            "new_file3.txt": {"content": "local 13:00", "date": "2014-01-01 13:00:00"},
            "new_file4.txt": {
                "content": "remote 13:00 with other content",
                "date": "2014-01-01 13:00:00",
            },
            "new_file5.txt": {
                "content": "remote 13:00:05",
                "date": "2014-01-01 13:00:05",
            },
            "new_file6.txt": {"content": "remote 13:00", "date": "2014-01-01 13:00:00"},
        }
        self.assert_test_folder_equal(get_test_folder("remote"), expect_remote)


# ===============================================================================
# FtpUploadResolveTest
# ===============================================================================


class FtpUploadResolveTest(UploadResolveTest):
    """Run the UploadResolveTest test suite against a local FTP server (ftp_target.FtpTarget)."""

    use_ftp_target = True


# ===============================================================================
# Main
# ===============================================================================
if __name__ == "__main__":
    unittest.main()
