import threading
import logging
import tkinter as tk
from timeit import default_timer


class Timer:

    def __init__(self, variable: tk.StringVar):
        self._variable = variable
        self.with_inspection = True

        self._running = False
        self._inspecting = False

        self._shallow_time = 0  # Shallow time in deciseconds
        self._inspection_time = 15  # Shallow time in seconds
        self._time = 0.0

        self._inspection_exit_event = threading.Event()
        self._timing_exit_event = threading.Event()

    def is_running(self):
        return self._running

    def is_inspecting(self):
        return self._inspecting

    def start(self):
        if not self._inspecting:
            if self.with_inspection:
                self._inspecting = True

            self._running = True
            threading.Thread(target=self._run, daemon=True).start()
        else:
            self._inspecting = False
            self._inspection_exit_event.set()

    def stop(self):
        self._running = False
        self._timing_exit_event.set()
        self._reset()

    def _reset(self):
        self._shallow_time = 0
        self._inspection_time = 15
        self._inspection_exit_event.clear()
        self._timing_exit_event.clear()

    def _run(self):
        logging.debug("Started timer thread")

        # If inspection is enabled, do this first
        if self.with_inspection:
            # Set variable before loop so that it displays 15
            self._variable.set(str(self._inspection_time))

            while self._inspecting:
                self._inspection_exit_event.wait(0.98)
                self._inspection_time -= 1
                if self._inspection_time >= 0:
                    self._variable.set(str(self._inspection_time))

        start_time = default_timer()

        while self._running:
            self._timing_exit_event.wait(0.098)
            self._shallow_time += 1
            self._variable.set("{:.1f}".format(self._shallow_time / 10))

        stop_time = default_timer()
        actual_time = "{:.2f}".format(stop_time - start_time)
        self._variable.set(actual_time)
        logging.debug(actual_time)
