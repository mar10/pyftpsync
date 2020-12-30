#!/usr/bin/env python

import os
import re
import sys

from setuptools import setup
from cx_Freeze import setup, Executable  # noqa re-import setup

from ftpsync import __version__


# Check for Windows MSI Setup
if "bdist_msi" not in sys.argv or len(sys.argv) != 2:
    raise RuntimeError(
        "This setup.py variant is only for creating 'bdist_msi' targets: {}\n"
        "Example `{} bdist_msi`".format(sys.argv, sys.argv[0])
    )

org_version = __version__

# 'setup.py upload' fails on Vista, because .pypirc is searched on 'HOME' path
if "HOME" not in os.environ and "HOMEPATH" in os.environ:
    os.environ.setdefault("HOME", os.environ.get("HOMEPATH", ""))
    print("Initializing HOME environment variable to '{}'".format(os.environ["HOME"]))

# Since we included pywin32 extensions, cx_Freeze tries to create a
# version resource. This only supports the 'a.b.c[.d]' format.
# Our version has either the for '1.2.3' or '1.2.3-a4'
major, minor, patch = org_version.split(".", 3)
if "-" in patch:
    patch, alpha = patch.split("-", 1)
    # Remove leading letters
    alpha = re.sub("^[a-zA-Z]+", "", alpha)
else:
    alpha = 0
version = "{}.{}.{}.{}".format(major, minor, patch, alpha)
print("Version {}, using {}".format(org_version, version))

try:
    readme = open("README.md", "rt").read()
except IOError:
    readme = "(readme not found. Running from tox/setup.py test?)"

install_requires = ["colorama", "keyring", "pysftp", "PyYAML"]
tests_require = ["pytest", "pytest-cov", "tox", "virtualenv"]
setup_requires = install_requires

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
        # copyright="(c) 2012-2020 Martin Wendt",  # requires cx_Freeze PR#94
        # trademarks="...",
    )
]

build_exe_options = {
    # "init_script": "Console",
    "includes": install_requires,
    "packages": ["keyring.backends"],  # loaded dynamically
    "constants": "BUILD_COPYRIGHT='(c) 2012-2020 Martin Wendt'",
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
    # copyright="(c) 2012-2020 Martin Wendt",
    maintainer="Martin Wendt",
    maintainer_email="pyftpsync@wwwendt.de",
    url="https://github.com/mar10/pyftpsync",
    description="Synchronize directories using FTP(S), SFTP, or file system access.",
    long_description=readme,
    long_description_content_type="text/markdown",
    # Development Status :: 2 - Pre-Alpha
    # Development Status :: 3 - Alpha
    # Development Status :: 4 - Beta
    # Development Status :: 5 - Production/Stable
    classifiers=[
        "Development Status :: 3 - Alpha",
        # "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: Information Technology",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Topic :: Internet :: File Transfer Protocol (FTP)",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Utilities",
    ],
    keywords="python ftp ftps sftp synchronize tls tool",
    license="The MIT License",
    install_requires=install_requires,
    setup_requires=setup_requires,
    tests_require=tests_require,
    packages=["ftpsync"],
    zip_safe=False,
    extras_require={},
    # cmdclass={"test": ToxCommand, "sphinx": SphinxCommand},
    entry_points={"console_scripts": ["pyftpsync=ftpsync.pyftpsync:run"]},
    executables=executables,
    options={"build_exe": build_exe_options, "bdist_msi": bdist_msi_options},
)
