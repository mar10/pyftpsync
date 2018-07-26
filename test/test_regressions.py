# -*- coding: utf-8 -*-
"""
Tests for pyftpsync
"""
from __future__ import print_function

import platform
import unittest
from unittest.case import SkipTest

from ftpsync.compat import urlparse
from test.fixture_tools import PYFTPSYNC_TEST_FTP_URL
from ftpsync.synchronizers import UploadSynchronizer
from ftpsync.targets import FsTarget

on_windows = platform.system() == "Windows"


# ===============================================================================
# FtpTest
# ===============================================================================
class RegressionTest(unittest.TestCase):
    """Test basic ftplib.FTP functionality."""
    def setUp(self):
        # Remote URL, e.g. "ftps://user:password@example.com/my/test/folder"
        ftp_url = PYFTPSYNC_TEST_FTP_URL
        if not ftp_url:
            raise SkipTest("Must configure an FTP target "
                           "(environment variable PYFTPSYNC_TEST_FTP_URL)")

        parts = urlparse(ftp_url, allow_fragments=False)
        # self.assertIn(parts.scheme.lower(), ["ftp", "ftps"])
        self.host = parts.netloc.split("@", 1)[1]
        self.path = parts.path
        self.username = parts.username
        self.password = parts.password
        self.remote = None

    def tearDown(self):
        if self.remote:
            self.remote.close()
            self.remote = None

    # def test_issue_5(self):
    #     """issue #5: Unable to navigate to working directory '' (Windows)"""
    #     if not on_windows:
    #         raise SkipTest("Windows only.")
    #     local = targets.FsTarget("c:/temp")
    #     remote = FtpTarget("/", "www.example.com", None, self.username, self.password)
    #     opts = {
    #         "resolve": "remote",
    #         "verbose": 3,
    #         "dry_run": True,
    #         }
    #     s = DownloadSynchronizer(local, remote, opts)
    #     s.run()

    def test_issue_31(self):
        """issue #31: exclude files"""
        local = FsTarget("/Users/martin/prj/git/pyftpsync")
        remote = FsTarget("/Users/martin/prj/temp")
        opts = {
            # "resolve": "remote",
            "verbose": 5,
            "dry_run": True,
            # "exclude": [".git", ".cache"],
            # "exclude": ".git,.cache",
            }
        s = UploadSynchronizer(local, remote, opts)
        s.run()
        # raise


# ===============================================================================
# Main
# ===============================================================================
if __name__ == "__main__":
    unittest.main()
