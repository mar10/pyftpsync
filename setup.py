#!/usr/bin/env python

from __future__ import print_function

import os
import sys

from setuptools import setup, find_packages, Command
from setuptools.command.test import test as TestCommand

from ftpsync import __version__


# Override 'setup.py test' command
class ToxCommand(TestCommand):
    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True
    def run_tests(self):
        # Import here, cause outside the eggs aren't loaded
        import tox
        errcode = tox.cmdline(self.test_args)
        sys.exit(errcode)


# Add custom command 'setup.py sphinx'
# See https://dankeder.com/posts/adding-custom-commands-to-setup-py/
# and http://stackoverflow.com/a/22273180/19166
class SphinxCommand(Command):
    user_options = []
    description = 'Build docs using Sphinx'

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        import subprocess
        sourcedir = os.path.join("doc", "sphinx")
        outdir = os.path.join("doc", "sphinx-build")
        res = subprocess.call("sphinx-build -b html doc/sphinx doc/sphinx-build",
            shell=True)
        if res:
            print("ERROR: sphinx-build exited with code {}".format(res))
        else:
            print("Documentation created at {}.".format(os.path.abspath(outdir)))


try:
  readme = open("readme_pypi.rst", "rt").read()
except IOError:
  readme = "(readme_pypi.rst not found. Running from tox/setup.py test?)"


try:
    from cx_Freeze import setup, Executable
    executables = [
        Executable(script="ftpsync/pyftpsync.py",
                   base=None,
                   targetName= "pyftpsync.exe",
                   # icon= "doc/logo.ico",
                   shortcutName= "pyftpsync",
                   )
         ]
except ImportError:
    # tox has problems to install cx_Freeze to it's venvs, but it is not needed
    # for the tests anyway
    print("Could not import cx_Freeze; 'build' and 'bdist' commands will not be available.")
    print("See https://pypi.python.org/pypi/cx_Freeze")
    executables = []


# 'setup.py upload' fails on Vista, because .pypirc is searched on 'HOME' path
if not "HOME" in os.environ and  "HOMEPATH" in os.environ:
    os.environ.setdefault("HOME", os.environ.get("HOMEPATH", ""))
    print("Initializing HOME environment variable to '{}'".format(os.environ["HOME"]))

install_requires = ["colorama",
                    "keyring",
                    ]
tests_require = ["pytest",
                 "pytest-cov",
                 "tox",
                 "virtualenv",
                 ]

setup_requires = install_requires

build_exe_options = {
    "init_script": "Console",
    "includes": install_requires,
    "packages": ["keyring.backends",  # loaded dynamically
                 ],
    "constants": "BUILD_COPYRIGHT='(c) 2012-2016 Martin Wendt'",
    }

bdist_msi_options = {
    "upgrade_code": "{8F4CA3EF-06AD-418E-A64D-B975E3CFA3F6}",
    "add_to_path": True,
    # TODO: configure target dir
#   "initial_target_dir": r"[ProgramFilesFolder]\%s\%s" % (company_name, product_name),
    # TODO: configure shortcuts:
    # http://stackoverflow.com/a/15736406/19166
    }


setup(name="pyftpsync",
      version = __version__,
      author = "Martin Wendt",
      author_email = "pyftpsync@wwwendt.de",
      # copyright = "(c) 2012-2016 Martin Wendt",
      maintainer = "Martin Wendt",
      maintainer_email = "pyftpsync@wwwendt.de",
      url = "https://github.com/mar10/pyftpsync",
      description = "Synchronize folders over FTP.",
      long_description = readme, #+ "\n\n" + changes,

        #Development Status :: 2 - Pre-Alpha
        #Development Status :: 3 - Alpha
        #Development Status :: 4 - Beta
        #Development Status :: 5 - Production/Stable

      classifiers = ["Development Status :: 4 - Beta",
                     "Environment :: Console",
                     "Intended Audience :: Information Technology",
                     "Intended Audience :: Developers",
                     "License :: OSI Approved :: MIT License",
                     "Operating System :: OS Independent",
                     "Programming Language :: Python :: 2",
                     "Programming Language :: Python :: 2.7",
                     "Programming Language :: Python :: 3",
                     "Programming Language :: Python :: 3.3",
                     "Programming Language :: Python :: 3.4",
                     "Programming Language :: Python :: 3.5",
                     "Topic :: Software Development :: Libraries :: Python Modules",
                     "Topic :: Utilities",
                     ],
      keywords = "python ftp synchronize tool",
#      platforms=["Unix", "Windows"],
      license = "The MIT License",
      install_requires = install_requires,
      setup_requires = setup_requires,
      tests_require = tests_require,
#      package_dir = {"": "src"},
      packages = ["ftpsync"],
      # packages = find_packages(exclude=['tests']),

      py_modules = [
#                    "ez_setup",
                    ],
      # See also MANIFEST.in
#      package_data={"": ["*.txt", "*.html", "*.conf"]},
#      include_package_data = True, # TODO: PP
      zip_safe = False,
      extras_require = {},
#      test_suite = "test.test_flow",
      cmdclass = {"test": ToxCommand,
                  "sphinx": SphinxCommand,
                  },
      entry_points = {
          "console_scripts" : ["pyftpsync = ftpsync.pyftpsync:run"],
          },
      executables = executables,
      options = {"build_exe": build_exe_options,
                 "bdist_msi": bdist_msi_options,
                 }
      )
