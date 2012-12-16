# -*- coding: iso-8859-1 -*-
"""
Tests for scioweb.eplm.formsheets.eplm_base
"""
import unittest


from unittest import TestCase

from ftpsync.targets import *  # @UnusedWildImport
from ftplib import FTP
from pprint import pprint

#===============================================================================
# BaseTest
#===============================================================================
class FtpTest(TestCase):                          
    """Test ."""
    HOST = "www.wwwendt.de"
    PATH = "/_temp"
    def setUp(self):
        user, passwd = get_stored_credentials("pyftpsync.pw", self.HOST)
        self.ftp = FTP()
#        self.ftp.debug(1) 
        self.ftp.connect(self.HOST)
        self.ftp.login(user, passwd)

    def tearDown(self):
#        self.ftp.abort()
#        self.ftp.close()
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
#        target = FtpTarget("http://www.wwwendt.de", user, password)

    def test_mlsd(self):
        ftp = self.ftp
        self.assertEqual(ftp.pwd(), "/")
        ftp.cwd(self.PATH)
        self.assertEqual(ftp.pwd(), self.PATH)
        
        def adder(line):
            print(line)
        ftp.retrlines("MLSD", adder)
#        target = FtpTarget("http://www.wwwendt.de", user, password)
#        dir = FTPDirectory(self.PATH)
#        dir.getdata(ftp)
#        for f in dir.walk():
#            print(f)

    def test_remote(self):
        user, passwd = get_stored_credentials("pyftpsync.pw", self.HOST)
        remote = FtpTarget(self.PATH, self.HOST, user, passwd)
        remote.cwd(self.PATH)
        self.assertEqual(remote.pwd(), self.PATH)
        self.assertRaises(RuntimeError, remote.cwd, "..")
        
    def test_download_fs_fs(self):
        local = FsTarget("/Users/martin/temp")
        remote = FsTarget("/Users/martin/temp2")
        opts = {"force": False, "delete": False}
        s = DownloadSynchronizer(local, remote, opts)
        s.run()
        stats = s.get_stats()
        pprint(stats)
#        self.assertEqual(stats["source_files"], 1)

    def test_download_fs_ftp(self):
        local = FsTarget("/Users/martin/temp")
        user, passwd = get_stored_credentials("pyftpsync.pw", self.HOST)
        remote = FtpTarget(self.PATH, self.HOST, user, passwd)
        opts = {"force": False, "delete": False}
        s = DownloadSynchronizer(local, remote, opts)
        s.run()
        stats = s.get_stats()
        pprint(stats)
#        self.assertEqual(stats["source_files"], 1)

    def test_upload_fs_fs(self):
        local = FsTarget("/Users/martin/temp")
        remote = FsTarget("/Users/martin/temp2")
        opts = {"force": False, "delete": False}
        s = UploadSynchronizer(local, remote, opts)
        s.run()
        stats = s.get_stats()
        pprint(stats)
#        self.assertEqual(stats["source_files"], 1)

    def test_upload_fs_ftp(self):
        local = FsTarget("/Users/martin/temp")
        user, passwd = get_stored_credentials("pyftpsync.pw", self.HOST)
        remote = FtpTarget(self.PATH, self.HOST, user, passwd)
        opts = {"force": False, "delete": False}
        s = UploadSynchronizer(local, remote, opts)
        s.run()
        stats = s.get_stats()
        pprint(stats)
#        self.assertEqual(stats["source_files"], 1)


class PlainTest(TestCase):                          
    """Test ."""
    HOST = "www.wwwendt.de"
    PATH = "/_temp"
    def setUp(self):
#        user, passwd = get_stored_credentials("pyftpsync.pw", self.HOST)
#        self.ftp = FTP()
##        self.ftp.debug(1) 
#        self.ftp.connect(self.HOST)
#        self.ftp.login(user, passwd)
        pass
    
    def tearDown(self):
        pass
    
    def test_json(self):
        user, passwd = get_stored_credentials("pyftpsync.pw", self.HOST)
        remote = FtpTarget(self.PATH, self.HOST, user, passwd)

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
                if not s: break
                print("%r" % s)
            buf.seek(0)
            print(buf.getvalue())
            b = io.BytesIO(bytes(buf.getvalue(), "utf8")) 
        res = remote.ftp.storlines("STOR " + "meta.json", b)
        print(res)


    def test_make_target(self):
        t = make_target("ftp://ftp.example.com/target/folder", connect=False)
        self.assertTrue(isinstance(t, FtpTarget))
        self.assertEqual(t.host, "ftp.example.com")
        self.assertEqual(t.root_dir, "/target/folder")
        self.assertEqual(t.username, None)
        # scheme is case-insensitive
        t = make_target("FTP://ftp.example.com/target/folder", connect=False)
        self.assertTrue(isinstance(t, FtpTarget))
        
        # pass credentials wit URL
        t = make_target("ftp://user:secret@ftp.example.com/target/folder", connect=False)
        self.assertTrue(isinstance(t, FtpTarget))
        self.assertEqual(t.host, "ftp.example.com")
        self.assertEqual(t.username, "user")
        self.assertEqual(t.password, "secret")
        self.assertEqual(t.root_dir, "/target/folder")

        t = make_target("ftp://www.user.com:secret@ftp.example.com/target/folder", connect=False)
        self.assertTrue(isinstance(t, FtpTarget))
        self.assertEqual(t.username, "www.user.com")
        self.assertEqual(t.password, "secret")
        self.assertEqual(t.root_dir, "/target/folder")

        # unsupported schemes
        self.assertRaises(ValueError, make_target, "http://example.com/test")
        self.assertRaises(ValueError, make_target, "https://example.com/test")


#===============================================================================
# Main
#===============================================================================
if __name__ == "__main__":
#    unittest.main()

    print(sys.version)
    suite = unittest.TestSuite()
#    suite.addTest(FtpTest("test_upload_fs_fs"))
#    suite.addTest(FtpTest("test_download_fs_fs"))
#    suite.addTest(FtpTest("test_upload_fs_ftp"))
#    suite.addTest(FtpTest("test_download_fs_ftp"))
    suite.addTest(PlainTest("test_json"))
    suite.addTest(PlainTest("test_make_target"))
    unittest.TextTestRunner(verbosity=1).run(suite)
