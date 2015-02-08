# pyftpsync [![Build Status](https://travis-ci.org/mar10/pyftpsync.png?branch=master)](https://travis-ci.org/mar10/pyftpsync) [![Latest Version](https://pypip.in/v/pyftpsync/badge.png)](https://pypi.python.org/pypi/pyftpsync/) [![Downloads](https://pypip.in/d/pyftpsync/badge.png)](https://pypi.python.org/pypi/pyftpsync/) [![License](https://pypip.in/license/pyftpsync/badge.png)](https://pypi.python.org/pypi/pyftpsync/)
Copyright (c) 2012-2015 Martin Wendt

Synchronize local directories with FTP server.

## Status
*This project has beta status: use at your own risk!*

Please submit bugs as you find them.


## Summary
Synchronize local directories with FTP server.

  * This is a command line tool...
  * ... and a library for use in your Python projects
  * Upload, download, and bi-directional synch mode
  * Allows FTP-to-FTP and Filesystem-to-Filesystem synchronization as well
  * Architecture is open to add other target types.

Note: 
The FTP server must support the [MLST command](http://tools.ietf.org/html/rfc3659).

## Usage 
*Preconditions:* [Python](http://www.python.org/download/ Python) 2.6+ or 3 is required, 
[pip](http://www.pip-installer.org/) or
[EasyInstall](http://pypi.python.org/pypi/setuptools#using-setuptools-and-easyinstall)
recommended. 

Install like this:

```bash
$ sudo pip install pyftpsync --upgrade
```
or
```bash
$ sudo easy_install -U pyftpsync
```

or on Windows:
```
> pip install pyftpsync --upgrade
```

If you plan to debug or contribute, install to run directly from the source:
```bash
$ python setup.py develop
```

After that the `ftpsync` package is available:
```bash
$ python
>>> from ftpsync import __version__
>>> __version__
'0.2.1'
```

*Script example*

```python
from ftpsync.targets import FsTarget, UploadSynchronizer
from ftpsync.ftp_target import FtpTarget

local = FsTarget("~/temp")
user ="joe"
passwd = "secret"
remote = FtpTarget("/temp", "example.com", user, passwd)
opts = {"force": False, "delete_unmatched": True, "verbose": 3, "execute": True, "dry_run" : False}
s = UploadSynchronizer(local, remote, opts)
s.run()
```


*Command line syntax*:

```
$ pyftpsync --help
macmartin:pyftpsync martin$ pyftpsync -h
usage: pyftpsync [-h] [--verbose] [--quiet] [--version] {upload,download} ...

Synchronize folders over FTP.

positional arguments:
  {upload,download}  sub-command help
    upload           copy new and modified files to remote folder
    download         copy new and modified files from remote folder to local
                     target

optional arguments:
  -h, --help         show this help message and exit
  --verbose, -v      increment verbosity by one (default: 3, range: 0..5)
  --quiet, -q        decrement verbosity by one
  --version          show program's version number and exit

See also https://github.com/mar10/pyftpsync
```


*Upload files syntax*:

```
$ pyftpsync upload --help
usage: pyftpsync upload [-h] [--force] [--delete] [--delete-unmatched] [-x]
                        [-f INCLUDE_FILES] [-o OMIT]
                        LOCAL REMOTE

positional arguments:
  LOCAL                 path to local folder (default: .)
  REMOTE                path to remote folder

optional arguments:
  -h, --help            show this help message and exit
  --force               overwrite different remote files, even if the target
                        is newer
  --delete              remove remote files if they don't exist locally
  --delete-unmatched    remove remote files if they don't exist locally or
                        don't match the current filter (implies '--delete'
                        option)
  -x, --execute         turn off the dry-run mode (which is ON by default),
                        that would just print status messages but does not
                        change anything
  -f INCLUDE_FILES, --include-files INCLUDE_FILES
                        wildcard for file names (default: all, separate
                        multiple values with ',')
  -o OMIT, --omit OMIT  wildcard of files and directories to exclude (applied
                        after --include)
```

*Example: Upload files*

Upload all new and modified files from user's temp folder to an FTP server.<br>
No files are changed on the local directory.

```bash
$ pyftpsync upload ~/temp ftp://example.com/target/folder
```

Add the ´--delete´ option to remove all files from the remote target that don't exist locally:
```bash
$ pyftpsync upload ~/temp ftp://example.com/target/folder --delete
```

Add the ´-x´ option to switch from DRY-RUN mode to real execution:
```bash
$ pyftpsync upload ~/temp ftp://example.com/target/folder --delete -x
```


## FAQ

  * Passwords may be stored and read from a custom file:
    https://github.com/mar10/pyftpsync/blob/master/ftpsync/sample_pyftpsync.pw
