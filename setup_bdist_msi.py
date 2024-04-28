#!/usr/bin/env python

# NOTE: isort must not chage this import order:
# isort: skip_file

import os
import re
import sys

from setuptools import setup
from cx_Freeze import setup, Executable  # noqa re-import setup

from ftpsync import __version__


# Check for Windows MSI Setup
if "bdist_msi" not in sys.argv:  # or len(sys.argv) != 2:
    raise RuntimeError(
        "This setup.py variant is only for creating 'bdist_msi' targets: {}\n"
        "Example `{} bdist_msi`".format(sys.argv, sys.argv[0])
    )

org_version = __version__

# # 'setup.py upload' fails on Vista, because .pypirc is searched on 'HOME' path
# if "HOME" not in os.environ and "HOMEPATH" in os.environ:
#     os.environ.setdefault("HOME", os.environ.get("HOMEPATH", ""))
#     print("Initializing HOME environment variable to '{}'".format(os.environ["HOME"]))

# Since we included pywin32 extensions, cx_Freeze tries to create a
# version resource. This only supports the 'a.b.c[.d]' format.
# Our version has either the for '1.2.3' or '1.2.3-a1'
unsafe_version = False
major, minor, patch = org_version.split(".", 3)
major = int(major)
minor = int(minor)
if "-" in patch:
    # We have a pre-release version, e.g. '1.2.3-a1'.
    # This is presumably a post-release increment after '1.2.2' release.
    # It must NOT be converted to '1.2.3.1', since that would be *greater*
    # than '1.2.3', which is not even released yet.
    # Approach 1:
    #     We cannot guarantee that '1.2.2.1' is correct either, so for
    #     pre-releases we assume '0.0.0.0':
    # major = minor = patch = alpha = 0
    # Approach 2:
    #     '1.2.3-a1' was presumably a post-release increment after '1.2.2',
    #     so assume '1.2.2.1':
    patch, alpha = patch.split("-", 1)
    patch = int(patch)
    # Remove leading letters
    alpha = re.sub("^[a-zA-Z]+", "", alpha)
    alpha = int(alpha)
    if unsafe_version and patch >= 1:
        patch -= 1  # 1.2.3-a1 => 1.2.2.1
    else:
        # may be 1.2.0-a1 or 2.0.0-a1: we don't know what the previous release was
        major = minor = patch = alpha = 0
else:
    patch = int(patch)
    alpha = 0

version = "{}.{}.{}.{}".format(major, minor, patch, alpha)
print("Version {}, using {}".format(org_version, version))

try:
    readme = open("README.md", "rt").read()
except IOError:
    readme = "(readme not found. Running from tox/setup.py test?)"

# NOTE: Only need to list requirements that are not discoverable by scanning
#       the main package. For example due to dynamic or optional imports.
# Also, cx_Freeze may have difficulties with packages listed here, e.g. PyYAML:
#    https://github.com/marcelotduarte/cx_Freeze/issues/1541
install_requires = []
setup_requires = install_requires
tests_require = []  

executables = [
    Executable(
        script="ftpsync/pyftpsync.py",
        base=None,
        # base="Win32GUI",
        target_name="pyftpsync.exe",
        icon="docs/logo.ico",
        shortcut_name="pyftpsync",
        copyright="(c) 2012-2024 Martin Wendt",
        # trademarks="...",
    )
]

# See https://cx-freeze.readthedocs.io/en/latest/distutils.html#build-exe
build_exe_options = {
    # "init_script": "Console",
    "includes": install_requires,
    "packages": ["keyring.backends"],  # loaded dynamically
    "excludes": [
        "tkinter",
    ],
    "constants": "BUILD_COPYRIGHT='(c) 2012-2024 Martin Wendt'",
    "include_msvcr": True,
}

# See https://cx-freeze.readthedocs.io/en/latest/distutils.html#bdist-msi
bdist_msi_options = {
    "upgrade_code": "{8F4CA3EF-06AD-418E-A64D-B975E3CFA3F6}",
    "add_to_path": True,
    # "install_icon": "docs/logo.ico",
    # "all_users": True,
    # "summary_data": {"author": "Martin Wendt"},
}


setup(
    name="pyftpsync",
    version=version,
    author="Martin Wendt",
    author_email="pyftpsync@wwwendt.de",
    # copyright="(c) 2012-2024 Martin Wendt",
    maintainer="Martin Wendt",
    maintainer_email="pyftpsync@wwwendt.de",
    url="https://github.com/mar10/pyftpsync",
    description="Synchronize directories using FTP(S), SFTP, or file system access.",
    long_description=readme,
    long_description_content_type="text/markdown",
    # Not required for this build-only setup config:
    classifiers=[],
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
