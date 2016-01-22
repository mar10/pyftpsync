# -*- coding: UTF-8 -*-
"""
Tests for EventBuffer.
https://gist.github.com/mar10/5c1bea071fa04ad4f6eb
"""
from __future__ import print_function

import logging
import sys
import threading
import time

if sys.version_info < (2, 7):
    # Python 2.6
    import unittest2 as unittest
    from unittest2.case import SkipTest
else:
    # Python 2.7+
    import unittest
    from unittest.case import SkipTest

from .event_buffer import EventBuffer

#-------------------------------------------------------------------------------
# EventBufferTest
#-------------------------------------------------------------------------------

class EventBufferTest(unittest.TestCase):

    def setUp(self):
#         raise SkipTest
        logging.basicConfig(level=logging.DEBUG,
            format="%(threadName)-14s - %(asctime)s.%(msecs).03d - %(message)s",
            datefmt="%H:%M:%S")

    def tearDown(self):
        pass

    def test_1(self):

        logging.debug("START")
        stats = {"t_count": 0, "e_count": 0, "start": time.time()}

        def _cb(event_queue, event_throttle):
            stats["e_count"] += len(event_queue)
            logging.debug("### EMIT START queue_lengt={0}: {1}".format(len(event_queue), event_queue))
            time.sleep(0.3)
            logging.debug("### EMIT STOP")

        eb = EventBuffer(1.0, max_collect_count=None, callback=_cb, at_start=False,
                         flush_timeout=True, async_emit=True)

        def _worker(stats):
            for i in range(50):
                # logging.debug("send trigger({0})".format(i))
                stats["t_count"] += 1
                eb.trigger(data=i, force_emit=False)
                time.sleep(0.12)
        worker = threading.Thread(target=_worker, args=(stats,), name="worker")
        # worker.daemon = False
        worker.start()
        worker.join()

        logging.debug("DONE triggered:{0}, emitted:{1}".format(stats["t_count"], stats["e_count"]))
        eb.join()  # Wait for emit timer
        logging.debug("Joined triggered:{0}, emitted:{1}".format(stats["t_count"], stats["e_count"]))

        self.assertEqual(stats["t_count"], stats["e_count"])
        logging.debug("ELAP: {0} sec".format(time.time() - stats["start"]))

    def test_2(self):
        # Slow
        logging.debug("START")
        stats = {"t_count": 0, "e_count": 0, "start": time.time()}

        def _cb(event_queue, event_throttle):
            stats["e_count"] += len(event_queue)
            logging.debug("### EMIT START queue_lengt={0}: {1}".format(len(event_queue), event_queue))
            time.sleep(0.3)
            logging.debug("### EMIT STOP")

        eb = EventBuffer(1.0, max_collect_count=10, callback=_cb, at_start=False,
                         flush_timeout=True, async_emit=True)

        def _worker(stats):
            for i in range(50):
                # logging.debug("send trigger({0})".format(i))
                stats["t_count"] += 1
                if i == 42:
                    eb.trigger(data=i, force_emit=True, wait=True)
                else:
                    eb.trigger(data=i, force_emit=False)
                time.sleep(0.12)
        worker = threading.Thread(target=_worker, args=(stats,), name="worker")
        # worker.daemon = False
        worker.start()
        worker.join()

        logging.debug("DONE triggered:{0}, emitted:{1}".format(stats["t_count"], stats["e_count"]))
        eb.join()  # Wait for emit timer
        logging.debug("Joined triggered:{0}, emitted:{1}".format(stats["t_count"], stats["e_count"]))

        self.assertEqual(stats["t_count"], stats["e_count"])
        logging.debug("ELAP: {0} sec".format(time.time() - stats["start"]))

#===============================================================================
# Main
#===============================================================================
if __name__ == "__main__":
    unittest.main()
