=======
CHANGES
=======

1.0.0 (unreleased)
==================
- Bi-directional synchronization
- Detect conflicts if both targets are modified since last sync.
- Optional resolve strategy (e.g. always use local).
- Distinguish whether a resource was added on local or removed on remote.
- Optionally prompt for username/password.
- Optionally store credentials in keyring.
- Custom password file (~/pyftpsync.pw) is no longer supported.
- Colored output
- Interactive mode
- Renamed _pyftpsync-meta.json to .pyftpsync-meta.json

0.2.1 (2013-05-07)
==================
- Fixes for py3

0.2.0 (2013-05-06)
==================
- Improved progress info
- Added `--progress` option

0.1.0 (2013-05-04)
==================
First release
