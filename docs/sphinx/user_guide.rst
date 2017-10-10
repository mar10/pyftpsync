==========
User Guide
==========

.. note::
    This page describes release 2.x.

    Run ``pyftpsync --help`` to get help on your current version.


Command Line Syntax
===================

Use the ``--help`` or ``-h`` argument to get help::

    $ pyftpsync -h
    usage: pyftpsync [-h] [--verbose | --quiet] [-V] [--progress]
                     {upload,download,sync,scan} ...

    Synchronize folders over FTP.

    positional arguments:
      {upload,download,sync,scan}
                            sub-command help
        upload              copy new and modified files to remote folder
        download            copy new and modified files from remote folder to
                            local target
        sync                synchronize new and modified files between remote
                            folder and local target
        scan                repair, purge, or check targets

    optional arguments:
      -h, --help            show this help message and exit
      --verbose, -v         increment verbosity by one (default: 3, range: 0..5)
      --quiet, -q           decrement verbosity by one
      -V, --version         show program's version number and exit
      --progress, -p        show progress info, even if redirected or verbose < 3

    See also https://github.com/mar10/pyftpsync
    $


Upload Files Syntax
-------------------

Command specific help is available like so::

    $ pyftpsync upload -h
    usage: pyftpsync upload [-h] [--dry-run] [-m MATCH] [-x EXCLUDE]
                            [--store-password] [--no-prompt] [--no-color]
                            [--force] [--resolve {local,skip,ask}] [--delete]
                            [--delete-unmatched]
                            LOCAL REMOTE

    positional arguments:
      LOCAL                 path to local folder (default: .)
      REMOTE                path to remote folder

    optional arguments:
      -h, --help            show this help message and exit
      --dry-run             just simulate and log results, but don't change
                            anything
      -m MATCH, --match MATCH
                            wildcard for file names (default: all, separate
                            multiple values with ',')
      -x EXCLUDE, --exclude EXCLUDE
                            wildcard of files and directories to exclude (applied
                            after --match, default: .DS_Store,.git,.hg,.svn
      --store-password      save password to keyring if login succeeds
      --no-prompt           prevent prompting for missing credentials
      --no-color            prevent use of ansi terminal color codes
      --force               overwrite remote files, even if the target is newer
                            (but no conflict was detected)
      --resolve {local,skip,ask}
                            conflict resolving strategy (default: 'ask')
      --delete              remove remote files if they don't exist locally
      --delete-unmatched    remove remote files if they don't exist locally or
                            don't match the current filter (implies '--delete'
                            option)
    $


Example: Upload Files
---------------------

Upload all new and modified files from user's temp folder to an FTP server.
No files are changed on the local directory::

  $ pyftpsync upload ~/temp ftp://example.com/target/folder

Add the ``--delete`` option to remove all files from the remote target that
don't exist locally::

  $ pyftpsync upload ~/temp ftp://example.com/target/folder --delete

Add the ``--dry-run`` option to switch to DRY-RUN mode, i.e. run in test mode without
modifying files::

  $ pyftpsync upload ~/temp ftp://example.com/target/folder --delete --dry-run

Add one or more  ``-v`` options to increase output verbosity::

  $ pyftpsync -vv upload ~/temp ftp://example.com/target/folder --delete

Mirror current directory to remote folder::

  $ pyftpsync upload . ftp://example.com/target/folder --force --delete --resolve=local


.. note:: Replace ``ftp://`` with ``ftps://`` to enable TLS encryption.


Synchronize Files Syntax
------------------------
::

    $ pyftpsync sync -h
    usage: pyftpsync sync [-h] [--dry-run] [-m MATCH] [-x EXCLUDE]
                          [--store-password] [--no-prompt] [--no-color]
                          [--resolve {old,new,local,remote,skip,ask}]
                          LOCAL REMOTE

    positional arguments:
      LOCAL                 path to local folder (default: .)
      REMOTE                path to remote folder

    optional arguments:
      -h, --help            show this help message and exit
      --dry-run             just simulate and log results, but don't change
                            anything
      -m MATCH, --match MATCH
                            wildcard for file names (default: all, separate
                            multiple values with ',')
      -x EXCLUDE, --exclude EXCLUDE
                            wildcard of files and directories to exclude (applied
                            after --match, default: .DS_Store,.git,.hg,.svn
      --store-password      save password to keyring if login succeeds
      --no-prompt           prevent prompting for missing credentials
      --no-color            prevent use of ansi terminal color codes
      --resolve {old,new,local,remote,skip,ask}
                            conflict resolving strategy (default: 'ask')
    $

Example: Synchronize Folders
----------------------------

Two-way synchronization of a local folder with an FTP server::

  $ pyftpsync sync --store-password --resolve=ask --execute ~/temp ftps://example.com/target/folder

Note that ``ftps:`` protocol was specified to enable TLS.


Script Examples
===============

All options described that are available for command line mode, can also be passed to
the synchronizers. For example ``--delete-unmatched`` becomes ``"delete_unmatched": True``.

Upload changes from local folder to FTP server::

  from ftpsync.targets import FsTarget
  from ftpsync.ftp_target import FtpTarget
  from ftpsync.synchronizers import UploadSynchronizer

  local = FsTarget("~/temp")
  user ="joe"
  passwd = "secret"
  remote = FtpTarget("/temp", "example.com", username=user, password=passwd)
  opts = {"force": False, "delete_unmatched": True, "verbose": 3}
  s = UploadSynchronizer(local, remote, opts)
  s.run()

Synchronize local folder with FTP server using TLS::

  from ftpsync.targets import FsTarget
  from ftpsync.ftp_target import FtpTarget
  from ftpsync.synchronizers import BiDirSynchronizer

  local = FsTarget("~/temp")
  user ="joe"
  passwd = "secret"
  remote = FtpTarget("/temp", "example.com", username=user, password=passwd, tls=True)
  opts = {"resolve": "skip", "verbose": 1}
  s = BiDirSynchronizer(local, remote, opts)
  s.run()
