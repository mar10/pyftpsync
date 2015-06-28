# -*- coding: UTF-8 -*-
"""
Tests for pyftpsync
"""
from __future__ import print_function

from ftplib import FTP
from pprint import pprint
import platform
import sys

if sys.version_info < (2, 7):
    # Python 2.6
    import unittest2 as unittest
    from unittest2.case import SkipTest
else:
    # Python 2.7+
    import unittest
    from unittest.case import SkipTest

on_windows = platform.system() == "Windows"

from ftpsync.ftp_target import *  # @UnusedWildImport
from ftpsync.targets import *  # @UnusedWildImport

from ftpsync.synchronizers import DownloadSynchronizer, UploadSynchronizer, \
    BiDirSynchronizer
from test.tools import PYFTPSYNC_TEST_FTP_URL, prepare_fixtures_1, \
    PYFTPSYNC_TEST_FOLDER, _get_test_file_date, STAMP_20140101_120000, \
    _empty_folder, _write_test_file, _touch_test_file


DO_BENCHMARKS = False #True

#===============================================================================
# Module setUp / tearDown
#===============================================================================
def setUpModule():
    pass

def tearDownModule():
    pass


#===============================================================================
# FtpTest
#===============================================================================
class RegressionTest(unittest.TestCase):                          
    """Test basic ftplib.FTP functionality."""
    def setUp(self):
        # Remote URL, e.g. "ftp://user:password@example.com/my/test/folder"
        ftp_url = PYFTPSYNC_TEST_FTP_URL
        if not ftp_url:
            self.skipTest("Must configure a FTP target (environment variable PYFTPSYNC_TEST_FTP_URL)")

        parts = urlparse(ftp_url, allow_fragments=False)
        # self.assertEqual(parts.scheme.lower(), "ftp")
        self.host = parts.netloc.split("@", 1)[1]
        self.path = parts.path
        self.username = parts.username
        self.password = parts.password
        self.remote = None

    def tearDown(self):
        if self.remote:
            self.remote.close()
            self.remote = None
        
    def test_issue_5(self):
        """issue #5: Unable to navigate to working directory '' (Windows)"""
        if not on_windows:
            raise SkipTest("Windows only")
        local = targets.FsTarget("c:/temp")
        remote = FtpTarget("/", "www.wwwendt.de", None, self.username, self.password)
        opts = {
            "resolve": "remote",
            "verbose": 3,
            "dry_run": True
        }
        s = DownloadSynchronizer(local, remote, opts)
        s.run()        

#===============================================================================
# Main
#===============================================================================
if __name__ == "__main__":
    unittest.main()
