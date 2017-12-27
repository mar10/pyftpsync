===========
Development
===========

Install for Development
=======================

First off, thanks for taking the time to contribute!

This small guideline may help takinf the first steps.

Happy hacking :)


Fork the Repository
-------------------

Clone pyftpsync to a local folder and checkout the branch you want to work on::

    $ git clone git@github.com:mar10/pyftpsync.git
    $ cd pyftpsync
    $ git checkout my_branch


Work in a Virtual Environment
-----------------------------

Install Python
^^^^^^^^^^^^^^
We need `Python 2.7 <https://www.python.org/downloads/>`_,
`Python 3.4+ <https://www.python.org/downloads/>`_,
and `pip <https://pip.pypa.io/en/stable/installing/#do-i-need-to-install-pip>`_ on our system.

If you want to run tests on *all* supported platforms, install Python 2.7, 3.4,
3.5, and 3.6.

Create and Activate the Virtual Environment
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Linux / macOS
"""""""""""""
On Linux/OS X, we recommend to use `pipenv <https://github.com/kennethreitz/pipenv>`_
to make this easy::

    $ cd /path/to/pyftpsync
    $ pipenv shell
    bash-3.2$

Windows
"""""""
Alternatively (especially on Windows), use `virtualenv <https://virtualenv.pypa.io/en/latest/>`_
to create and activate the virtual environment.
For example using Python's builtin ``venv`` (instead of ``virtualenvwrapper``)
in a Windows PowerShell::

    > cd /path/pyftpsync
    > py -3.6 -m venv c:\env\pyftpsync_py36
    > c:\env\pyftpsync_py36\Scripts\Activate.ps1
    (pyftpsync_py36) $

Install Requirements
^^^^^^^^^^^^^^^^^^^^
Now that the new environment exists and is activated, we can setup the
requirements::

    $ pip install -r requirements-dev.txt

and install pyftpsync to run from source code::

    $ pip install -e .

..    $ python setup.py develop

The code should now run::

    $ pyftpsync --version
    $ 2.0.0

The test suite should run as well::

    $ python setup.py test
    $ pytest -v -rs

Build Sphinx documentation::

    $ python setup.py sphinx


Run Tests
=========

The unit tests create fixtures in a special folder. By default, a temporary folder
is created on every test run, but it is recommended to define a location using the
``PYFTPSYNC_TEST_FOLDER`` environment variable, for example::

    export PYFTPSYNC_TEST_FOLDER=/Users/USER/pyftpsync_test

Run all tests with coverage report. Results are written to <pyftpsync>/htmlcov/index.html::

    $ pytest -v -rsx --cov=ftpsync --cov-report=html

Run selective tests::

    $ pytest -v -rsx -k FtpBidirSyncTest
    $ pytest -v -rsx -k "FtpBidirSyncTest and test_default"
    $ pytest -v -rsx -m benchmark

Run tests on multiple Python versions using `tox <https://tox.readthedocs.io/en/latest/#>`_
(need to install those Python versions first)::

    $ tox
    $ tox -e py36

In order to run realistic tests through an FTP server, we need a setup that publishes
a folder that is also accessible using file-system methods.

This can be achieved by configuring an FTP server to allow access to the `remote`
folder::

  <PYFTPSYNC_TEST_FOLDER>/
    local/
      folder1/
        file1_1.txt
        ...
      file1.txt
      ...
    remote/  # <- FTP server should publish this folder as <PYFTPSYNC_TEST_FTP_URL>
      ...

The test suite checks if ``PYFTPSYNC_TEST_FTP_URL`` is defined and accessible.
Otherwise FTP tests will be skipped.

For example, environment variables may look like this, assuming the FTP server is rooted
at the user's home directory::

    export PYFTPSYNC_TEST_FOLDER=/Users/USER/pyftpsync_test
    export PYFTPSYNC_TEST_FTP_URL=ftp://USER:PASSWORD@localhost/pyftpsync_test/remote

This environment variable may be set to generate ``.pyftpsync-meta`` files in a
larger, but more readable format::

    export PYFTPSYNC_VERBOSE_META=True


.pyftpsyncrc
------------

Instead of using environment variables, it is recommended to create a ``.pyftsyncrc``
file in the user's home directory::

    [test]
    folder = /Users/USER/pyftpsync_test
    ftp_url = ftp://USER:PASSWORD@localhost/pyftpsync_test/remote

    [debug]
    verbose_meta = True

Settings from environment variables still take precedence.


Run Manual Tests
----------------

In order to run the command line script against a defined test scenario, we can use the
``test.fixture_tools`` helper function to set up the default fixture::

    $ python -m test.fixture_tools
    Created fixtures at /Users/USER/test_pyftpsync

    $ ls -al /Users/USER/test_pyftpsync
    total 0
    drwxrwxrwx   4 martin  staff  136  7 Okt 15:32 .
    drwxr-xr-x   7 martin  staff  238 20 Aug 20:26 ..
    drwxr-xr-x  19 martin  staff  646  7 Okt 15:32 local
    drwxr-xr-x  18 martin  staff  612  7 Okt 15:32 remote

The fixture set's up files with defined time stamps (2014-01-01) and already contains
meta data, so conflicts can be detected::

                            Local (UTC)     Remote (UTC)
    ------------------------------------------------------------------------------
    file1.txt               12:00           12:00        (unmodified)
    file2.txt               13:00           12:00
    file3.txt                 x             12:00
    file4.txt               12:00           13:00
    file5.txt               12:00             x
    file6.txt               13:00           13:00:05     CONFLICT!
    file7.txt               13:00:05        13:00        CONFLICT!
    file8.txt                 x             13:00        CONFLICT!
    file9.txt               13:00             x          CONFLICT!

    folder1/file1_1.txt     12.00           12:00        (unmodified)
    folder2/file2_1.txt     13.00           12:00
    folder3/file3_1.txt       x             12:00        (folder deleted)
    folder4/file4_1.txt       x             13:00        (*) undetected CONFLICT!
    folder5/file5_1.txt     12:00           13:00
    folder6/file6_1.txt     12:00             x          (folder deleted)
    folder7/file7_1.txt     13:00             x          (*) undetected CONFLICT!

    new_file1.txt           13:00             -
    new_file2.txt             -             13:00
    new_file3.txt           13:00           13:00        (same size)
    new_file4.txt           13:00           13:00        CONFLICT! (different size)
    new_file5.txt           13:00           13:00:05     CONFLICT!
    new_file6.txt           13:00:05        13:00        CONFLICT!

    NOTE: (*) currently conflicts are NOT detected, when a file is edited on one
    target and the parent folder is removed on the peer target.
    The folder will be removed on sync!

Now run pyftpsync with arbitrary options, passing local and remote folders as targets,
for example::

    $ pyftpsync -v sync /Users/USER/test_pyftpsync/local /Users/USER/test_pyftpsync/remote

If an FTP server was configured, we can also run the script against it::

    $ pyftpsync -v sync /Users/USER/test_pyftpsync/local ftp://localhost/Users/USER/test_pyftpsync/remote

Run  ``python -m test.fixture_tools`` again to reset the test folders.


Run FTP Server
--------------
Run ``pylibdftp`` FTP Server Locally
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

In develpoment mode, pyftpsync installs `pyftpdlib <https://github.com/giampaolo/pyftpdlib>`_
which can be used to run an FTP server for testing.
We allow anonymous access and use a custom port > 1024, so we don't need to sudo::

  $ python -m pyftpdlib  -p 8021 -w -d /Users/martin/test_pyftpsync/remote

Also set the test options accordingly in ``.pyftpsyncrc``::

  [test]
  folder = /Users/USER/pyftpsync_test
  ftp_url = ftp://anonymous:@localhost:8021


Run Built-in FTP Server on macOS Sierra
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Note:** This does **not** work anymore with macOS *High* Sierra.

On OSX (starting with Sierra) the built-in FTP server needs to be activated like so::

  $ sudo -s launchctl load -w /System/Library/LaunchDaemons/ftp.plist

It can be stopped the same way::

  $ sudo -s launchctl unload -w /System/Library/LaunchDaemons/ftp.plist

The FTP server exposes the whole file system, so the URL must start from root::

  [test]
  folder = /Users/USER/pyftpsync_test
  ftp_url = ftp://USER:PASSWORD@localhost/Users/USER/pyftpsync_test/remote

.. warning::

   Exposing the file system is dangerous! Make sure to stop the FTP server after testing.


Run FTP Server on Windows
^^^^^^^^^^^^^^^^^^^^^^^^^

On Windows the
`Filezilla Server <https://filezilla-project.org/download.php?type=server>`_
may be a good choice.


Code
====

.. note::

    	Follow the Style Guide, basically
        `PEP 8 <https://www.python.org/dev/peps/pep-0008/>`_.

        Failing tests or not follwing PEP 8 will break builds on
        `travis <https://travis-ci.org/mar10/pyftpsync>`_,
        so run ``$ pytest`` and ``$ flake8`` frequently and before you commit!


Create a Pull Request
=====================

.. todo::

    	TODO
