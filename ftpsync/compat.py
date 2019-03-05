# -*- coding: utf-8 -*-
"""
(c) 2012-2019 Martin Wendt; see https://github.com/mar10/pyftpsync
Licensed under the MIT license: https://www.opensource.org/licenses/mit-license.php
"""
# flake8: noqa

import sys

PY2 = sys.version_info < (3, 0)
PY3 = not PY2
_filesystemencoding = sys.getfilesystemencoding()


try:  # py2
    import ConfigParser as configparser
    from cStringIO import StringIO

    BytesIO = StringIO
    import Queue as queue
except ImportError:  # py3
    import configparser  # noqa
    from io import StringIO  # noqa
    from io import BytesIO  # noqa
    import queue  # noqa

try:  # py3
    from urllib.parse import quote, unquote, urlparse  # noqa
except ImportError:  # py2
    from urllib import quote, unquote  # noqa
    from urlparse import urlparse  # noqa

try:
    console_input = raw_input
except NameError:
    console_input = input

try:
    xrange = xrange  # py2
except NameError:
    xrange = range  # py3

try:
    CompatFileNotFoundError = FileNotFoundError
except NameError:
    CompatFileNotFoundError = IOError

try:
    CompatConnectionError = ConnectionError
except NameError:
    CompatConnectionError = OSError


# String Abstractions

if PY2:

    from base64 import decodestring as base64_decodebytes
    from base64 import encodestring as base64_encodebytes
    from cgi import escape as html_escape

    def is_basestring(s):
        """Return True for any string type, i.e. for str/unicode on Py2 and bytes/str on Py3."""
        return isinstance(s, basestring)

    def is_bytes(s):
        """Return True for bytestrings, i.e. for str on Py2 and bytes on Py3."""
        return isinstance(s, str)

    def is_native(s):
        """Return True for native strings, i.e. for str on Py2 and Py3."""
        return isinstance(s, str)

    def is_unicode(s):
        """Return True for unicode strings, i.e. for unicode on Py2 and str on Py3."""
        return isinstance(s, unicode)

    def to_bytes(s, encoding="utf-8"):
        """Convert unicode (text strings) to binary data, i.e. str on Py2 and bytes on Py3."""
        if type(s) is unicode:
            s = s.encode(encoding)
        elif type(s) is not str:
            s = str(s)
        return s

    to_native = to_bytes
    """Convert data to native str type, i.e. bytestring on Py2 and unicode on Py3."""

    def to_unicode(s, encoding="utf-8"):
        """Convert data to unicode text, i.e. unicode on Py2 and str on Py3."""
        if type(s) is not unicode:
            s = unicode(s, encoding)
        return s


else:  # Python 3

    from base64 import decodebytes as base64_decodebytes
    from base64 import encodebytes as base64_encodebytes
    from html import escape as html_escape

    def is_basestring(s):
        """Return True for any string type, i.e. for str/unicode on Py2 and bytes/str on Py3."""
        return isinstance(s, (str, bytes))

    def is_bytes(s):
        """Return True for bytestrings, i.e. for str on Py2 and bytes on Py3."""
        return isinstance(s, bytes)

    def is_native(s):
        """Return True for native strings, i.e. for str on Py2 and Py3."""
        return isinstance(s, str)

    def is_unicode(s):
        """Return True for unicode strings, i.e. for unicode on Py2 and str on Py3."""
        return isinstance(s, str)

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

b_empty = to_bytes("")
b_slash = to_bytes("/")
