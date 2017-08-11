Installation
============

*Requirements:* `Python <https://www.python.org/downloads/>`_ 2.7+ or 3 is required.

Releases are hosted on `PyPI <https://pypi.python.org/pypi/pyftpsync>`_ and can
be installed using `pip <http://www.pip-installer.org/>`_::

  $ pip install pyftpsync --upgrade
  $ pyftpsync --help

.. todo::
   There will be a MSI installer for Windows available in v2.0.

Now the ``pyftpsync`` command is available::

  $ pyftpsync --version
  1.0.3

and the ``ftpsync`` package can be used in Python code::

  $ python
  >>> from ftpsync import __version__
  >>> __version__
  '1.0.3'
