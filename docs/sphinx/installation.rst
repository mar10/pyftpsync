Installation
============

Requirements: `Python <https://www.python.org/downloads/>`_ 3.8 or later is 
required.

Releases are hosted on `PyPI <https://pypi.python.org/pypi/pyftpsync>`_ and can
be installed using `pip <http://www.pip-installer.org/>`_::

  $ pip install pyftpsync
  $ pyftpsync --version -v
  pyftpsync/4.0.0-a4 Python/3.9.12 macOS-12.4-arm64-arm-64bit, Python: /path/virtualenvs/pyftpsync-Bl7Oc59w/bin/python

.. note::
   MS Windows users that only need the command line interface may prefer the
   `MSI installer <https://github.com/mar10/pyftpsync/releases>`_ or install
   using the Windows Package Manager::

     > winget install pyftpsync
  
Now the ``pyftpsync`` command is available::

  $ pyftpsync --help

and the ``ftpsync`` package can be used in Python code::

  $ python
  >>> from ftpsync import __version__
  >>> __version__
  '2.0.0'
