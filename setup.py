#!/usr/bin/env python

from __future__ import print_function

import os
import sys

from setuptools import Command, setup
from setuptools.command.test import test as TestCommand

from ftpsync import __version__


version = __version__


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
# and https://stackoverflow.com/a/22273180/19166
class SphinxCommand(Command):
    user_options = []
    description = "Build docs using Sphinx"

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        import subprocess

        # sourcedir = os.path.join("docs", "sphinx")
        outdir = os.path.join("docs", "sphinx-build")
        res = subprocess.call(
            "sphinx-build -b html docs/sphinx docs/sphinx-build", shell=True
        )
        if res:
            print("ERROR: sphinx-build exited with code {}".format(res))
        else:
            print("Documentation created at {}.".format(os.path.abspath(outdir)))


try:
    readme = open("README.md", "rt").read()
    # readme = open("readme_pypi.rst", "rt").read()
except IOError:
    readme = "(readme not found. Running from tox/setup.py test?)"


# 'setup.py upload' fails on Vista, because .pypirc is searched on 'HOME' path
if "HOME" not in os.environ and "HOMEPATH" in os.environ:
    os.environ.setdefault("HOME", os.environ.get("HOMEPATH", ""))
    print("Initializing HOME environment variable to '{}'".format(os.environ["HOME"]))

install_requires = ["colorama", "keyring", "PyYAML"]
# The Windows MSI Setup should include some extras?
# if "bdist_msi" in sys.argv:
#     install_requires.extend([])

tests_require = ["pytest", "pytest-cov", "tox", "virtualenv"]

setup_requires = install_requires


use_cx_freeze = False
for cmd in ["bdist_msi"]:
    if cmd in sys.argv:
        use_cx_freeze = True
        break

if use_cx_freeze:
    # Since we included pywin32 extensions, cx_Freeze tries to create a
    # version resource. This only supports the 'a.b.c[.d]' format:
    try:
        int_version = list(map(int, version.split(".")))
    except ValueError:
        # version = "0.0.0.{}".format(datetime.now().strftime("%Y%m%d"))
        version = "0.0.0"

    try:
        from cx_Freeze import setup, Executable  # noqa re-import setup

        # cx_Freeze seems to be confused by module name 'PyYAML' which
        # must be imported as 'yaml', so we rename here. However it must
        # be listed as 'PyYAML' in the requirements.txt and be installed!
        install_requires.remove("PyYAML")
        install_requires.append("yaml")

        executables = [
            Executable(
                script="ftpsync/pyftpsync.py",
                base=None,
                # base="Win32GUI",
                targetName="pyftpsync.exe",
                # icon="docs/logo.ico",
                shortcutName="pyftpsync",
                # copyright="(c) 2012-2019 Martin Wendt",  # requires cx_Freeze PR#94
                # trademarks="...",
            )
        ]
    except ImportError:
        # tox has problems to install cx_Freeze to it's venvs, but it is not needed
        # for the tests anyway
        print(
            "Could not import cx_Freeze; 'build' and 'bdist' commands will not be available."
        )
        print("See https://pypi.python.org/pypi/cx_Freeze")
        executables = []
else:
    print(
        "Did not import cx_Freeze, because 'bdist_msi' commands are not used ({}).".format(
            sys.argv
        )
    )
    print("NOTE: this is a hack, because cx_Freeze seemed to sabotage wheel creation")
    executables = []


build_exe_options = {
    # "init_script": "Console",
    "includes": install_requires,
    "packages": ["keyring.backends"],  # loaded dynamically
    "constants": "BUILD_COPYRIGHT='(c) 2012-2019 Martin Wendt'",
}

bdist_msi_options = {
    "upgrade_code": "{8F4CA3EF-06AD-418E-A64D-B975E3CFA3F6}",
    "add_to_path": True,
    # TODO: configure target dir
    # "initial_target_dir": r"[ProgramFilesFolder]\%s\%s" % (company_name, product_name),
    # TODO: configure shortcuts:
    # https://stackoverflow.com/a/15736406/19166
}


setup(
    name="pyftpsync",
    version=version,
    author="Martin Wendt",
    author_email="pyftpsync@wwwendt.de",
    # copyright="(c) 2012-2019 Martin Wendt",
    maintainer="Martin Wendt",
    maintainer_email="pyftpsync@wwwendt.de",
    url="https://github.com/mar10/pyftpsync",
    description="Synchronize directories using FTP(S) or file system access.",
    long_description=readme,
    long_description_content_type="text/markdown",
    # Development Status :: 2 - Pre-Alpha
    # Development Status :: 3 - Alpha
    # Development Status :: 4 - Beta
    # Development Status :: 5 - Production/Stable
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: Information Technology",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Utilities",
    ],
    keywords="python ftp ftps synchronize tls tool",
    license="The MIT License",
    install_requires=install_requires,
    setup_requires=setup_requires,
    tests_require=tests_require,
    packages=["ftpsync"],
    zip_safe=False,
    extras_require={},
    cmdclass={"test": ToxCommand, "sphinx": SphinxCommand},
    entry_points={"console_scripts": ["pyftpsync=ftpsync.pyftpsync:run"]},
    executables=executables,
    options={"build_exe": build_exe_options, "bdist_msi": bdist_msi_options},
)
