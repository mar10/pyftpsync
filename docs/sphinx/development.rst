===========
Development
===========

Install for Development
=======================

If you plan to debug or contribute, install to run directly from the source.


Fork Repository
---------------

.. todo:: Describe


Work in a virtual environment
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


Run built-in FTP Server on macOS Sierra
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


Run ProFTPD on macOS Sierra
---------------------------

.. todo::
    This did not work yet due to permission problems.

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
