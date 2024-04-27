# ![logo](https://raw.githubusercontent.com/mar10/pyftpsync/master/docs/logo_48x48.png) pyftpsync

[![Tests](https://github.com/mar10/pyftpsync/actions/workflows/python-app.yml/badge.svg)](https://github.com/mar10/pyftpsync/actions/workflows/python-app.yml)
[![Latest Version](https://img.shields.io/pypi/v/pyftpsync.svg)](https://pypi.python.org/pypi/pyftpsync/)
[![License](https://img.shields.io/pypi/l/pyftpsync.svg)](https://github.com/mar10/pyftpsync/blob/master/LICENSE.txt)
[![Documentation Status](https://readthedocs.org/projects/pyftpsync/badge/?version=latest)](https://pyftpsync.readthedocs.io/)
[![Coverage Status](https://coveralls.io/repos/github/mar10/pyftpsync/badge.svg?branch=master)](https://coveralls.io/github/mar10/pyftpsync?branch=master)
[![codecov](https://codecov.io/github/mar10/pyftpsync/graph/badge.svg?token=0JM9CN8RYW)](https://codecov.io/github/mar10/pyftpsync)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/ambv/black)
[![Released with: Yabs](https://img.shields.io/badge/released%20with-yabs-yellowgreen)](https://github.com/mar10/yabs)
[![StackOverflow: pyftpsync](https://img.shields.io/badge/StackOverflow-pyftpsync-blue.svg)](https://stackoverflow.com/questions/tagged/pyftpsync)

> Synchronize directories using FTP(S), SFTP, or file system access.

[ ![sample](teaser.png?raw=true) ](https://github.com/mar10/pyftpsync "Live demo")

## Summary

Synchronize directories using FTP(S), SFTP, or file system access.

-   This is a command line tool...
-   ... and a library for use in your Python projects.
-   Upload, download, and bi-directional synch mode.
-   Allows FTP-to-FTP and Filesystem-to-Filesystem synchronization as well.
-   Architecture is open to add other target types.

**Note:** Version 4.0 drops support for Python 2.

## Quickstart

[Python](https://www.python.org/download/Python) 3.7+ is required,
[pip](http://www.pip-installer.org/) recommended:

```bash
$ pip install pyftpsync --upgrade
$ pyftpsync --help
```

**Note:** <br>
MS Windows users that only need the command line interface may prefer the
[MSI Installer](https://github.com/mar10/pyftpsync/releases/latest) or install
using the Windows Package Manager:

```ps1
> winget install pyftpsync
```

See [Command Line Interface](https://pyftpsync.readthedocs.io/en/latest/ug_cli.html)
for details.

In addition to the direct invocation of `upload`, `download`, or `sync`
commands, version 3.x allows to define a `pyftpsync_yaml` file
in your project's root folder which then can be executed like so::

    $ pyftpsync run

See [Run from pyftpsync.yaml](https://pyftpsync.readthedocs.io/en/latest/ug_run.html)
for details.

## Documentation

[Read the Docs](https://pyftpsync.readthedocs.io/) for details.
