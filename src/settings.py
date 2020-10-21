import json
import logging
import tkinter as tk
from tkinter import messagebox
from tkinter import colorchooser
from tkinter import filedialog
from typing import Callable, Tuple

from src.session import FileCorruptedError
from src.data import DATA_PATH, DEFAULT_BACKGROUND_COLOR, DEFAULT_TIMER_SIZE, DEFAULT_SCRAMBLE_SIZE, recreate_data_file
from src.timer import DEFAULT_READY_COLOR, DEFAULT_INSPECTION_COLOR


class Settings(tk.Frame):

    def __init__(self, top_level: tk.Toplevel, on_apply: Callable[[int, int, bool, str, str, bool, str, str, str], None],
                 x: int, y: int):
        super().__init__(top_level)
        self.top_level = top_level
        self.on_apply = on_apply
        self.pack(padx=10, pady=10, expand=True)

        self.top_level.title("Settings")
        self.top_level.geometry(f"+{x}+{y}")

        tk.Label(self, text="Timer size").grid(row=0, column=0, sticky="s")
        tk.Label(self, text="Scramble size").grid(row=1, column=0, sticky="s")

        error = False

        try:
            timer_size, scramble_size, enable_inspection, background_color, foreground_color, \
                enable_backup, backup_path, ready_color, inspection_color = get_settings()
        except FileNotFoundError:
            messagebox.showerror("Data Error", "The data file was missing.", parent=self.top_level)
            error = True
        except FileCorruptedError:
            messagebox.showerror("Data Error", "The data file was corrupted.", parent=self.top_level)
            error = True
        except KeyError:
            messagebox.showerror("Data Error", "Missing entry in data file.", parent=self.top_level)
            error = True

        if error:
            timer_size = DEFAULT_TIMER_SIZE
            scramble_size = DEFAULT_SCRAMBLE_SIZE
            enable_inspection = True
            background_color = DEFAULT_BACKGROUND_COLOR
            foreground_color = "#000000"
            enable_backup = False
            backup_path = ""
            ready_color = DEFAULT_READY_COLOR
            inspection_color = DEFAULT_INSPECTION_COLOR

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
        frm_color.grid(row=4, column=0, columnspan=2, pady=(0, 14))

        tk.Label(frm_color, text="Background color").grid(row=0, column=0, padx=(0, 8))
        tk.Label(frm_color, text="Foreground color").grid(row=1, column=0, padx=(0, 8))
        tk.Label(frm_color, text="Timer ready color").grid(row=2, column=0, padx=(0, 8))
        tk.Label(frm_color, text="Timer inspection color").grid(row=3, column=0, padx=(0, 8))

        self.var_background_color = tk.StringVar(frm_color, value=background_color)
        self.var_foreground_color = tk.StringVar(frm_color, value=foreground_color)
        self.var_ready_color = tk.StringVar(frm_color, value=ready_color)
        self.var_inspection_color = tk.StringVar(frm_color, value=inspection_color)

        self.btn_background_color = tk.Button(frm_color, text=self.var_background_color.get(),
                                              command=self.choose_background_color)
        self.btn_background_color.grid(row=0, column=1)

        self.btn_foreground_color = tk.Button(frm_color, text=self.var_foreground_color.get(),
                                              command=self.choose_foreground_color)
        self.btn_foreground_color.grid(row=1, column=1)

        self.btn_ready_color = tk.Button(frm_color, text=self.var_ready_color.get(), command=self.choose_ready_color)
        self.btn_ready_color.grid(row=2, column=1)

        self.btn_inspection_color = tk.Button(frm_color, text=self.var_inspection_color.get(),
                                              command=self.choose_inspection_color)
        self.btn_inspection_color.grid(row=3, column=1)

        # Default background (maybe): 240, 240, 237

        frm_backup = tk.Frame(self)
        frm_backup.grid(row=5, column=0, columnspan=2)

        self.var_enable_backup = tk.BooleanVar(frm_backup, value=enable_backup)
        self.var_backup_path = tk.StringVar(frm_backup, value=backup_path)
        tk.Checkbutton(frm_backup, text="Enable backup", variable=self.var_enable_backup) \
            .grid(row=0, column=0, padx=(0, 8))

        backup_path = self.var_backup_path.get()
        button_text = backup_path if backup_path else "<path>"
        self.btn_backup_path = tk.Button(frm_backup, text=button_text, command=self.choose_backup_path,
                                         font="Times, 7", wraplength=120)
        self.btn_backup_path.grid(row=0, column=1)

        frm_buttons = tk.Frame(self)
        frm_buttons.grid(row=6, column=0, columnspan=2, pady=(12, 0))

        tk.Button(frm_buttons, text="Reset to default", command=self.default).grid(row=0, column=0)
        tk.Button(frm_buttons, text="Apply", command=self.apply).grid(row=0, column=1, padx=(6, 0))
        tk.Button(frm_buttons, text="Cancel", command=self.top_level.destroy).grid(row=0, column=2, padx=(6, 0))

    def choose_background_color(self):
        color: tuple = colorchooser.askcolor(title="Background Color", initialcolor=self.var_background_color.get(),
                                             parent=self.top_level)
        if color[1] is not None:  # If the user didn't press cancel
            self.var_background_color.set(color[1])
            self.btn_background_color.configure(text=self.var_background_color.get())

    def choose_foreground_color(self):
        color: tuple = colorchooser.askcolor(title="Foreground Color", initialcolor=self.var_foreground_color.get(),
                                             parent=self.top_level)
        if color[1] is not None:  # If the user didn't press cancel
            self.var_foreground_color.set(color[1])
            self.btn_foreground_color.configure(text=self.var_foreground_color.get())

    def choose_backup_path(self):
        directory: str = filedialog.askdirectory(parent=self.top_level)
        if directory:  # If the user didn't press cancel
            self.var_backup_path.set(directory)
            self.btn_backup_path.configure(text=directory)

    def choose_ready_color(self):
        color: tuple = colorchooser.askcolor(title="Timer Ready Color", initialcolor=self.var_ready_color.get(),
                                             parent=self.top_level)
        if color[1] is not None:  # If the user didn't press cancel
            self.var_ready_color.set(color[1])
            self.btn_ready_color.configure(text=self.var_ready_color.get())

    def choose_inspection_color(self):
        color: tuple = colorchooser.askcolor(title="Timer Inspection Color", initialcolor=self.var_inspection_color.get(),
                                             parent=self.top_level)
        if color[1] is not None:  # If the user didn't press cancel
            self.var_inspection_color.set(color[1])
            self.btn_inspection_color.configure(text=self.var_inspection_color.get())

    def apply(self):
        timer_size = self.scl_timer_size.get()
        scramble_size = self.scl_scramble_size.get()
        enable_inspection = self.var_enable_inspection.get()

        hex_background = self.var_background_color.get()
        hex_foreground = self.var_foreground_color.get()

        enable_backup = self.var_enable_backup.get()
        backup_path = self.var_backup_path.get()

        hex_ready = self.var_ready_color.get()
        hex_inspection = self.var_inspection_color.get()

        self.on_apply(timer_size, scramble_size, enable_inspection, hex_background, hex_foreground,
                      enable_backup, backup_path, hex_ready, hex_inspection)
        self.write_settings(timer_size, scramble_size, enable_inspection, hex_background, hex_foreground,
                            enable_backup, backup_path, hex_ready, hex_inspection)
        self.top_level.destroy()

    def default(self):
        if messagebox.askyesno("Revert To Default", "Are you sure you want to revert to default settings?",
                               parent=self.top_level):
            self.scl_timer_size.set(DEFAULT_TIMER_SIZE)
            self.scl_scramble_size.set(DEFAULT_SCRAMBLE_SIZE)
            self.var_enable_inspection.set(True)

            self.var_background_color.set(DEFAULT_BACKGROUND_COLOR)
            self.var_foreground_color.set("#000000")
            self.var_ready_color.set(DEFAULT_READY_COLOR)
            self.var_inspection_color.set(DEFAULT_INSPECTION_COLOR)

            self.btn_background_color.configure(text=DEFAULT_BACKGROUND_COLOR)
            self.btn_foreground_color.configure(text="#000000")
            self.btn_ready_color.configure(text=DEFAULT_READY_COLOR)
            self.btn_inspection_color.configure(text=DEFAULT_INSPECTION_COLOR)

            self.var_enable_backup.set(False)
            self.var_backup_path.set("")
            self.btn_backup_path.configure(text="<path>")

    def write_settings(self, timer_size: int, scramble_size: int, enable_inspection: bool, background_color: str,
                       foreground_color: str, enable_backup: bool, backup_path: str, ready_color: str,
                       inspection_color: str):
        try:
            with open(DATA_PATH, "r+") as file:
                contents = json.load(file)

                file.seek(0)

                contents["timer_size"] = timer_size
                contents["scramble_size"] = scramble_size
                contents["enable_inspection"] = enable_inspection
                contents["background_color"] = background_color
                contents["foreground_color"] = foreground_color
                contents["enable_backup"] = enable_backup
                contents["backup_path"] = backup_path
                contents["ready_color"] = ready_color
                contents["inspection_color"] = inspection_color

                json.dump(contents, file, indent=2)
                file.truncate()
        except FileNotFoundError:
            logging.error("Data file was missing")
            recreate_data_file()
            messagebox.showerror("Data Error", "The data file was missing.", parent=self.top_level)
        except json.decoder.JSONDecodeError:
            logging.error("Data file was somehow corrupted")
            recreate_data_file()
            messagebox.showerror("Data Error", "The data file was corrupted.", parent=self.top_level)


def get_settings() -> Tuple[int, int, bool, str, str, bool, str, str, str]:
    try:
        with open(DATA_PATH, "r") as file:
            contents = json.load(file)
    except FileNotFoundError:
        logging.error("Data file was missing")
        recreate_data_file()
        raise
    except json.decoder.JSONDecodeError:
        logging.error("Data file was somehow corrupted")
        recreate_data_file()
        raise FileCorruptedError

    try:
        return contents["timer_size"], contents["scramble_size"], contents["enable_inspection"], \
            contents["background_color"], contents["foreground_color"], contents["enable_backup"], contents["backup_path"], \
            contents["ready_color"], contents["inspection_color"]
    except KeyError as err:
        logging.error(f"Missing entry: {err}")
        recreate_data_file()
        raise
