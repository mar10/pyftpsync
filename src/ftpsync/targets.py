'''
Created on 14.09.2012

@author: Wendt
'''
import os

#===============================================================================
# _Target
#===============================================================================
class _Target(object):
    def __init__(self):
        self.readonly = True
        self.root = None
        self.connected = False
    def __del__(self):
        self.close()
    def open(self):
        raise NotImplementedError
    def close(self):
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
    def __init__(self, url, username=None, password=None):
        self.url = url
        self.username = username
        self.password = password
        super(FtpTarget, self).__init__()


#===============================================================================
# Synchronizer
#===============================================================================
class Synchronizer(object):
    def __init__(self, source, target):
        self.source = source
        self.target = target

    def upload(self, overwrite=True, backups=False, dry_run=False):
        pass

    def download(self, overwrite=True, backups=False, dry_run=False):
        pass
