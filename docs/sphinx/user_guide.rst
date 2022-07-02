==========
User Guide
==========

..
    .. toctree::
    :hidden:

    ug_run


.. warning::
  Major version updates (e.g. 3.0 => 4.0, ...) introduce *breaking changes* to 
  the previous versions.
  Make sure to adjust your scripts accordingly after update.


Command Line Interface
======================

Use the ``--help`` or ``-h`` argument to get help::

    $ pyftpsync --help
    usage: pyftpsync [-h] [-v | -q] [--debug {classify}] [--case {strict,local,remote}] [-V]
                    {upload,download,sync,run,scan,tree} ...

    Synchronize folders over FTP.

    positional arguments:
      {upload,download,sync,run,scan,tree}
                            sub-command help
        upload              copy new and modified files to remote folder
        download            copy new and modified files from remote folder to local target
        sync                synchronize new and modified files between remote folder and local target
        run                 run pyftpsync with configuration from `pyftpsync.yaml` in current or parent folder
        scan                repair, purge, or check targets
        tree                list target folder structure

    optional arguments:
      -h, --help            show this help message and exit
      -v, --verbose         increment verbosity by one (default: 3, range: 0..5)
      -q, --quiet           decrement verbosity by one
      --debug {classify}    enable additional specific logging (requires -v)
      --case {strict,local,remote}
                            how to handle file names that only differ in casing (default: stop if ambigous files are encountered)
      -V, --version         show program's version number and exit

    See also https://github.com/mar10/pyftpsync
    $


`run` command
-------------

In addition to the direct invocation of `upload`, `download`, or `sync`
commands, version 3.x allows to define a ``pyftpsync_yaml`` file
in your project's root folder which then can be executed like so::

    $ pyftpsync run

.. seealso::
   See :doc:`ug_run` for details.


`scan` command
--------------

TODO: The scan command can be used for different tasks.


`tree` command
--------------

Example: display a hierarchical directory listing::

    $ pyftpsync tree sftp://demo:password@test.rebex.net
    Connecting demo:*** to sftp://test.rebex.net
    Could not write lock file: [Errno 13] Access denied.
    [/]
    +- [aspnet_client]
    |   `- [system_web]
    |       `- [4_0_30319]
    `- [pub]
        +- [192.168.1.114]
        |   +- [2020-10-07]
        |   +- [2020-10-08]
        |   `- [2020-10-09]
        `- [example]
    Scanning 0 files in 10 directories took 2.93 seconds.

Options ``--files``, ``--sort``, etc. are also available.


Target URLs
-----------

The ``local`` and ``remote`` target arguments can be file paths or URLs
(currently the ``ftp:``, ``ftps``, and ``sftp:`` protocols are supported)::

    $ pyftpsync upload ~/temp ftp://example.com/target/folder

FTP URLs may contain credentials (*not* recommended)::

    $ pyftpsync upload ~/temp ftp://joe:secret@example.com/target/folder

Note that `pyftpsync` also supports prompting for passwords and storing
passwords in the system keyring and ``.netrc`` files.

.. note::

  The *content* of the local target folder is synchronized with the *content* of
  the remote target folder, so both folders must exist, with one exception: |br|
  If the remote target does *not* exist, but its parent folder does, the 
  ``--create-folder`` option may be passed.


Authentication
--------------

FTP targets often require authentication. There are multiple ways to handle
this:

  1. Pass credentials with the target URL: |br|
     ``ftp://user:password@example.com/target/folder``
  2. Pass only a user name with the target URL: |br|
     ``ftp://user@example.com/target/folder`` |br|
     The CLI will prompt for a password (the library would raise an error).
  3. Don't pass any credentials with the URL: |br|
     ``ftp://example.com/target/folder`` |br|
     `pyftpsync` will now

     1. Try to lookup credentials for host ('example.com') in the system
        keyring storage.
     2. Try to lookup credentials for host ('example.com') in the ``.netrc``
        file in the
        user's home directory.
     3. CLI will prompt for username and password.
     4. Assume anonymous access.

  4. If authentication fails, the CLI will prompt for a password again.

Credential discovery can be controlled by ``--no-keyring``, ``--no-netrc``,
and ``--no-prompt`` options.
``--prompt`` will force prompting, even if lookup is possible.
``--store-password`` will save credentials to the system keyring storage upon
successful login.

.. note::

    In order to use ``.netrc`` on Windows, the `%HOME%` environment variable 
    should be set. If not, try this: |br|
    ``> set HOME=%USERPROFILE%`` |br|
    (`see here <https://superuser.com/a/620146>`_).

.. note::

    The SFTP protocol checks if the public key of the remote server is
    known, by looking for an entry in the ``~/.ssh/known_hosts`` file. |br|
    This can be disabled by passing ``--no-verify-host-keys``, but a safer
    and recommended solution is to add the real key using a tool like
    ``ssh-keyscan HOST``.


Matching and Filtering
----------------------

The ``--match`` option filters processed files using on or more patterns
(using the `fnmatch syntax <https://docs.python.org/3/library/fnmatch.html#module-fnmatch>`_). |br|
**Note:**  These patterns are only applied to files, not directories.

The ``--exclude`` option is applied after `--match` and removes entries from
processing. Unlike `--match`, these patterns are also applied to directories.

Example::

    $ pyftpsync scan /my/folder --list --match=*.js,*.css --exclude=.git,build,node_modules


Upload Files Syntax
-------------------

Command specific help is available like so::

    $ pyftpsync upload -h
    usage: pyftpsync upload [-h] [-v | -q] [--debug {classify}] [--case {strict,local,remote}] [-n] [--progress] [--no-color]
                            [--ftp-active] [--migrate] [--no-verify-host-keys] [-m MATCH] [-x EXCLUDE] [--prompt | --no-prompt]
                            [--no-keyring] [--no-netrc] [--store-password] [--force] [--resolve {local,skip,ask}] [--delete]
                            [--delete-unmatched] [--create-folder]
                            LOCAL REMOTE

    positional arguments:
      LOCAL                 path to local folder (default: .)
      REMOTE                path to remote folder

    optional arguments:
      -h, --help            show this help message and exit
      -v, --verbose         increment verbosity by one (default: 3, range: 0..5)
      -q, --quiet           decrement verbosity by one
      --debug {classify}    enable additional specific logging (requires -v)
      --case {strict,local,remote}
                            how to handle file names that only differ in casing (default: stop if ambigous files are encountered)
      -n, --dry-run         just simulate and log results, but don't change anything
      --progress            show progress info, even if redirected or verbose < 3
      --no-color            prevent use of ansi terminal color codes
      --ftp-active          use Active FTP mode instead of passive
      --migrate             replace meta data files from different pyftpsync versions with current format. Existing data will be
                            discarded.
      --no-verify-host-keys
                            do not check SFTP connection against `~/.ssh/known_hosts`
      -m MATCH, --match MATCH
                            wildcard for file names (but not directories) using fnmatch syntax (default: match all, separate
                            multiple values with ',')
      -x EXCLUDE, --exclude EXCLUDE
                            wildcard of files and directories to exclude (applied after --match, default:
                            '.DS_Store,.git,.hg,.svn,#recycle')
      --prompt              always prompt for password
      --no-prompt           prevent prompting for invalid credentials
      --no-keyring          prevent use of the system keyring service for credential lookup
      --no-netrc            prevent use of .netrc file for credential lookup
      --store-password      save password to keyring if login succeeds
      --force               overwrite remote files, even if the target is newer (but no conflict was detected)
      --resolve {local,skip,ask}
                            conflict resolving strategy (default: 'ask')
      --delete              remove remote files if they don't exist locally
      --delete-unmatched    remove remote files if they don't exist locally or don't match the current filter (implies '--delete'
                            option)
      --create-folder       Create remote folder if missing
    $


Example: Upload Files
---------------------

Upload all new and modified files from user's temp folder to an FTP server.
No files are changed on the local directory::

  $ pyftpsync upload ~/temp ftp://example.com/target/folder

Add the ``--delete`` option to remove all files from the remote target that
don't exist locally::

  $ pyftpsync upload ~/temp ftp://example.com/target/folder --delete

Add the ``--dry-run`` option to switch to DRY-RUN mode, i.e. run in test mode
without modifying files::

  $ pyftpsync upload ~/temp ftp://example.com/target/folder --delete --dry-run

Add one or more  ``-v`` options to increase output verbosity::

  $ pyftpsync upload ~/temp ftp://example.com/target/folder --delete -vv

Mirror current directory to remote folder::

  $ pyftpsync upload . ftp://example.com/target/folder --force --delete --resolve=local


.. note::

    Replace ``ftp://`` with ``ftps://`` to enable TLS encryption. |br|
    Replace ``ftp://`` with ``sftp://`` to use the SFTP protocol.


Download Files Syntax
---------------------

This is generally the same as `upload` with swapped targets.


Synchronize Files Syntax
------------------------
::

    $ pyftpsync sync -h
    usage: pyftpsync sync [-h] [-v | -q] [--debug {classify}] [--case {strict,local,remote}] [-n] [--progress] [--no-color]
                          [--ftp-active] [--migrate] [--no-verify-host-keys] [-m MATCH] [-x EXCLUDE] [--prompt | --no-prompt]
                          [--no-keyring] [--no-netrc] [--store-password] [--resolve {old,new,local,remote,skip,ask}]
                          [--create-folder]
                          LOCAL REMOTE

    positional arguments:
      LOCAL                 path to local folder (default: .)
      REMOTE                path to remote folder

    optional arguments:
      -h, --help            show this help message and exit
      -v, --verbose         increment verbosity by one (default: 3, range: 0..5)
      -q, --quiet           decrement verbosity by one
      --debug {classify}    enable additional specific logging (requires -v)
      --case {strict,local,remote}
                            how to handle file names that only differ in casing (default: stop if ambigous files are encountered)
      -n, --dry-run         just simulate and log results, but don't change anything
      --progress            show progress info, even if redirected or verbose < 3
      --no-color            prevent use of ansi terminal color codes
      --ftp-active          use Active FTP mode instead of passive
      --migrate             replace meta data files from different pyftpsync versions with current format. Existing data will be
                            discarded.
      --no-verify-host-keys
                            do not check SFTP connection against `~/.ssh/known_hosts`
      -m MATCH, --match MATCH
                            wildcard for file names (but not directories) using fnmatch syntax (default: match all, separate
                            multiple values with ',')
      -x EXCLUDE, --exclude EXCLUDE
                            wildcard of files and directories to exclude (applied after --match, default:
                            '.DS_Store,.git,.hg,.svn,#recycle')
      --prompt              always prompt for password
      --no-prompt           prevent prompting for invalid credentials
      --no-keyring          prevent use of the system keyring service for credential lookup
      --no-netrc            prevent use of .netrc file for credential lookup
      --store-password      save password to keyring if login succeeds
      --resolve {old,new,local,remote,skip,ask}
                            conflict resolving strategy (default: 'ask')
      --create-folder       Create remote folder if missing
    $


Example: Synchronize Folders
----------------------------

Two-way synchronization of a local folder with an SFTP server::

  $ pyftpsync sync --store-password --resolve=ask ~/temp sftp://example.com/target/folder

Note that ``sftp:`` protocol was specified to enable SFTP.


Verbosity Level
---------------

The verbosity level can have a value from 0 to 6:

=========  ======  ===========  =============================================
Verbosity  Option  Log level    Remarks
=========  ======  ===========  =============================================
  0        -qqq    CRITICAL     quiet
  1        -qq     ERROR        show errors only
  2        -q      WARN         show conflicts and 1 line summary only
  3                INFO         show write operations
  4        -v      DEBUG        show equal files
  5        -vv     DEBUG        diff-info and benchmark summary
  6        -vvv    DEBUG        show FTP commands
=========  ======  ===========  =============================================


Exit Codes
----------

The CLI returns those exit codes::

    0: OK
    1: Error (network, internal, ...)
    2: CLI syntax error
    3: Aborted by user

..    10: Unresolved conflicts remaining (with option --conflicts-as-error)


Script Examples
===============

All options that are available for command line, can also be passed to
the synchronizers. For example ``--delete-unmatched`` becomes
``"delete_unmatched": True``.

Upload modified files from local folder to FTP server::

  from ftpsync.targets import FsTarget
  from ftpsync.ftp_target import FTPTarget
  from ftpsync.synchronizers import UploadSynchronizer

  local = FsTarget("~/temp")
  user ="joe"
  passwd = "secret"
  remote = FTPTarget("/temp", "example.com", username=user, password=passwd)
  opts = {"force": False, "delete_unmatched": True, "verbose": 3}
  s = UploadSynchronizer(local, remote, opts)
  s.run()

Synchronize a local folder with an FTP server using TLS::

  from ftpsync.targets import FsTarget
  from ftpsync.ftp_target import FTPTarget
  from ftpsync.synchronizers import BiDirSynchronizer

  local = FsTarget("~/temp")
  user ="joe"
  passwd = "secret"
  remote = FTPTarget("/temp", "example.com", username=user, password=passwd, tls=True)
  opts = {"resolve": "skip", "verbose": 1}
  s = BiDirSynchronizer(local, remote, opts)
  s.run()

.. note::
    The class ``FTPTarget`` was renamed with release 4.0 (named ``FtpTarget`` 
    before).


Logging
-------

By default, the library initializes and uses a
`python logger <https://docs.python.org/library/logging.html>`_ named 'pyftpsync'.
This logger can be customized like so::

    import logging

    logger = logging.getLogger("pyftpsync")
    logger.setLevel(logging.DEBUG)

and replaced like so::

    import logging
    import logging.handlers
    from ftpsync.util import set_pyftpsync_logger

    custom_logger = logging.getLogger("my.logger")
    log_path = "/my/path/pyftpsync.log"
    handler = logging.handlers.WatchedFileHandler(log_path)
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    custom_logger.addHandler(handler)

    set_pyftpsync_logger(custom_logger)


.. note::

    The CLI calls ``set_pyftpsync_logger(None)`` on startup, so it logs to stdout
    (and stderr).
