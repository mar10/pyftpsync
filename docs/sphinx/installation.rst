Installation
============

Requirements: `Python <https://www.python.org/downloads/>`_ 2.7+ or 3.4+ is required.

Releases are hosted on `PyPI <https://pypi.python.org/pypi/pyftpsync>`_ and can
be installed using `pip <http://www.pip-installer.org/>`_::

  $ pip install pyftpsync
  $ pyftpsync --version
  2.0.0

.. note::
   During the beta phase of 2.x, the module must be installed using the
   ``--pre`` switch::

       $ pip install --pre pyftpsync

.. note::
   MS Windows users may prefer the
   `MSI installer <https://github.com/mar10/pyftpsync/releases>`_ .

Now the ``pyftpsync`` command is available::

  $ pyftpsync --help

and the ``ftpsync`` package can be used in Python code::

  $ python
  >>> from ftpsync import __version__
  >>> __version__
  '2.0.0'
