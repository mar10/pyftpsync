# -*- coding: utf-8 -*-
"""
(c) 2012-2020 Martin Wendt; see https://github.com/mar10/pyftpsync
Licensed under the MIT license: https://www.opensource.org/licenses/mit-license.php
"""
import configparser
import getpass
import logging
import netrc
import os
import sys
from datetime import datetime

_logger = None


PYTHON_VERSION = "{}.{}.{}".format(
    sys.version_info[0], sys.version_info[1], sys.version_info[2]
)


# def is_basestring(s):
#     """Return True for any string type, i.e. for str/unicode on Py2 and bytes/str on Py3."""
#     return isinstance(s, (str, bytes))


# def is_bytes(s):
#     """Return True for bytestrings, i.e. for str on Py2 and bytes on Py3."""
#     return isinstance(s, bytes)


def is_native(s):
    """Return True for native strings, i.e. for str on Py2 and Py3."""
    return isinstance(s, str)


# def is_unicode(s):
#     """Return True for unicode strings, i.e. for unicode on Py2 and str on Py3."""
#     return isinstance(s, str)


def to_bytes(s, encoding="utf-8"):
    """Convert a text string (unicode) to bytestring, i.e. str on Py2 and bytes on Py3."""
    if type(s) is not bytes:
        s = bytes(s, encoding)
    return s


def to_native(s, encoding="utf-8"):
    """Convert data to native str type, i.e. bytestring on Py2 and unicode on Py3."""
    if type(s) is bytes:
        s = str(s, encoding)
    elif type(s) is not str:
        s = str(s)
    return s


to_unicode = to_native
"""Convert binary data to unicode (text strings) on Python 2 and 3."""

# Binary Strings

# b_empty = to_bytes("")
# b_slash = to_bytes("/")


def get_pyftpsync_logger():
    return _logger


def set_pyftpsync_logger(logger=True):
    """Define target for common output.

    Args:
        logger (bool | None | logging.Logger):
            Pass None to use `print()` to stdout instead of logging.
            Pass True to create a simple standard logger.
    """
    global _logger
    prev_logger = _logger
    if logger is True:
        logging.basicConfig(level=logging.INFO)
        _logger = logging.getLogger("pyftpsync")
        _logger.setLevel(logging.DEBUG)
    else:
        _logger = logger
    return prev_logger


# Init default logger
set_pyftpsync_logger(True)


def write(*args, **kwargs):
    """Redirectable wrapper for print statements."""
    debug = kwargs.pop("debug", None)
    warning = kwargs.pop("warning", None)
    if _logger:
        kwargs.pop("end", None)
        kwargs.pop("file", None)
        if debug:
            _logger.debug(*args, **kwargs)
        elif warning:
            _logger.warning(*args, **kwargs)
        else:
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
    write_error(
        "Unable to import 'colorama' library: Colored output is not available. "
        "Try `pip install colorama`."
    )
    colorama = None


def check_cli_verbose(default=3):
    """Check for presence of `--verbose`/`--quiet` or `-v`/`-q` without using argparse."""
    args = sys.argv[1:]
    verbose = default + args.count("--verbose") - args.count("--quiet")

    for arg in args:
        if arg.startswith("-") and not arg.startswith("--"):
            verbose += arg[1:].count("v")
            verbose -= arg[1:].count("q")
    return verbose


try:
    # prevent loading messages
    if check_cli_verbose() <= 3:
        logging.getLogger("keyring.backend").setLevel(logging.WARNING)
    import keyring
except ImportError:
    write_error(
        "Unable to import 'keyring' library: Storage of passwords is not available. "
        "Try `pip install keyring`."
    )
    keyring = None


DEFAULT_CREDENTIAL_STORE = "pyftpsync.pw"
DRY_RUN_PREFIX = "(DRY-RUN) "
IS_REDIRECTED = os.fstat(0) != os.fstat(1)
# DEFAULT_BLOCKSIZE = 8 * 1024
VT_ERASE_LINE = "\x1b[2K"


def namespace_to_dict(o):
    """Convert an argparse namespace object to a dictionary."""
    d = {}
    for k, v in o.__dict__.items():
        if not callable(v):
            d[k] = v
    return d


def eps_compare(f1, f2, eps):
    """Return true if |f1-f2| <= eps."""
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
    return datetime.fromtimestamp(stamp).strftime("%Y-%m-%d %H:%M:%S")


_pyftpsyncrc_parser = configparser.RawConfigParser()
_pyftpsyncrc_parser.read(os.path.expanduser("~/.pyftpsyncrc"))


def get_option(env_name, section, opt_name, default=None):
    """Return a configuration setting from environment var or .pyftpsyncrc"""
    val = os.environ.get(env_name)
    if val is None:
        try:
            val = _pyftpsyncrc_parser.get(section, opt_name)
        except (configparser.NoSectionError, configparser.NoOptionError):
            pass
    if val is None:
        val = default
    return val


# ===============================================================================
#
# ===============================================================================


def prompt_for_password(url, user=None, default_user=None):
    """Prompt for username and password.

    If a user name is passed, only prompt for a password.
    Args:
        url (str): hostname
        user (str, optional):
            Pass a valid name to skip prompting for a user name
        default_user (str, optional):
            Pass a valid name that is used as default when prompting
            for a user name
    Raises:
        KeyboardInterrupt if user hits Ctrl-C
    Returns:
        (username, password) or None
    """
    if user is None:
        default_user = default_user or getpass.getuser()
        while user is None:
            user = input("Enter username for {} [{}]: ".format(url, default_user))
            if user.strip() == "" and default_user:
                user = default_user
    if user:
        pw = getpass.getpass(
            "Enter password for {}@{} (Ctrl+C to abort): ".format(user, url)
        )
        if pw or pw == "":
            return (user, pw)
    return None


def get_credentials_for_url(url, opts, force_user=None):
    """Lookup credentials for a given target in keyring and .netrc.

    Optionally prompts for credentials if not found.

    Args:
        url (str): target URL (without username or password parts)
        opts (dict):
        force_user (str, optional) username to be used instead of prompting
    Returns:
        2-tuple (username, password) or None
    """
    assert "@" not in url
    creds = None
    verbose = int(opts.get("verbose", 3))
    force_prompt = opts.get("prompt", False)
    allow_prompt = not opts.get("no_prompt", True)
    allow_keyring = not opts.get("no_keyring", False) and not force_user
    allow_netrc = not opts.get("no_netrc", False) and not force_user

    # print("get_credentials_for_url", url, force_user, allow_prompt)
    if force_user and not allow_prompt:
        raise RuntimeError(
            "Cannot get credentials for a distinct user ({}) from keyring or .netrc and "
            "prompting is disabled.".format(force_user)
        )

    # Lookup our own pyftpsync 1.x credential store. This is deprecated with 2.x
    home_path = os.path.expanduser("~")
    file_path = os.path.join(home_path, DEFAULT_CREDENTIAL_STORE)
    if os.path.isfile(file_path):
        raise RuntimeError(
            "Custom password files are no longer supported. Delete {} and use .netrc instead.".format(
                file_path
            )
        )

    # 1. Try keyring database
    if creds is None and keyring and allow_keyring and not force_prompt:
        try:
            # Note: we pass the url as `username` and username:password as `password`
            c = keyring.get_password("pyftpsync", url)
            if c is not None:
                creds = c.split(":", 1)
                write(
                    "Using credentials from keyring('pyftpsync', '{}'): {}:***.".format(
                        url, creds[0]
                    )
                )
            else:
                if verbose >= 4:
                    write(
                        "No credentials found in keyring('pyftpsync', '{}').".format(
                            url
                        )
                    )
        # except keyring.errors.TransientKeyringError:
        except Exception as e:
            # e.g. user clicked 'no'
            write_error("Could not get password from keyring {}".format(e))

    # 2. Try .netrc file
    if creds is None and allow_netrc and not force_prompt:
        try:
            authenticators = None
            authenticators = netrc.netrc().authenticators(url)
        except FileNotFoundError:
            if verbose >= 4:
                write("Could not get password (no .netrc file).")
        except Exception as e:
            write_error("Could not read .netrc: {}.".format(e))

        if authenticators:
            creds = (authenticators[0], authenticators[2])
            write("Using credentials from .netrc file: {}:***.".format(creds[0]))
        else:
            if verbose >= 4:
                write("Could not find entry for '{}' in .netrc file.".format(url))

    # 3. Prompt for password if we don't have credentials yet, or --prompt was set.
    if creds is None and allow_prompt and not force_prompt:
        creds = prompt_for_password(url, user=force_user)
    if force_prompt:
        # --prompt was set but we can provide a default for the user name
        assert not creds
        creds = prompt_for_password(url, default_user=force_user)
        # creds = prompt_for_password(url, default_user=creds[0])

    return creds


def save_password(url, username, password):
    """Store credentials in keyring."""
    if keyring:
        if ":" in username:
            raise RuntimeError(
                "Unable to store credentials if username contains a ':' ({}).".format(
                    username
                )
            )

        try:
            # Note: we pass the url as `username` and username:password as `password`
            if password is None:
                keyring.delete_password("pyftpsync", url)
                write("Delete credentials from keyring ({})".format(url))
            else:
                keyring.set_password(
                    "pyftpsync", url, "{}:{}".format(username, password)
                )
                write(
                    "Store credentials in keyring ({}, {}:***).".format(url, username)
                )
        #        except keyring.errors.TransientKeyringError:
        except Exception as e:
            write("Could not delete/set password {}.".format(e))
            pass  # e.g. user clicked 'no'
    else:
        write("Could not store credentials (missing keyring support).")
    return


def str_to_bool(val):
    """Return a boolean for '0', 'false', 'on', ..."""
    val = str(val).lower().strip()
    if val in ("1", "true", "on", "yes"):
        return True
    elif val in ("0", "false", "off", "no"):
        return False
    raise ValueError(
        "Invalid value '{}'"
        "(expected '1', '0', 'true', 'false', 'on', 'off', 'yes', 'no').".format(val)
    )


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

    Returns:
        (bool, int): offset of first mismatch or 0 if equal
    """
    bufsize = 16 * 1024
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


# def decode_dict_keys(d, coding="utf-8"):
#     """Convert all keys to unicde (recursively)."""
#     assert compat.PY2
#     res = {}
#     for k, v in d.items():  #
#         if type(k) is str:
#             k = k.decode(coding)
#         if type(v) is dict:
#             v = decode_dict_keys(v, coding)
#         res[k] = v
#     return res


def make_native_dict_keys(d):
    """Convert all keys to native `str` type (recursively)."""
    res = {}
    for k, v in d.items():  #
        k = to_native(k)
        if type(v) is dict:
            v = make_native_dict_keys(v)
        res[k] = v
    return res


# def decode_utf8_safe(s, fallback="cp1252", raise_error=True):
#     """Try to decode a binary string using UTF-8 but fall back to CP-1252.

#     Returns:
#         (state, unicode): 2-tuple.
#             state: 0:success, 1:fallback worked, 2:failed
#     """
#     if compat.is_unicode(s):
#         return s

#     try:
#         return (0, s.decode("utf-8"))
#     except UnicodeDecodeError:
#         try:
#             return (1, s.decode(fallback))
#         except UnicodeDecodeError:
#             if raise_error:
#                 raise
#     return (2, None)


# def re_encode_binary_to_utf8(s, fallback="cp1252", raise_error=True):
#     """Check if a binary string is UTF-8 compatible, and if not try to re-encode using CP-1252.

#     Returns:
#         (state, bytes): 2-tuple.
#             state: 0:success, 1:fallback worked, 2:failed
#     Raises:
#         UnicodeDecodeError if enocde failed and raise_error was true
#     """
#     assert compat.is_bytes(s)

#     try:
#         # We decode for testing only, then discard the result
#         s.decode("utf-8")
#         return 0, s
#     except UnicodeDecodeError:
#         try:
#             return (1, s.decode(fallback).encode("utf-8"))
#         except UnicodeDecodeError:
#             if not raise_error:
#                 return (2, None)
#     # This will raise the UnicodeDecodeError error again:
#     s.decode("utf-8")
