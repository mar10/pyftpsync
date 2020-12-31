# -*- coding: utf-8 -*-
"""
(c) 2012-2021 Martin Wendt; see https://github.com/mar10/pyftpsync
Licensed under the MIT license: https://www.opensource.org/licenses/mit-license.php
"""

import time

from ftpsync.cli_common import (
    common_parser,
    creds_parser,
    matcher_parser,
    verbose_parser,
)
from ftpsync.synchronizers import match_path, process_options
from ftpsync.targets import make_target
from ftpsync.util import namespace_to_dict


def add_tree_parser(subparsers):
    # --- Create the parser for the "scan" command -----------------------------

    parser = subparsers.add_parser(
        "tree",
        parents=[verbose_parser, common_parser, matcher_parser, creds_parser],
        help="list target folder structure",
    )
    parser.add_argument(
        "target",
        metavar="TARGET",
        default=".",
        help="path to target folder (default: %(default)s)",
    )
    parser.add_argument("--files", action="store_true", help="list files")
    parser.add_argument(
        "--sort", action="store_true", help="sort by name (folders before files)"
    )

    parser.set_defaults(command=tree_handler)

    return parser


def tree_handler(parser, args):
    """Implement `scan` sub-command."""
    opts = namespace_to_dict(args)
    opts.update({"ftp_debug": args.verbose >= 6})
    target = make_target(args.target, opts)
    target.readonly = True
    start = time.time()
    dir_count = 1
    file_count = 0

    opts = namespace_to_dict(args)
    process_options(opts)

    def _pred(entry):
        """Walker predicate that check match/exclude options."""
        if not match_path(entry, opts):
            return False

    try:
        target.open()

        print("[{}]".format(target.root_dir))
        for path, entry in target.walk_tree(
            sort=args.sort, files=args.files, pred=_pred
        ):
            name = entry.name
            if entry.is_dir():
                dir_count += 1
                line = "{}[{}]".format(path, name)
            else:
                file_count += 1
                line = "{}{:<20} {}".format(path, name, entry.as_string())
            print(line)
    finally:
        target.close()

    print(
        "Scanning {:,} files in {:,} directories took {:02.2f} seconds.".format(
            file_count, dir_count, time.time() - start
        )
    )
