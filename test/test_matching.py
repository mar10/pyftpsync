# -*- coding: utf-8 -*-
"""
Tests for pyftpsync
"""

# Don't check for double quotes
# flake8: noqa: Q000

from __future__ import print_function

import re
import unittest
from test.fixture_tools import (
    _SyncTestBase,
    get_local_test_url,
    get_remote_test_url,
    run_script,
)


# ===============================================================================
# MatchTest
# ===============================================================================
class MatchTest(_SyncTestBase):
    """Test --match and --exclude."""

    def setUp(self):
        super(MatchTest, self).setUp()
        self.local = get_local_test_url()
        self.remote = get_remote_test_url()

    def tearDown(self):
        super(MatchTest, self).tearDown()

    re_whitespace = re.compile(r"\s+")

    def assert_scan_equal(self, out, expect, ignore_order=True):
        # out = out.strip().split("\n")
        # out = map(lambda s: re.sub(self.re_whitespace, " ", s), out)
        #
        # out = list(out)
        a = []
        for s in out.split("\n"):
            # append first token (i.e. file or folder name)
            if s.startswith("Scanning "):
                break
            a.append(s.strip().split(" ")[0].strip())
        # print(out)
        if isinstance(expect, str):
            expect = expect.strip().split("\n")
        if ignore_order:
            a.sort()
            expect = sorted(expect)
        self.assertListEqual(a, expect)

    def test_match_all(self):
        out = run_script("scan", self.local, "--list", "--recursive")
        self.assert_scan_equal(
            out,
            [
                "file1.txt",
                "file2.txt",
                "file3.txt",
                "file4.txt",
                "file5.txt",
                "file6.txt",
                "file7.txt",
                "file8.txt",
                "file9.txt",
                "[folder1]",
                "file1_1.txt",
                "[folder2]",
                "file2_1.txt",
                "[folder3]",
                "file3_1.txt",
                "[folder4]",
                "file4_1.txt",
                "[folder5]",
                "file5_1.txt",
                "[folder6]",
                "file6_1.txt",
                "[folder7]",
                "file7_1.txt",
            ],
        )

    def test_match_flat(self):
        out = run_script("scan", self.local, "--list")
        self.assert_scan_equal(
            out,
            [
                "file1.txt",
                "file2.txt",
                "file3.txt",
                "file4.txt",
                "file5.txt",
                "file6.txt",
                "file7.txt",
                "file8.txt",
                "file9.txt",
                "[folder1]",
                "[folder2]",
                "[folder3]",
                "[folder4]",
                "[folder5]",
                "[folder6]",
                "[folder7]",
            ],
        )

    def test_match_5(self):
        out = run_script("scan", self.local, "--list", "--recursive", "--match", "*5*")
        self.assert_scan_equal(
            out,
            [
                "file5.txt",
                "[folder1]",
                "[folder2]",
                "[folder3]",
                "[folder4]",
                "[folder5]",
                "file5_1.txt",
                "[folder6]",
                "[folder7]",
            ],
        )

    def test_match_5b(self):
        out = run_script(
            "scan",
            self.local,
            "--list",
            "--recursive",
            "--match",
            "*5*",
            "--exclude",
            "folder?",
        )
        self.assert_scan_equal(out, ["file5.txt"])


# ===============================================================================
# FtpMatchTest
# ===============================================================================


class FtpMatchTest(MatchTest):
    """Run the BidirSyncTest test suite against a local FTP server (ftp_target.FtpTarget)."""

    use_ftp_target = True


# ===============================================================================
# Main
# ===============================================================================
if __name__ == "__main__":
    unittest.main()
