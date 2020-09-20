# -*- coding: utf-8 -*-
"""
(c) 2012-2020 Martin Wendt; see https://github.com/mar10/pyftpsync
Licensed under the MIT license: https://www.opensource.org/licenses/mit-license.php
"""

import os

import yaml

from ftpsync.cli_common import common_parser, creds_parser, verbose_parser
from ftpsync.synchronizers import CONFIG_FILE_NAME
from ftpsync.util import write


MANDATORY_TASK_ARGS = set(("command", "remote"))

KNOWN_TASK_ARGS = set(
    (
        "delete",
        "delete_unmatched",
        "dry_run",
        "exclude",
        "force",
        "ftp_active",
        "here",
        "match",
        "no_color",
        "no_keyring",
        "no_netrc",
        "no_prompt",
        "progress",
        "prompt",
        "resolve",
        "root",
        "verbose",
    )
)

# Flag-style arguments that default to False
OVERRIDABLE_BOOL_ARGS = set(
    (
        "dry_run",
        "force",
        "no_color",
        "no_keyring",
        "no_netrc",
        "no_prompt",
        "progress",
        # "resolve",
    )
)


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
    MAX_LEVELS = 15

    # --- Look for `pyftpsync.yaml` in current folder and parents ---

    cur_level = 0
    cur_folder = os.getcwd()
    config_path = None
    while cur_level < MAX_LEVELS:
        path = os.path.join(cur_folder, CONFIG_FILE_NAME)
        # print("Searching for {}...".format(path))
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

    # --- Parse `pyftpsync.yaml` and set `args` attributes ---

    try:
        with open(config_path, "rb") as f:
            config = yaml.safe_load(f)
    except Exception as e:
        parser.error("Error parsing {}: {}".format(config_path, e))
        # write_error("Error parsing {}: {}".format(config_path, e))
        # raise

    # print(config)
    if "tasks" not in config:
        parser.error("Missing option `tasks` in {}".format(config_path))

    common_config = config.get("common_config", {})

    default_task = config.get("default_task", "default")
    task_name = args.task or default_task
    if task_name not in config["tasks"]:
        parser.error("Missing option `tasks.{}` in {}".format(task_name, config_path))
    task = config["tasks"][task_name]

    write("Running task '{}' from {}".format(task_name, config_path))

    common_config.update(task)
    task = common_config
    # write("task", task)

    # --- Check task syntax ---

    task_args = set(task.keys())

    missing_args = MANDATORY_TASK_ARGS.difference(task_args)
    if missing_args:
        parser.error(
            "Missing mandatory options: tasks.{}.{}".format(
                task_name, ", ".join(missing_args)
            )
        )

    allowed_args = KNOWN_TASK_ARGS.union(MANDATORY_TASK_ARGS)
    invalid_args = task_args.difference(allowed_args)
    if invalid_args:
        parser.error(
            "Invalid options: tasks.{}.{}".format(task_name, ", ".join(invalid_args))
        )

    # write("args", args)

    for name in allowed_args:
        val = task.get(name, None)  # default)

        if val is None:
            continue  # option not specified in yaml

        # Override yaml entry by command line
        cmd_val = getattr(args, name, None)

        # write("check --{}: {} => {}".format(name, val, cmd_val))

        if cmd_val != val:
            override = False
            if name in OVERRIDABLE_BOOL_ARGS and cmd_val:
                override = True
            elif name in {"here", "root"} and (args.here or args.root):
                override = True
            elif name == "verbose" and cmd_val != 3:
                override = True

            if override:
                write(
                    "Yaml entry overriden by --{}: {} => {}".format(name, val, cmd_val)
                )
                continue

        setattr(args, name, val)

    # --- Figure out local target path ---

    cur_folder = os.getcwd()
    root_folder = os.path.dirname(config_path)
    path_ofs = os.path.relpath(os.getcwd(), root_folder)

    if cur_level == 0 or args.root:
        path_ofs = ""
        args.local = root_folder
    elif args.here:
        write("Using sub-branch {sub} of {root}".format(root=root_folder, sub=path_ofs))
        args.local = cur_folder
        args.remote = os.path.join(args.remote, path_ofs)
    else:
        parser.error(
            "`.pyftpsync.yaml` configuration was found in a parent directory. "
            "Please pass an additional argument to clarify:\n"
            "  --root: synchronize whole project ({root})\n"
            "  --here: synchronize sub branch ({root}/{sub})".format(
                root=root_folder, sub=path_ofs
            )
        )
