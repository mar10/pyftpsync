# -*- coding: utf-8 -*-
"""
Tests for pyftpsync
"""
import unittest
from test.fixture_tools import (
    PYFTPSYNC_TEST_FOLDER,
    _SyncTestBase,
    get_metadata,
    get_test_folder,
    is_test_file,
    read_test_file,
)

from ftpsync.sftp_target import SFTPTarget
from ftpsync.targets import make_target


# ===============================================================================
# PlainTest
# ===============================================================================
class SFTPTest(unittest.TestCase):
    """Tests that don't connect."""

    def setUp(self):
        # user, passwd = get_stored_credentials("pyftpsync.pw", self.HOST)
        pass

    def tearDown(self):
        pass

    def test_make_target(self):
        t = make_target("sftp://ftp.example.com/target/folder")
        self.assertTrue(isinstance(t, SFTPTarget))
        self.assertEqual(t.host, "ftp.example.com")
        self.assertEqual(t.root_dir, "/target/folder")
        self.assertEqual(t.username, None)

        # scheme is case-insensitive
        t = make_target("SFTP://ftp.example.com/target/folder")
        self.assertTrue(isinstance(t, SFTPTarget))
        self.assertEqual(t.host, "ftp.example.com")
        self.assertEqual(t.root_dir, "/target/folder")
        self.assertEqual(t.username, None)

        # pass credentials with URL
        url = "user:secret@ftp.example.com/target/folder"
        t = make_target("sftp://" + url)
        self.assertTrue(isinstance(t, SFTPTarget))
        self.assertEqual(t.host, "ftp.example.com")
        self.assertEqual(t.username, "user")
        self.assertEqual(t.password, "secret")
        self.assertEqual(t.root_dir, "/target/folder")

        url = "user@example.com:secret@ftp.example.com/target/folder"
        t = make_target("sftp://" + url)
        self.assertTrue(isinstance(t, SFTPTarget))
        self.assertEqual(t.host, "ftp.example.com")
        self.assertEqual(t.username, "user@example.com")
        self.assertEqual(t.password, "secret")
        self.assertEqual(t.root_dir, "/target/folder")


# class SFTPServerTest(unittest.TestCase):
#     """Tests that use `pytest.sftpserver` fixture."""
#     def test_sftp_fetch(self, sftpserver):
#         url = "user@example.com:secret@ftp.example.com/target/folder"
#         t = make_target("sftp://" + url)
#         with sftpserver.serve_content({"a_dir": {"somefile.txt": "File content"}}):
#             assert (
#                 get_sftp_file(
#                     sftpserver.host,
#                     sftpserver.port,
#                     "user",
#                     "pw",
#                     "/a_dir/somefile.txt",
#                 )
#                 == "File content"
#             )


# ===============================================================================
# Main
# ===============================================================================
if __name__ == "__main__":
    unittest.main()
