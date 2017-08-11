============
Architecture
============

.. toctree::
   :maxdepth: 2


Class Inheritance Diagram
=========================

.. inheritance-diagram:: ftpsync.targets ftpsync.ftp_target ftpsync.resources ftpsync.synchronizers
   :parts: 1
   :private-bases:


Algorithm
=========

See `pyftpsync-spec.pdf <https://raw.githubusercontent.com/mar10/pyftpsync/master/docs/pyftpsync-spec.pdf>`_
for some explanations.


.. Test Case
  =========

.. Testdata2.

  =====================================  =======================================  =========================
  Local PC 1                              Remote 1                                Local PC 2
  =====================================  =======================================  =========================
      a.txt  01-07-2014 12:00
      b.txt  01-07-2014 12:00
      c.txt  01-07-2014 12:00
      d.txt  01-07-2014 12:00

  SYNC @ 02-07-2014 12:00 >>

      a.txt  01-07-2014 12:00             a.txt  01-07-2014 12:00    CREATE
      b.txt  01-07-2014 12:00             b.txt  01-07-2014 12:00
      c.txt  01-07-2014 12:00             c.txt  01-07-2014 12:00
      d.txt  01-07-2014 12:00             d.txt  01-07-2014 12:00

  EDIT FILES @ 03-07-2014 12:00
      & SYNC >>

      a.txt  01-07-2014 12:00             a.txt  01-07-2014 12:00
      b.txt  01-07-2014 12:00            *b.txt  03-07-2014 12:00    DOWNLOAD
     *c.txt  03-07-2014 12:00             c.txt  01-07-2014 12:00    UPLOAD
     *d.txt  03-07-2014 12:00            *d.txt  03-07-2014 12:00    ?? Conflict
     *e.txt  03-07-2014 12:00                                        UPLOAD
                                         *f.txt  03-07-2014 12:00    DOWNLOAD

  SYNC >>

                                          a.txt  01-07-2014 12:00                  a.txt  01-07-2014 12:00
                                          b.txt  01-07-2014 12:00                 *b.txt  03-07-2014 12:00    DOWNLOAD
                                         *c.txt  03-07-2014 12:00                  c.txt  01-07-2014  12:00    UPLOAD
                                         *d.txt  03-07-2014 12:00                 *d.txt  03-07-2014 12:00    ?? Conflict
                                         *e.txt  03-07-2014 12:00    UPLOAD
                                                                                  *f.txt  03-07-2014 12:00    DOWNLOAD
  =====================================  =======================================  =========================
