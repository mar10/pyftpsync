# -*- coding: UTF-8 -*-
"""
Tests for pyftpsync
"""
from __future__ import print_function

import unittest

from ftpsync.synchronizers import DownloadSynchronizer, UploadSynchronizer
from test.fixture_tools import _SyncTestBase, run_script, get_local_test_url,\
    get_remote_test_url, write_test_file, empty_folder, PYFTPSYNC_TEST_FOLDER
from unittest.case import SkipTest
from ftpsync.targets import make_target, FsTarget
import os
from ftpsync.ftp_target import FtpTarget
from tempfile import SpooledTemporaryFile


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

        opts = {
            "verbose": 5,
            }

        local_target = make_target(self.local_url)
        remote_target = make_target(self.remote_url)

        ftp_downloader = DownloadSynchronizer(local_target, remote_target, opts)
        ftp_uploader = UploadSynchronizer(local_target, remote_target, opts)

        write_test_file("local/large1.txt", size=10*1000)
        write_test_file("remote/large2.txt", size=10*1000)
        ftp_downloader.run()
        ftp_uploader.run()

    def test_issue_21(self):
        if not self.use_ftp_target:
            raise SkipTest("Only FTP targets.")
        write_test_file("local/large.txt", size=10*1000)
        write_test_file("remote/large.txt", size=10*1000)

        out = run_script("-vvv", "download", self.local_url, self.remote_url)
#         print(out)
        assert not ("*cmd* 'PORT" in out or "*cmd* 'EPRT" in out)
        assert "*cmd* 'PASV" in out or "*cmd* 'EPSV" in out

        out = run_script("-vvv", "download", self.local_url, self.remote_url, "--ftp-active")
#         print(out)
        assert "*cmd* 'PORT" in out or "*cmd* 'EPRT" in out
        assert not ("*cmd* 'PASV" in out or "*cmd* 'EPSV" in out)

    def test_logging(self):
        pass
        # import requests
        # import logging
        #
        # # Enabling debugging at http.client level (requests->urllib3->http.client)
        # # you will see the REQUEST, including HEADERS and DATA, and RESPONSE with HEADERS but without DATA.
        # # the only thing missing will be the response.body which is not logged.
        # try: # for Python 3
        #     from http.client import HTTPConnection
        # except ImportError:
        #     from httplib import HTTPConnection
        # HTTPConnection.debuglevel = 1
        #
        # logging.basicConfig() # you need to initialize logging, otherwise you will not see anything from requests
        # logging.getLogger().setLevel(logging.DEBUG)
        # requests_log = logging.getLogger("requests.packages.urllib3")
        # requests_log.setLevel(logging.DEBUG)
        # requests_log.propagate = True

    def test_issue_24(self):
        if not self.use_ftp_target:
            raise SkipTest("Only FTP targets.")

#         empty_folder()
        empty_folder(os.path.join(PYFTPSYNC_TEST_FOLDER, "local"))
        empty_folder(os.path.join(PYFTPSYNC_TEST_FOLDER, "remote"))

        local_target = make_target(self.local_url)
        remote_target = make_target(self.remote_url)

        write_test_file("local/large1.txt", size=1000*1000)
        write_test_file("remote/large2.txt", size=1000*1000)

        opts = {
            "verbose": 5,
            "match": "large*.txt",
            }
        synchronizer = DownloadSynchronizer(local_target, remote_target, opts)

        synchronizer.run()
        # assert False


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
