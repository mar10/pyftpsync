# -*- coding: UTF-8 -*-
"""
Tests for scioweb.eplm.formsheets.eplm_base
"""
import unittest


from unittest import TestCase

#from ftpsync.targets import *  # @UnusedWildImport
#from ftpsync.ftp_target import *  # @UnusedWildImport
#from ftplib import FTP
from pprint import pprint
import tempfile
import os
import sys
import shutil
from ftpsync.targets import make_target, FsTarget, DownloadSynchronizer,\
    UploadSynchronizer

# Remote URL, e.g. "ftp://user:password@example.com/my/test/folder"
FTP_URL = os.environ["TEST_FTP_URL"]
# 
TEMP_FOLDER = os.environ.get("TEST_TEMP_FOLDER") or tempfile.mkdtemp()

def _write_test_file(name, size=None, content=None):
    """Create a file inside the temporary folder, optionally creating subfolders.
    
    `name` must use '/' as path separator, even on Windows.
    """
    path = os.path.join(TEMP_FOLDER, name.replace("/", os.sep))
    if "/" in name:
        parent_dir = os.path.dirname(path)
        if not os.path.isdir(parent_dir):
            os.makedirs(parent_dir)
        
    with open(path, "wt") as f:
        if content is None:
            if size is None:
                f.write(name)
            else:
                f.write("*" * size)
        else:
            f.write(content)


def _set_test_file_date(name, date=None):
    """Set file access and modification time to `date` (default: now)."""
    path = os.path.join(TEMP_FOLDER, name.replace("/", os.sep))
    if date is not None:
        date = (date, date)
    os.utime(path, date)


def _read_test_file(name):
    path = os.path.join(TEMP_FOLDER, name.replace("/", os.sep))
    with open(path, "rb") as f:
        return f.readall()


def _empty_folder(folder_path):
    """Remove all files and subfolders, but leave the empty parent intact."""
    for file_object in os.listdir(folder_path):
        file_object_path = os.path.join(folder_path, file_object)
        if os.path.isfile(file_object_path):
            os.unlink(file_object_path)
        else:
            shutil.rmtree(file_object_path)


#===============================================================================
# prepare_test_folder
#===============================================================================
def prepare_test_folder():
    print("prepare_test_folder", TEMP_FOLDER)
    assert os.path.isdir(TEMP_FOLDER)
    # Reset all
    _empty_folder(TEMP_FOLDER)
    # Add some files to ../temp1/
    _write_test_file("temp1/file1.txt", content="111")
    _write_test_file("temp1/file2.txt", content="222")
    _write_test_file("temp1/file3.txt", content="333")
    _write_test_file("temp1/folder1/file1_1.txt", content="1.111")
    _write_test_file("temp1/folder2/file2_1.txt", content="2.111")
    _write_test_file("temp1/big_file.txt", size=1024*16)
    # Create empty ../temp2/
    os.mkdir(os.path.join(TEMP_FOLDER, "temp2"))


#===============================================================================
# Module setUp / tearDown
#===============================================================================
def setUpModule():
    prepare_test_folder()

def tearDownModule():
#    _empty_folder(TEMP_FOLDER)
    pass
    

#===============================================================================
# BaseTest
#===============================================================================
class FilesystemTest(TestCase):
    """Test ."""
    def setUp(self):
        prepare_test_folder()
    
    def tearDown(self):
        pass
        
#    def test_remote(self):
#        
#        remote = make_target(FTP_URL)
#        remote.readonly = False
#        remote.cwd(self.PATH)
#        self.assertEqual(remote.pwd(), self.PATH)
#        
#        if sys.version_info[0] < 3:
#            # 'abc_äöü_ß¿€'
#            b = 'abc_\xc3\xa4\xc3\xb6\xc3\xbc_\xc3\x9f\xc2\xbf\xe2\x82\xac'
#            u = b.decode("utf8")
#        else:
#            u = "abc_äöü_¿ß"
#        s = u.encode("utf8")
#
#        remote.write_text("write_test_u.txt", u)
#        self.assertEqual(remote.read_text("write_test_u.txt"), u)
#
#        remote.write_text("write_test_s.txt", s)
#        self.assertEqual(remote.read_text("write_test_s.txt"), u)
        
    def test_download_fs_fs(self):
        local = FsTarget(os.path.join(TEMP_FOLDER, "temp2"))
        remote = FsTarget(os.path.join(TEMP_FOLDER, "temp1"))
        opts = {"force": False, "delete": False, "dry_run": False}
        s = DownloadSynchronizer(local, remote, opts)
        s.run()
        stats = s.get_stats()
        pprint(stats)
        self.assertEqual(stats["local_dirs"], 2)
#        self.assertEqual(stats["local_files"], 6)
        self.assertEqual(stats["remote_dirs"], 0)
        self.assertEqual(stats["remote_files"], 0)
        self.assertEqual(stats["files_written"], 6)
        self.assertEqual(stats["dirs_written"], 2)
        self.assertEqual(stats["bytes_written"], 16403)
        #
        s = DownloadSynchronizer(local, remote, opts)
        s.run()
        stats = s.get_stats()
        pprint(stats)
        self.assertEqual(stats["local_dirs"], 2)
        self.assertEqual(stats["local_files"], 6)
#        self.assertEqual(stats["remote_dirs"], 0)
#        self.assertEqual(stats["remote_files"], 0)
#        self.assertEqual(stats["files_written"], 6)
#        self.assertEqual(stats["dirs_written"], 2)
#        self.assertEqual(stats["bytes_written"], 16403)

    def test_upload_fs_fs(self):
        local = FsTarget(os.path.join(TEMP_FOLDER, "temp1"))
        remote = FsTarget(os.path.join(TEMP_FOLDER, "temp2"))
        opts = {"force": False, "delete": False, "dry_run": False}
        s = UploadSynchronizer(local, remote, opts)
        s.run()
        stats = s.get_stats()
        pprint(stats)
        self.assertEqual(stats["files_written"], 6)

#    def test_download_fs_ftp(self):
#        local = FsTarget("/Users/martin/temp")
#        user, passwd = get_stored_credentials("pyftpsync.pw", self.HOST)
#        remote = FtpTarget(self.PATH, self.HOST, user, passwd)
#        opts = {"force": False, "delete": False}
#        s = DownloadSynchronizer(local, remote, opts)
#        s.run()
#        stats = s.get_stats()
#        pprint(stats)
##        self.assertEqual(stats["source_files"], 1)
#
#    def test_upload_fs_fs(self):
#        local = FsTarget("/Users/martin/temp")
#        remote = FsTarget("/Users/martin/temp2")
#        opts = {"force": False, "delete": False}
#        s = UploadSynchronizer(local, remote, opts)
#        s.run()
#        
#        stats = s.get_stats()
#        pprint(stats)
##        self.assertEqual(stats["source_files"], 1)
#
#    def test_upload_fs_ftp(self):
#        local = FsTarget("~/temp")
#        user, passwd = get_stored_credentials("pyftpsync.pw", self.HOST)
#        remote = FtpTarget(self.PATH, self.HOST, user, passwd)
#        opts = {"force": False, "delete": True, "verbose": 3, "dry_run": False}
#        s = UploadSynchronizer(local, remote, opts)
#        s.run()
#        
#        stats = s.get_stats()
#        pprint(stats)
##        self.assertEqual(stats["source_files"], 1)


#===============================================================================
# Main
#===============================================================================
if __name__ == "__main__":
    print(sys.version)
    unittest.main()

#    suite = unittest.TestSuite()
##    suite.addTest(FtpTest("test_upload_fs_fs"))
##    suite.addTest(FtpTest("test_download_fs_fs"))
#    suite.addTest(FtpTest("test_upload_fs_ftp"))
#    suite.addTest(FtpTest("test_download_fs_ftp"))
##    suite.addTest(PlainTest("test_json"))
##    suite.addTest(PlainTest("test_make_target"))
##    suite.addTest(FtpTest("test_readwrite"))
#    unittest.TextTestRunner(verbosity=1).run(suite)
