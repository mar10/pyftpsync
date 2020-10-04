# -*- coding: utf-8 -*-
"""
(c) 2012-2020 Martin Wendt; see https://github.com/mar10/pyftpsync
Licensed under the MIT license: https://www.opensource.org/licenses/mit-license.php
"""
import argparse

from ftpsync.synchronizers import DEFAULT_OMIT

# --- verbose_parser ----------------------------------------------------------

verbose_parser = argparse.ArgumentParser(add_help=False)

qv_group = verbose_parser.add_mutually_exclusive_group()
qv_group.add_argument(
    "-v",
    "--verbose",
    action="count",
    default=3,
    help="increment verbosity by one (default: %(default)s, range: 0..5)",
)
qv_group.add_argument(
    "-q", "--quiet", default=0, action="count", help="decrement verbosity by one"
)


# --- common_parser ----------------------------------------------------------


common_parser = argparse.ArgumentParser(add_help=False)

common_parser.add_argument(
    "-n",
    "--dry-run",
    action="store_true",
    help="just simulate and log results, but don't change anything",
)

common_parser.add_argument(
    "--progress",
    action="store_true",
    default=False,
    help="show progress info, even if redirected or verbose < 3",
)

common_parser.add_argument(
    "--no-color", action="store_true", help="prevent use of ansi terminal color codes"
)

common_parser.add_argument(
    "--ftp-active", action="store_true", help="use Active FTP mode instead of passive"
)

common_parser.add_argument(
    "--migrate",
    action="store_true",
    default=False,
    help="replace meta data files from different pyftpsync versions "
    "with current format. Existing data will be discarded.",
)

common_parser.add_argument(
    "--no-verify-host-keys",
    action="store_true",
    help="do not check SFTP connection against `~/.ssh/known_hosts`",
)


# --- matcher_parser ---------------------------------------------------------


matcher_parser = argparse.ArgumentParser(add_help=False)

matcher_parser.add_argument(
    "-m",
    "--match",
    help="wildcard for file names using fnmatch syntax "
    "(default: match all, separate multiple values with ',')",
)
matcher_parser.add_argument(
    "-x",
    "--exclude",
    default=",".join(DEFAULT_OMIT),
    help="wildcard of files and directories to exclude "
    "(applied after --match, default: '%(default)s')",
)
# matcher_parser.add_argument("--no-default-excludes",
#                     action="store_true",
#                     help="If set, ignore patterns will replace the default "
#                     "ignore list instead of adding to it")


# --- creds_parser -----------------------------------------------------------


creds_parser = argparse.ArgumentParser(add_help=False)

p_group = creds_parser.add_mutually_exclusive_group()
p_group.add_argument("--prompt", action="store_true", help="always prompt for password")
p_group.add_argument(
    "--no-prompt", action="store_true", help="prevent prompting for invalid credentials"
)

creds_parser.add_argument(
    "--no-keyring",
    action="store_true",
    help="prevent use of the system keyring service for credential lookup",
)
creds_parser.add_argument(
    "--no-netrc",
    action="store_true",
    help="prevent use of .netrc file for credential lookup",
)

creds_parser.add_argument(
    "--store-password",
    action="store_true",
    help="save password to keyring if login succeeds",
)
