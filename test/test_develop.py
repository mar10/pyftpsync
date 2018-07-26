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
    empty_folder,
    get_local_test_url,
    get_remote_test_url,
    get_test_file_size,
    is_test_file,
    run_script,
    write_test_file,
)
from unittest.case import SkipTest

from ftpsync.synchronizers import DownloadSynchronizer, UploadSynchronizer
from ftpsync.targets import make_target


# ===============================================================================
# TempDevelopTest
# ===============================================================================
class TempDevelopTest(_SyncTestBase):
    """Test DownSynchronizer on file system targets with different resolve modes."""

    def setUp(self):
        # Call self._prepare_initial_synced_fixture():
        super(TempDevelopTest, self).setUp()
        self.local_url = get_local_test_url()
        self.remote_url = get_remote_test_url()

    def tearDown(self):
        super(TempDevelopTest, self).tearDown()

    def test_issue_20(self):

        opts = {"verbose": 5}

        local_target = make_target(self.local_url)
        remote_target = make_target(self.remote_url)

        ftp_downloader = DownloadSynchronizer(local_target, remote_target, opts)
        ftp_uploader = UploadSynchronizer(local_target, remote_target, opts)

        write_test_file("local/large1.txt", size=10 * 1000)
        write_test_file("remote/large2.txt", size=10 * 1000)
        ftp_downloader.run()
        ftp_uploader.run()

    def test_issue_21(self):
        if not self.use_ftp_target:
            raise SkipTest("Only FTP targets.")
        write_test_file("local/large.txt", size=10 * 1000)
        write_test_file("remote/large.txt", size=10 * 1000)

        out = run_script("download", "-vvv", self.local_url, self.remote_url)
        #         print(out)
        assert not ("*cmd* 'PORT" in out or "*cmd* 'EPRT" in out)
        assert "*cmd* 'PASV" in out or "*cmd* 'EPSV" in out

        out = run_script(
            "download", self.local_url, self.remote_url, "-vvv", "--ftp-active"
        )
        #         print(out)
        assert "*cmd* 'PORT" in out or "*cmd* 'EPRT" in out
        assert not ("*cmd* 'PASV" in out or "*cmd* 'EPSV" in out)

    def test_issue_24(self):
        if not self.use_ftp_target:
            raise SkipTest("Only FTP targets.")

        #         empty_folder()
        empty_folder(os.path.join(PYFTPSYNC_TEST_FOLDER, "local"))
        empty_folder(os.path.join(PYFTPSYNC_TEST_FOLDER, "remote"))

        local_target = make_target(self.local_url)
        remote_target = make_target(self.remote_url)

        SIZE = 1000 * 1000
        write_test_file("local/large1.txt", size=SIZE)
        write_test_file("remote/large2.txt", size=SIZE)

        opts = {"verbose": 5, "match": "large*.txt"}
        synchronizer = DownloadSynchronizer(local_target, remote_target, opts)

        assert is_test_file("local/large1.txt")
        assert is_test_file("remote/large2.txt")
        assert not is_test_file("remote/large1.txt")
        assert not is_test_file("local/large2.txt")

        synchronizer.run()

        # Expect that large2 was downloaded
        assert not is_test_file("remote/large1.txt")
        assert get_test_file_size("local/large2.txt") == SIZE


# ===============================================================================
# TempDevelopTest
# ===============================================================================


class FtpTempDevelopTest(TempDevelopTest):
    """Run the DownloadResolveTest test suite against a local FTP server (ftp_target.FtpTarget)."""

    use_ftp_target = True


# ===============================================================================
# Main
# ===============================================================================
if __name__ == "__main__":
    unittest.main()
