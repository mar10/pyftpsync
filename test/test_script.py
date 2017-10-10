# -*- coding: UTF-8 -*-
"""
Tests for pyftpsync
"""
from __future__ import print_function

import os
import sys
import unittest

from ftpsync import pyftpsync, __version__
from test.fixture_tools import _SyncTestBase, PYFTPSYNC_TEST_FOLDER


try:
    from io import StringIO
except ImportError:
    from cStringIO import StringIO


class Capturing(list):
    def __enter__(self):
        self._stdout = sys.stdout
        sys.stdout = self._stringio = StringIO()
        return self
    def __exit__(self, *args):
        self.extend(self._stringio.getvalue().splitlines())
        del self._stringio    # free up some memory
        sys.stdout = self._stdout


def run_script(*args, expect_code=0, **kw):
    """Run `pyftpsync args` and return (errcode, output)."""
    pyftpsync.sys.argv = ["pyftpsync_dummy"] + list(args)
    # print("S", sys.argv)
    errcode = 0
    out = []
    try:
        with Capturing() as out:
            pyftpsync.run()
    except SystemExit as e:
        errcode = e.code

    if expect_code is not None:
        assert errcode == expect_code

    return "\n".join(out).strip()


#===============================================================================
# ScriptTest
#===============================================================================

class ScriptTest(_SyncTestBase):
    """Test command line script interface."""

    def setUp(self):
        # Call self._prepare_initial_synced_fixture():
        super(ScriptTest, self).setUp()

    def tearDown(self):
        super(ScriptTest, self).tearDown()

    def test_basic(self):
        out = run_script("--version")
        # self.assertEqual(errcode, 0)
        self.assertEqual(out, __version__)

        out = run_script("--help")
        assert "usage: pyftpsync" in out

        out = run_script("foobar", expect_code=2)

    def test_scan_list(self):
        out = run_script("scan", os.path.join(PYFTPSYNC_TEST_FOLDER, "local"), "--list")
        assert "file1.txt                                2014-01-01 13:00:00" in out


#===============================================================================
# Main
#===============================================================================
if __name__ == "__main__":
    unittest.main()
