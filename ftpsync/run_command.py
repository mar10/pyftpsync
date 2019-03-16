# -*- coding: utf-8 -*-
"""
(c) 2012-2019 Martin Wendt; see https://github.com/mar10/pyftpsync
Licensed under the MIT license: https://www.opensource.org/licenses/mit-license.php
"""

from __future__ import print_function

import os
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


def add_run_parser(subparsers):
    # --- Create the parser for the "scan" command -----------------------------

    parser = subparsers.add_parser(
        "run",
        # parents=[verbose_parser, common_parser, matcher_parser, creds_parser],
        help="run pyftpsync with configuration from `pyftpsync.yaml` in current or parent folder",
    )

    parser.add_argument(
        "task",
        # metavar="TASK",
        nargs="?",
        help="task to run (default: use `default_task` from pyftpsync.yaml)",
    )

    p_group = parser.add_mutually_exclusive_group()
    p_group.add_argument(
        "--here", action="store_true", help="use current folder as root"
    )
    p_group.add_argument(
        "--root",
        action="store_true",
        help="use folder of nearest `pyftpsync.yaml` as root",
    )

    parser.set_defaults(command=run_handler)

    return parser


def run_handler(args):
    """Implement `run` sub-command."""
    CONFIG_FILE_NAME = "pyftpsync.yaml"
    MAX_LEVELS = 10
    cur_level = 0
    cur_folder = os.getcwd()
    config_path = None
    while cur_level < MAX_LEVELS:
        path = os.path.join(cur_folder, CONFIG_FILE_NAME)
        print("Searching for {}...".format(path))
        if os.path.isfile(path):
            config_path = path
            break
        parent = os.path.dirname(cur_folder)
        if parent == cur_folder:
            break
        cur_folder = parent
        cur_level += 1

    if not config_path:
        raise RuntimeError(
            "Could not locate `pyftpsync.yaml` in {} or {} parent folder levels.".format(
                os.getcwd(), cur_level
            )
        )
    # opts = namespace_to_dict(args)
    # opts.update({"ftp_debug": args.verbose >= 6})
    # target = make_target(args.target, opts)
    # target.readonly = True
    # root_depth = target.root_dir.count("/")
    # start = time.time()
    # dir_count = 1
    # file_count = 0
    # processed_files = set()

    opts = namespace_to_dict(args)
    process_options(opts)

    print(
        "Scanning {:,} files in {:,} directories took {:02.2f} seconds.".format(
            file_count, dir_count, time.time() - start
        )
    )
