import json
import logging
import tkinter as tk
from tkinter import messagebox
from typing import Callable, Tuple, Union

from src.data import DATA_PATH, recreate_data_file


class Settings(tk.Frame):

    def __init__(self, top_level: tk.Toplevel, on_apply: Callable[[int, int, bool, str, str], None]):
        super().__init__(top_level)
        self.top_level = top_level
        self.on_apply = on_apply
        self.pack(padx=10, pady=10, expand=True)

        self.top_level.title("Settings")

        tk.Label(self, text="Timer size").grid(row=0, column=0, sticky="S")
        tk.Label(self, text="Scramble size").grid(row=1, column=0, sticky="S")

        try:
            timer_size, scramble_size, enable_inspection, background_color, foreground_color = get_settings()
        except FileNotFoundError:
            messagebox.showerror("Data Error", "The data file was missing.", parent=self.top_level)
            timer_size = 120; scramble_size = 28; enable_inspection = True
            background_color = [240, 240, 237]; foreground_color = [0, 0, 0]
        except json.decoder.JSONDecodeError:
            messagebox.showerror("Data Error", "The data file was corrupted.", parent=self.top_level)
            timer_size = 120; scramble_size = 28; enable_inspection = True
            background_color = [240, 240, 237]; foreground_color = [0, 0, 0]
        except KeyError:
            messagebox.showerror("Data Error", "Missing entry in data file.", parent=self.top_level)
            timer_size = 120; scramble_size = 28; enable_inspection = True
            background_color = [240, 240, 237]; foreground_color = [0, 0, 0]

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

        self.ent_back_red = tk.Entry(frm_color, width=4)
        self.ent_back_red.grid(row=0, column=1)
        self.ent_back_green = tk.Entry(frm_color, width=4)
        self.ent_back_green.grid(row=0, column=2)
        self.ent_back_blue = tk.Entry(frm_color, width=4)
        self.ent_back_blue.grid(row=0, column=3)

        self.ent_forg_red = tk.Entry(frm_color, width=4)
        self.ent_forg_red.grid(row=1, column=1)
        self.ent_forg_green = tk.Entry(frm_color, width=4)
        self.ent_forg_green.grid(row=1, column=2)
        self.ent_forg_blue = tk.Entry(frm_color, width=4)
        self.ent_forg_blue.grid(row=1, column=3)

        self.ent_back_red.insert("end", background_color[0])
        self.ent_back_green.insert("end", background_color[1])
        self.ent_back_blue.insert("end", background_color[2])

        self.ent_forg_red.insert("end", foreground_color[0])
        self.ent_forg_green.insert("end", foreground_color[1])
        self.ent_forg_blue.insert("end", foreground_color[2])

        # Default background (maybe): 240, 240, 237

        frm_buttons = tk.Frame(self)
        frm_buttons.grid(row=5, column=0, columnspan=2, pady=(8, 0))

        tk.Button(frm_buttons, text="Reset to deafult", command=self.default).grid(row=0, column=0)
        tk.Button(frm_buttons, text="Apply", command=self.apply).grid(row=0, column=1, padx=(6, 0))
        tk.Button(frm_buttons, text="Cancel", command=self.top_level.destroy).grid(row=0, column=2, padx=(6, 0))

    @staticmethod
    def constrain(x: str):
        x = int(x)
        if x < 0 or x > 255:
            raise ValueError
        return x

    def apply(self):
        timer_size = self.scl_timer_size.get()
        scramble_size = self.scl_scramble_size.get()
        enable_inspection = self.var_enable_inspection.get()
        try:
            background_color = (Settings.constrain(self.ent_back_red.get()),
                                Settings.constrain(self.ent_back_green.get()),
                                Settings.constrain(self.ent_back_blue.get()))
            foreground_color = (Settings.constrain(self.ent_forg_red.get()),
                                Settings.constrain(self.ent_forg_green.get()),
                                Settings.constrain(self.ent_forg_blue.get()))
        except ValueError:
            messagebox.showerror("Invalid Color Value", "Please insert color values between 0 and 255.",
                                 parent=self.top_level)
            return

        hex_background = rgb_to_hex(background_color)
        hex_foreground = rgb_to_hex(foreground_color)

        self.on_apply(timer_size, scramble_size, enable_inspection, hex_background, hex_foreground)
        self.write_settings(timer_size, scramble_size, enable_inspection, background_color, foreground_color)
        self.top_level.destroy()

    def default(self):
        if messagebox.askyesno("Revert To Default", "Are you sure you want to revert to default settings?",
                               parent=self.top_level):
            self.scl_timer_size.set(120)
            self.scl_scramble_size.set(28)
            self.var_enable_inspection.set(True)

            self.ent_back_red.delete(0, "end")
            self.ent_back_green.delete(0, "end")
            self.ent_back_blue.delete(0, "end")
            self.ent_forg_red.delete(0, "end")
            self.ent_forg_green.delete(0, "end")
            self.ent_forg_blue.delete(0, "end")

            self.ent_back_red.insert("end", "240")
            self.ent_back_green.insert("end", "240")
            self.ent_back_blue.insert("end", "237")
            self.ent_forg_red.insert("end", "0")
            self.ent_forg_green.insert("end", "0")
            self.ent_forg_blue.insert("end", "0")

    def write_settings(self, timer_size: int, scramble_size: int, enable_inspection: bool, background_color: tuple,
                       foreground_color: tuple):
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


def get_settings() -> Tuple[int, int, bool, list, list]:
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


def rgb_to_hex(color: Union[tuple, list]) -> str:
    return "#%02x%02x%02x" % (color[0], color[1], color[2])
