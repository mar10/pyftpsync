# If true, then the svn revision won't be used to calculate the
# revision (set to True for real releases)
import os
import sys
RELEASE = False

#from ez_setup import use_setuptools
#use_setuptools()

from setuptools import setup #, find_packages

# Get description and __version__ without using import
readme = open("readme_pypi.rst", "rt").read()
g_dict = {}
exec(open("ftpsync/_version.py").read(), g_dict)
version = g_dict["__version__"]

# 'setup.py upload' fails on Vista, because .pypirc is searched on 'HOME' path
if not "HOME" in os.environ and  "HOMEPATH" in os.environ:
    os.environ.setdefault("HOME", os.environ.get("HOMEPATH", ""))
    print("Initializing HOME environment variable to '%s'" % os.environ["HOME"])

install_requires = []
if sys.version_info < (2, 7):
    install_requires += ["argparse"]

setup(name="pyftpsync",
      version = version,
      author = "Martin Wendt",
      author_email = "pyftpsync@wwwendt.de",
      maintainer = "Martin Wendt",
      maintainer_email = "pyftpsync@wwwendt.de",
      url = "http://pyftpsync.googlecode.com/",
      description = "Synchronize folders over FTP.",
      long_description = readme, #+ "\n\n" + changes,

        #Development Status :: 2 - Pre-Alpha
        #Development Status :: 3 - Alpha
        #Development Status :: 4 - Beta
        #Development Status :: 5 - Production/Stable

      classifiers = ["Development Status :: 3 - Alpha",
                     "Environment :: Console",
                     "Intended Audience :: Information Technology",
                     "Intended Audience :: Developers",
                     "License :: OSI Approved :: MIT License",
                     "Operating System :: OS Independent",
                     "Programming Language :: Python :: 2",
                     "Programming Language :: Python :: 3",
                     "Topic :: Software Development :: Libraries :: Python Modules",
                     "Topic :: Utilities",
                     ],
      keywords = "python ftp synchronize tool", 
#      platforms=["Unix", "Windows"],
      license = "The MIT License",
      install_requires = install_requires,
#      package_dir = {"": "src"},
      packages = ["ftpsync"],
#      packages = find_packages(exclude=[]),
      
      py_modules = [
#                    "ez_setup", 
                    ],
      # See also MANIFEST.in
#      package_data={"": ["*.txt", "*.html", "*.conf"]},
#      include_package_data = True, # TODO: PP
      zip_safe = False,
      extras_require = {},
      test_suite = "test.test_flow",
      entry_points = {
          "console_scripts" : ["pyftpsync = ftpsync.pyftpsync:run"],
          },
      )
