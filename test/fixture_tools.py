# -*- coding: UTF-8 -*-
"""
Tests for pyftpsync
"""
from __future__ import print_function

# noqa: E501
import calendar
import copy
import datetime
import errno
from ftplib import FTP, error_perm
import io
import json
import os
from pprint import pprint
import shutil
import sys
import tempfile
import time
import unittest
from unittest.case import SkipTest

from ftpsync import pyftpsync
from ftpsync.metadata import DirMetadata
from ftpsync.synchronizers import BiDirSynchronizer
from ftpsync.targets import FsTarget, make_target
from ftpsync.util import to_str, to_binary, urlparse, StringIO


PYFTPSYNC_TEST_FOLDER = os.environ.get("PYFTPSYNC_TEST_FOLDER") or tempfile.mkdtemp()
PYFTPSYNC_TEST_FTP_URL = os.environ.get("PYFTPSYNC_TEST_FTP_URL")
STAMP_20140101_120000 = 1388577600.0  # Wed, 01 Jan 2014 12:00:00 GMT


class CaptureStdout(list):
    """Context manager that redirects sys.stdout into a buffer.

    Usage:
        with CaptureStdout() as out:
            do_semthing()
        print(out)

    Taken from here https://stackoverflow.com/a/16571630/19166
    and expanded to capture stderr as well.

    Note: For testing python scripts, it may dependend on the Python version whether
    output is some output is written to stdout or stderr, so we need to check both:
    https://stackoverflow.com/a/31715011/19166
    """
    def __init__(self, stdout=True, stderr=True):
        self._do_stdout = stdout
        self._do_stderr = stderr

    def __enter__(self):
        self._stdout = sys.stdout
        self._stderr = sys.stderr
        self._stringio = StringIO()
        if self._do_stdout:
            sys.stdout = self._stringio
        if self._do_stderr:
            sys.stderr = self._stringio
        return self

    def __exit__(self, *args):
        self.extend(self._stringio.getvalue().splitlines())
        del self._stringio    # free up some memory
        sys.stdout = self._stdout
        sys.stderr = self._stderr


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


def prepare_fixture():
    """Helper for command line testing.

    Example:
        >>>python -m test.fixture_tools
        Created fixtures at /Users/martin/prj/test/pyftpsync_test_folder
        >>>ls /Users/martin/prj/test/pyftpsync_test_folder
        local	remote
    """
    use_ftp = False
    if "--no-ftp" not in sys.argv:
        try:
            check_ftp_test_connection(PYFTPSYNC_TEST_FOLDER, PYFTPSYNC_TEST_FTP_URL)
            use_ftp = True
        except SkipTest:
            pass

    class _DummySuite(_SyncTestBase):
        use_ftp_target = use_ftp

    _DummySuite._prepare_initial_synced_fixture()
    _DummySuite._prepare_modified_fixture()

    print("Created fixtures at {}".format(PYFTPSYNC_TEST_FOLDER))
    if use_ftp:
        print("NOTE: The remote target is prepared for FTP access, using PYFTPSYNC_TEST_FTP_URL.")
        print("      Pass `--no-ftp` to prepare for file access.")
    else:
        print("NOTE: The remote target is prepared for FILE SYSTEM access, because\n"
              "      PYFTPSYNC_TEST_FTP_URL is invalid or no server is running.")


def write_test_file(name, size=None, content=None, dt=None, age=None):
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
    # # Make sure everyone can write here (for example our anonymous FTP server user)
    # os.chmod(path, 0o777)
    return


def touch_test_file(name, dt=None, ofs_sec=None):
    """Set file access and modification time to `date` (default: now)."""
    path = os.path.join(PYFTPSYNC_TEST_FOLDER, name.replace("/", os.sep))
    if dt is not None:
        if isinstance(dt, str):
            dt = datetime.datetime.strptime(dt, "%Y-%m-%d %H:%M:%S")
        stamp = calendar.timegm(dt.timetuple())
        dt = (stamp, stamp)
    # existed = os.path.isfile(path)
    os.utime(path, dt)
    # if not existed:
    #     # Make sure everyone can write here (for example our anonymous FTP server user)
    #     os.chmod(path, 0o777)


def get_test_file_date(name):
    path = os.path.join(PYFTPSYNC_TEST_FOLDER, name.replace("/", os.sep))
    stat = os.lstat(path)
    return stat.st_mtime


def read_test_file(name):
    path = os.path.join(PYFTPSYNC_TEST_FOLDER, name.replace("/", os.sep))
    with open(path, "rb") as fp:
        return to_str(fp.read())


def is_test_file(name):
    path = os.path.join(PYFTPSYNC_TEST_FOLDER, name.replace("/", os.sep))
    return os.path.isfile(path)


def remove_test_file(name):
    path = os.path.join(PYFTPSYNC_TEST_FOLDER, name.replace("/", os.sep))
    assert os.path.isfile(path)
    return os.remove(path)


def remove_test_folder(name):
    path = os.path.join(PYFTPSYNC_TEST_FOLDER, name.replace("/", os.sep))
    assert os.path.isdir(path)
    shutil.rmtree(path)


def empty_folder(folder_path):
    """Remove all files and subfolders, but leave the empty parent intact."""
    for file_object in os.listdir(folder_path):
        file_object_path = os.path.join(folder_path, file_object)
        if os.path.isfile(file_object_path):
            os.unlink(file_object_path)
        else:
            shutil.rmtree(file_object_path)
    return


def delete_metadata(folder_path, recursive=True):
    """Remove all .pyftpsync-meta.json files."""
    for file_object in os.listdir(folder_path):
        file_object_path = os.path.join(folder_path, file_object)
        if file_object == DirMetadata.META_FILE_NAME:
            print("Remove {}".format(file_object_path))
            os.unlink(file_object_path)
        elif recursive and os.path.isdir(file_object_path):
            delete_metadata(file_object_path, recursive)
    return


def get_test_folder(folder_name):
    """"Convert test folder content to dict for comparisons."""
#     root_path = os.path.join(PYFTPSYNC_TEST_FOLDER, folder_name.replace("/", os.sep))
    file_map = {}
    root_folder = os.path.join(PYFTPSYNC_TEST_FOLDER, folder_name)

    def __scan(rel_folder_path):
        abs_folder_path = os.path.join(root_folder, rel_folder_path)
        for fn in os.listdir(abs_folder_path):
            if fn.startswith("."):  # or fn == DirMetadata.DEBUG_META_FILE_NAME:
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
                            # "size": stat.st_size,
                            }
            with open(abs_file_path, "rb") as fp:
                file_map[rel_file_path]["content"] = to_str(fp.read())
    __scan("")
    return file_map


def get_metadata(folder_path):
    try:
        meta = read_test_file(os.path.join(folder_path, DirMetadata.META_FILE_NAME))
    except OSError as e:  # FileNotFoundError is only available in Python 3
        if e.errno == errno.ENOENT:
            return None
        raise
    # print("meta", meta)
    meta = json.loads(meta)
    # print("meta", meta)
    pprint(meta)
    return meta


# ===============================================================================
#
# ===============================================================================

MSG_FTP_TESTS_NOT_AVAILABLE = """\
    Skipping FTP tests.
    Seems that the `PYFTPSYNC_TEST_FTP_URL` environment variable is missing, invalid, or
    the FTP server is not runing.
    See http://pyftpsync.readthedocs.io/en/latest/development.html for details.
    """

#: bool:
FTP_PRECONDITIONS_PASSED = None


def check_ftp_test_connection(test_folder, ftp_url, keep_open=False):
    """Check if we have a FTP server for a locally accessible test folder.

    Results are cached after first call.

    Raises:
        SkipTest if the connection fails or is no good.
    """
    # Cache result after first call
    global FTP_PRECONDITIONS_PASSED

    if FTP_PRECONDITIONS_PASSED is False:
        raise SkipTest("Previous check for FTP server configuration failed.")
    elif FTP_PRECONDITIONS_PASSED is True:
        if keep_open:
            # TODO: open and connect
            raise NotImplementedError
        return True

    def _skip(msg):
        msg = "Check for FTP server configuration failed:\n{}\n{}" \
            .format(msg, MSG_FTP_TESTS_NOT_AVAILABLE)
        print(msg, file=sys.stderr)
        # raise RuntimeError(msg)
        raise SkipTest(msg)

    FTP_PRECONDITIONS_PASSED = False
    if not ftp_url:
        _skip("No FTP URL")
    #
    try:
        connected = False
        parts = urlparse(ftp_url, allow_fragments=False)
        assert parts.scheme.lower() in ("ftp", "ftps")
#         print(ftp_url, "->", parts, ", ", parts.username, ":", parts.password)
        if "@" in parts.netloc:
            host = parts.netloc.rsplit("@", 1)[1]
        else:
            host = parts.netloc
        # self.PATH = parts.path
        ftp = FTP()
        # ftp.set_debuglevel(2)
        # Can we connect to host?
        ftp.connect(host)
        ftp.login(parts.username, parts.password)
        # Change directory
        ftp.cwd(parts.path)
        # Check for MLSD command support
        try:
            ftp.retrlines("MLSD", lambda _line: None)
        except error_perm as e:
            if "500" in str(e.args):
                _skip("The FTP server does not support the 'MLSD' command.")
            raise

        # Check if we have write access
        data = "{}".format(time.time())
        buf = io.BytesIO(to_binary(data))
        probe_file = "pyftpsync_probe.txt"
        ftp.storbinary("STOR {}".format(probe_file), buf)
        # Check if the FTP target is identical to the FS path
#         buf = ftp.retrbinary("RETR {}".format(probe_file))
        try:
            data2 = read_test_file("remote/{}".format(probe_file))
        except OSError as e:  # FileNotFoundError is only available in Python 3
            if e.errno == errno.ENOENT:
                _skip("FTP target path {} does not match `PYFTPSYNC_TEST_FOLDER/remote`"
                      .format(parts.path))
            raise

        if data != data2:
            _skip("Probe file content mismatch")
        # Cleanup
        ftp.delete(probe_file)
        # Convinced: Ok!
        FTP_PRECONDITIONS_PASSED = True

    except Exception as e:
        _skip("{}".format(e))

    finally:
        if connected and not keep_open:
            ftp.quit()

    if keep_open:
        return (ftp, parts.path)
    return True


def get_local_test_url():
    """Return path to local fixture folder."""
    return os.path.join(PYFTPSYNC_TEST_FOLDER, "local")


def get_remote_test_url():
    """Return URL to remote fixture (ftp:// URL if available, folder path otherwise)."""
    if FTP_PRECONDITIONS_PASSED is None:
        try:
            check_ftp_test_connection(PYFTPSYNC_TEST_FOLDER, PYFTPSYNC_TEST_FTP_URL)
        except SkipTest:
            pass

    if FTP_PRECONDITIONS_PASSED:
        return PYFTPSYNC_TEST_FTP_URL
    return os.path.join(PYFTPSYNC_TEST_FOLDER, "remote")


# ===============================================================================
# _SyncTestBase
# ===============================================================================

class _SyncTestBase(unittest.TestCase):
    """Test BiDirSynchronizer on file system targets with different resolve modes."""
    #: str: by default, the `remote` target is a file system folder
#     remote_url = PYFTPSYNC_TEST_FOLDER
    #: bool: Derived FTP-based testing classes will set this True. Default: False.
    use_ftp_target = False

    local_fixture_unmodified = {
        'file1.txt':           {'content': 'local1',   'date': '2014-01-01 12:00:00'},
        'file2.txt':           {'content': 'local2',   'date': '2014-01-01 12:00:00'},
        'file3.txt':           {'content': 'local3',   'date': '2014-01-01 12:00:00'},
        'file4.txt':           {'content': 'local4',   'date': '2014-01-01 12:00:00'},
        'file5.txt':           {'content': 'local5',   'date': '2014-01-01 12:00:00'},
        'file6.txt':           {'content': 'local6',   'date': '2014-01-01 12:00:00'},
        'file7.txt':           {'content': 'local7',   'date': '2014-01-01 12:00:00'},
        'file8.txt':           {'content': 'local8',   'date': '2014-01-01 12:00:00'},
        'file9.txt':           {'content': 'local9',   'date': '2014-01-01 12:00:00'},
        'folder1/file1_1.txt': {'content': 'local1_1', 'date': '2014-01-01 12:00:00'},
        'folder2/file2_1.txt': {'content': 'local2_1', 'date': '2014-01-01 12:00:00'},
        'folder3/file3_1.txt': {'content': 'local3_1', 'date': '2014-01-01 12:00:00'},
        'folder4/file4_1.txt': {'content': 'local4_1', 'date': '2014-01-01 12:00:00'},
        'folder5/file5_1.txt': {'content': 'local5_1', 'date': '2014-01-01 12:00:00'},
        'folder6/file6_1.txt': {'content': 'local6_1', 'date': '2014-01-01 12:00:00'},
        'folder7/file7_1.txt': {'content': 'local7_1', 'date': '2014-01-01 12:00:00'},
        }

    local_fixture_modified = {
        'file1.txt':           {'content': 'local1',         'date': '2014-01-01 12:00:00'},
        'file2.txt':           {'content': 'local 13:00',    'date': '2014-01-01 13:00:00'},
        'file4.txt':           {'content': 'local4',         'date': '2014-01-01 12:00:00'},
        'file5.txt':           {'content': 'local5',         'date': '2014-01-01 12:00:00'},
        'file6.txt':           {'content': 'local 13:00',    'date': '2014-01-01 13:00:00'},
        'file7.txt':           {'content': 'local 13:00:05', 'date': '2014-01-01 13:00:05'},
        'file9.txt':           {'content': 'local 13:00',    'date': '2014-01-01 13:00:00'},
        'folder1/file1_1.txt': {'content': 'local1_1',       'date': '2014-01-01 12:00:00'},
        'folder2/file2_1.txt': {'content': 'local 13:00',    'date': '2014-01-01 13:00:00'},
        'folder5/file5_1.txt': {'content': 'local5_1',       'date': '2014-01-01 12:00:00'},
        'folder6/file6_1.txt': {'content': 'local6_1',       'date': '2014-01-01 12:00:00'},
        'folder7/file7_1.txt': {'content': 'local 13:00',    'date': '2014-01-01 13:00:00'},
        'new_file1.txt':       {'content': 'local 13:00',    'date': '2014-01-01 13:00:00'},
        'new_file3.txt':       {'content': 'local 13:00',    'date': '2014-01-01 13:00:00'},
        'new_file4.txt':       {'content': 'local 13:00',    'date': '2014-01-01 13:00:00'},
        'new_file5.txt':       {'content': 'local 13:00',    'date': '2014-01-01 13:00:00'},
        'new_file6.txt':       {'content': 'local 13:00:05', 'date': '2014-01-01 13:00:05'},
        }

    remote_fixture_modified = {
        'file1.txt':           {'content': 'local1',          'date': '2014-01-01 12:00:00'},
        'file2.txt':           {'content': 'local2',          'date': '2014-01-01 12:00:00'},
        'file3.txt':           {'content': 'local3',          'date': '2014-01-01 12:00:00'},
        'file4.txt':           {'content': 'remote 13:00',    'date': '2014-01-01 13:00:00'},
        'file6.txt':           {'content': 'remote 13:00:05', 'date': '2014-01-01 13:00:05'},
        'file7.txt':           {'content': 'remote 13:00',    'date': '2014-01-01 13:00:00'},
        'file8.txt':           {'content': 'remote 13:00',    'date': '2014-01-01 13:00:00'},
        'folder1/file1_1.txt': {'content': 'local1_1',        'date': '2014-01-01 12:00:00'},
        'folder2/file2_1.txt': {'content': 'local2_1',        'date': '2014-01-01 12:00:00'},
        'folder3/file3_1.txt': {'content': 'local3_1',        'date': '2014-01-01 12:00:00'},
        'folder4/file4_1.txt': {'content': 'remote 13:00',    'date': '2014-01-01 13:00:00'},
        'folder5/file5_1.txt': {'content': 'remote 13:00',    'date': '2014-01-01 13:00:00'},
        'new_file2.txt':       {'content': 'remote 13:00',    'date': '2014-01-01 13:00:00'},
        'new_file3.txt':       {'content': 'local 13:00',     'date': '2014-01-01 13:00:00'},
        'new_file4.txt':       {'content': 'remote 13:00 with other content',
                                                              'date': '2014-01-01 13:00:00'},
        'new_file5.txt':       {'content': 'remote 13:00:05', 'date': '2014-01-01 13:00:05'},
        'new_file6.txt':       {'content': 'remote 13:00',    'date': '2014-01-01 13:00:00'},
        }

    def setUp(self):
        if self.use_ftp_target:
            # Check for a running FTP server that exposes the /remote fixture folder.
            # Raise SkipTest otherwise
            check_ftp_test_connection(PYFTPSYNC_TEST_FOLDER, PYFTPSYNC_TEST_FTP_URL)

        self._prepare_initial_synced_fixture()
        self.maxDiff = None  # Do not truncate dict diffs
        self.verbose = 4  # Default option for synchronizers

    def tearDown(self):
        pass

    @classmethod
    def _prepare_initial_local_fixture(cls):
        """
        Create a local folder that has some files and folders with defined mtimes.

        The remote folder is empty. No meta data created yet.

                                  Local           Remote
          file1.txt               12:00           -
          file2.txt               12:00           -
          file3.txt               12:00           -
          file4.txt               12:00           -
          file5.txt               12:00           -
          file6.txt               12:00           -
          file7.txt               12:00           -
          file8.txt               12:00           -
          file9.txt               12:00           -
          folder1/file1_1.txt     12.00           -
          folder2/file2_1.txt     12:00           -
          folder3/file3_1.txt     12:00           -
          folder4/file4_1.txt     12:00           -
          folder5/file5_1.txt     12:00           -
          folder6/file6_1.txt     12:00           -
          folder7/file7_1.txt     12:00           -
        """
        assert os.path.isdir(PYFTPSYNC_TEST_FOLDER), \
            "Invalid folder: {}".format(PYFTPSYNC_TEST_FOLDER)
        # Reset all
        empty_folder(PYFTPSYNC_TEST_FOLDER)
        # Add some files to ../local/
        dt = "2014-01-01 12:00:00"
        for i in range(1, 10):
            write_test_file("local/file{}.txt".format(i), dt=dt,
                            content="local{}".format(i))

        write_test_file("local/folder1/file1_1.txt", dt=dt, content="local1_1")
        write_test_file("local/folder2/file2_1.txt", dt=dt, content="local2_1")
        write_test_file("local/folder3/file3_1.txt", dt=dt, content="local3_1")
        write_test_file("local/folder4/file4_1.txt", dt=dt, content="local4_1")
        write_test_file("local/folder5/file5_1.txt", dt=dt, content="local5_1")
        write_test_file("local/folder6/file6_1.txt", dt=dt, content="local6_1")
        write_test_file("local/folder7/file7_1.txt", dt=dt, content="local7_1")

        # Create empty ../remote/
        remote_path = os.path.join(PYFTPSYNC_TEST_FOLDER, "remote")
        os.mkdir(remote_path)
        # # Make sure everyone can write here (for example our anonymous FTP server user)
        # os.chmod(remote_path, 0o777)
        return

    @classmethod
    def _prepare_initial_synced_fixture(cls):
        """Create two folders that have already been sync'ed (so meta data is available).

                                  Local           Remote
          file1.txt               12:00           12:00
          file2.txt               12:00           12:00
          file3.txt               12:00           12:00
          file4.txt               12:00           12:00
          file5.txt               12:00           12:00
          file6.txt               12:00           12:00
          file7.txt               12:00           12:00
          file8.txt               12:00           12:00
          file9.txt               12:00           12:00
          folder1/file1_1.txt     12.00           12:00
          folder2/file2_1.txt     12:00           12:00
          folder3/file3_1.txt     12:00           12:00
          folder4/file4_1.txt     12:00           12:00
          folder5/file5_1.txt     12:00           12:00
          folder6/file6_1.txt     12:00           12:00
          folder7/file7_1.txt     12:00           12:00
        """
        cls._prepare_initial_local_fixture()

        # Synchronize folders (also creates meta data files)
        opts = {"verbose": 0}
        stats = cls._sync_test_folders(BiDirSynchronizer, opts)

        assert stats["files_written"] == 16
        assert stats["dirs_created"] == 7
        return

    @classmethod
    def _prepare_synced_fixture_without_meta(cls):
        """Create two identical fixture folders.

        This creates the same result as`_prepare_initial_synced_fixture()`,
        but without using BiDirSynchronizer, so no meta data is created.

        For FTP based tests, BiDirSynchronizer copies files via FTP, so the
        time stamps are set to `now` (but are recorded correctly in the remote meta data).
        If we want to write FTP tests for scenarios that don't yet have meta data
        generated, _prepare_synced_fixture_without_meta() sets up the fixture with
        time stamps as expected by the asserts, so we can re-use the test cases from
        file system tests.
        """
        # The setUp() code already used `_prepare_initial_synced_fixture()`,
        # so we have to reset and do it again:
        cls._prepare_initial_local_fixture()

        # Use file system commands to copy local to remote (maintan 12:00:00 times)
        remove_test_folder("remote")
        shutil.copytree(os.path.join(PYFTPSYNC_TEST_FOLDER, "local"),
                        os.path.join(PYFTPSYNC_TEST_FOLDER, "remote"))

    @classmethod
    def _prepare_modified_fixture(cls):
        """Modify both folders and run sync with specific options.

        1. This method assumes that _prepare_initial_synced_fixture() was already run
           by the setUp() code and has initialized local & remote with 12 files in 5 folders:

                                  Local           Remote
          file?.txt               12:00           12:00
          ...

        2. Metadata was also created accordingly.

        3. Now we simulate user modifications on both targets:

                                  Local           Remote
          ------------------------------------------------------------------------------
          file1.txt               12:00           12:00        (unmodified)
          file2.txt               13:00           12:00
          file3.txt                 x             12:00
          file4.txt               12:00           13:00
          file5.txt               12:00             x
          file6.txt               13:00           13:00:05     CONFLICT!
          file7.txt               13:00:05        13:00        CONFLICT!
          file8.txt                 x             13:00        CONFLICT!
          file9.txt               13:00             x          CONFLICT!

          folder1/file1_1.txt     12.00           12:00        (unmodified)
          folder2/file2_1.txt     13.00           12:00
          folder3/file3_1.txt       x             12:00        (folder deleted)
          folder4/file4_1.txt       x             13:00        (*) undetected CONFLICT!
          folder5/file5_1.txt     12:00           13:00
          folder6/file6_1.txt     12:00             x          (folder deleted)
          folder7/file7_1.txt     13:00             x          (*) undetected CONFLICT!

          new_file1.txt           13:00             -
          new_file2.txt             -             13:00
          new_file3.txt           13:00           13:00        (same size)
          new_file4.txt           13:00           13:00        CONFLICT! (different size)
          new_file5.txt           13:00           13:00:05     CONFLICT!
          new_file6.txt           13:00:05        13:00        CONFLICT!

          NOTE: (*) currently conflicts are NOT detected, when a file is edited on one
                    target and the parent folder is removed on the peer target.
                    The folder will be removed on sync!

        4. Finally we call bi-dir sync with the custom options and return runtime stats.
        """

        if not cls.use_ftp_target:
            # On local targets, we can rely on mtimes:
            assert get_test_file_date("remote/folder5/file5_1.txt") == STAMP_20140101_120000

        # # If this method is run from an FTP-based instance, we cannot rely on mtimes.
        # meta = get_metadata("remote/folder5")
        # if meta:
        #     # We are using an FTP target, so remote file times are not reliable.
        #     # Instead we use meta data files:
        #     assert meta["mtimes"]["file5_1.txt"]["m"] == STAMP_20140101_120000
        # else:
        #     # On local targets, we can rely on mtimes:
        #     assert get_test_file_date("remote/folder5/file5_1.txt") == STAMP_20140101_120000

        # Change, remove, and add local only
        write_test_file("local/file2.txt", dt="2014-01-01 13:00:00", content="local 13:00")
        remove_test_file("local/file3.txt")
        write_test_file("remote/file4.txt", dt="2014-01-01 13:00:00", content="remote 13:00")
        remove_test_file("remote/file5.txt")
        # Conflict: changed local and remote, remote is newer
        write_test_file("local/file6.txt", dt="2014-01-01 13:00:00", content="local 13:00")
        write_test_file("remote/file6.txt", dt="2014-01-01 13:00:05", content="remote 13:00:05")
        # Conflict: changed local and remote, local is newer
        write_test_file("local/file7.txt", dt="2014-01-01 13:00:05", content="local 13:00:05")
        write_test_file("remote/file7.txt", dt="2014-01-01 13:00:00", content="remote 13:00")
        # Conflict: removed local, but modified remote
        remove_test_file("local/file8.txt")
        write_test_file("remote/file8.txt", dt="2014-01-01 13:00:00", content="remote 13:00")
        # Conflict: removed remote, but modified local
        write_test_file("local/file9.txt", dt="2014-01-01 13:00:00", content="local 13:00")
        remove_test_file("remote/file9.txt")

        write_test_file("local/folder2/file2_1.txt", dt="2014-01-01 13:00:00", content="local 13:00")
        remove_test_folder("local/folder3")
        # Conflict: Modify sub-folder item on remote, but remove parent folder on local
        remove_test_folder("local/folder4")
        write_test_file("remote/folder4/file4_1.txt", dt="2014-01-01 13:00:00", content="remote 13:00")

        write_test_file("remote/folder5/file5_1.txt", dt="2014-01-01 13:00:00", content="remote 13:00")
        remove_test_folder("remote/folder6")
        # Conflict: Modify sub-folder item on local, but remove parent folder on remote
        write_test_file("local/folder7/file7_1.txt", dt="2014-01-01 13:00:00", content="local 13:00")
        remove_test_folder("remote/folder7")

        write_test_file("local/new_file1.txt", dt="2014-01-01 13:00:00", content="local 13:00")
        write_test_file("remote/new_file2.txt", dt="2014-01-01 13:00:00", content="remote 13:00")
        # Identical files on both sides (same time and size):
        write_test_file("local/new_file3.txt", dt="2014-01-01 13:00:00", content="local 13:00")
        write_test_file("remote/new_file3.txt", dt="2014-01-01 13:00:00", content="local 13:00")
        # Identical files on both sides (same time but different size):
        write_test_file("local/new_file4.txt", dt="2014-01-01 13:00:00", content="local 13:00")
        write_test_file("remote/new_file4.txt", dt="2014-01-01 13:00:00", content="remote 13:00 with other content")
        # Two new files on both sides with same name but different time
        write_test_file("local/new_file5.txt", dt="2014-01-01 13:00:00", content="local 13:00")
        write_test_file("remote/new_file5.txt", dt="2014-01-01 13:00:05", content="remote 13:00:05")
        # Two new files on both sides with same name but different time
        write_test_file("local/new_file6.txt", dt="2014-01-01 13:00:05", content="local 13:00:05")
        write_test_file("remote/new_file6.txt", dt="2014-01-01 13:00:00", content="remote 13:00")

    @classmethod
    def _make_remote_target(cls):
        """Return the remote target instance, depending on `use_ftp_target`."""
        if cls.use_ftp_target:
            check_ftp_test_connection(PYFTPSYNC_TEST_FOLDER, PYFTPSYNC_TEST_FTP_URL)
            remote = make_target(PYFTPSYNC_TEST_FTP_URL)
        else:
            remote = FsTarget(os.path.join(PYFTPSYNC_TEST_FOLDER, "remote"))
        return remote

    @classmethod
    def _sync_test_folders(cls, synchronizer_class, options, remote=None):
        """Run synchronizer with fresh objects and custom options."""
        local = FsTarget(os.path.join(PYFTPSYNC_TEST_FOLDER, "local"))
        if remote is None:
            remote = cls._make_remote_target()
        opts = {"verbose": 1}
        if options:
            opts.update(options)

        s = synchronizer_class(local, remote, opts)
        s.run()
        s.close()
        return s.get_stats()

    def do_run_suite(self, synchronizer_class, opts):
        """Run a synchronizer with specific options against a defined fixture."""
        self._prepare_modified_fixture()
        # Synchronize folders
        stats = self._sync_test_folders(synchronizer_class, opts)
        return stats

    def assert_test_folder_equal(self, dict_1, dict_2):
        """Compare two folder content dicts, depending on `use_ftp_target`."""
        if self.use_ftp_target:
            # FTP target does not maintain the file time, so we ignore it for comparisons.
            a = copy.deepcopy(dict_1)
            for v in a.values():
                v["date"] = "?"

            b = copy.deepcopy(dict_2)
            for v in b.values():
                v["date"] = "?"

            self.assertDictEqual(a, b)
        else:
            self.assertDictEqual(dict_1, dict_2)
        return

    def _dump_de_facto_results(self, stats):
        """Print current fixture (handy while writing new test cases)."""
        print("*** stats:")
        pprint(stats)
        print("*** local:")
        pprint(get_test_folder("local"), width=128)
        print("*** remote:")
        pprint(get_test_folder("remote"), width=128)


if __name__ == "__main__":
    prepare_fixture()
