pyftpsync
=========
Copyright (c) 2012 Martin Wendt

Synchronize local directories with FTP server.

This is both:
  - a command line tool 
  - a library for use in your projects


Project home: http://pyftpsync.googlecode.com/

Requires Python 2.6+ or 3

Known limitations
-----------------
  - The current status is alpha and barely tested.
  - The FTP server must support the MLST command.


Usage
-----
Note:
    $ pyftpsync upload A B
is essentially the same as
    $ pyftpsync download B A

Verbose modes (default: 3)
    0: quiet
    1: errors only
    2: errors and summary
    3: errors, changes, and summary
    4: errors, files, and summary
    5: debug output including FTP commands
