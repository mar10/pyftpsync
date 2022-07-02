# pyftpsync
[![Build Status](https://travis-ci.com/mar10/pyftpsync.svg?branch=master)](https://app.travis-ci.com/github/mar10/pyftpsync)
[![Latest Version](https://img.shields.io/pypi/v/pyftpsync.svg)](https://pypi.python.org/pypi/pyftpsync/)
[![License](https://img.shields.io/pypi/l/pyftpsync.svg)](https://github.com/mar10/pyftpsync/blob/master/LICENSE.txt)
[![Documentation Status](https://readthedocs.org/projects/pyftpsync/badge/?version=latest)](https://pyftpsync.readthedocs.io/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/ambv/black)
[![Released with: Yabs](https://img.shields.io/badge/released%20with-yabs-yellowgreen)](https://github.com/mar10/yabs)
[![StackOverflow: pyftpsync](https://img.shields.io/badge/StackOverflow-pyftpsync-blue.svg)](https://stackoverflow.com/questions/tagged/pyftpsync)

> Synchronize directories using FTP(S), SFTP, or file system access.

[ ![sample](teaser.png?raw=true) ](https://github.com/mar10/pyftpsync "Live demo")


## Summary

Synchronize directories using FTP(S), SFTP, or file system access.

  * This is a command line tool...
  * ... and a library for use in your Python projects.
  * Upload, download, and bi-directional synch mode.
  * Allows FTP-to-FTP and Filesystem-to-Filesystem synchronization as well.
  * Architecture is open to add other target types.

**Note:** Version 4.0 drops support for Python 2.


## Quickstart

[Python](https://www.python.org/download/Python) 3.7+ is required,
[pip](http://www.pip-installer.org/) recommended:

```bash
$ pip install pyftpsync --upgrade
$ pyftpsync --help
```

In addition to the direct invocation of `upload`, `download`, or `sync`
commands, version 3.x allows to define a ``pyftpsync_yaml`` file
in your project's root folder which then can be executed like so::

    $ pyftpsync run

See [Run from pyftpsync.yaml](https://pyftpsync.readthedocs.io/en/latest/ug_run.html) 
for details.


**Note:** Windows users may prefer the 
[MSI Installer](https://github.com/mar10/pyftpsync/releases/latest).


## Documentation

[Read the Docs](https://pyftpsync.readthedocs.io/) for details.
