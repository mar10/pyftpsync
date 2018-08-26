# -*- coding: utf-8 -*-
"""
Tests for pyftpsync

<local_test_root_folder>/
    local/
    remote/
"""
from __future__ import print_function

import os
import sys
import unittest

# from ftpsync.targets import *  # @UnusedWildImport
from test.fixture_tools import (
    PYFTPSYNC_TEST_FOLDER,
    PYFTPSYNC_TEST_FTP_URL,
    empty_folder,
    write_test_file,
)
from test.test_1x import prepare_fixtures_1

# from ftpsync.ftp_target import *  # @UnusedWildImport
from ftpsync.synchronizers import DownloadSynchronizer, UploadSynchronizer
from ftpsync.targets import FsTarget, make_target

DO_BENCHMARKS = False  # True
# slow = pytest.mark.skipif(not pytest.config.getoption("--runslow"), reason="need --runslow")


# ===============================================================================
# BenchmarkTest
# ===============================================================================
class BenchmarkTest(unittest.TestCase):
    """Test ftp_target.FtpTarget functionality."""

    def setUp(self):
        if not DO_BENCHMARKS:
            self.skipTest("DO_BENCHMARKS is not set.")
        # Remote URL, e.g. "ftps://user:password@example.com/my/test/folder"
        ftp_url = PYFTPSYNC_TEST_FTP_URL
        if not ftp_url:
            self.skipTest(
                "Must configure an FTP target "
                "(environment variable PYFTPSYNC_TEST_FTP_URL)"
            )
        self.assertTrue(
            "/test" in ftp_url or "/temp" in ftp_url,
            "FTP target path must include '/test' or '/temp'",
        )

        # Create temp/local folder with files and empty temp/remote folder
        prepare_fixtures_1()

        self.remote = make_target(ftp_url)
        self.remote.open()
        # Delete all files in remote target folder
        self.remote._rmdir_impl(".", keep_root_folder=True)

    def tearDown(self):
        self.remote.close()
        del self.remote

    def _transfer_files(self, count, size):
        temp1_path = os.path.join(PYFTPSYNC_TEST_FOLDER, "local")
        empty_folder(temp1_path)  # remove standard test files

        local = FsTarget(temp1_path)
        remote = self.remote

        for i in range(count):
            write_test_file("local/file_{}.txt".format(i), size=size)

        # Upload all of temp/local to remote

        opts = {"force": False, "delete": False, "verbose": 3}
        s = UploadSynchronizer(local, remote, opts)
        s.run()
        stats = s.get_stats()
        #        pprint(stats)

        self.assertEqual(stats["files_written"], count)
        self.assertEqual(stats["bytes_written"], count * size)
        #        pprint(stats)
        print(
            "Upload {} x {} bytes took {}: {}".format(
                count, size, stats["upload_write_time"], stats["upload_rate_str"]
            ),
            file=sys.stderr,
        )

        # Download all of remote to temp/remote

        local = FsTarget(os.path.join(PYFTPSYNC_TEST_FOLDER, "remote"))

        opts = {"force": False, "delete": True, "verbose": 3}
        s = DownloadSynchronizer(local, remote, opts)
        s.run()
        stats = s.get_stats()
        #        pprint(stats)

        self.assertEqual(stats["files_written"], count)
        self.assertEqual(stats["bytes_written"], count * size)

        #        pprint(stats)
        print(
            "Download {} x {} bytes took {}: {}".format(
                count, size, stats["download_write_time"], stats["download_rate_str"]
            ),
            file=sys.stderr,
        )

    def test_transfer_small_files(self):
        """Transfer 20 KiB in many small files."""
        self._transfer_files(count=10, size=2 * 1024)

    def test_transfer_large_files(self):
        """Transfer 20 KiB in one large file."""
        self._transfer_files(count=1, size=20 * 1024)


# ===============================================================================
# Main
# ===============================================================================
if __name__ == "__main__":
    unittest.main()
