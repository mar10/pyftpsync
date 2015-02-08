# -*- coding: UTF-8 -*-
"""
Tests for pyftpsync
"""
from __future__ import print_function

import calendar
import datetime
import os
from pprint import pprint
import shutil
import sys
import tempfile
from unittest import TestCase
import unittest

from ftpsync.targets import FsTarget

from ftpsync.synchronizers import DownloadSynchronizer, UploadSynchronizer, \
    BiDirSynchronizer
import time


PYFTPSYNC_TEST_FOLDER = os.environ.get("PYFTPSYNC_TEST_FOLDER") or tempfile.mkdtemp()
PYFTPSYNC_TEST_FTP_URL = os.environ.get("PYFTPSYNC_TEST_FTP_URL")


def _write_test_file(name, size=None, content=None, dt=None, age=None):
    """Create a file inside the temporary folder, optionally creating subfolders.
    
    `name` must use '/' as path separator, even on Windows.
    """
    path = os.path.join(PYFTPSYNC_TEST_FOLDER, name.replace("/", os.sep))
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
    if age:
        assert dt is None
        dt = datetime.datetime.now() - datetime.timedelta(seconds=age)
    if dt:
        stamp = calendar.timegm(dt.timetuple())
        date = (stamp, stamp)
        os.utime(path, date)
    return
        


def _set_test_file_date(name, dt=None, ofs_sec=None):
    """Set file access and modification time to `date` (default: now)."""
    path = os.path.join(PYFTPSYNC_TEST_FOLDER, name.replace("/", os.sep))
    if dt is not None:
        stamp = calendar.timegm(dt.timetuple())
        dt = (stamp, stamp)
    os.utime(path, dt)

def _get_test_file_date(name):
    path = os.path.join(PYFTPSYNC_TEST_FOLDER, name.replace("/", os.sep))
    stat = os.lstat(path)
    return stat.st_mtime

def _read_test_file(name):
    path = os.path.join(PYFTPSYNC_TEST_FOLDER, name.replace("/", os.sep))
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
# prepare_fixtures
#===============================================================================

STAMP_20140101_120000 = 1388577600.0  # Wed, 01 Jan 2014 12:00:00 GMT

def prepare_fixtures():
    """Create two test folders and some files."""
    print("prepare_fixtures", PYFTPSYNC_TEST_FOLDER)
    assert os.path.isdir(PYFTPSYNC_TEST_FOLDER)
    # Reset all
    _empty_folder(PYFTPSYNC_TEST_FOLDER)
    # Add some files to ../temp1/
    dt = datetime.datetime(2014, 1, 1, 12, 0, 0)
    _write_test_file("temp1/file1.txt", content="111", dt=dt)
    _write_test_file("temp1/file2.txt", content="222", dt=dt)
    _write_test_file("temp1/file3.txt", content="333", dt=dt)
    _write_test_file("temp1/folder1/file1_1.txt", content="1.111", dt=dt)
    _write_test_file("temp1/folder2/file2_1.txt", content="2.111", dt=dt)
    _write_test_file("temp1/big_file.txt", size=1024*16, dt=dt)
    # Create empty ../temp2/
    os.mkdir(os.path.join(PYFTPSYNC_TEST_FOLDER, "temp2"))


#===============================================================================
# Module setUp / tearDown
#===============================================================================
def setUpModule():
#    prepare_fixtures()
    pass

def tearDownModule():
#    _empty_folder(PYFTPSYNC_TEST_FOLDER)
    pass
    

#===============================================================================
# BaseTest
#===============================================================================
class FilesystemTest(TestCase):
    """Test different synchronizers on file system targets."""
    def setUp(self):
        prepare_fixtures()
    
    def tearDown(self):
        pass
        
    def test_download_fs_fs(self):
        # Download files from temp1 to temp2 (which is empty)
        local = FsTarget(os.path.join(PYFTPSYNC_TEST_FOLDER, "temp2"))
        remote = FsTarget(os.path.join(PYFTPSYNC_TEST_FOLDER, "temp1"))
        opts = {"force": False, "delete": False, "dry_run": False}
        s = DownloadSynchronizer(local, remote, opts)
        s.run()
        stats = s.get_stats()
#        pprint(stats)
        self.assertEqual(stats["local_dirs"], 0)
        self.assertEqual(stats["local_files"], 0)
        self.assertEqual(stats["remote_dirs"], 2)
        self.assertEqual(stats["remote_files"], 4) # currently files are not counted, when inside a *new* folder
        self.assertEqual(stats["files_written"], 6)
        self.assertEqual(stats["dirs_created"], 2)
        self.assertEqual(stats["bytes_written"], 16403)
        # Again: nothing to do
        s = DownloadSynchronizer(local, remote, opts)
        s.run()
        stats = s.get_stats()
#        pprint(stats)
        self.assertEqual(stats["local_dirs"], 2)
        self.assertEqual(stats["local_files"], 6)
        self.assertEqual(stats["remote_dirs"], 2)
        self.assertEqual(stats["remote_files"], 6)
        self.assertEqual(stats["files_written"], 0)
        self.assertEqual(stats["dirs_created"], 0)
        self.assertEqual(stats["bytes_written"], 0)
        # file times are preserved
        self.assertEqual(_get_test_file_date("temp1/file1.txt"), STAMP_20140101_120000)
        self.assertEqual(_get_test_file_date("temp2/file1.txt"), STAMP_20140101_120000)


    def test_upload_fs_fs(self):
        local = FsTarget(os.path.join(PYFTPSYNC_TEST_FOLDER, "temp1"))
        remote = FsTarget(os.path.join(PYFTPSYNC_TEST_FOLDER, "temp2"))
        opts = {"force": False, "delete": False, "dry_run": False}
        s = UploadSynchronizer(local, remote, opts)
        s.run()
        stats = s.get_stats()
#        pprint(stats)
        self.assertEqual(stats["local_dirs"], 2)
        self.assertEqual(stats["local_files"], 4) # currently files are not counted, when inside a *new* folder
        self.assertEqual(stats["remote_dirs"], 0)
        self.assertEqual(stats["remote_files"], 0)
        self.assertEqual(stats["files_written"], 6)
        self.assertEqual(stats["dirs_created"], 2)
        self.assertEqual(stats["bytes_written"], 16403)
        # file times are preserved
        self.assertEqual(_get_test_file_date("temp1/file1.txt"), STAMP_20140101_120000)
        self.assertEqual(_get_test_file_date("temp2/file1.txt"), STAMP_20140101_120000)


    def test_sync_fs_fs(self):
        local = FsTarget(os.path.join(PYFTPSYNC_TEST_FOLDER, "temp1"))
        remote = FsTarget(os.path.join(PYFTPSYNC_TEST_FOLDER, "temp2"))
        opts = {"dry_run": False, "verbose": 3}
        s = BiDirSynchronizer(local, remote, opts)
        s.run()
        stats = s.get_stats()
#        pprint(stats)
        self.assertEqual(stats["local_dirs"], 2)
        self.assertEqual(stats["local_files"], 4) # currently files are not counted, when inside a *new* folder
        self.assertEqual(stats["remote_dirs"], 0)
        self.assertEqual(stats["remote_files"], 0)
        self.assertEqual(stats["files_written"], 6)
        self.assertEqual(stats["dirs_created"], 2)
        self.assertEqual(stats["bytes_written"], 16403)
        # file times are preserved
        self.assertEqual(_get_test_file_date("temp1/file1.txt"), STAMP_20140101_120000)
        self.assertEqual(_get_test_file_date("temp2/file1.txt"), STAMP_20140101_120000)
        
        
        # Again: nothing to do
        s = BiDirSynchronizer(local, remote, opts)
        s.run()
        stats = s.get_stats()
#        pprint(stats)
        self.assertEqual(stats["local_dirs"], 2)
        self.assertEqual(stats["local_files"], 6)
        self.assertEqual(stats["remote_dirs"], 2)
        self.assertEqual(stats["remote_files"], 6)
        self.assertEqual(stats["files_created"], 0)
        self.assertEqual(stats["files_deleted"], 0)
        self.assertEqual(stats["files_written"], 0)
        self.assertEqual(stats["dirs_created"], 0)
        self.assertEqual(stats["bytes_written"], 0)

        # Modify remote and/or remote
        _set_test_file_date("temp1/file1.txt")
        _set_test_file_date("temp2/file2.txt")
        # file3.txt will cause a conflict:
        _set_test_file_date("temp1/file3.txt")
        dt = datetime.datetime.now() - datetime.timedelta(seconds=10)
        _set_test_file_date("temp2/file3.txt", dt=dt)

        s = BiDirSynchronizer(local, remote, opts)
        s.run()
        stats = s.get_stats()
#        pprint(stats)
        self.assertEqual(stats["entries_seen"], 18)
        self.assertEqual(stats["entries_touched"], 2)
        self.assertEqual(stats["files_created"], 0)
        self.assertEqual(stats["files_deleted"], 0)
        self.assertEqual(stats["files_written"], 2)
        self.assertEqual(stats["dirs_created"], 0)
        self.assertEqual(stats["download_files_written"], 1)
        self.assertEqual(stats["upload_files_written"], 1)
        self.assertEqual(stats["conflict_files"], 1)
        self.assertEqual(stats["bytes_written"], 6)

    def test_sync_conflicts(self):
        local = FsTarget(os.path.join(PYFTPSYNC_TEST_FOLDER, "temp1"))
        remote = FsTarget(os.path.join(PYFTPSYNC_TEST_FOLDER, "temp2"))
        opts = {"dry_run": False, "verbose": 3}
        
        # Copy temp1 -> temp2
        
        s = BiDirSynchronizer(local, remote, opts)
        s.run()
        stats = s.get_stats()
        self.assertEqual(stats["files_written"], 6)
        self.assertEqual(stats["dirs_created"], 2)
        
        
        # Modify local and remote

        # conflict 1: local is newer 
        dt = datetime.datetime.now()
        _set_test_file_date("temp1/file1.txt", dt)
        dt = datetime.datetime.now() - datetime.timedelta(seconds=10)
        _set_test_file_date("temp2/file1.txt", dt=dt)
#         path = os.path.join(PYFTPSYNC_TEST_FOLDER, "temp2/file1.txt")
#         stamp = time.time() - 10
#         os.utime(path, (stamp, stamp))

        # conflict 2: remote is newer 
        _set_test_file_date("temp2/file2.txt")
        dt = datetime.datetime.now() - datetime.timedelta(seconds=10)
        _set_test_file_date("temp1/file2.txt", dt=dt)


        s = BiDirSynchronizer(local, remote, opts)
        s.run()
        stats = s.get_stats()
        pprint(stats)
        self.assertEqual(stats["entries_seen"], 18)
        self.assertEqual(stats["entries_touched"], 0)
        self.assertEqual(stats["bytes_written"], 0)
        self.assertEqual(stats["conflict_files"], 2)


#===============================================================================
# Main
#===============================================================================
if __name__ == "__main__":
    print(sys.version)
    unittest.main()
