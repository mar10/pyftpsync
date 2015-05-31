======================
pyftpsync Architecture
======================

.. comment, because grqphwiz currently doesn't work on my mac
  x

Classes
=======
.. inheritance-diagram:: ftpsync.targets ftpsync.resources ftpsync.synchronizers
   :parts: 1
   :private-bases:


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

