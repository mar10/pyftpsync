# -*- coding: UTF-8 -*-
"""
(c) 2015 Martin Wendt
Licensed under the MIT license: http://www.opensource.org/licenses/mit-license.php
"""
from __future__ import print_function

import logging
import threading
import time

#-------------------------------------------------------------------------------
# EventBuffer
#-------------------------------------------------------------------------------
class EventBuffer(object):
    """
    This object consumes events that are generated in arbitrary frequency and 
    emits a predictable sequence of events with a minimum and maximum frequency.

    IN (1 character is 1 second)
      |   ||| |  (pause)   | ||    |

    OUT (max_collect_time=5)
           |               |     |
           
    OUT (max_collect_time=5, at_start=True) 
      |    |               |      |
      
    OUT (max_collect_time=5, flush_timeout=True) 
           |    |               |       |
    
    Example 1:
    Use a callback and set flush_timeout=True to emit at end of event sequence:

        def _cb(event_queue, event_throttle):
            print("### EMIT queue_lengt={}".format(len(event_queue)))
            
        eb = EventBuffer(0.5, callback=_cb, at_start=False, flush_timeout=True)
    
        for i in range(300):
            eb.trigger()
            time.sleep(0.01)
        
        et.join()  # Optionally wait for timer to emit remaining queue entries
    
    Example 2:
    Use a derived class and pass True to last trigger call, so no timer is needed:
    
        class MyThrottle(EventBuffer):
            def __init__(self, max_collect_time, flush_timeout):
                super(MyThrottle, self).__init__(max_collect_time, flush_timeout)
            def on_emit(self, event_queue):
                print("### EMIT queue_lengt={}".format(len(event_queue)))
            
        eb = MyThrottle(0.5, flush_timeout=False)
    
        for i in range(300):
            eb.trigger(force_emit=(i==299))
            time.sleep(0.01)
    
    """
    _thread_id = 0
    
    def __init__(self, max_collect_time=None, max_collect_count=None,
                 at_start=False, flush_timeout=True, async_emit=True,
                 callback=None):
        """
        @param float max_collect_time:  Emit event queue, when last emit was before x seconds
        @param int max_collect_count:  Force emit of event queue, when more than x events have cumulated
        @param bool at_start:  immediately emit on first event (at start or after pause)
        @param float flush_timeout:  Use a timer to make sure cumulated events are finally flushed (True: use max_collect_time)
        @param bool async_emit:  Call on_emit() in a separate thread
        @param callback: fn(event_queue, event_buffer) called on emit
        """
        self._lock = threading.RLock()
        self._emit_lock = threading.Lock()  # Not recursive
        self._emit_thread = None

        self._emit_timer = None
        self.event_queue = []
        self.last_emit = None
        self.last_reset = None
        self.last_trigger = None
        
        self.max_collect_time = max_collect_time
        self.max_collect_count = max_collect_count
        self.at_start = bool(at_start)
        self.async_emit = bool(async_emit)
        self.callback = callback

        if flush_timeout is True:
            flush_timeout = max_collect_time
        self.flush_timeout = float(flush_timeout)

    def _do_emit(self, async):
        """Emit current buffer and clear event queue.

        Emitting may be asynchronous (called in a seperate thread), so while 
        the buffer is being processed, new calls to trigger() are accepted.
        """
        # logging.debug("### _do_emit({0})".format(async))
        with self._lock:
            if self._emit_timer:
                self._emit_timer.cancel()
                self._emit_timer = None
            event_queue = self.event_queue
            self.event_queue = []

            # Even if emitting is async, we serialize multiple calls.
            self._emit_lock.acquire()
            def _worker():
                self.last_emit = self.last_reset = time.time()
                
                # Here we flush the current event queue. This may take some time!
                try:
                    self.on_emit(event_queue)
                finally:
                    # print ("end _emit_thread", self._emit_thread)
                    self._emit_thread = None
                    self._emit_lock.release()

            if async:
                assert self._emit_thread is None
                EventBuffer._thread_id += 1
                self._emit_thread = threading.Thread(name="emit_worker_{0}".format(EventBuffer._thread_id), 
                                                     target=_worker)
                self._emit_thread.start()
                # self._emit_thread.name = "emit_worker_{0}".format(self._emit_thread.ident)
                # print ("start _emit_thread", self._emit_thread)
            else:
                _worker()

    def _start_emit_timer(self, timeout):
        """Schedule a timer that will emit, even if trigger() method is not called again."""
        # logging.debug("### start timer({0})".format(self.flush_timeout))
        if self._emit_timer:
            self._emit_timer.cancel()

        # TODO: is it more efficient to re-use the same timer? (http://stackoverflow.com/a/13261840/19166)
        def _worker():
            self._do_emit(async=self.async_emit)

        self._emit_timer = threading.Timer(timeout, _worker)
        self._emit_timer.name = "emit_timer"
        self._emit_timer.start()

    def join(self, cancel=False):
        """Wait for emit timer to flush pending events.
        
        :param bool cancel: interrupt pending timer (and preventing final emit) 
        """
        # Wait for emit timer thread
        if self._emit_timer:
            if cancel:
                self._emit_timer.cancel()
            # logging.debug("join _emit_timer {0}...".format(self._emit_timer))
            self._emit_timer.join()
            # logging.debug("join _emit_timer {0}... done.".format(self._emit_timer))
            self._emit_timer = None
        # Also wait for emit thread if any
        if self._emit_thread:
            # logging.debug("join _emit_thread {0}...".format(self._emit_thread))
            self._emit_thread.join()
            # logging.debug("join _emit_thread {0}... done.".format(self._emit_thread))
        
    def trigger(self, data=None, force_emit=False, wait=False):
        """Queue an event (with optional data) and emit if conditions are met.
        
        :param data: optional event data (appended to event queue)
        :param bool force_emit: Immediately flush event queue  
        :param bool wait: Wait for async emit
        :return: True if event queue was flushed.
        :rtype: bool
        """
        with self._lock:
            now = time.time()
            self.last_trigger = now
            if self.last_reset is None:
                self.last_reset = now
            self.event_queue.append(data)
            logging.debug("trigger({0})".format(data))
            do_emit = (force_emit 
                       or (self.max_collect_count and len(self.event_queue) >= self.max_collect_count)
                       or (self.max_collect_time and (now - self.last_reset) >= self.max_collect_time)
                       or (self.at_start and self.last_emit is None)
                       )
            if do_emit:
                if force_emit and wait:
                    self._do_emit(False)
                else:
                    self._do_emit(self.async_emit)

            elif self.flush_timeout and not self._emit_timer:
                # This is the first trigger after a flush. 
                # Schedule a timer that will emit even if trigger() method is not called again.
                self._start_emit_timer(self.flush_timeout)

        return do_emit

    def on_emit(self, event_queue):
        """This callback is triggered when the event queue is flushed.
        
        Either pass a handler function as `callback` argument to the constructor,
        or override this `on_emit()` method.
        
        :param list event_queue: event list to be flushed (self.event_queue is already cleared)
        """
        return self.callback(event_queue, self)
