# -*- coding: iso-8859-1 -*-
'''
Created on 14.09.2012

@author: Wendt
'''
import os
import time
import collections
from ftplib import FTP
from urlparse import urljoin


def get_stored_credentials(filename, url):
    """Parse a file in the user's home director, formatted like:
    
    URL = user:password
    """
    home_path = os.path.expanduser("~")
    file_path = os.path.join(home_path, filename)
    if os.path.isfile(file_path):
        with open(file_path, "rt") as f:
            for line in f:
                line = line.strip()
                if not "=" in line or line.startswith("#") or line.startswith(";"):
                    continue
                u, creds = line.split("=", 1)
                if not creds or u.strip().lower() != url:
                    continue
                creds = creds.strip()
                return creds.split(":", 1)
    return None


#===============================================================================
# FTPDirectory
# @see http://stackoverflow.com/questions/2867217/how-to-delete-files-with-a-python-script-from-a-ftp-server-which-are-older-than/3114477#3114477
#===============================================================================
FTPDir = collections.namedtuple("FTPDir", "name size mtime tree")
FTPFile = collections.namedtuple("FTPFile", "name size mtime")

class FTPDirectory(object):
    def __init__(self, path="."):
        self.dirs = []
        self.files = []
        self.path = path

    def getdata(self, ftpobj):
        def _addline(line):
            data, _, name = line.partition("; ")
            target = size = mtime = None
            fields = data.split(";")
            # http://tools.ietf.org/html/rfc3659#page-23
            # "Size" / "Modify" / "Create" / "Type" / "Unique" / "Perm" / "Lang" / "Media-Type" / "CharSet" / os-depend-fact / local-fact
            for field in fields:
                field_name, _, field_value = field.partition("=")
                field_name = field_name.lower()
                if field_name == "type":
                    target = self.dirs if field_value == "dir" else self.files
                elif field_name in ("sizd", "size"):
                    size = int(field_value)
                elif field_name == "modify":
                    mtime = time.mktime(time.strptime(field_value, "%Y%m%d%H%M%S"))
            if target is self.files:
                target.append(FTPFile(name, size, mtime))
            else:
                target.append(FTPDir(name, size, mtime, self.__class__(os.path.join(self.path, name))))
        # raises error_perm, if command is not supported
        ftpobj.retrlines("MLSD", _addline)


    def walk(self):
        for ftpfile in self.files:
            yield self.path, ftpfile
        for ftpdir in self.dirs:
            for path, ftpfile in ftpdir.tree.walk():
                yield path, ftpfile


class FTPTree(FTPDirectory):
    def getdata(self, ftpobj):
        super(FTPTree, self).getdata(ftpobj)
        for dirname in self.dirs:
            ftpobj.cwd(dirname.name)
            dirname.tree.getdata(ftpobj)
            ftpobj.cwd("..")



class _Resource(object):
    def __init__(self, name, size, mtime):
        self.name = name
        self.size = size
        self.mtime = mtime

    def __eq__(self, other):
        return other and other.__class__ == self.__class__ and other.name == self.name and other.size == self.size and other.mtime == self.mtime
        

class File(_Resource):
    def __init__(self, name, size, mtime):
        super(File, self).__init__(name, size, mtime)


class Directory(_Resource):
    def __init__(self, name, size, mtime):
        super(File, self).__init__(name, size, mtime)
        # None: unknown, []: empty
        self.files = None
        self.dirs = None

    def walk(self):
        for ftpfile in self.files:
            yield self.path, ftpfile
        for ftpdir in self.dirs:
            for path, ftpfile in ftpdir.tree.walk():
                yield path, ftpfile
    
#===============================================================================
# _Target
#===============================================================================
class _Target(object):
    def __init__(self, root):
        self.readonly = True
        self.root_dir = root
        self.cur_dir = None
        self.connected = False
        self.save_mode = True
        self.dry_run = True
    def __del__(self):
        self.close()
    def open(self):
        raise NotImplementedError
    def close(self):
        raise NotImplementedError
    def walk(self):
        raise NotImplementedError
    def get_dir(self, rel_path):
        """Return a list of filenames."""
        raise NotImplementedError


#===============================================================================
# DirTarget
#===============================================================================
class DirTarget(_Target):
    def __init__(self, path, create=False):
        super(DirTarget, self).__init__()
        self.path = os.path.abspath(path)
        if not os.path.isdir(self.path):
            raise ValueError("%s is not a directory" % self.path)


#===============================================================================
# FtpTarget
#===============================================================================
class FtpTarget(_Target):
    def __init__(self, path, host, username=None, password=None, connect=True, debug=1):
        path = path or "/"
        super(FtpTarget, self).__init__(path)
        self.ftp = FTP()
        self.ftp.debug(debug)
        self.host = host
        self.username = username
        self.password = password
        if connect:
            self.open()

    def __str__(self):
        return "ftp:%s/%s" % (self.host, self.cur_dir)
    
    def open(self):
        self.ftp.connect(self.host)
        if self.username:
            self.ftp.login(self.username, self.password)
        self.ftp.cwd(self.root_dir)
        pwd = self.ftp.pwd()
        if pwd != self.root_dir:
            raise RuntimeError("Unable to navigate to working directory %r" % self.root_dir)
        self.cur_dir = pwd 
        
    def close(self):
        self.ftp.quit()
        
    def cwd(self, dirname):
        path =  urljoin(self.cur_dir, dirname)
        if not path.startswith(self.root_dir):
            raise RuntimeError("Tried to navigate outside root %r: %r" % (self.root_dir, path))
        self.ftp.cwd(dirname)
        self.cur_dir = path

    def pwd(self):
        return self.ftp.pwd()

    def get_dir(self, deep=False):
        d = Directory(self.cur_dir, None, None)

        def _addline(line):
            data, _, name = line.partition("; ")
            target = size = mtime = None
            fields = data.split(";")
            d.files = []
            d.dirs = []
            # http://tools.ietf.org/html/rfc3659#page-23
            # "Size" / "Modify" / "Create" / "Type" / "Unique" / "Perm" / "Lang" / "Media-Type" / "CharSet" / os-depend-fact / local-fact
            for field in fields:
                field_name, _, field_value = field.partition("=")
                field_name = field_name.lower()
                if field_name == "type":
                    target = self.dirs if field_value == "dir" else self.files
                elif field_name in ("sizd", "size"):
                    size = int(field_value)
                elif field_name == "modify":
                    mtime = time.mktime(time.strptime(field_value, "%Y%m%d%H%M%S"))

            if target is self.files:
                target.append(File(name, size, mtime))
            else:
                target.append(Directory(name, size, mtime, self.__class__(os.path.join(self.path, name))))
        # raises error_perm, if command is not supported
        self.ftp.retrlines("MLSD", _addline)
        return d


#===============================================================================
# Synchronizer
#===============================================================================
class Synchronizer(object):
    def __init__(self, local, remote):
        self.local = local
        self.remote = remote

    def upload(self, overwrite=True, backups=False, dry_run=False):
        pass

    def download(self, overwrite=True, backups=False, dry_run=False):
        pass
