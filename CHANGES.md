2.0.0 (unreleased)
------------------
**Note**: the command line options have changed!  
**Be careful with existing shell scripts after updating from v1.x!**

- Write mode is now on by default.<br>
  The `-x`, `--execute` option was removed, use `--dry-run` instead.
- `-f`, `--include-files` option was renamed to `-m`, `--match`.
- `-o`, `--omit` option was renamed to `-x`, `--exclude`.
- Modified format of .pyftpsync.meta.json
- Dropped support for Python 2.6 and 3.3
- CLI: return defined error codes.
- New `scan` command to list, purge, etc remote targets.
- Remove lock file on Ctrl-C.
- Add FTPS (TLS) support.
- Split into more modules.
- Release as Wheel
- Enforce PEP8

1.0.4 (unreleased)
------------------
- Add FTPS (TLS) support on Python 2.7/3.2+

1.0.3 (2015-06-28)
------------------
- Add conflict handling to upload and download commands
- Move documentation to Read The Docs
- Use tox for tests

1.0.2 (2015-05-17)
------------------
- Bi-directional synchronization
- Detect conflicts if both targets are modified since last sync
- Optional resolve strategy (e.g. always use local)
- Distinguish whether a resource was added on local or removed on remote
- Optionally prompt for username/password
- Optionally store credentials in keyring
- Custom password file (~/pyftpsync.pw) is no longer supported
- Colored output
- Interactive mode
- Renamed _pyftpsync-meta.json to .pyftpsync-meta.json
- MSI installer for MS Windows

0.2.1 (2013-05-07)
------------------
- Fixes for py3

0.2.0 (2013-05-06)
------------------
- Improved progress info
- Added `--progress` option

0.1.0 (2013-05-04)
------------------
First release
