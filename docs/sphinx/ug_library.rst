============
Script Usage
============

All options that are available for command line, can also be passed to
the synchronizers. For example ``--delete-unmatched`` becomes
``"delete_unmatched": true``.

Upload modified files from local folder to FTP server::

  from ftpsync.targets import FsTarget
  from ftpsync.ftp_target import FTPTarget
  from ftpsync.synchronizers import UploadSynchronizer

  local = FsTarget("~/temp")
  user ="joe"
  passwd = "secret"
  remote = FTPTarget("/temp", "example.com", username=user, password=passwd)
  opts = {"force": False, "delete_unmatched": True, "verbose": 3}
  s = UploadSynchronizer(local, remote, opts)
  s.run()

Synchronize a local folder with an FTP server using TLS::

  from ftpsync.targets import FsTarget
  from ftpsync.ftp_target import FTPTarget
  from ftpsync.synchronizers import BiDirSynchronizer

  local = FsTarget("~/temp")
  user ="joe"
  passwd = "secret"
  remote = FTPTarget("/temp", "example.com", username=user, password=passwd, tls=True)
  opts = {"resolve": "skip", "verbose": 1}
  s = BiDirSynchronizer(local, remote, opts)
  s.run()

.. note::
    The class ``FTPTarget`` was renamed with release 4.0 (named ``FtpTarget`` 
    before).


Logging
-------

By default, the library initializes and uses a
`python logger <https://docs.python.org/library/logging.html>`_ named 'pyftpsync'.
This logger can be customized like so::

    import logging

    logger = logging.getLogger("pyftpsync")
    logger.setLevel(logging.DEBUG)

and replaced like so::

    import logging
    import logging.handlers
    from ftpsync.util import set_pyftpsync_logger

    custom_logger = logging.getLogger("my.logger")
    log_path = "/my/path/pyftpsync.log"
    handler = logging.handlers.WatchedFileHandler(log_path)
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    custom_logger.addHandler(handler)

    set_pyftpsync_logger(custom_logger)


.. note::

    The CLI calls ``set_pyftpsync_logger(None)`` on startup, so it logs to stdout
    (and stderr).
