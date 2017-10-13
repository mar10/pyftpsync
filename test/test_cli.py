# -*- coding: UTF-8 -*-
"""
Tests for pyftpsync
"""
from __future__ import print_function

import os
import re
import sys
import unittest

from ftpsync import pyftpsync, __version__
from test.fixture_tools import _SyncTestBase, PYFTPSYNC_TEST_FOLDER, CaptureStdout, \
    get_local_test_url, get_remote_test_url


def run_script(*args, **kw):
    """Run `pyftpsync <args>`, check exit code, and return output.

    Example:
        out = run_script("-h")
        assert "pyftpsync" in out

        out = run_script("foobar", expect_code=2)
    """
    expect_code = kw.get("expect_code", 0)
    sys.argv = ["pyftpsync_dummy"] + list(args)
    errcode = 0
    out = []
    try:
        # Depending on the Python version, some output may go to stdout or stderr,
        # so we capture both (see https://stackoverflow.com/a/31715011/19166)
        with CaptureStdout() as out:
            pyftpsync.run()
    except SystemExit as e:
        errcode = e.code

    if expect_code is not None:
        assert errcode == expect_code

    return "\n".join(out).strip()


#===============================================================================
# CliTest
#===============================================================================

class CliTest(_SyncTestBase):
    """Test command line script interface."""

    def setUp(self):
        # Call self._prepare_initial_synced_fixture():
        super(CliTest, self).setUp()
        self.local = get_local_test_url()
        self.remote = get_remote_test_url()

    def tearDown(self):
        super(CliTest, self).tearDown()

    def test_basic(self):
        out = run_script("--version")
        assert out == __version__

        out = run_script("--help")
        assert "usage: pyftpsync" in out

        out = run_script("foobar", expect_code=2)

    def test_scan_list(self):
        out = run_script("scan", self.local, "--list")
        # We expect "file1.txt [spaces] 2014-01-01 13:00:00"
        # but the time zone may be different on the travis server, so we relax:
        assert re.match("file1.txt\s+2014-01-01 \d\d:00:00", out)

    def test_sync(self):
        out = run_script("sync", self.local, self.remote, "--dry-run")
        assert "(DRY-RUN) Wrote 0/16 files in 7 dirs" in out

    def test_upload(self):
        out = run_script("upload", self.local, self.remote, "--dry-run")
        assert "(DRY-RUN) Wrote 0/16 files in 7 dirs" in out

    def test_download(self):
        out = run_script("download", self.local, self.remote, "--dry-run")
        assert "(DRY-RUN) Wrote 0/16 files in 7 dirs" in out


#===============================================================================
# Main
#===============================================================================
if __name__ == "__main__":
    unittest.main()
