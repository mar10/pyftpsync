# -*- coding: utf-8 -*-
"""
(c) 2012-2019 Martin Wendt; see https://github.com/mar10/pyftpsync
Licensed under the MIT license: https://www.opensource.org/licenses/mit-license.php
"""

from __future__ import print_function

import os
import time
from datetime import timedelta

import yaml

from ftpsync.cli_common import (
    common_parser,
    creds_parser,
    matcher_parser,
    verbose_parser,
)
from ftpsync.metadata import DirMetadata
from ftpsync.resources import DirectoryEntry
from ftpsync.synchronizers import match_path, process_options, CONFIG_FILE_NAME
from ftpsync.targets import make_target
from ftpsync.util import namespace_to_dict, pretty_stamp, write, write_error


MANDATORY_TASK_ARGS = set((
    "command",
    "remote",
))

KNOWN_TASK_ARGS = set((
    "delete",
    "delete_unmatched",
    "dry_run",
    "exclude",
    "force",
    "ftp_active",
    "match",
    "no_color",
    "no_keyring",
    "no_netrc",
    "no_prompt",
    "progress",
    "prompt",
    "resolve",
    "verbose",
))


def add_run_parser(subparsers):
    # --- Create the parser for the "scan" command -----------------------------

    parser = subparsers.add_parser(
        "run",
        # parents=[verbose_parser, common_parser, matcher_parser, creds_parser],
        parents=[verbose_parser, common_parser, creds_parser],
        help="run pyftpsync with configuration from `.pyftpsync.yaml` in current or parent folder",
    )

    parser.add_argument(
        "task",
        # metavar="TASK",
        nargs="?",
        help="task to run (default: use `default_task` from `.pyftpsync.yaml`)",
    )

    p_group = parser.add_mutually_exclusive_group()
    p_group.add_argument(
        "--here", action="store_true", help="use current folder as root"
    )
    p_group.add_argument(
        "--root",
        action="store_true",
        help="use folder of nearest `.pyftpsync.yaml` as root",
    )

    # parser.set_defaults(command=run_handler)
    parser.set_defaults(command="run")

    return parser


def handle_run_command(parser, args):
    """Implement `run` sub-command."""
    MAX_LEVELS = 10

    # Look for `pyftpsync.yaml` in current folder and parents
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
        parser.error(
            "Could not locate `.pyftpsync.yaml` in {} or {} parent folders.".format(
                os.getcwd(), cur_level
            )
        )

    if cur_level > 0:
        if args.here:
            local_path = os.path.dirname(config_path)
            path_ofs = os.path.relpath(cur_folder, local_path)
        elif args.root:
            local_path = os.path.dirname(config_path)
            path_ofs = ""
        else:
            parser.error(
                "Config file was found above current directory. "
                "Pass --here or --root  to clarify.".format(
                )
            )

    # Parse `pyftpsync.yaml` and set `args` attributes
    try:
        with open(config_path, "rb") as f:
            config = yaml.safe_load(f)
    except Exception as e:
        parser.error("Error parsing {}: {}".format(config_path, e))
        # write_error("Error parsing {}: {}".format(config_path, e))
        # raise

    print(config)
    if "tasks" not in config:
        parser.error("Missing option `tasks` in {}".format(config_path))

    default_config = config.get("config", {})

    default_task = config.get("default_task", "default")
    task_name = args.task or default_task
    if task_name not in config["tasks"]:
        parser.error("Missing option `tasks.{}` in {}".format(task_name, config_path))
    task = config["tasks"][task_name]
    write("Using task '{}' from {}".format(task_name, config_path))

    default_config.update (task)
    task = default_config
    print(task)

    task_args = set(task.keys())

    missing_args = MANDATORY_TASK_ARGS.difference(task_args)
    if missing_args:
        parser.error("Missing mandatory options: tasks.{}.{}".format(task_name, ", ".join(missing_args)))

    allowed_args = KNOWN_TASK_ARGS.union(MANDATORY_TASK_ARGS)
    invalid_args = task_args.difference(allowed_args)
    if invalid_args:
        parser.error("Invalid options: tasks.{}.{}".format(task_name, ", ".join(invalid_args)))

    for name in allowed_args:
        val = task.get(name, None)  # default)
        if val is None:
            continue
        if name == "remote" and path_ofs:
            val = os.path.join(val, path_ofs)
        setattr(args, name, val)

    args.local = local_path

    # opts = namespace_to_dict(args)
    # opts.update({"ftp_debug": args.verbose >= 6})
    # target = make_target(args.target, opts)
    # target.readonly = True
    # root_depth = target.root_dir.count("/")
    # start = time.time()
    # dir_count = 1
    # file_count = 0
    # processed_files = set()
    print(args)
    # opts = namespace_to_dict(args)
    # process_options(opts)

    # print(
    #     "Scanning {:,} files in {:,} directories took {:02.2f} seconds.".format(
    #         file_count, dir_count, time.time() - start
    #     )
    # )
