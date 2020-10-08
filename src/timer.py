import threading
import logging
import math
import sys
import tkinter as tk
from timeit import default_timer

import src.globals

DEFAULT_READY_COLOR = "green"
DEFAULT_INSPECTION_COLOR = "red"


class Timer:

    if sys.platform == "win32":
        WAIT_TIME_INSPECTION = 0.97
        WAIT_TIME_SOLVE = 0.097
    else:
        WAIT_TIME_INSPECTION = 0.99
        WAIT_TIME_SOLVE = 0.099

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
        self._inspecting = False
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
                self._inspection_exit_event.wait(Timer.WAIT_TIME_INSPECTION)
                self._inspection_time -= 1
                if self._inspection_time >= 0:
                    self._variable.set(str(self._inspection_time))

        start_time = default_timer()

        while self._running:
            self._timing_exit_event.wait(Timer.WAIT_TIME_SOLVE)
            self._shallow_time += 1
            self._variable.set(Timer._format_time_deciseconds(self._shallow_time))

        stop_time = default_timer()
        actual_time = format_time_seconds(stop_time - start_time + 0.05)
        self._variable.set(actual_time)
        if not src.globals.pressed_escape:
            src.globals.can_save_solve_now = True
        src.globals.pressed_escape = False

        logging.debug(f"Actual time: {actual_time}")

    @staticmethod
    def _format_time_deciseconds(time: int) -> str:
        """
        Turns into this: 0:00.0

        """
        in_minutes = time / 10
        fractional, whole = math.modf(in_minutes)

        minutes = int(whole // 60)
        if minutes:
            seconds = f"{int(whole) % 60}".zfill(2)
        else:
            seconds = f"{int(whole) % 60}"
        deciseconds = f"{fractional:.1f}"[2:3]

        if minutes:
            return f"{minutes}:{seconds}.{deciseconds}"
        else:
            return f"{seconds}.{deciseconds}"


def format_time_seconds(time: float) -> str:
    """
    Turns into this: 0:00.00

    """
    if time == math.inf:
        return "inf"

    fractional, whole = math.modf(time)

    minutes = int(whole // 60)
    if minutes:
        seconds = f"{int(whole) % 60}".zfill(2)
    else:
        seconds = f"{int(whole) % 60}"
    deciseconds = f"{fractional:0.2f}"[2:4]

    if minutes:
        return f"{minutes}:{seconds}.{deciseconds}"
    else:
        return f"{seconds}.{deciseconds}"


def interpret_time_in_seconds(time: str) -> float:
    """
    time is for example 1:17.30

    """
    if time == "inf":
        return math.inf

    colon = time.find(":")
    dot = time.find(".")

    if colon != -1:
        minutes = int(time[0:colon])
        seconds = int(time[colon + 1:dot])
    else:
        seconds = int(time[0:dot])

    deciseconds = float("0." + time[dot + 1:])

    if colon != -1:
        return minutes * 60 + seconds + deciseconds
    else:
        return seconds + deciseconds
