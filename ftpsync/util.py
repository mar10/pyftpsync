# -*- coding: iso-8859-1 -*-
"""
(c) 2012-2017 Martin Wendt; see https://github.com/mar10/pyftpsync
Licensed under the MIT license: http://www.opensource.org/licenses/mit-license.php
"""

from __future__ import print_function

from datetime import datetime
import getpass
import os
import sys
import logging

from ftpsync import compat


_logger = None


def write(*args, **kwargs):
    """Redirectable wrapper for print statements."""
    if _logger:
        kwargs.pop("end", None)
        kwargs.pop("file", None)
        _logger.info(*args, **kwargs)
    else:
        print(*args, **kwargs)


def write_error(*args, **kwargs):
    """Redirectable wrapper for print sys.stderr statements."""
    if _logger:
        kwargs.pop("end", None)
        kwargs.pop("file", None)
        _logger.error(*args, **kwargs)
    else:
        print(*args, file=sys.stderr, **kwargs)


try:
    import colorama  # provide color codes, ...
    colorama.init()  # improve color handling on windows terminals
except ImportError:
    write_error("Unable to import 'colorama' library: Colored output is not available. "
                "Try `pip install colorama`.")
    colorama = None

try:
    import keyring
except ImportError:
    write_error("Unable to import 'keyring' library: Storage of passwords is not available. "
                "Try `pip install keyring`.")
    keyring = None


DEFAULT_CREDENTIAL_STORE = "pyftpsync.pw"
DRY_RUN_PREFIX = "(DRY-RUN) "
IS_REDIRECTED = (os.fstat(0) != os.fstat(1))
# DEFAULT_BLOCKSIZE = 8 * 1024
VT_ERASE_LINE = "\x1b[2K"

# DEBUG_FLAGS = set()
#
# def init_debug_flags(verbosity):
#     if verbosity >= 3:
#         DEBUG_FLAGS.add("runtime_stats")
#     if verbosity >= 4:
#         DEBUG_FLAGS.add("ftp_commands")


def set_logger(logger=True):
    """Define target for common output.

    Args:
        logger (bool|logging.Logger):
            Pass None to use `print()` to stdout instead of logging.
            Pass True to create a simple standard logger.
    """
    global _logger
    if logger is True:
        logging.basicConfig(level=logging.INFO)
        _logger = logging.getLogger("pyftpsync")
        _logger.setLevel(logging.DEBUG)
    else:
        _logger = logger


# Init default logger
set_logger()


def namespace_to_dict(o):
    """Convert an argparse namespace object to a dictionary."""
    d = {}
    for k, v in o.__dict__.items():
        if not callable(v):
            d[k] = v
    return d


def eps_compare(f1, f2, eps):
    res = f1 - f2
    if abs(res) <= eps:  # '<=',so eps == 0 works as expected
        return 0
    elif res < 0:
        return -1
    return 1


def pretty_stamp(stamp):
    """Convert timestamp to verbose string (strip fractions of seconds)."""
    if stamp is None:
        return "n.a."
    # return time.ctime(stamp)
    # return datetime.fromtimestamp(stamp).isoformat(" ")
    return datetime.fromtimestamp(stamp).strftime("%Y-%m-%d %H:%M:%S")


_pyftpsyncrc_parser = compat.configparser.RawConfigParser()
_pyftpsyncrc_parser.read(os.path.expanduser("~/.pyftpsyncrc"))


def get_option(env_name, section, opt_name, default=None):
    """Return a configuration setting from environment var or .pyftpsyncrc"""
    val = os.environ.get(env_name)
    if val is None:
        try:
            val = _pyftpsyncrc_parser.get(section, opt_name)
        except (compat.configparser.NoSectionError, compat.configparser.NoOptionError):
            pass
    if val is None:
        val = default
    return val


# ===============================================================================
#
# ===============================================================================

def prompt_for_password(url, user=None):
    if user is None:
        default_user = getpass.getuser()
        while user is None:
            user = compat.console_input("Enter username for {} [{}]: "
                                        .format(url, default_user))
            if user.strip() == "" and default_user:
                user = default_user
    if user:
        pw = getpass.getpass("Enter password for {}@{}: ".format(user, url))
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
        raise RuntimeError("Custom password files are no longer supported. Consider deleting {}."
                           .format(file_path))

    # Query
    if creds is None and keyring:
        try:
            # Note: we pass the url as `username` and username:password as `password`
            c = keyring.get_password("pyftpsync", url)
            if c is not None:
                creds = c.split(":", 1)
                write("Using credentials from keyring('pyftpsync', '{}'): {}:***."
                      .format(url, creds[0]))
#        except keyring.errors.TransientKeyringError:
        except Exception as e:
            write("Could not get password {}".format(e))
            pass  # e.g. user clicked 'no'

    # Prompt
    if creds is None and allow_prompt:
        creds = prompt_for_password(url)

    return creds


def save_password(url, username, password):
    if keyring:
        if ":" in username:
            raise RuntimeError("Unable to store credentials if username contains a ':' ({})."
                               .formta(username))

        try:
            # Note: we pass the url as `username` and username:password as `password`
            if password is None:
                keyring.delete_password("pyftpsync", url)
                write("Delete credentials from keyring ({})".format(url))
            else:
                keyring.set_password("pyftpsync", url, "{}:{}".format(username, password))
                write("Store credentials in keyring ({}, {}:***).".format(url, username))
#        except keyring.errors.TransientKeyringError:
        except Exception as e:
            write("Could not delete/set password {}.".format(e))
            pass  # e.g. user clicked 'no'
    else:
        write("Could not store credentials (missing keyring support).")
    return


def str_to_bool(val):
    """Return a boolean for '0', 'false', 'on', ...."""
    val = str(val).lower().strip()
    if val in ("1", "true", "on", "yes"):
        return True
    elif val in ("0", "false", "off", "no"):
        return False
    raise ValueError(
        "Invalid value '{}'"
        "(expected '1', '0', 'true', 'false', 'on', 'off', 'yes', 'no').".format(val))


def ansi_code(name):
    """Return ansi color or style codes or '' if colorama is not available."""
    try:
        obj = colorama
        for part in name.split("."):
            obj = getattr(obj, part)
        return obj
    except AttributeError:
        return ""


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
