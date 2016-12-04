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
import tempfile
from ftpsync.targets import FsTarget
from ftpsync.synchronizers import BiDirSynchronizer
from ftpsync.metadata import DirMetadata
from ftpsync.util import to_str



PYFTPSYNC_TEST_FOLDER = os.environ.get("PYFTPSYNC_TEST_FOLDER") or tempfile.mkdtemp()
PYFTPSYNC_TEST_FTP_URL = os.environ.get("PYFTPSYNC_TEST_FTP_URL")
STAMP_20140101_120000 = 1388577600.0  # Wed, 01 Jan 2014 12:00:00 GMT

# dt = datetime.datetime.strptime("2014-01-01 12:00:00", "%Y-%m-%d %H:%M:%S")
# stamp = calendar.timegm(dt.timetuple())
# print(stamp)  # --> 1388577600
# 1/0

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
            assert size is None
            f.write(content)
    if age:
        assert dt is None
        dt = datetime.datetime.now() - datetime.timedelta(seconds=age)
    if dt:
        if isinstance(dt, str):
            dt = datetime.datetime.strptime(dt, "%Y-%m-%d %H:%M:%S")
        stamp = calendar.timegm(dt.timetuple())
        date = (stamp, stamp)
        os.utime(path, date)
    return

def _touch_test_file(name, dt=None, ofs_sec=None):
    """Set file access and modification time to `date` (default: now)."""
    path = os.path.join(PYFTPSYNC_TEST_FOLDER, name.replace("/", os.sep))
    if dt is not None:
        if isinstance(dt, str):
            dt = datetime.datetime.strptime(dt, "%Y-%m-%d %H:%M:%S")
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

def _is_test_file(name):
    path = os.path.join(PYFTPSYNC_TEST_FOLDER, name.replace("/", os.sep))
    return os.path.isfile(path)

def _remove_test_file(name):
    path = os.path.join(PYFTPSYNC_TEST_FOLDER, name.replace("/", os.sep))
    assert os.path.isfile(path)
    return os.remove(path)

def _remove_test_folder(name):
    path = os.path.join(PYFTPSYNC_TEST_FOLDER, name.replace("/", os.sep))
    assert os.path.isdir(path)
    shutil.rmtree(path)

def _empty_folder(folder_path):
    """Remove all files and subfolders, but leave the empty parent intact."""
    for file_object in os.listdir(folder_path):
        file_object_path = os.path.join(folder_path, file_object)
        if os.path.isfile(file_object_path):
            os.unlink(file_object_path)
        else:
            shutil.rmtree(file_object_path)

def _get_test_folder(folder_name):
    """"Convert test folder content to dict for comparisons."""
#     root_path = os.path.join(PYFTPSYNC_TEST_FOLDER, folder_name.replace("/", os.sep))
    file_map = {}
    root_folder = os.path.join(PYFTPSYNC_TEST_FOLDER, folder_name)
    def __scan(rel_folder_path):
        abs_folder_path = os.path.join(root_folder, rel_folder_path)
        for fn in os.listdir(abs_folder_path):
            if fn.startswith(".") or fn == DirMetadata.DEBUG_META_FILE_NAME:
                continue
            abs_file_path = os.path.join(abs_folder_path, fn)
            if os.path.isdir(abs_file_path):
                __scan(os.path.join(rel_folder_path, fn))
                continue
            stat = os.lstat(abs_file_path)
            dt = datetime.datetime.utcfromtimestamp(stat.st_mtime)
            rel_file_path = os.path.join(rel_folder_path, fn).replace(os.sep, "/")
            file_map[rel_file_path] = {
                            "date": dt.strftime("%Y-%m-%d %H:%M:%S"),
                            #"size": stat.st_size,
                            }
            with open(abs_file_path, "rb") as fp:
                file_map[rel_file_path]["content"] = to_str(fp.read())
    __scan("")
    return file_map


# def prepare_test_folder(path, files):
#     _empty_folder(path)
#     for f in files:
#         pass

def _sync_test_folders(options):
    """Run bi-dir sync with fresh objects."""
    local = FsTarget(os.path.join(PYFTPSYNC_TEST_FOLDER, "local"))
    remote = FsTarget(os.path.join(PYFTPSYNC_TEST_FOLDER, "remote"))
    opts = {"dry_run": False, "verbose": 3}
    if options:
        opts.update(options)

    s = BiDirSynchronizer(local, remote, opts)
    s.run()
    return s.get_stats()


#===============================================================================
# prepare_fixtures_1
#===============================================================================

def prepare_fixtures_1():
    """Create two test folders and some files.

    """
    print("prepare_fixtures", PYFTPSYNC_TEST_FOLDER)
    assert os.path.isdir(PYFTPSYNC_TEST_FOLDER)
    # Reset all
    _empty_folder(PYFTPSYNC_TEST_FOLDER)
    # Add some files to ../local/
    dt = datetime.datetime(2014, 1, 1, 12, 0, 0)
    _write_test_file("local/file1.txt", content="111", dt=dt)
    _write_test_file("local/file2.txt", content="222", dt=dt)
    _write_test_file("local/file3.txt", content="333", dt=dt)
    _write_test_file("local/folder1/file1_1.txt", content="1.111", dt=dt)
    _write_test_file("local/folder2/file2_1.txt", content="2.111", dt=dt)
    _write_test_file("local/big_file.txt", size=1024*16, dt=dt)
    # Create empty ../remote/
    os.mkdir(os.path.join(PYFTPSYNC_TEST_FOLDER, "remote"))


#===============================================================================
# prepare_fixtures_2
#===============================================================================

def prepare_fixtures_2():
    """
    Create two folders that have already been synched (so meta data is available).

                              Local           Remote
      file1.txt               12:00           12:00
      file2.txt               12:00           12:00
      file3.txt               12:00           12:00
      file4.txt               12:00           12:00
      file5.txt               12:00           12:00
      file6.txt               12:00           12:00
      file7.txt               12:00           12:00
      file8.txt               12:00           12:00
      folder1/file1_1.txt     12.00           12:00
      folder2/file2_1.txt     12:00           12:00
      folder3/file3_1.txt     12:00           12:00
      folder4/file4_1.txt     12:00           12:00
    """
    assert os.path.isdir(PYFTPSYNC_TEST_FOLDER), "Invalid folder: {}".format(PYFTPSYNC_TEST_FOLDER)
    # Reset all
    _empty_folder(PYFTPSYNC_TEST_FOLDER)
    # Add some files to ../local/
    dt = "2014-01-01 12:00:00"
    for i in range(1, 9):
        _write_test_file("local/file{}.txt".format(i), dt=dt,
                         content="local{}".format(i))

    _write_test_file("local/folder1/file1_1.txt", dt=dt, content="local1_1")
    _write_test_file("local/folder2/file2_1.txt", dt=dt, content="local2_1")
    _write_test_file("local/folder3/file3_1.txt", dt=dt, content="local3_1")
    _write_test_file("local/folder4/file4_1.txt", dt=dt, content="local4_1")

    # Create empty ../remote/
    os.mkdir(os.path.join(PYFTPSYNC_TEST_FOLDER, "remote"))

    # Synchronize folders
    opts = {"dry_run": False, "verbose": 0}
    stats = _sync_test_folders(opts)
    assert stats["files_written"] == 12
    assert stats["dirs_created"] == 4
