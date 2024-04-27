## 4.1.0 (unreleased)

-   Fix #82 Error importing SFTPTarget with paramiko > 3.0
-   Drop support for Python 3.7 (end-of-life: 2023-06-27)

    4.0.0 (2022-07-31)

---

-   Add SFTP support
-   Improve `run` command
-   New `tree` command
-   New `--case` argument for better handling of ambigous files that only differ
    in the name's casing
-   New `--create-folder` argument to allow creation of missing remote folders
-   New `--report-problems` argument to return exit code 10 on skipped files
    like unresolved conflicts or copy errors
-   New `--no-dry-run` argument to `run` command to override a default dry_run
    configuration (alias: `--execute`)
-   New `--debug classify` argument helps with analysis of synchronization problems
-   `--migrate` now always removes outdated metadata files (before, this was only
    done when a file inside that directory was touched)
-   Copy errors (e.g. due to encoding problems) are skipped (see also `--report-problems`)
-   Fix #26: Crash when not setting verbose option
-   Use [Yabs](https://github.com/mar10/yabs) as release tool
-   Available on Windows Package Manager
-   **Breaking Changes:**

    -   Drop support for Python 2.x (end-of-life: 2020-01-01)
    -   Rename `.pyftpsync.yaml` to `pyftpsync.yaml`
    -   Rename FtpTarget => FTPTarget

    3.1.1+

---

See branch `maintain_3.x`.

## 3.1.0 (2019-12-26)

-   Drop support for Python 3.4 (end-of-life: 2019-03-18)
-   Add support for Python 3.8
-   Fix #38 Remove trailing '/' before checking PWD response

    3.0.0 (2019-04-20)

---

-   This release addresses some known **encoding-related issues**:

    -   The internal path format are now native strings (i.e. unicode on Python 3
        or UTF-8 bytes on Python 2)
    -   FTP targets are now assumed to support UTF-8.
    -   #30: Fallback to CP-1252 encoding when FTP server returns non-UTF-8
    -   Local filesystem targets now consider the OS encoding.
    -   Modified format of `.pyftpsync-meta.json`: File names are now stored as UTF-8
        (was the unmodified binary format of the target platform before).
    -   See also the 'encoding' section in the
        [spec](https://github.com/mar10/pyftpsync/blob/master/docs/sphinx/pyftpsync-spec.pdf).

-   **New `run` command** reads and executes settings from a configuration file
    `.pyftpsync.yaml`
-   Remove trailing garbage from output lines

**Breaking Changes:**

-   Modified format of `.pyftpsync-meta.json`.
    Pass `--migrate` option to convert from a prvious version (note that this
    cannot be undone)

## 2.1.0 (2018-08-25)

-   Allow `-v` with `--version` option.
-   Fix #26: Crash when not setting verbose option.
-   Print SYST and FEAT when -vv is passed
-   Accept list type options for `exclude` argument in CLI mode
-   Apply and enforce Black formatter
-   Fix #27: Download- and UploadSynchronizer honor `--delete` flag for all
    conditions.<br>
    **NOTE:** default settings will no longer delete files for up- and downloads.

    2.0.0 (2018-01-01)

---

**Note**: the command line options have changed:
**Be careful with existing shell scripts after updating from v1.x!**

**New Features:**

-   New `scan` command to list, purge, etc. remote targets.
-   Add FTPS (TLS) support.
-   Support Active FTP.
-   Support for `.netrc` files.
-   CLI returns defined error codes.
-   Use configurable logger for output when not in CLI mode.
-   Release as Wheel.

**Breaking Changes:**

-   Write mode is now on by default.
    The `-x`, `--execute` option was removed, use `--dry-run` instead.
-   `-f`, `--include-files` option was renamed to `-m`, `--match`.<br>
    `-o`, `--omit` option was renamed to `-x`, `--exclude`.
-   Modified format of `.pyftpsync-meta.json`.
-   Dropped support for Python 2.6 and 3.3.

**Fixes and Improvements:**

-   Remove lock file on Ctrl-C.
-   Refactored and split into more modules.
-   Improved test framework and documentation.
-   Enforce PEP8, use flake8.

    1.0.4 (unreleased)

---

-   Add FTPS (TLS) support on Python 2.7/3.2+

    1.0.3 (2015-06-28)

---

-   Add conflict handling to upload and download commands
-   Move documentation to Read The Docs
-   Use tox for tests

    1.0.2 (2015-05-17)

---

-   Bi-directional synchronization
-   Detect conflicts if both targets are modified since last sync
-   Optional resolve strategy (e.g. always use local)
-   Distinguish whether a resource was added on local or removed on remote
-   Optionally prompt for username/password
-   Optionally store credentials in keyring
-   Custom password file (~/pyftpsync.pw) is no longer supported
-   Colored output
-   Interactive mode
-   Renamed \_pyftpsync-meta.json to .pyftpsync-meta.json
-   MSI installer for MS Windows

    0.2.1 (2013-05-07)

---

-   Fixes for py3

    0.2.0 (2013-05-06)

---

-   Improved progress info
-   Added `--progress` option

    0.1.0 (2013-05-04)

---

First release
