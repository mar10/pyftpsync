# pyftpsync [![Build Status](https://travis-ci.org/mar10/pyftpsync.png?branch=master)](https://travis-ci.org/mar10/pyftpsync) [![Latest Version](https://pypip.in/v/pyftpsync/badge.png)](https://pypi.python.org/pypi/pyftpsync/) [![Downloads](https://pypip.in/d/pyftpsync/badge.png)](https://pypi.python.org/pypi/pyftpsync/) [![License](https://pypip.in/license/pyftpsync/badge.png)](https://pypi.python.org/pypi/pyftpsync/)
Copyright (c) 2012-2015 Martin Wendt

Synchronize local directories with FTP servers.

[ ![sample](teaser.png?raw=true) ](https://github.com/mar10/pyftpsync "Live demo")

## Summary

Synchronize local directories with FTP server.

  * This is a command line tool...
  * ... and a library for use in your Python projects
  * Upload, download, and bi-directional synch mode
  * Allows FTP-to-FTP and Filesystem-to-Filesystem synchronization as well
  * Architecture is open to add other target types.

#### Known limitations 

  * The FTP server must support the [MLST command](http://tools.ietf.org/html/rfc3659).
  * pyftpsync uses file size and modification dates to detect file changes. 
    This is efficient, but not as robust as CRC checksums could be.
  * pyftpsync tries to detect conflicts (i.e. simultaneous modifications of 
    local and remote targets) by storing last sync time and size in a separate
    meta data file inside the local folders. This is not bullet proof and may
    fail under some conditions.

In short: pyftpsync is not (nor tries to be a replacement for) a distributed 
version control system. Make sure you have backups.


## Quickstart 

*Preconditions:* [Python](http://www.python.org/download/ Python) 2.6+ or 3 is required, 
[pip](http://www.pip-installer.org/) or
[EasyInstall](http://pypi.python.org/pypi/setuptools#using-setuptools-and-easyinstall)
recommended. 

Install like this:

```bash
$ pip install pyftpsync --upgrade
$ pyftpsync --help
```


## Documentation

[Read the Docs](http://pyftpsync.readthedocs.org/en/latest/) for details.
