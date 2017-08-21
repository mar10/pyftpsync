.. pyftpsync documentation master file, created by
   sphinx-quickstart on Sun May 24 20:50:55 2015.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

.. _main-index:

#########
Pyftpsync
#########

*Synchronize local directories with FTP servers.*

:Project:   https://github.com/mar10/pyftpsync/
:Version:   |version|, Date: |today|

|travis_badge| |nbsp| |pypi_badge| |nbsp| |lic_badge| |nbsp| |rtd_badge|

.. toctree::
   :hidden:

   Overview<self>
   installation
   user_guide.md
   reference_guide
   development
   changes


.. image:: ../../teaser.png
  :target: https://github.com/mar10/pyftpsync
  :name: Live demo

Features
========

  * This is a command line tool...
  * ... and a library for use in your Python projects.
  * Upload, download, and bi-directional synch mode.
  * FTPS (TLS) support on Python 2.7/3.2+.
  * Allows FTP-to-FTP and Filesystem-to-Filesystem synchronization as well.
  * Architecture is open to add other target types.

.. note:: Known Limitations

  * The FTP server must support the `MLSD command <http://tools.ietf.org/html/rfc3659>`_.
  * pyftpsync uses file size and modification dates to detect file changes.
    This is efficient, but not as robust as CRC checksums could be.
  * pyftpsync tries to detect conflicts (i.e. simultaneous modifications of
    local and remote targets) by storing last sync time and size in a separate
    meta data file inside the local folders. This is not bullet proof and may
    fail under some conditions.

  In short: pyftpsync is not (nor tries to be a replacement for) a distributed
  version control system. Make sure you have backups.


Quickstart
==========

Releases are hosted on `PyPI <https://pypi.python.org/pypi/pyftpsync>`_ and can
be installed using `pip <http://www.pip-installer.org/>`_::

  $ pip install pyftpsync --upgrade
  $ pyftpsync --help


..
  Indices and tables
  ==================

  * :ref:`genindex`
  * :ref:`modindex`
  * :ref:`search`


.. |travis_badge| image:: https://travis-ci.org/mar10/pyftpsync.svg?branch=master
   :alt: Build Status
   :target: https://travis-ci.org/mar10/pyftpsync

.. |pypi_badge| image:: https://img.shields.io/pypi/v/pyftpsync.svg
   :alt: PyPI Version
   :target: https://pypi.python.org/pypi/pyftpsync/

.. |lic_badge| image:: https://img.shields.io/pypi/l/pyftpsync.svg
   :alt: License
   :target: https://github.com/mar10/pyftpsync/blob/master/LICENSE.txt

.. |rtd_badge| image:: https://readthedocs.org/projects/pyftpsync/badge/?version=latest
   :target: http://pyftpsync.readthedocs.io/
   :alt: Documentation Status
