.. pyftpsync documentation master file, created by
   sphinx-quickstart on Sun May 24 20:50:55 2015.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

.. _main-index:

#############################
pyftpsync Documentation
#############################

:Project: pyftpsync, https://github.com/mar10/pyftpsync/
:Copyright: Licensed under `The MIT License <https://raw.github.com/mar10/pyftpsync/master/LICENSE>`_
:Author: Martin Wendt
:Version: |version|
:Date: |today|


.. toctree::
   :maxdepth: 2

*Synchronize local directories with FTP server.*

  * This is a command line tool...
  * ... and a library for use in your Python projects.
  * Upload, download, and bi-directional synch mode.
  * Allows FTP-to-FTP and Filesystem-to-Filesystem synchronization as well.
  * Architecture is open to add other target types.

**Known limitations**
  * The FTP server must support the `MLST command <http://tools.ietf.org/html/rfc3659>`_.
  * pyftpsync uses file size and modification dates to detect file changes. 
    This is efficient, but not as robust as CRC checksums could be.
  * pyftpsync tries to detect conflicts (i.e. simultaneous modifications of 
    local and remote targets) by storing last sync time and size in a separate
    meta data file inside the local folders. This is not bullet proof and may
    fail under some conditions.

In short: pyftpsync is not (nor tries to be a replacement for) a distributed 
version control system. Make sure you have backups.


Quickstart
===========
**Install**

Releases are hosted on `PyPI <https://pypi.python.org/pypi/pyftpsync>`_. 
Install like::

	$ pip install -U pyftpsync

.. seealso::
	See the `project page <https://github.com/mar10/pyftpsync/blob/master/CHANGES.md>`_  
	for details.



Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

