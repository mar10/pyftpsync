# Contribution Guideline
## Setup for Contributors

We need [Python 2.7](https://www.python.org/downloads/), [Python 3.4+](https://www.python.org/downloads/), and [pip](https://pip.pypa.io/en/stable/installing/#do-i-need-to-install-pip) on our system:

Then clone pyftpsync to a local folder and checkout the branch you want to work on:

```
$ git clone git@github.com:mar10/pyftpsync.git
$ cd pyftpsync
$ git checkout my_branch
```

Now set up a virtual enviroment.

For example using Python's builtin `venv` (instead of `virtualenvwrapper`)
in a Windows PowerShell:
```
> py -3.6 -m venv c:\env\pyftpsync_py36
> c:\env\pyftpsync_py36\Scripts\Activate.ps1
```

The new environment exists and is activated.
Now install the development dependencies into that environemt:
```
(pyftpsync_py36) $ pip install -r requirements-dev.txt
```

Finally install pyftpsync to the environment in a debuggable version
```
(pyftpsync_py36) $ python setup.py develop
(pyftpsync_py36) $ pyftpsync --version
(pyftpsync_py36) $ 1.3.0pre1
```

The test suite should run as well:
```
(pyftpsync_py36) $ python setup.py test
```

Happy hacking :)
