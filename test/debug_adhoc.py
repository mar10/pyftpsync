# -*- coding: utf-8 -*-
"""
Tests for pyftpsync
"""
from __future__ import print_function

import os
import sys

sys.path.append(os.path.dirname(__file__) + "/..")


# ===============================================================================
# Main
# ===============================================================================


def do_sync():
    from ftpsync.synchronizers import BiDirSynchronizer
    from ftpsync.targets import make_target

    local_target = make_target("c:/tmp/test_pyftpsync")
    remote_target = make_target("ftp://wwwendt.de/test_pyftpsync", {"ftp_debug": False})
    opts = {"verbose": 4, "dry_run": False, "no_progress": True}
    s = BiDirSynchronizer(local_target, remote_target, opts)
    s.run()


def do_scan():
    from ftpsync.scan_command import scan_handler

    class args(object):
        """"""

    args.target = "ftp://wwwendt.de/test_pyftpsync"
    args.list = True
    args.verbose = 4
    args.recursive = False
    args.remove_meta = False
    args.remove_locks = False
    scan_handler(args)


if __name__ == "__main__":
    do_sync()
    # do_scan()
