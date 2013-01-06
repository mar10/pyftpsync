# -*- coding: iso-8859-1 -*-
"""
SCIO-Portal collector tool.
(c) Martin Wendt 2012

Usage examples:
  > pyftpsync.py --help
  > pyftpsync.py upload ftp://example.com/myfolder
"""
from ftpsync.targets import make_target, UploadSynchronizer, BaseSynchronizer
from pprint import pprint
#def disable_stdout_buffering():
#    """http://stackoverflow.com/questions/107705/python-output-buffering"""
#    # Appending to gc.garbage is a way to stop an object from being
#    # destroyed.  If the old sys.stdout is ever collected, it will
#    # close() stdout, which is not good.
#    gc.garbage.append(sys.stdout)
#    sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 0)
#disable_stdout_buffering()


try:
    import argparse
except ImportError:
    print("argparse missing (requires 2.7+, 3.2+ or easy_install)")
    raise


from ftpsync._version import __version__


def namespace_to_dict(o):
    """Convert an argparse namespace object to a dictionary."""
    d = {}
    for k, v in o.__dict__.iteritems():
        if not callable(v):
            d[k] = v
    return d


#===============================================================================
# backup_command
#===============================================================================

def upload_command(parser, args):
    ftp_debug = 0
    if args.verbose >= 5:
        ftp_debug = 1 
    local = make_target(args.local, debug=ftp_debug)
    remote = make_target(args.remote, debug=ftp_debug)
    opts = namespace_to_dict(args)
    s = UploadSynchronizer(local, remote, opts)
    s.run()
    stats = s.get_stats()
    if args.verbose >= 4:
        pprint(stats)
    elif args.verbose >= 1:
        print("Wrote %s/%s files in %s dirs. Elap: %s" 
              % (stats["files_written"], stats["local_files"], stats["local_dirs"], stats["elap"]))
    

#===============================================================================
# info_command
#===============================================================================

def info_command(parser, args):
    """Dump plugin info."""


#===============================================================================
# run
#===============================================================================
def run():
    parser = argparse.ArgumentParser(
        description="Synchronize folders over FTP.",
        epilog="See also http://pyftpsync.googlecode.com/"
        )
    parser.add_argument("--verbose", "-v", action="count", default=3,
                        help="increment verbosity by one (default: %(default)s, range: 0..5")
    parser.add_argument("--quiet", "-q", action="count", default=0,
                        help="decrement verbosity by one")
    parser.add_argument("--version", action="version", version="%s" % (__version__))
    
    subparsers = parser.add_subparsers(help="sub-command help")
    
    # create the parser for the "upload" command
    upload_parser = subparsers.add_parser("upload", 
                                           help="copy new and modified files to remote folder")
    upload_parser.add_argument("remote", 
                             metavar="REMOTE",
#                             required=True,
#                             default=".",
                             help="path to remote folder")
    upload_parser.add_argument("--local", 
                             metavar="LOCAL",
#                             required=True,
                             default=".",
                             help="path to local folder (default: %(default)s)")      
    upload_parser.add_argument("--force", 
                             action="store_true",
                             help="overwrite different remote files, even if the target is newer")
    upload_parser.add_argument("--delete", 
                             action="store_true",
                             help="remove remote files if they don't exist locally")
#    upload_parser.add_argument("--dry-run", 
#                             action="store_true",
#                             help="just simulate and log results; don't change anything")
    upload_parser.add_argument("-x", "--execute", 
                               action="store_false", dest="dry_run", default=True,
                               help="turn off the dry-run mode (which is ON by default), "
                               "that would just print status messages but does "
                               "not change anything")
    upload_parser.set_defaults(func=upload_command)
    

    # create the parser for the "download" command
    download_parser = subparsers.add_parser("download", 
                                           help="copy new and modified files to local folder")
    download_parser.add_argument("remote", 
                             metavar="REMOTE",
#                             required=True,
#                             default=".",
                             help="path to remote folder")
    download_parser.add_argument("--local", 
                             metavar="LOCAL",
#                             required=True,
                             default=".",
                             help="path to local folder (default: %(default)s)")      
    download_parser.add_argument("--force", 
                             action="store_true",
                             help="overwrite different local files, even if the source is older")
    download_parser.add_argument("--delete", 
                             action="store_true",
                             help="remove local files if they don't exist remotely")
    download_parser.add_argument("--dry-run", 
                             action="store_true",
                             help="just simulate and log results; don't change anything")
    download_parser.set_defaults(func=upload_command)
    
#    # create the parser for the "dump" command
#    dump_parser = subparsers.add_parser("dump", help="print or export snapshot data")
#    dump_parser.add_argument("--names", 
#                             default="*",
#                             help="table name(s) (separate multiple entries with comma, default: %(default)s)")
##    dump_parser.add_argument("--filter", 
##                             default="*",
##                             help="only print lines that contain this string (case insensitive)")
##    dump_parser.add_argument("--format", 
##                             help="CSV, ...")
#    dump_parser.set_defaults(func=dump_command)
#    
#    # create the parser for the "backup" command
#    backup_parser = subparsers.add_parser("backup", help="backup and optionally purge snapshot data")
#    backup_parser.add_argument("--names", 
#                               default="*",
#                               help="table name(s) (separate multiple entries with comma, default: %(default)s)")
#    backup_parser.add_argument("--format", 
#                               default="csv",
#                               help="table name(s) (separate multiple entries with comma, default: %(default)s)")
#    backup_parser.add_argument("--date-from", 
#                               help="oldest entry (yyy-mm-dd)")
#    backup_parser.add_argument("--date-to", 
#                               help="newest entry (yyy-mm-dd)")
#    backup_parser.set_defaults(func=backup_command)
#    
#    # create the parser for the "migrate" command
##    migrate_parser = subparsers.add_parser("migrate", help="migrate previous versions to current")
##    migrate_parser.add_argument("--feature", 
##                             help="what to migrate")      
##    migrate_parser.add_argument("--execute", 
##                             action="store_true",
##                             help="pass this argument to actually write changes (otherwise DRY_RUN is enabled)")      
##    migrate_parser.set_defaults(func=migrate_command)
    
    args = parser.parse_args()
    args.verbose -= args.quiet
    del args.quiet

    args.func(parser, args)
    

if __name__ == "__main__":
    run()
