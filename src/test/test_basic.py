# -*- coding: iso-8859-1 -*-
"""
Tests for scioweb.eplm.formsheets.eplm_base
"""
import unittest


from unittest import TestCase

from ftpsync.targets import *
from ftplib import FTP

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
        print res
        res = ftp.dir()
        print res
#        target = FtpTarget("http://www.wwwendt.de", user, password)

    def test_mlsd(self):
        ftp = self.ftp
        self.assertEqual(ftp.pwd(), "/")
        ftp.cwd(self.PATH)
        self.assertEqual(ftp.pwd(), self.PATH)
        
        def adder(line):
            print line
        ftp.retrlines("MLSD", adder)
#        target = FtpTarget("http://www.wwwendt.de", user, password)
        dir = FTPDirectory(self.PATH)
        dir.getdata(ftp)
        for f in dir.walk():
            print f

    def test_remote(self):
        user, passwd = get_stored_credentials("pyftpsync.pw", self.HOST)
        remote = FtpTarget(self.PATH, self.HOST, user, passwd)
        remote.cwd(self.PATH)
        self.assertEqual(remote.pwd(), self.PATH)
        self.assertRaises(RuntimeError, remote.cwd, "..")


#===============================================================================

# Main
#===============================================================================
if __name__ == "__main__":
    unittest.main()   
