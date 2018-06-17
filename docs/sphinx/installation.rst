Installation
============

Requirements: `Python <https://www.python.org/downloads/>`_ 2.7+ or 3.4+ is required.

Releases are hosted on `PyPI <https://pypi.python.org/pypi/pyftpsync>`_ and can
be installed using `pip <http://www.pip-installer.org/>`_::

  $ pip install pyftpsync
  $ pyftpsync --version -v
  pyftpsync/2.0.1 Python/3.6.1 Darwin-17.6.0-x86_64-i386-64bit

.. note::
   MS Windows users that only need the command line interface may prefer the
   `MSI installer <https://github.com/mar10/pyftpsync/releases>`_.

Now the ``pyftpsync`` command is available::

  $ pyftpsync --help

and the ``ftpsync`` package can be used in Python code::

  $ python
  >>> from ftpsync import __version__
  >>> __version__
  '2.0.0'
