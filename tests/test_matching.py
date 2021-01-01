# -*- coding: utf-8 -*-
"""
Tests for pyftpsync
"""

# Don't check for double quotes
# flake8: noqa: Q000

import re
import unittest

import pytest
from wcmatch.glob import GLOBSTAR, globmatch

from tests.fixture_tools import (
    _SyncTestBase,
    get_local_test_url,
    get_remote_test_url,
    run_script,
)


# ===============================================================================
# MatchTest
# ===============================================================================
class MatchTest(unittest.TestCase):
    """Test --match and --exclude."""

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_wcmatch(self):
        """Test basic wcmatch library behavior (with flags=GLOBSTAR)."""
        # We use the GLOBSTAR flag
        def gm(*args, flags=GLOBSTAR):
            return globmatch(*args, flags=flags)

        # Simple '*' only matches top-level entries:
        assert gm("folder5", ["*5*"]) is True
        assert gm("file1.txt", ["*5*"]) is False
        assert gm("file5.txt", ["*5*"]) is True
        assert gm("folder5/file5_1.txt", ["*5*"]) is False
        assert gm("folder1/file5_1.txt", ["*5*"]) is False
        # '**' matches all directories
        assert gm("folder5/file5_1.txt", ["**/*5*"]) is True
        assert gm("folder1/file5_1.txt", ["**/*5*"]) is True
        assert gm("folder1/file1_1.txt", ["**/*5*"]) is False
        # ... even multi-level
        assert gm("folder1/folder1.1/file5_1.txt", ["**/*5*"]) is True
        # ... or top-level
        assert gm("file5_1.txt", ["**/*5*"]) is True
        # '*/' can be used to match direct parent folders
        assert gm("folder1/file5_1.txt", ["*5*/*5*"]) is False
        assert gm("folder5/file5_1.txt", ["*5*/*5*"]) is True
        # ... but not indirect
        assert gm("folder5/folder5/file5_1.txt", ["*5*/*5*"]) is False
        assert gm("folder5/folder5/file5_1.txt", ["*5*/*5*/*5*"]) is True


# ===============================================================================
# ScanTest
# ===============================================================================
class ScanTest(_SyncTestBase):
    """Test --match and --exclude."""

    def setUp(self):
        super(ScanTest, self).setUp()
        self.local = get_local_test_url()
        self.remote = get_remote_test_url()

    def tearDown(self):
        super(ScanTest, self).tearDown()

    re_whitespace = re.compile(r"\s+")

    def assert_scan_equal(self, out, expect, msg=None, ignore_order=True):
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
        self.assertListEqual(a, expect, msg=msg)

    def test_scan_all(self):

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
            msg="Match all files and folders (flat)",
        )

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
            msg="Match all files and folders (recursive)",
        )

    def test_scan_match_flat(self):
        out = run_script("scan", self.local, "--list", "--match", "*5.*")
        self.assert_scan_equal(
            out,
            [
                "file5.txt",
            ],
            msg="Match all files and folders containing '5' (flat)",
        )
        # If '**' pattern is used, --recursive is mandatory
        with pytest.raises(RuntimeError, match=r".* --recursive .*"):
            run_script("scan", self.local, "--list", "--match", "**/5.*")

    def test_scan_match_deep(self):
        out = run_script("scan", self.local, "--list", "--recursive", "--match", "*5*")
        self.assert_scan_equal(
            out,
            [
                "file5.txt",
                "[folder5]",
            ],
            msg="Match all files and folders containing '5' (recursive)",
        )

        out = run_script(
            "scan", self.local, "--list", "--recursive", "--match", "**/*5*"
        )
        self.assert_scan_equal(
            out,
            [
                "file5.txt",
                "[folder5]",
                "file5_1.txt",
            ],
            msg="Match all files and folders containing '5' (recursive)",
        )

        # out = run_script("scan", self.local, "--list", "--recursive", "--match", "*5*")
        # self.assert_scan_equal(
        #     out,
        #     [
        #         "file5.txt",
        #     ],
        #     msg="Match all files and folders containing '5' (flat)",
        # )


# ===============================================================================
# FtpMatchTest
# ===============================================================================


class FtpScanTest(ScanTest):
    """Run the BidirSyncTest test suite against a local FTP server (ftp_target.FTPTarget)."""

    use_ftp_target = True


# ===============================================================================
# Main
# ===============================================================================
if __name__ == "__main__":
    unittest.main()
