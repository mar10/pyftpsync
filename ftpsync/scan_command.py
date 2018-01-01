# -*- coding: utf-8 -*-
"""
(c) 2012-2018 Martin Wendt; see https://github.com/mar10/pyftpsync
Licensed under the MIT license: http://www.opensource.org/licenses/mit-license.php
"""

from __future__ import print_function

from datetime import timedelta
import time

from ftpsync.cli_common import add_cli_sub_args, add_matcher_sub_args, add_credential_sub_args
from ftpsync.metadata import DirMetadata
from ftpsync.resources import DirectoryEntry
from ftpsync.targets import make_target
from ftpsync.synchronizers import process_options, match_path
from ftpsync.util import pretty_stamp, namespace_to_dict


def add_scan_parser(subparsers):
    # --- Create the parser for the "scan" command -----------------------------

    parser = subparsers.add_parser(
            "scan",
            help="repair, purge, or check targets")

    parser.add_argument("target",
                        metavar="TARGET",
                        default=".",
                        help="path to target folder (default: %(default)s)")

    parser.add_argument("--list",
                        action="store_true",
                        help="print target files")
    parser.add_argument("-r", "--recursive",
                        action="store_true",
                        help="visit sub folders")
    parser.add_argument("--remove-meta",
                        action="store_true",
                        help="delete all {} files".format(DirMetadata.META_FILE_NAME))
    parser.add_argument("--remove-locks",
                        action="store_true",
                        help="delete all {} files".format(DirMetadata.LOCK_FILE_NAME))

    add_cli_sub_args(parser)
    add_matcher_sub_args(parser)
    add_credential_sub_args(parser)

    parser.set_defaults(command=scan_handler)

    return parser


def scan_handler(args):
    """Implement `cleanup` sub-command."""
    opts = namespace_to_dict(args)
    opts.update({
        "ftp_debug": args.verbose >= 6,
        })
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

    print("Scanning {:,} files in {:,} directories took {:02.2f} seconds."
          .format(file_count, dir_count, time.time()-start))
