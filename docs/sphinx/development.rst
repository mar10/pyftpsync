===========
Development
===========

Status and Contribution
=======================




## Run Tests

If you plan to debug or contribute, install to run directly from the source::

	$ python setup.py develop
	$ python setup.py test

The use of `virtualenv <https://virtualenv.pypa.io/en/latest/>`_ is recommended.


How to Contribute
=================

.. todo:
    https://pip.pypa.io/en/stable/development/

Create a Fork:


Checkout the source code:

TODO

Work in a virtual environment
-----------------------------

On Linux/OS X, I recommend to use `pipenv <https://github.com/kennethreitz/pipenv>`_
to make this easy::

	$ cd /path/pyftpsync
	$ pipenv shell

Alternatively (especially on Windows), use `virtualenv <https://virtualenv.pypa.io/en/latest/>`_
to create and activate the virtual environment::

	TODO

Now we can setup the requirements::

	$ pip install -r requirements-dev.txt
	$ python setup.py test
	$ python setup.py develop
	$ python setup.py sphinx

Create a Pull Request::

	TODO

.. Make a release::

	$ python setup.py test
	$ python setup.py bdist_wheel
	$ twine upload
