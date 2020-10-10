# -*- coding: utf-8 -*-
"""
(c) 2012-2020 Martin Wendt; see https://github.com/mar10/pyftpsync
Licensed under the MIT license: https://www.opensource.org/licenses/mit-license.php
"""

import time
from datetime import timedelta

from ftpsync.cli_common import (
    common_parser,
    creds_parser,
    matcher_parser,
    verbose_parser,
)
from ftpsync.metadata import DirMetadata
from ftpsync.resources import DirectoryEntry
from ftpsync.synchronizers import match_path, process_options
from ftpsync.targets import make_target
from ftpsync.util import namespace_to_dict, pretty_stamp


def add_scan_parser(subparsers):
    # --- Create the parser for the "scan" command -----------------------------

    parser = subparsers.add_parser(
        "scan",
        parents=[verbose_parser, common_parser, matcher_parser, creds_parser],
        help="repair, purge, or check targets",
    )

    parser.add_argument(
        "target",
        metavar="TARGET",
        default=".",
        help="path to target folder (default: %(default)s)",
    )

    eg = parser.add_mutually_exclusive_group(required=False)
    eg.add_argument("--list", action="store_true", help="print target files")
    eg.add_argument(
        "--tree", action="store_true", help="print target directory structure"
    )
    parser.add_argument(
        "-r", "--recursive", action="store_true", help="visit sub folders"
    )
    parser.add_argument(
        "--remove-meta",
        action="store_true",
        help="delete all {} files".format(DirMetadata.META_FILE_NAME),
    )
    parser.add_argument(
        "--remove-locks",
        action="store_true",
        help="delete all {} files".format(DirMetadata.LOCK_FILE_NAME),
    )

    parser.set_defaults(command=scan_handler)

    return parser


def scan_handler(parser, args):
    """Implement `scan` sub-command."""
    opts = namespace_to_dict(args)
    opts.update({"ftp_debug": args.verbose >= 6})
    target = make_target(args.target, opts)
    target.readonly = True
    root_depth = target.root_dir.count("/")
    start = time.time()
    dir_count = 1
    file_count = 0
    processed_files = set()

    opts = namespace_to_dict(args)
    process_options(opts)

    def _pred(entry):
        """Walker predicate that check match/exclude options."""
        if not match_path(entry, opts):
            return False

    try:
        target.open()
        if args.tree:
            for path, entry in target.walk_tree():
                name = entry.name
                if entry.is_dir():
                    name = "[{}]".format(name)
                print("{}{:<20} {}".format(path, name, entry.as_string()))
            return

        for e in target.walk(recursive=args.recursive, pred=_pred):
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
                    dt_modified = pretty_stamp(e.mtime)
                    if delta:
                        prefix = "+" if delta > 0 else ""
                        print(
                            indent,
                            "{e.name:<40} {dt_modified} (system: {prefix}{delta})".format(
                                e=e,
                                prefix=prefix,
                                delta=timedelta(seconds=delta),
                                dt_modified=dt_modified,
                            ),
                        )
                    else:
                        print(
                            indent,
                            "{e.name:<40} {dt_modified}".format(
                                e=e, dt_modified=dt_modified
                            ),
                        )

            if (
                args.remove_meta
                and target.cur_dir_meta
                and target.cur_dir_meta.was_read
            ):
                fspec = target.cur_dir_meta.get_full_path()
                if fspec not in processed_files:
                    processed_files.add(fspec)
                    print("DELETE {}".format(fspec))

            if (
                args.remove_locks
                and not is_dir
                and e.name == DirMetadata.LOCK_FILE_NAME
            ):
                fspec = e.get_rel_path()
                print("DELETE {}".format(fspec))
    finally:
        target.close()

    print(
        "Scanning {:,} files in {:,} directories took {:02.2f} seconds.".format(
            file_count, dir_count, time.time() - start
        )
    )
