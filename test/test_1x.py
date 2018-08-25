# -*- coding: utf-8 -*-
"""
Tests for pyftpsync
"""
from __future__ import print_function

import datetime
import os
import unittest
from test.fixture_tools import (
    PYFTPSYNC_TEST_FOLDER,
    STAMP_20140101_120000,
    empty_folder,
    get_test_file_date,
    touch_test_file,
    write_test_file,
)

from ftpsync.synchronizers import (
    BiDirSynchronizer,
    DownloadSynchronizer,
    UploadSynchronizer,
)
from ftpsync.targets import FsTarget


# ===============================================================================
# prepare_fixtures_1
# ===============================================================================
def prepare_fixtures_1():
    """Create two test folders and some files.

    """
    print("Prepare_fixtures", PYFTPSYNC_TEST_FOLDER)
    # print("PYFTPSYNC_TEST_FOLDER", os.environ.get("PYFTPSYNC_TEST_FOLDER"))
    # print("PYFTPSYNC_TEST_FTP_URL", os.environ.get("PYFTPSYNC_TEST_FTP_URL"))

    assert os.path.isdir(PYFTPSYNC_TEST_FOLDER)
    # Reset all
    empty_folder(PYFTPSYNC_TEST_FOLDER)
    # Add some files to ../local/
    dt = datetime.datetime(2014, 1, 1, 12, 0, 0)
    write_test_file("local/file1.txt", content="111", dt=dt)
    write_test_file("local/file2.txt", content="222", dt=dt)
    write_test_file("local/file3.txt", content="333", dt=dt)
    write_test_file("local/folder1/file1_1.txt", content="1.111", dt=dt)
    write_test_file("local/folder2/file2_1.txt", content="2.111", dt=dt)
    write_test_file("local/big_file.txt", size=1024 * 16, dt=dt)
    # Create empty ../remote/
    os.mkdir(os.path.join(PYFTPSYNC_TEST_FOLDER, "remote"))


# ===============================================================================
# FilesystemTest
# ===============================================================================


class FilesystemTest(unittest.TestCase):
    """Test different synchronizers on file system targets."""

    def setUp(self):
        # raise SkipTest
        self.verbose = 3  # 4
        prepare_fixtures_1()

    def tearDown(self):
        pass

    def test_download_fs_fs(self):
        # Download files from local to remote (which is empty)
        local = FsTarget(os.path.join(PYFTPSYNC_TEST_FOLDER, "remote"))
        remote = FsTarget(os.path.join(PYFTPSYNC_TEST_FOLDER, "local"))
        opts = {"force": False, "delete": False, "verbose": self.verbose}
        s = DownloadSynchronizer(local, remote, opts)
        s.run()
        stats = s.get_stats()
        #        pprint(stats)
        self.assertEqual(stats["local_dirs"], 0)
        self.assertEqual(stats["local_files"], 0)
        self.assertEqual(stats["remote_dirs"], 2)
        # currently files are not counted, when inside a *new* folder:
        self.assertEqual(stats["remote_files"], 4)
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
        self.assertEqual(get_test_file_date("local/file1.txt"), STAMP_20140101_120000)
        self.assertEqual(get_test_file_date("remote/file1.txt"), STAMP_20140101_120000)

    def test_upload_fs_fs(self):
        local = FsTarget(os.path.join(PYFTPSYNC_TEST_FOLDER, "local"))
        remote = FsTarget(os.path.join(PYFTPSYNC_TEST_FOLDER, "remote"))
        opts = {"force": False, "delete": False, "verbose": self.verbose}
        s = UploadSynchronizer(local, remote, opts)
        s.run()
        stats = s.get_stats()
        #        pprint(stats)
        self.assertEqual(stats["local_dirs"], 2)
        # currently files are not counted, when inside a *new* folder:
        self.assertEqual(stats["local_files"], 4)
        self.assertEqual(stats["remote_dirs"], 0)
        self.assertEqual(stats["remote_files"], 0)
        self.assertEqual(stats["files_written"], 6)
        self.assertEqual(stats["dirs_created"], 2)
        self.assertEqual(stats["bytes_written"], 16403)
        # file times are preserved
        self.assertEqual(get_test_file_date("local/file1.txt"), STAMP_20140101_120000)
        self.assertEqual(get_test_file_date("remote/file1.txt"), STAMP_20140101_120000)

    def test_sync_fs_fs(self):
        local = FsTarget(os.path.join(PYFTPSYNC_TEST_FOLDER, "local"))
        remote = FsTarget(os.path.join(PYFTPSYNC_TEST_FOLDER, "remote"))
        opts = {"dry_run": False, "verbose": self.verbose}  # , "resolve": "ask"}
        s = BiDirSynchronizer(local, remote, opts)
        s.run()
        stats = s.get_stats()
        #        pprint(stats)
        self.assertEqual(stats["local_dirs"], 2)
        # currently files are not counted, when inside a *new* folder:
        self.assertEqual(stats["local_files"], 4)
        self.assertEqual(stats["remote_dirs"], 0)
        self.assertEqual(stats["remote_files"], 0)
        self.assertEqual(stats["files_written"], 6)
        self.assertEqual(stats["dirs_created"], 2)
        self.assertEqual(stats["bytes_written"], 16403)
        # file times are preserved
        self.assertEqual(get_test_file_date("local/file1.txt"), STAMP_20140101_120000)
        self.assertEqual(get_test_file_date("remote/file1.txt"), STAMP_20140101_120000)

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
        touch_test_file("local/file1.txt")
        touch_test_file("remote/file2.txt")
        # file3.txt will cause a conflict:
        touch_test_file("local/file3.txt")
        dt = datetime.datetime.utcnow() - datetime.timedelta(seconds=10)
        touch_test_file("remote/file3.txt", dt=dt)

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
        touch_test_file("local/file1.txt", dt)
        dt = datetime.datetime.utcnow() - datetime.timedelta(seconds=10)
        touch_test_file("remote/file1.txt", dt=dt)
        #         path = os.path.join(PYFTPSYNC_TEST_FOLDER, "remote/file1.txt")
        #         stamp = time.time() - 10
        #         os.utime(path, (stamp, stamp))

        # conflict 2: remote is newer
        touch_test_file("remote/file2.txt")
        dt = datetime.datetime.utcnow() - datetime.timedelta(seconds=10)
        touch_test_file("local/file2.txt", dt=dt)

        s = BiDirSynchronizer(local, remote, opts)
        s.run()
        stats = s.get_stats()
        #         pprint(stats)
        self.assertEqual(stats["entries_seen"], 18)
        self.assertEqual(stats["entries_touched"], 0)
        self.assertEqual(stats["bytes_written"], 0)
        self.assertEqual(stats["conflict_files"], 2)


# ===============================================================================
# Main
# ===============================================================================
if __name__ == "__main__":
    unittest.main()
