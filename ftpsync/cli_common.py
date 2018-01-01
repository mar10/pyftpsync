# -*- coding: iso-8859-1 -*-
"""
(c) 2012-2018 Martin Wendt; see https://github.com/mar10/pyftpsync
Licensed under the MIT license: http://www.opensource.org/licenses/mit-license.php
"""
from __future__ import print_function

from ftpsync.synchronizers import DEFAULT_OMIT


def add_cli_sub_args(parser):
    parser.add_argument("-n", "--dry-run",
                        action="store_true",
                        help="just simulate and log results, but don't change anything")

    qv_group = parser.add_mutually_exclusive_group()
    qv_group.add_argument("-v", "--verbose", action="count", default=3,
                          help="increment verbosity by one (default: %(default)s, range: 0..5)")
    qv_group.add_argument("-q", "--quiet", action="count", default=0,
                          help="decrement verbosity by one")

    parser.add_argument("--progress",
                        action="store_true",
                        default=False,
                        help="show progress info, even if redirected or verbose < 3")

    parser.add_argument("--no-color",
                        action="store_true",
                        help="prevent use of ansi terminal color codes")

    parser.add_argument("--ftp-active",
                        action="store_true",
                        help="use Active FTP mode instead of passive")

    parser.add_argument("--migrate",
                        action="store_true",
                        default=False,
                        help="replace meta data files from different pyftpsync versions "
                             "with current format. Existing data will be discarded.")

    return


def add_matcher_sub_args(parser):
    parser.add_argument("-m", "--match",
                        help="wildcard for file names using fnmatch syntax "
                        "(default: match all, separate multiple values with ',')")
    parser.add_argument("-x", "--exclude",
                        default=",".join(DEFAULT_OMIT),
                        help="wildcard of files and directories to exclude "
                        "(applied after --match, default: '%(default)s')")
    return


def add_credential_sub_args(parser):
    p_group = parser.add_mutually_exclusive_group()
    p_group.add_argument("--prompt",
                         action="store_true",
                         help="always prompt for password")
    p_group.add_argument("--no-prompt",
                         action="store_true",
                         help="prevent prompting for invalid credentials")

    parser.add_argument("--no-keyring",
                        action="store_true",
                        help="prevent use of the system keyring service for credential lookup")
    parser.add_argument("--no-netrc",
                        action="store_true",
                        help="prevent use of .netrc file for credential lookup")

    parser.add_argument("--store-password",
                        action="store_true",
                        help="save password to keyring if login succeeds")
    return
