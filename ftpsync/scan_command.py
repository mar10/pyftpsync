# -*- coding: iso-8859-1 -*-
"""
(c) 2012-2017 Martin Wendt; see https://github.com/mar10/pyftpsync
Licensed under the MIT license: http://www.opensource.org/licenses/mit-license.php
"""

from __future__ import print_function

import time
from datetime import timedelta, datetime

from ftpsync.metadata import DirMetadata
from ftpsync.resources import DirectoryEntry
from ftpsync.targets import make_target


def add_scan_parser(subparsers):
    # --- Create the parser for the "scan" command -----------------------------

    scan_parser = subparsers.add_parser("scan",
            help="repair, purge, or check targets")
    # __add_common_sub_args(scan_parser)

    scan_parser.add_argument("target",
            metavar="TARGET",
            default=".",
            help="path to target folder (default: %(default)s)")
    scan_parser.add_argument("--dry-run",
            action="store_true",
            help="just simulate and log results, but don't change anything")
    scan_parser.add_argument("--store-password",
            action="store_true",
            help="save password to keyring if login succeeds")
    scan_parser.add_argument("--no-prompt",
            action="store_true",
            help="prevent prompting for missing credentials")
    scan_parser.add_argument("--no-color",
            action="store_true",
            help="prevent use of ansi terminal color codes")
    scan_parser.add_argument("--list",
            action="store_true",
            help="print target files")
    scan_parser.add_argument("-r", "--recursive",
            action="store_true",
            help="visit sub folders")
    scan_parser.add_argument("--remove-meta",
            action="store_true",
            help="delete all {} files".format(DirMetadata.META_FILE_NAME))
    # scan_parser.add_argument("--remove-debug",
    #         action="store_true",
    #         help="delete all {} files".format(DirMetadata.DEBUG_META_FILE_NAME))
    scan_parser.add_argument("--remove-locks",
            action="store_true",
            help="delete all {} files".format(DirMetadata.LOCK_FILE_NAME))

    scan_parser.set_defaults(command=scan_handler)

    return scan_parser


def scan_handler(args):
    """Implement `cleanup` sub-command."""
    target = make_target(args.target, {"ftp_debug": args.verbose >= 5})
    target.readonly = True
    root_depth = target.root_dir.count("/")
    start = time.time()
    dir_count = 1
    file_count = 0
    processed_files = set()

    try:
        target.open()
        for e in target.walk(recursive=args.recursive):
            is_dir = isinstance(e, DirectoryEntry)
            indent = "    " * (target.cur_dir.count("/") - root_depth)

            if is_dir:
                dir_count += 1
            else:
                file_count += 1

            if args.list:
                if is_dir:
                    print(indent, "[{e.name}]".format(e=e))
                else:
                    delta = e.mtime_org - e.mtime
                    dt_modified = datetime.fromtimestamp(e.mtime)
                    if delta:
                        prefix = "+" if delta > 0 else ""
                        print(indent, "{e.name:<40} {dt_modified} (system: {prefix}{delta})"
                            .format(e=e, prefix=prefix, delta=timedelta(seconds=delta),
                                    dt_modified=dt_modified))
                    else:
                        print(indent, "{e.name:<40} {dt_modified}"
                            .format(e=e, dt_modified=dt_modified))

            if args.remove_meta and target.cur_dir_meta and target.cur_dir_meta.was_read:
                fspec = target.cur_dir_meta.get_full_path()
                if fspec not in processed_files:
                    processed_files.add(fspec)
                    print("DELETE {}".format(fspec))

            if args.remove_locks and not is_dir and e.name == DirMetadata.LOCK_FILE_NAME:
                fspec = e.get_rel_path()
                print("DELETE {}".format(fspec))
    finally:
        target.close()

    print("Scanning {:,} files in {:,} dirs took {:02.2f} seconds."
            .format(file_count, dir_count, time.time()-start))
