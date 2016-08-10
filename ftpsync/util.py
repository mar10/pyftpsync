# -*- coding: iso-8859-1 -*-
"""
(c) 2012-2016 Martin Wendt; see https://github.com/mar10/pyftpsync
Licensed under the MIT license: http://www.opensource.org/licenses/mit-license.php
"""

from __future__ import print_function

import os
import sys
import getpass


try:
    from urllib.parse import urlparse
except ImportError:
    # Python 2
    from urlparse import urlparse  # @UnusedImport

try:
    import colorama  # provide color codes, ...
    colorama.init()  # improve color handling on windows terminals
except ImportError:
    print("Unable to import 'colorama' library: Colored output is not available. Try `pip install colorama`.")
    colorama = None

try:
    import keyring
except ImportError:
    print("Unable to import 'keyring' library: Storage of passwords is not available. Try `pip install keyring`.")
    keyring = None


DEFAULT_CREDENTIAL_STORE = "pyftpsync.pw"
DRY_RUN_PREFIX = "(DRY-RUN) "
IS_REDIRECTED = (os.fstat(0) != os.fstat(1))
DEFAULT_BLOCKSIZE = 8 * 1024
VT_ERASE_LINE = "\x1b[2K"

#===============================================================================
#
#===============================================================================

def prompt_for_password(url, user=None):
    if user is None:
        default_user = getpass.getuser()
        while user is None:
            user = console_input("Enter username for %s [%s]: " % (url, default_user))
            if user.strip() == "" and default_user:
                user = default_user
    if user:
        pw = getpass.getpass("Enter password for %s@%s: " % (user, url))
        if pw:
            return (user, pw)
    return None


def get_credentials_for_url(url, allow_prompt):
    """
    @returns 2-tuple (username, password) or None
    """
    creds = None

    # Lookup our own credential store
    # Parse a file in the user's home directory, formatted like:
    # URL = user:password
    home_path = os.path.expanduser("~")
    file_path = os.path.join(home_path, DEFAULT_CREDENTIAL_STORE)
    if os.path.isfile(file_path):
        raise RuntimeError("Custom password files are no longer supported. Consider deleting {0}.".format(file_path))
#         with open(file_path, "rt") as f:
#             for line in f:
#                 line = line.strip()
#                 if not "=" in line or line.startswith("#") or line.startswith(";"):
#                     continue
#                 u, c = line.split("=", 1)
#                 if c and u.strip().lower() == url.lower():
#                     c = c.strip()
#                     creds = c.split(":", 1)
#                     print("Using credentials from %s ('%s'): %s:***)" % (file_path, url, creds[0]))
#                     break

    # Query
    if creds is None and keyring:
        try:
            # Note: we pass the url as `username` and username:password as `password`
            c = keyring.get_password("pyftpsync", url)
            if c is not None:
                creds = c.split(":", 1)
#                print(creds)
                print("Using credentials from keyring('pyftpsync', '%s'): %s:***)" % (url, creds[0]))
#        except keyring.errors.TransientKeyringError:
        except Exception as e:
            print("Could not get password {0}".format(e))
            pass # e.g. user clicked 'no'

    # Prompt
    if creds is None and allow_prompt:
        creds = prompt_for_password(url)

    return creds


def save_password(url, username, password):
    if keyring:
        if ":" in username:
            raise RuntimeError("Unable to store credentials if username contains a ':' (%s)" % username)

        try:
            # Note: we pass the url as `username` and username:password as `password`
            if password is None:
                keyring.delete_password("pyftpsync", url)
                print("delete_password(%s)" % url)
            else:
                keyring.set_password("pyftpsync", url, "%s:%s" % (username, password))
                print("save_password(%s, %s:***)" % (url, username))
#        except keyring.errors.TransientKeyringError:
        except Exception as e:
            print("Could not delete/set password {0}".format(e))
            pass # e.g. user clicked 'no'
    else:
        print("Could not store password (missing keyring library)")
    return


def ansi_code(name):
    """Return ansi color or style codes or '' if colorama is not available."""
    try:
        obj = colorama
        for part in name.split("."):
            obj = getattr(obj, part)
        return obj
    except AttributeError:
        return ""


if sys.version_info[0] < 3:
    # Python 2
    def to_binary(s):
        """Convert unicode (text strings) to binary data on Python 2 and 3."""
        if type(s) is not str:
            s = s.encode("utf8")
        return s

    def to_text(s):
        """Convert binary data to unicode (text strings) on Python 2 and 3."""
        if type(s) is not unicode:
            s = s.decode("utf8")
        return s

    def to_str(s):
        """Convert unicode to native str on Python 2 and 3."""
        if type(s) is unicode:
            s = s.encode("utf8")
        return s
else:
    # Python 3
    def to_binary(s):
        """Convert unicode (text strings) to binary data on Python 2 and 3."""
        if type(s) is str:
            s = bytes(s, "utf8")
        return s

    def to_text(s):
        """Convert binary data to unicode (text strings) on Python 2 and 3."""
        if type(s) is bytes:
            s = str(s, "utf8")
        return s

    def to_str(s):
        """Convert binary data to unicode (text strings) on Python 2 and 3."""
        if type(s) is bytes:
            s = str(s, "utf8")
        return s

try:
    console_input = raw_input
except NameError:
    console_input = input


def byte_compare(stream_a, stream_b):
    """Byte compare two files (early out on first difference).
    
    @return: (bool, int): offset of first mismatch or 0 if equal
    """
    bufsize = DEFAULT_BLOCKSIZE
    equal = True
    ofs = 0
    while True:
        b1 = stream_a.read(bufsize)
        b2 = stream_b.read(bufsize)
        if b1 != b2:
            equal = False
            if b1 and b2:
                # we have two different buffers: find first mismatch
                for a, b in zip(b1, b2):
                    if a != b:
                        break
                    ofs += 1
            break
        ofs += len(b1)
        if not b1:  # both buffers empty
            break
    return (equal, ofs)

#===============================================================================
# LogginFileWrapper
# Wrapper around a file for writing to write a hash sign every block.
#===============================================================================
#class LoggingFileWrapper(object):
#    def __init__(self, fp, callback=None):
#        self.fp = fp
#        self.callback = callback or self.default_callback
#        self.bytes = 0
#
#    def __enter__(self):
#        return self
#
#    def __exit__(self, type, value, tb):
#        self.close()
#
#    @staticmethod
#    def default_callback(wrapper, data):
#        print("#", end="")
#        sys.stdout.flush()
#
#    def write(self, data):
#        self.bytes += len(data)
#        self.fp.write(data)
#        self.callback(self, data)
#
#    def close(self):
#        self.fp.close()
