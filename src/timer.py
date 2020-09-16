import time
import threading
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

    def stop(self):
        self._running = False
        self.reset()

    def reset(self):
        self._shallow_time = 0
        self._inspection_time = 15

    def _run(self):
        print("Started timer thread")

        # If inspection is enabled, do this first
        if self.with_inspection:
            while self._inspecting:
                self._inspection_time -= 1
                if self._inspection_time >= 0:
                    self._variable.set(str(self._inspection_time))
                time.sleep(0.98)

        start_time = default_timer()

        while self._running:
            self._shallow_time += 1
            self._variable.set("{:.1f}".format(self._shallow_time / 10.0))
            time.sleep(0.098)

        stop_time = default_timer()
        actual_time = "{:.2f}".format(stop_time - start_time)
        self._variable.set(actual_time)
        print(actual_time)
