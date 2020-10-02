import json
import logging
import tkinter as tk
from tkinter import messagebox
from tkinter import colorchooser
from typing import Callable, Tuple, Union

from src.data import DATA_PATH, DEFAULT_BACKGROUND_COLOR, DEFAULT_TIMER_SIZE, DEFAULT_SCRAMBLE_SIZE, recreate_data_file


class Settings(tk.Frame):

    def __init__(self, top_level: tk.Toplevel, on_apply: Callable[[int, int, bool, str, str], None]):
        super().__init__(top_level)
        self.top_level = top_level
        self.on_apply = on_apply
        self.pack(padx=10, pady=10, expand=True)

        self.top_level.title("Settings")

        tk.Label(self, text="Timer size").grid(row=0, column=0, sticky="s")
        tk.Label(self, text="Scramble size").grid(row=1, column=0, sticky="s")

        try:
            timer_size, scramble_size, enable_inspection, background_color, foreground_color = get_settings()
        except FileNotFoundError:
            messagebox.showerror("Data Error", "The data file was missing.", parent=self.top_level)
            timer_size = DEFAULT_TIMER_SIZE; scramble_size = DEFAULT_SCRAMBLE_SIZE; enable_inspection = True
            background_color = DEFAULT_BACKGROUND_COLOR; foreground_color = "#000000"
        except json.decoder.JSONDecodeError:
            messagebox.showerror("Data Error", "The data file was corrupted.", parent=self.top_level)
            timer_size = DEFAULT_TIMER_SIZE; scramble_size = DEFAULT_SCRAMBLE_SIZE; enable_inspection = True
            background_color = DEFAULT_BACKGROUND_COLOR; foreground_color = "#000000"
        except KeyError:
            messagebox.showerror("Data Error", "Missing entry in data file.", parent=self.top_level)
            timer_size = DEFAULT_TIMER_SIZE; scramble_size = DEFAULT_SCRAMBLE_SIZE; enable_inspection = True
            background_color = DEFAULT_BACKGROUND_COLOR; foreground_color = "#000000"

        self.scl_timer_size = tk.Scale(self, from_=50, to=180, resolution=2, orient="horizontal")
        self.scl_timer_size.grid(row=0, column=1)
        self.scl_timer_size.set(timer_size)

        self.scl_scramble_size = tk.Scale(self, from_=16, to=60, resolution=2, orient="horizontal")
        self.scl_scramble_size.grid(row=1, column=1)
        self.scl_scramble_size.set(scramble_size)

        self.var_enable_inspection = tk.BooleanVar(self, value=enable_inspection)
        tk.Checkbutton(self, text="Enable inspection", variable=self.var_enable_inspection) \
            .grid(row=3, column=0, columnspan=2, pady=(10, 10))

        frm_color = tk.Frame(self)
        frm_color.grid(row=4, column=0, columnspan=2)

        tk.Label(frm_color, text="Background color").grid(row=0, column=0, padx=(0, 8))
        tk.Label(frm_color, text="Foreground color").grid(row=1, column=0, padx=(0, 8))

        self.var_background_color = tk.StringVar(frm_color, value=background_color)
        tk.Label(frm_color, textvariable=self.var_background_color).grid(row=0, column=1, padx=(0, 8))

        self.var_foreground_color = tk.StringVar(frm_color, value=foreground_color)
        tk.Label(frm_color, textvariable=self.var_foreground_color).grid(row=1, column=1, padx=(0, 8))

        tk.Button(frm_color, text="Change", command=self.choose_background_color).grid(row=0, column=2)
        tk.Button(frm_color, text="Change", command=self.choose_foreground_color).grid(row=1, column=2)

        # Default background (maybe): 240, 240, 237

        frm_buttons = tk.Frame(self)
        frm_buttons.grid(row=5, column=0, columnspan=2, pady=(12, 0))

        tk.Button(frm_buttons, text="Reset to deafult", command=self.default).grid(row=0, column=0)
        tk.Button(frm_buttons, text="Apply", command=self.apply).grid(row=0, column=1, padx=(6, 0))
        tk.Button(frm_buttons, text="Cancel", command=self.top_level.destroy).grid(row=0, column=2, padx=(6, 0))

    def choose_background_color(self):
        color: tuple = colorchooser.askcolor(title="Background Color", parent=self.top_level)
        if color[1] is not None:  # If the user didn't press cancel
            self.var_background_color.set(color[1])

    def choose_foreground_color(self):
        color: tuple = colorchooser.askcolor(title="Foreground Color", parent=self.top_level)
        if color[1] is not None:  # If the user didn't press cancel
            self.var_foreground_color.set(color[1])

    def apply(self):
        timer_size = self.scl_timer_size.get()
        scramble_size = self.scl_scramble_size.get()
        enable_inspection = self.var_enable_inspection.get()

        hex_background = self.var_background_color.get()
        hex_foreground = self.var_foreground_color.get()

        self.on_apply(timer_size, scramble_size, enable_inspection, hex_background, hex_foreground)
        self.write_settings(timer_size, scramble_size, enable_inspection, hex_background, hex_foreground)
        self.top_level.destroy()

    def default(self):
        if messagebox.askyesno("Revert To Default", "Are you sure you want to revert to default settings?",
                               parent=self.top_level):
            self.scl_timer_size.set(DEFAULT_TIMER_SIZE)
            self.scl_scramble_size.set(DEFAULT_SCRAMBLE_SIZE)
            self.var_enable_inspection.set(True)

            self.var_background_color.set(DEFAULT_BACKGROUND_COLOR)
            self.var_foreground_color.set("#000000")

    def write_settings(self, timer_size: int, scramble_size: int, enable_inspection: bool, background_color: str,
                       foreground_color: str):
        try:
            with open(DATA_PATH, "r+") as file:
                contents = json.load(file)

                file.seek(0)

                contents["timer_size"] = timer_size
                contents["scramble_size"] = scramble_size
                contents["enable_inspection"] = enable_inspection
                contents["background_color"] = background_color
                contents["foreground_color"] = foreground_color

                json.dump(contents, file, indent=2)
                file.truncate()
        except FileNotFoundError:
            recreate_data_file()
            logging.error("Data file was missing")
            messagebox.showerror("Data Error", "The data file was missing.", parent=self.top_level)
        except json.decoder.JSONDecodeError:
            recreate_data_file()
            logging.error("Data file was somehow corrupted")
            messagebox.showerror("Data Error", "The data file was corrupted.", parent=self.top_level)


def get_settings() -> Tuple[int, int, bool, str, str]:
    try:
        with open(DATA_PATH, "r") as file:
            contents = json.load(file)
    except FileNotFoundError:
        recreate_data_file()
        logging.error("Data file was missing")
        raise
    except json.decoder.JSONDecodeError:
        recreate_data_file()
        logging.error("Data file was somehow corrupted")
        raise

    try:
        return contents["timer_size"], contents["scramble_size"], contents["enable_inspection"], \
               contents["background_color"], contents["foreground_color"]
    except KeyError as err:
        recreate_data_file()
        logging.error(f"Missing entry: {err}")
        raise
