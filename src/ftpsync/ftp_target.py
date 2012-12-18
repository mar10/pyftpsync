# -*- coding: iso-8859-1 -*-
"""
"""
from __future__ import print_function

import time
import io
from posixpath import join as join_url
from ftpsync.targets import FileEntry, DirectoryEntry, _Target
import calendar
import json
import sys
from ftplib import FTP


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
        self.cur_dir_meta = None
        self.cur_dir_meta_modified = False
        if connect:
            self.open()

    def __str__(self):
        return "ftp:%s%s" % (self.host, self.cur_dir)

    def open(self):
        self.ftp.connect(self.host)
        if self.username:
            self.ftp.login(self.username, self.password)
        # TODO: case sensivity?
#        resp = self.ftp.sendcmd("system")
#        self.is_unix = "unix" in resp.lower()
        self.ftp.cwd(self.root_dir)
        pwd = self.ftp.pwd()
        if pwd != self.root_dir:
            raise RuntimeError("Unable to navigate to working directory %r" % self.root_dir)
        self.cur_dir = pwd
        self.connected = True

    def close(self):
        if self.connected:
            self.ftp.quit()
        self.connected = False
        
    def cwd(self, dir_name):
        path = join_url(self.cur_dir, dir_name)
        if not path.startswith(self.root_dir):
            raise RuntimeError("Tried to navigate outside root %r: %r" % (self.root_dir, path))
        self.ftp.cwd(dir_name)
        self.cur_dir = path
        self.cur_dir_meta = None
        return self.cur_dir

    def pwd(self):
        return self.ftp.pwd()

    def flush_meta(self):
        if self.readonly:
            return
        if self.cur_dir_meta:
            s = json.dumps(self.cur_dir_meta, indent=4, sort_keys=True)
            self.write_text(self.META_FILE_NAME, s)
        elif self.cur_dir_meta is not None:
            self.ftp.delete(self.META_FILE_NAME)
            return
        self.cur_dir_meta_modified = False

    def get_dir(self):
        entry_list = []
        entry_map = {}
        local_res = {"has_meta": False} # pass local variables outside func scope 
        
        def _addline(line):
            data, _, name = line.partition("; ")
            res_type = size = mtime = unique = None
            fields = data.split(";")
            # http://tools.ietf.org/html/rfc3659#page-23
            # "Size" / "Modify" / "Create" / "Type" / "Unique" / "Perm" / "Lang"
            #   / "Media-Type" / "CharSet" / os-depend-fact / local-fact
            for field in fields:
                field_name, _, field_value = field.partition("=")
                field_name = field_name.lower()
                if field_name == "type":
                    res_type = field_value
                elif field_name in ("sizd", "size"):
                    size = int(field_value)
                elif field_name == "modify":
                    # Use calendar.timegm() instead of time.mktime(), because
                    # the date was returned as UTC
                    mtime = calendar.timegm(time.strptime(field_value, "%Y%m%d%H%M%S"))
                elif field_name == "unique":
                    unique = field_value
                    
            entry = None
            if res_type == "dir":
                entry = DirectoryEntry(self, self.cur_dir, name, size, mtime, unique)
            elif res_type == "file":
                if name == self.META_FILE_NAME:
                    local_res["has_meta"] = True
                else:
                    entry = FileEntry(self, self.cur_dir, name, size, mtime, unique)
            elif res_type in ("cdir", "pdir"):
                pass
            else:
                raise NotImplementedError

            if entry:
                entry_map[name] = entry
                entry_list.append(entry)
                
        # raises error_perm, if command is not supported
        self.ftp.retrlines("MLSD", _addline)

        # load stored meta data if present
        self.cur_dir_meta = None
        self.cur_dir_meta_modified = False
        if local_res["has_meta"]:        
            try:
                m = self.read_text(self.META_FILE_NAME)
                self.cur_dir_meta = json.loads(m)
            except Exception as e:
                print("Could not read meta info: %s" % e, file=sys.stderr)

            # Adjust file mtime from meta data if present
            missing = []
            for n in self.cur_dir_meta:
                if n in entry_map:
                    entry_map[n].mtime_real = self.cur_dir_meta[n]["mtime"]
                    print("*** ADJUST META ENTRY FOR %s: %s -> %s" % (n, entry_map[n].mtime, entry_map[n].mtime_real))
                else:
                    missing.append(n)
            # Remove missing files from cur_dir_meta 
            for n in missing:
                self.cur_dir_meta.pop(n)
                self.cur_dir_meta_modified = True
                print("*** REMOVING META ENTRY FOR %s" % n)

        return entry_list

    def open_readable(self, name):
        """Open cur_dir/name for reading."""
        out = io.BytesIO()
        self.ftp.retrbinary("RETR %s" % name, out.write)
        out.flush()
        out.seek(0)
        return out

    def write_file(self, name, fp_src, blocksize=8192, callback=None):
        self.check_write(name)
        self.ftp.storbinary("STOR %s" % name, fp_src, blocksize, callback)
        # TODO: check result
        
    def remove_file(self, name):
        """Remove cur_dir/name."""
        self.check_write(name)
        if self.cur_dir_meta and self.cur_dir_meta.pop(name, None):
            self.cur_dir_meta_modified = True
        self.ftp.delete(name)

    def set_mtime(self, name, mtime):
        self.check_write(name)
        # We cannot set the mtime on FTP servers, so we store this as additional
        # meta data in the directory
        if self.cur_dir_meta is None:
            self.cur_dir_meta = {}
        self.cur_dir_meta[name] = {"touch": time.mktime(time.gmtime()), 
                                   "mtime": mtime}
        self.cur_dir_meta_modified = True
