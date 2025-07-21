import threading
import time


"""
Timer class
interval - interval between ticks in seconds
callback - tick handler function
"""
class Timer:
    def __init__(self, interval, callback):
        self._interval = interval
        self._callback = callback
        self._running = False
        self._thread = None

    def _run(self):
        while self._running:
            start = time.time()
            self._callback()
            elapsed = time.time() - start
            time.sleep(max(0, self._interval - elapsed))

    def start(self):
        if not self._running:
            self._running = True
            self._thread = threading.Thread(target=self._run, daemon=True)
            self._thread.start()

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join()
            self._thread = None

