import json
import logging
import tkinter as tk
from tkinter import messagebox
from typing import Callable, Tuple

from src.data import DATA_PATH, recreate_data_file


class Settings(tk.Frame):

    def __init__(self, top_level: tk.Toplevel, on_apply: Callable[[int, int, bool], None]):
        super().__init__(top_level)
        self.top_level = top_level
        self.on_apply = on_apply
        self.pack(padx=10, pady=10, expand=True)

        self.top_level.title("Settings")

        tk.Label(self, text="Timer size").grid(row=0, column=0, sticky="S")
        tk.Label(self, text="Scramble size").grid(row=1, column=0, sticky="S")

        try:
            timer_size, scramble_size, enable_inspection = get_settings()
        except FileNotFoundError:
            messagebox.showerror("Data Error", "The data file was missing.", parent=self.top_level)
            timer_size = 120; scramble_size = 26; enable_inspection = True
        except ValueError:
            messagebox.showerror("Data Error", "The data file was corrupted.", parent=self.top_level)
            timer_size = 120; scramble_size = 26; enable_inspection = True
        except KeyError:
            messagebox.showerror("Data Error", "Missing entry in data file.", parent=self.top_level)
            timer_size = 120; scramble_size = 26; enable_inspection = True

        self.scl_timer_size = tk.Scale(self, from_=50, to=180, resolution=2, orient="horizontal")
        self.scl_timer_size.grid(row=0, column=1)
        self.scl_timer_size.set(timer_size)

        self.scl_scramble_size = tk.Scale(self, from_=16, to=60, resolution=2, orient="horizontal")
        self.scl_scramble_size.grid(row=1, column=1)
        self.scl_scramble_size.set(scramble_size)

        self.var_enable_inspection = tk.BooleanVar(self, value=enable_inspection)
        tk.Checkbutton(self, text="Enable inspection", variable=self.var_enable_inspection) \
            .grid(row=3, column=0, columnspan=2, pady=(10, 10))

        frm_buttons = tk.Frame(self)
        frm_buttons.grid(row=4, column=0, columnspan=2)

        tk.Button(frm_buttons, text="Reset to deafult", command=self.default).grid(row=0, column=0)
        tk.Button(frm_buttons, text="Apply", command=self.apply).grid(row=0, column=1, padx=(6, 0))

    def apply(self):
        timer_size = self.scl_timer_size.get()
        scramble_size = self.scl_scramble_size.get()
        enable_inspection = self.var_enable_inspection.get()

        self.on_apply(timer_size, scramble_size, enable_inspection)
        self.write_settings(timer_size, scramble_size, enable_inspection)
        self.top_level.destroy()

    def default(self):
        if messagebox.askyesno("Revert To Default", "Are you sure you want to revert to default settings?",
                               parent=self.top_level):
            self.scl_timer_size.set(120)
            self.scl_scramble_size.set(26)
            self.var_enable_inspection.set(True)

    def write_settings(self, timer_size: int, scramble_size: int, enable_inspection: bool):
        try:
            with open(DATA_PATH, "r+") as file:
                contents = json.load(file)

                file.seek(0)

                contents["timer_size"] = timer_size
                contents["scramble_size"] = scramble_size
                contents["enable_inspection"] = enable_inspection

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


def get_settings() -> Tuple[int, int, bool]:
    try:
        with open(DATA_PATH, "r") as file:
            contents = json.load(file)
    except FileNotFoundError:
        recreate_data_file()
        logging.error("Data file was missing")
        raise ValueError
    except json.decoder.JSONDecodeError:
        recreate_data_file()
        logging.error("Data file was somehow corrupted")
        raise

    try:
        return contents["timer_size"], contents["scramble_size"], contents["enable_inspection"]
    except KeyError as err:
        recreate_data_file()
        logging.error(f"Missing entry: {err}")
        raise
