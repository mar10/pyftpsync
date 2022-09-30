# -*- coding: utf-8 -*-
"""
Tests for pyftpsync
"""
import os
import sys

from build.lib.ftpsync.util import get_debug_option

sys.path.append(os.path.dirname(__file__) + "/..")


# ===============================================================================
# Main
# ===============================================================================

PYFTPSYNC_REMOTE_URL = get_debug_option(
    "PYFTPSYNC_DEBUG_FTP_URL", "debug", "ftp_url", "ftp://example.com/test_pyftpsync"
)


def do_sync():
    from ftpsync.synchronizers import BiDirSynchronizer
    from ftpsync.targets import make_target

    local_target = make_target("~/test_pyftpsync_dl")
    # local_target = make_target("c:/tmp/test_pyftpsync")
    remote_target = make_target(PYFTPSYNC_REMOTE_URL, {"ftp_debug": False})
    opts = {"verbose": 6, "dry_run": False, "resolve": "local"}
    s = BiDirSynchronizer(local_target, remote_target, opts)
    s.run()


def do_scan():
    from ftpsync.scan_command import scan_handler

    class args:  # noqa: N801
        """"""

    args.target = PYFTPSYNC_REMOTE_URL
    args.list = True
    args.verbose = 4
    args.recursive = False
    args.remove_meta = False
    args.remove_locks = False
    scan_handler(None, args)


if __name__ == "__main__":
    do_sync()
    # do_scan()
