# -*- coding: utf-8 -*-
"""
Tests for pyftpsync
"""
from __future__ import print_function

import io
import json
import os
import sys
import unittest
from ftplib import FTP
from pprint import pprint
from test.fixture_tools import (
    PYFTPSYNC_TEST_FOLDER,
    PYFTPSYNC_TEST_FTP_URL,
    STAMP_20140101_120000,
    get_test_file_date,
    touch_test_file,
)
from test.test_1x import prepare_fixtures_1

from ftpsync.compat import urlparse
from ftpsync.metadata import DirMetadata
from ftpsync.synchronizers import (
    BiDirSynchronizer,
    DownloadSynchronizer,
    UploadSynchronizer,
)
from ftpsync.targets import FsTarget, make_target


# ===============================================================================
# FtpTest
# ===============================================================================
class FtpTest(unittest.TestCase):
    """Test basic ftplib.FTP functionality."""

    def setUp(self):
        # TODO: some of those tests are still relevant
        self.skipTest("Not yet implemented.")
        # Remote URL, e.g. "ftps://user:password@example.com/my/test/folder"
        ftp_url = PYFTPSYNC_TEST_FTP_URL
        if not ftp_url:
            self.skipTest(
                "Must configure an FTP target "
                "(environment variable PYFTPSYNC_TEST_FTP_URL)."
            )

        parts = urlparse(ftp_url, allow_fragments=False)
        self.assertIn(parts.scheme.lower(), ["ftp", "ftps"])
        print(ftp_url, parts)
        if "@" in parts.netloc:
            host = parts.netloc.split("@", 1)[1]
        else:
            host = parts.netloc
        self.PATH = parts.path
        self.ftp = FTP()
        #        self.ftp.debug(1)
        self.ftp.connect(host)
        self.ftp.login(parts.username, parts.password)

    def tearDown(self):
        # self.ftp.abort()
        # self.ftp.close()
        self.ftp.quit()
        del self.ftp

    def test_ftp(self):
        ftp = self.ftp
        self.assertEqual(ftp.pwd(), "/")
        ftp.cwd(self.PATH)
        self.assertEqual(ftp.pwd(), self.PATH)
        res = ftp.nlst()
        print(res)
        res = ftp.dir()
        print(res)

    def test_mlsd(self):
        ftp = self.ftp
        self.assertEqual(ftp.pwd(), "/")
        ftp.cwd(self.PATH)
        self.assertEqual(ftp.pwd(), self.PATH)

        def adder(line):
            print(line)

        ftp.retrlines("MLSD", adder)


#        dir = FTPDirectory(self.PATH)
#        dir.getdata(ftp)
#        for f in dir.walk():
#            print(f)


# ===============================================================================
# FtpTargetTest
# ===============================================================================
class FtpTargetTest(unittest.TestCase):
    """Test ftp_target.FtpTarget functionality."""

    def setUp(self):
        # Remote URL, e.g. "ftps://user:password@example.com/my/test/folder"

        # TODO: some of those tests are still relevant
        self.skipTest("Not yet implemented.")

        ftp_url = PYFTPSYNC_TEST_FTP_URL
        if not ftp_url:
            self.skipTest(
                "Must configure an FTP target "
                "(environment variable PYFTPSYNC_TEST_FTP_URL)"
            )
        self.assertTrue(
            "/test" in ftp_url or "/temp" in ftp_url,
            "FTP target path must include '/test' or '/temp'",
        )

        # Create temp/local folder with files and empty temp/remote folder
        prepare_fixtures_1()

        #        print(ftp_url)

        parts = urlparse(ftp_url, allow_fragments=False)
        self.assertIn(parts.scheme.lower(), ["ftp", "ftps"])
        #        print(parts)
        #        self.creds = parts.username, parts.password
        #        self.HOST = parts.netloc.split("@", 1)[1]
        self.PATH = parts.path
        #        user, passwd = get_stored_credentials("pyftpsync.pw", self.HOST)

        self.remote = make_target(ftp_url)
        self.remote.open()
        # This check is already performed in the constructor:
        #        self.assertEqual(self.remote.pwd(), self.PATH)

        # Delete all files in remote target folder, except for LOCK file
        self.remote._rmdir_impl(
            ".",
            keep_root_folder=True,
            predicate=lambda n: n != DirMetadata.LOCK_FILE_NAME,
        )

    def tearDown(self):
        # self.remote._rmdir_impl(".", keep_root_folder=True)
        self.remote.close()
        del self.remote

    def test_remote(self):
        remote = self.remote

        self.assertEqual(remote.pwd(), self.PATH)

        remote.cwd(self.PATH)
        self.assertEqual(remote.pwd(), self.PATH)

        self.assertRaises(RuntimeError, remote.cwd, "..")
        self.assertEqual(remote.pwd(), self.PATH)

    def test_readwrite(self):
        remote = self.remote

        if sys.version_info[0] < 3:
            # 'abc_äöü_ß¿€'
            b = "abc_\xc3\xa4\xc3\xb6\xc3\xbc_\xc3\x9f\xc2\xbf\xe2\x82\xac"
            u = b.decode("utf-8")
        else:
            u = "abc_äöü_¿ß"
        s = u.encode("utf-8")

        remote.write_text("write_test_u.txt", u)
        self.assertEqual(remote.read_text("write_test_u.txt"), u)

        remote.write_text("write_test_s.txt", s)
        self.assertEqual(remote.read_text("write_test_s.txt"), u)

    def test_json(self):
        remote = self.remote

        d = {"a": 1, "b": 2, "sub": {"x": 10, "y": 11}}
        pprint(d)
        if sys.version_info[0] == 2:
            s = json.dumps(d, indent=4, sort_keys=True)
            b = io.BytesIO(s)
        else:
            buf = io.StringIO()
            json.dump(d, buf, indent=4, sort_keys=True)
            #        print(buf.getvalue())
            buf.flush()
            buf.seek(0)
            while 1:
                s = buf.readline()
                if not s:
                    break
                print("%r" % s)
            buf.seek(0)
            print(buf.getvalue())
            b = io.BytesIO(bytes(buf.getvalue(), "utf-8"))
        res = remote.ftp.storlines("STOR " + "meta.json", b)
        print(res)

    #     def test_download_fs_ftp(self):
    #         local = FsTarget(os.path.join(PYFTPSYNC_TEST_FOLDER, "local"))
    #         remote = self.remote
    #         opts = {"force": False, "delete": False}
    #         s = DownloadSynchronizer(local, remote, opts)
    #         s.run()
    #         stats = s.get_stats()
    #         pprint(stats)
    # #        self.assertEqual(stats["source_files"], 1)

    def test_sync_fs_ftp(self):
        local = FsTarget(os.path.join(PYFTPSYNC_TEST_FOLDER, "local"))
        remote = self.remote

        # Upload all of temp/local to remote

        opts = {"force": False, "delete": True, "verbose": 3}
        s = UploadSynchronizer(local, remote, opts)
        s.run()

        stats = s.get_stats()
        #         pprint(stats)

        self.assertEqual(stats["local_dirs"], 2)
        # currently files are not counted, when inside a *new* folder:
        self.assertEqual(stats["local_files"], 4)
        self.assertEqual(stats["remote_dirs"], 0)
        self.assertEqual(stats["remote_files"], 0)
        self.assertEqual(stats["files_written"], 6)
        self.assertEqual(stats["dirs_created"], 2)
        self.assertEqual(stats["bytes_written"], 16403)

        # Change one file and upload again

        touch_test_file("local/file1.txt")

        opts = {"force": False, "delete": True, "verbose": 3}
        s = UploadSynchronizer(local, remote, opts)
        s.run()
        stats = s.get_stats()
        #         pprint(stats)
        #         assert False

        self.assertEqual(stats["entries_seen"], 18)  # ???
        self.assertEqual(stats["entries_touched"], 1)
        self.assertEqual(stats["files_created"], 0)
        self.assertEqual(stats["files_deleted"], 0)
        self.assertEqual(stats["files_written"], 1)
        self.assertEqual(stats["dirs_created"], 0)
        self.assertEqual(stats["download_files_written"], 0)
        self.assertEqual(stats["upload_files_written"], 1)
        self.assertEqual(stats["conflict_files"], 0)
        self.assertEqual(stats["bytes_written"], 3)

        # Download all from remote to temp/remote

        local = FsTarget(os.path.join(PYFTPSYNC_TEST_FOLDER, "remote"))

        opts = {"force": False, "delete": True, "verbose": 3}
        s = DownloadSynchronizer(local, remote, opts)
        s.run()
        stats = s.get_stats()
        #        pprint(stats)

        self.assertEqual(stats["entries_seen"], 8)
        self.assertEqual(stats["entries_touched"], 8)
        #        self.assertEqual(stats["files_created"], 6)
        self.assertEqual(stats["files_deleted"], 0)
        self.assertEqual(stats["files_written"], 6)
        self.assertEqual(stats["dirs_created"], 2)
        self.assertEqual(stats["download_files_written"], 6)
        self.assertEqual(stats["upload_files_written"], 0)
        self.assertEqual(stats["conflict_files"], 0)
        self.assertEqual(stats["bytes_written"], 16403)

        # Original file times are preserved, even when retrieved from FTP

        self.assertNotEqual(
            get_test_file_date("local/file1.txt"), STAMP_20140101_120000
        )
        self.assertEqual(
            get_test_file_date("local/file1.txt"),
            get_test_file_date("local//file1.txt"),
        )

        self.assertEqual(get_test_file_date("local/file2.txt"), STAMP_20140101_120000)
        self.assertEqual(get_test_file_date("remote//file2.txt"), STAMP_20140101_120000)

        # Synchronize temp/local <=> remote : nothing to do

        local = FsTarget(os.path.join(PYFTPSYNC_TEST_FOLDER, "local"))

        opts = {"verbose": 3}
        s = BiDirSynchronizer(local, remote, opts)
        s.run()
        stats = s.get_stats()
        pprint(stats)
        self.assertEqual(stats["entries_touched"], 0)
        self.assertEqual(stats["conflict_files"], 0)
        self.assertEqual(stats["bytes_written"], 0)

        # Synchronize temp/remote <=> remote : nothing to do

        local = FsTarget(os.path.join(PYFTPSYNC_TEST_FOLDER, "remote"))

        opts = {"verbose": 3}
        s = BiDirSynchronizer(local, remote, opts)
        s.run()
        stats = s.get_stats()
        pprint(stats)
        self.assertEqual(stats["entries_touched"], 0)
        self.assertEqual(stats["conflict_files"], 0)
        self.assertEqual(stats["bytes_written"], 0)


# ===============================================================================
# Main
# ===============================================================================
if __name__ == "__main__":
    unittest.main()
