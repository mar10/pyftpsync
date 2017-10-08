===========
Development
===========

Install for Development
=======================

If you plan to debug or contribute, install to run directly from the source.


Fork Repository
---------------

.. todo:: Describe


Work in a Virtual Environment
-----------------------------

On Linux/OS X, we recommend to use `pipenv <https://github.com/kennethreitz/pipenv>`_
to make this easy::

	$ cd /path/to/pyftpsync
	$ pipenv shell

Alternatively (especially on Windows), use `virtualenv <https://virtualenv.pypa.io/en/latest/>`_
to create and activate the virtual environment::

	TODO

Now we can setup the requirements and install pyftpsync to run from source code::

	$ pip install -r requirements-dev.txt
	$ python setup.py develop
	$ python setup.py test

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


Run Manual Tests
----------------

In order to run the command line script against a defined test scenario, we can use the
``test.fixture_tools`` helper function to set up the default fixture::

    $ python -m test.fixture_tools
    Created fixtures at /Users/USER/pyftpsync_test_folder

    $ ls -al /Users/USER/pyftpsync_test_folder
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

    $ pyftpsync -v sync /Users/USER/pyftpsync_test_folder/local /Users/USER/pyftpsync_test_folder/remote

If an FTP server was configured, we can also run the script against it::

    $ pyftpsync -v sync /Users/USER/pyftpsync_test_folder/local ftp://localhost/Users/USER/pyftpsync_test_folder/remote

Run  ``python -m test.fixture_tools`` again to reset the test folders.


Run Built-in FTP Server on macOS Sierra
---------------------------------------

On OSX (starting with Sierra) the built-in FTP server needs to be activated like so::

  $ sudo -s launchctl load -w /System/Library/LaunchDaemons/ftp.plist

It can be stopped the same way::

  $ sudo -s launchctl unload -w /System/Library/LaunchDaemons/ftp.plist

The FTP server exposes the whole file system, so the URL must start from root::

  export PYFTPSYNC_TEST_FOLDER=/Users/USER/pyftpsync_test
  export PYFTPSYNC_TEST_FTP_URL=ftp://USER:PASSWORD@localhost/Users/USER/pyftpsync_test/remote

.. warning::

   Exposing the file system may be dangerous! Make sure to stop the FTP server after testing.


.. Run ProFTPD on macOS Sierra
    ---------------------------

    .. todo::
        This did not work yet due to permission problems.
        If anyone get's this to run, please document here.

    For example, environment variables may look like this, assuming the FTP server is rooted
    at the user's home directory::

        export PYFTPSYNC_TEST_FOLDER=/Users/USER/pyftpsync_test
        export PYFTPSYNC_TEST_FTP_URL=ftp://USER:PASSWORD@localhost/pyftpsync_test/remote

    We could install XAMPP and add this to `proftpd.conf`::

      <Anonymous /Users/joe/pyftpsync_test_folder/remote>
        User  ftp
        Group ftp

        # We want clients to be able to login with "anonymous" as well as "ftp"
        UserAlias anonymous ftp

        # Limit the maximum number of anonymous logins
        MaxClients  10

        # Limit WRITE everywhere in the anonymous chroot
        <Limit WRITE>
          AllowAll
         </Limit>
        AllowOverwrite  on
      </Anonymous>


    .. seealso::
      https://delightlylinux.wordpress.com/2017/06/10/how-to-set-up-anonymous-ftp-with-proftp/


How to Contribute
=================

.. todo:
    https://pip.pypa.io/en/stable/development/

Create a Fork:


Checkout the source code:

TODO


Create a Pull Request::

	TODO

.. Make a release::

	$ python setup.py test
	$ python setup.py bdist_wheel
	$ twine upload