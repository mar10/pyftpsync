# -*- coding: utf-8 -*-
"""
Tests for pyftpsync
"""

# Don't check for double quotes
# flake8: noqa: Q000

import re
import unittest
from pprint import pprint

from tests.fixture_tools import (
    _SyncTestBase,
    get_local_test_url,
    get_remote_test_url,
    run_script,
)


# ===============================================================================
# TreeTest
# ===============================================================================
class TreeTest(_SyncTestBase):
    """Test `tree`command."""

    def setUp(self):
        super(TreeTest, self).setUp()
        self.local = get_local_test_url()
        self.remote = get_remote_test_url()

    def tearDown(self):
        super(TreeTest, self).tearDown()

    re_whitespace = re.compile(r"\s+")

    def assert_tree_equal(self, out, expect):
        # Strip away trailing file date and size and ignore summary line
        a = []
        for s in out.split("\n"):
            if s.startswith("Scanning "):
                break
            s = s.split(" 2014-", 1)[0]
            a.append(s.rstrip())
        pprint(a)
        # if isinstance(expect, str):
        #     expect = expect.rstrip().split("\n")
        self.assertListEqual(a, expect)

    def test_all_files(self):
        out = run_script("tree", self.local, "--files", "--sort")
        self.assert_tree_equal(
            out,
            [
                "[C:\\Prj\\test\\test_pyftpsync\\local]",
                " +- file1.txt",
                " +- file2.txt",
                " +- file3.txt",
                " +- file4.txt",
                " +- file5.txt",
                " +- file6.txt",
                " +- file7.txt",
                " +- file8.txt",
                " +- file9.txt",
                " +- [folder1]",
                " |   `- file1_1.txt",
                " +- [folder2]",
                " |   `- file2_1.txt",
                " +- [folder3]",
                " |   `- file3_1.txt",
                " +- [folder4]",
                " |   `- file4_1.txt",
                " +- [folder5]",
                " |   `- file5_1.txt",
                " +- [folder6]",
                " |   `- file6_1.txt",
                " `- [folder7]",
                "     `- file7_1.txt",
            ],
        )


# ===============================================================================
# FtpTreeTest
# ===============================================================================


class FtpTreeTest(TreeTest):
    """Run the BidirSyncTest test suite against a local FTP server (ftp_target.FTPTarget)."""

    use_ftp_target = True


# ===============================================================================
# Main
# ===============================================================================
if __name__ == "__main__":
    unittest.main()
