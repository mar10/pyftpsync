# -*- coding: UTF-8 -*-
"""
Tests for pyftpsync
"""
from __future__ import print_function

import unittest

from ftpsync.synchronizers import DownloadSynchronizer
from test.fixture_tools import get_test_folder, _SyncTestBase, run_script, get_local_test_url,\
    get_remote_test_url, write_test_file
from unittest.case import SkipTest


# ===============================================================================
# TempDevelopTest
# ===============================================================================
class TempDevelopTest(_SyncTestBase):
    """Test DownSynchronizer on file system targets with different resolve modes."""

    def setUp(self):
        # Call self._prepare_initial_synced_fixture():
        super(TempDevelopTest, self).setUp()
        if self.__class__ is TempDevelopTest:
            raise SkipTest("Only FTP")
        self.local = get_local_test_url()
        self.remote = get_remote_test_url()

    def tearDown(self):
        super(TempDevelopTest, self).tearDown()

    def test_issue_20(self):

        opts = {
            "verbose": 10,
            "ftp_debug": 1,
            "ftp_active": True,
#             "resolve": "remote",
#             "delete": True,
#             "delete_unmatched": True,
#             "force": True,
#             "match": "*1.txt",
            }

        write_test_file("remote/large.txt", size=10*1000)
        out = run_script("-vvv", "download", self.local, self.remote)
        print(out)
        assert not "*cmd* 'PORT" in out or "*cmd* 'EPRT" in out 
        assert ("*cmd* 'PASV" in out or "*cmd* 'EPSV" in out)   
#         assert "Wrote 1/16 files" in out

        out = run_script("-vvv", "download", self.local, self.remote, "--ftp-active")
        print(out)
        assert "*cmd* 'PORT" in out or "*cmd* 'EPRT" in out 
        assert not ("*cmd* 'PASV" in out or "*cmd* 'EPSV" in out)   

#         stats = self.do_run_suite(DownloadSynchronizer, opts)
#         self._dump_de_facto_results(stats)
# 
#         # We expect 7 conflicts, and leave them unresolved (i.e. skip them all)
# 
#         # self.assertEqual(stats["files_written"], 3)
#         # self.assertEqual(stats["files_written"], 3)
#         # self.assertEqual(stats["download_files_written"], 0)
#         # self.assertEqual(stats["upload_files_written"], 3)
#         # self.assertEqual(stats["files_deleted"], 1)
#         # self.assertEqual(stats["dirs_deleted"], 2)
#         # self.assertEqual(stats["conflict_files"], 7)
#         # self.assertEqual(stats["conflict_files_skipped"], 7)
# 
#         # We expect that remote remains unmodified
#         self.assert_test_folder_equal(get_test_folder("remote"),
#                                       _SyncTestBase.remote_fixture_modified)
# 
#         # We expect that local only contains files that match '*1.txt'
#         expect_local = {
#             'file1.txt': {'content': 'local1', 'date': '2014-01-01 12:00:00'},
#             'folder1/file1_1.txt': {'content': 'local1_1', 'date': '2014-01-01 12:00:00'},
#             'folder2/file2_1.txt': {'content': 'local2_1', 'date': '2014-01-01 12:00:00'},
#             'folder3/file3_1.txt': {'content': 'local3_1', 'date': '2014-01-01 12:00:00'},
#             'folder4/file4_1.txt': {'content': 'remote 13:00', 'date': '2014-01-01 13:00:00'},
#             'folder5/file5_1.txt': {'content': 'remote 13:00', 'date': '2014-01-01 13:00:00'},
#             }
#         self.assert_test_folder_equal(get_test_folder("local"), expect_local)


# ===============================================================================
# TempDevelopTest
# ===============================================================================

class FtpDownloadResolveTest(TempDevelopTest):
    """Run the DownloadResolveTest test suite against a local FTP server (ftp_target.FtpTarget)."""
    use_ftp_target = True


# ===============================================================================
# Main
# ===============================================================================
if __name__ == "__main__":
    unittest.main()
