import logging
import time
import threading
import datetime
import copy
import tkinter as tk
from tkinter import messagebox
from typing import Optional

import src.globals
from src.timer import Timer, interpret_time_in_seconds, format_time_seconds
from src.scramble import generate_scramble
from src.session import create_new_session, dump_data, SessionData, Solve, remember_last_session, get_last_session, \
    load_session_data, remove_solve_out_of_session, rename_session, destroy_session
from src.select_session import SelectSession, Mode
from src.settings import Settings, get_settings
from src.data import data_folder_exists, recreate_data_folder, DEFAULT_BACKGROUND_COLOR, DEFAULT_TIMER_SIZE, \
    DEFAULT_SCRAMBLE_SIZE
from src.about import About
from src.plot import plot

logging.basicConfig(level=logging.DEBUG, format="%(levelname)s:%(lineno)d:%(message)s")
if not __debug__:
    logging.disable()


class MainApplication(tk.Frame):

    def __init__(self, root: tk.Tk):
        super().__init__(root)
        self.root = root
        self.pack(fill="both", expand=True)
        self.columnconfigure(0, weight=0)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=0)
        self.rowconfigure(1, weight=1)

        self.root.option_add("*tearOff", False)
        self.root.title("Py-Cube-Timer")
        self.root.wm_protocol("WM_DELETE_WINDOW", self.exit)
        self.root.geometry("1024x576")

        # Main menu
        men_file = tk.Menu(self)
        men_file.add_command(label="New Session", command=self.new_session)
        men_file.add_command(label="Open Session", command=self.open_session)
        men_file.add_command(label="See Statistics", command=self.see_statistics)
        men_file.add_command(label="Exit", command=self.exit)

        men_edit = tk.Menu(self)
        men_edit.add_command(label="Remove Last Solve", command=self.remove_last_solve_out_of_session)
        men_edit.add_command(label="Rename This Session", command=self.rename_this_session)
        men_edit.add_command(label="Delete This Session", command=self.delete_this_session)
        men_edit.add_command(label="Settings", command=self.settings)

        men_help = tk.Menu(self)
        men_help.add_command(label="Info", command=None)
        men_help.add_command(label="About", command=self.about)

        men_main = tk.Menu(self)
        men_main.add_cascade(label="File", menu=men_file)
        men_main.add_cascade(label="Edit", menu=men_edit)
        men_main.add_cascade(label="Help", menu=men_help)
        self.root.configure(menu=men_main)

        # Main frames
        frm_left_side = tk.Frame(self, relief="ridge", bd=3)
        frm_left_side.grid(row=0, column=0, rowspan=2, sticky="wns")
        frm_left_side.rowconfigure(3, weight=1)

        frm_scramble = tk.Frame(self, relief="ridge", bd=3)
        frm_scramble.grid(row=0, column=1, sticky="wen")

        frm_timer = tk.Frame(self)
        frm_timer.grid(row=1, column=1)

        # Get settings from data
        try:
            timer_size, scramble_size, enable_inspection, background_color, foreground_color = get_settings()
        except FileNotFoundError:
            messagebox.showerror("Data Error", "The data file was missing.", parent=self.root)
            timer_size = DEFAULT_TIMER_SIZE; scramble_size = DEFAULT_SCRAMBLE_SIZE; enable_inspection = True
            background_color = DEFAULT_BACKGROUND_COLOR; foreground_color = "#000000"
        except ValueError:
            messagebox.showerror("Data Error", "The data file was corrupted.", parent=self.root)
            timer_size = DEFAULT_TIMER_SIZE; scramble_size = DEFAULT_SCRAMBLE_SIZE; enable_inspection = True
            background_color = DEFAULT_BACKGROUND_COLOR; foreground_color = "#000000"
        except KeyError:
            messagebox.showerror("Data Error", "Missing entry in data file.", parent=self.root)
            timer_size = DEFAULT_TIMER_SIZE; scramble_size = DEFAULT_SCRAMBLE_SIZE; enable_inspection = True
            background_color = DEFAULT_BACKGROUND_COLOR; foreground_color = "#000000"

        self.root.tk_setPalette(background=background_color, foreground=foreground_color)

        # Scramble area
        self.var_scramble = tk.StringVar(frm_scramble, value=generate_scramble())
        self.lbl_scramble = tk.Label(frm_scramble, textvariable=self.var_scramble, font=f"Times, {scramble_size}")
        self.lbl_scramble.pack()

        frm_scramble.bind("<Configure>", self.on_window_resize)

        # Left side area
        # Session name
        self.var_session_name = tk.StringVar(frm_left_side, value="")
        lbl_session_name = tk.Label(frm_left_side, textvariable=self.var_session_name, font="Times, 15")
        lbl_session_name.grid(row=0, column=0, pady=(0, 6))

        # Statistics
        frm_statistics = tk.Frame(frm_left_side)
        frm_statistics.grid(row=1, column=0)

        lbl_current = tk.Label(frm_statistics, text="current", font="Times, 14")
        lbl_current.grid(row=0, column=1)

        lbl_best = tk.Label(frm_statistics, text="best", font="Times, 14")
        lbl_best.grid(row=0, column=2)

        lbl_time = tk.Label(frm_statistics, text="time", font="Times, 14")
        lbl_time.grid(row=1, column=0)

        lbl_ao5 = tk.Label(frm_statistics, text="ao5", font="Times, 14")
        lbl_ao5.grid(row=2, column=0)

        lbl_ao12 = tk.Label(frm_statistics, text="ao12", font="Times, 14")
        lbl_ao12.grid(row=3, column=0)

        self.var_current_time = tk.StringVar(frm_statistics, value="n/a")
        lbl_current_time = tk.Label(frm_statistics, textvariable=self.var_current_time, font="Times, 14")
        lbl_current_time.grid(row=1, column=1)

        self.var_current_ao5 = tk.StringVar(frm_statistics, value="n/a")
        lbl_current_ao5 = tk.Label(frm_statistics, textvariable=self.var_current_ao5, font="Times, 14")
        lbl_current_ao5.grid(row=2, column=1)

        self.var_current_ao12 = tk.StringVar(frm_statistics, value="n/a")
        lbl_current_ao12 = tk.Label(frm_statistics, textvariable=self.var_current_ao12, font="Times, 14")
        lbl_current_ao12.grid(row=3, column=1)

        self.var_best_time = tk.StringVar(frm_statistics, value="n/a")
        lbl_best_time = tk.Label(frm_statistics, textvariable=self.var_best_time, font="Times, 14")
        lbl_best_time.grid(row=1, column=2)

        self.var_best_ao5 = tk.StringVar(frm_statistics, value="n/a")
        lbl_best_ao5 = tk.Label(frm_statistics, textvariable=self.var_best_ao5, font="Times, 14")
        lbl_best_ao5.grid(row=2, column=2)

        self.var_best_ao12 = tk.StringVar(frm_statistics, value="n/a")
        lbl_best_ao12 = tk.Label(frm_statistics, textvariable=self.var_best_ao12, font="Times, 14")
        lbl_best_ao12.grid(row=3, column=2)

        # Session mean
        self.var_session_mean = tk.StringVar(frm_left_side, value="n/a")
        lbl_session_mean = tk.Label(frm_left_side, textvariable=self.var_session_mean, font="Times, 20")

        lbl_session_mean.grid(row=2, column=0, pady=6)

        # Times
        frm_times = tk.Frame(frm_left_side)
        frm_times.grid(row=3, column=0, sticky="ns")

        bar_times = tk.Scrollbar(frm_times, orient="vertical")
        bar_times.pack(side="right", fill="y")

        self.cvs_times = tk.Canvas(frm_times, width=140, borderwidth=0, yscrollcommand=bar_times.set)
        self.cvs_times.pack(side="left", fill="both", expand=True)

        bar_times.configure(command=self.cvs_times.yview)

        self.frm_canvas_frame = tk.Frame(frm_times)
        self.cvs_times.create_window((0, 0), window=self.frm_canvas_frame, anchor="nw")
        self.frm_canvas_frame.bind("<Configure>", lambda event: self.frame_configure())

        self.solve_index = 1
        self.MAX_SOLVES = 9998  # TODO get rid of this limitation

        # Timer area
        self.var_time = tk.StringVar(frm_timer, value="0.00")
        self.lbl_time = tk.Label(frm_timer, textvariable=self.var_time, font=f"Times, {timer_size}")
        self.lbl_time.pack()

        self.check_to_save_in_session()  # FIXME I thing I've got some problems

        self.timer = Timer(self.var_time)
        self.timer.with_inspection = enable_inspection
        self.root.bind("<KeyPress>", self.kt_report_key_press)
        self.root.bind("<KeyRelease>", self.kt_report_key_release)
        self.root.bind("<Alt-z>", self.on_alt_z_key_press)
        self.root.bind("<Escape>", self.on_escape_press)

        # Flag to handle timer start
        self.stopped_timer = False

        # Variables to fix the key repeating functionality
        # There is still the bug that there are two key presses registered, if holding down a key
        self.last_press_time = 0.0
        self.last_release_time = 0.0

        # Data class to hold a session
        self.session_data: Optional[SessionData] = None

        # Check for data folder
        if not data_folder_exists():
            logging.error("The data folder is missing")
            messagebox.showerror("No Data folder", "The data folder is missing.", parent=self.root)
            recreate_data_folder()

        # Load session; sets session_data variable
        self.load_last_session()

    def frame_configure(self):
        self.cvs_times.configure(scrollregion=self.cvs_times.bbox("all"))

    def on_window_resize(self, event):
        self.lbl_scramble.configure(wraplength=event.width)

    def on_key_press(self, event):
        if self.timer.is_running() and not self.timer.is_inspecting():
            self.timer.stop()
            self.stopped_timer = True

            logging.debug("Timer STOP")

    def on_key_release(self, event):
        if self.session_data is None:
            messagebox.showerror("No Session", "Please select or create a new session to use the timer.", parent=self.root)
            return

        if event.char == " ":
            if not self.stopped_timer:
                if not self.timer.is_running() or self.timer.is_inspecting():
                    self.timer.start()

                    logging.debug("Timer START")
            else:
                self.stopped_timer = False

    def on_alt_z_key_press(self, event):
        self.remove_last_solve_out_of_session()

    def on_escape_press(self, event):
        if self.timer.is_running():
            src.globals.pressed_escape = True
            self.timer.stop()
        self.var_time.set("0.00")

    def save_solve_in_session(self, solve_time: str):  # solve_time is already formatted
        assert self.session_data is not None

        if self.solve_index == self.MAX_SOLVES:
            messagebox.showerror("Saving Failure", "Could not save the solve, because the "
                                 "amount of solves per session was exceeded.", parent=self.root)
            return

        # Update left GUI list
        tk.Label(self.frm_canvas_frame, text=f"{self.solve_index}. {solve_time}", font="Times, 14") \
            .grid(row=self.MAX_SOLVES - self.solve_index, column=0, sticky="W")
        self.solve_index += 1

        if self.solve_index == self.MAX_SOLVES:
            messagebox.showinfo("Session Ended", "The maximum amount of solves per session has exceeded."
                                "This session is done.", parent=self.root)
            return

        # Update list
        self.session_data.solves.append(interpret_time_in_seconds(solve_time))

        self.update_statistics(self.session_data)

        assert self.session_data.name
        try:
            dump_data(self.session_data.name + ".json",
                      Solve(solve_time, self.var_scramble.get(), str(datetime.datetime.now())))
        except FileNotFoundError:
            logging.error("Could not save the solve in session, because the file is missing")
            messagebox.showerror("Saving Failure", "Could not save the solve in session, because the file is missing.",
                                 parent=self.root)
        except ValueError:
            logging.error("Could not save the solve, because the file is corrupted")
            messagebox.showerror("Saving Failure", "Could not save the solve, because the file is corrupted.",
                                 parent=self.root)
        else:
            logging.info("Saved solve")

        # Generate new scramble
        self.var_scramble.set(generate_scramble())

    def remove_last_solve_out_of_session(self):
        assert self.session_data is not None

        if not self.session_data.solves:
            messagebox.showinfo("No Solves", "There are no solves in this session.", parent=self.root)
            return

        if not messagebox.askyesno("Remove Last Solve", "Are you sure you want to remove the last solve in the session?",
                                   parent=self.root):
            return

        # Update left GUI list
        labels = self.frm_canvas_frame.winfo_children()
        assert labels
        labels[-1].destroy()
        self.solve_index -= 1

        # Update list
        del self.session_data.solves[-1]

        if self.session_data.solves:
            self.update_statistics(self.session_data)

        # Update these which don't always show
        if len(self.session_data.solves) < 5:
            self.var_current_ao5.set("n/a")
            self.var_best_ao5.set("n/a")
        elif len(self.session_data.solves) < 12:
            self.var_current_ao12.set("n/a")
            self.var_best_ao12.set("n/a")

        if not self.session_data.solves:
            self.var_current_time.set("n/a")
            self.var_best_time.set("n/a")
            self.var_session_mean.set("n/a")

        assert self.session_data.name
        try:
            remove_solve_out_of_session(self.session_data.name + ".json")
        except FileNotFoundError:
            logging.error("Could not remove the solve from the session, because the file is missing")
            messagebox.showerror("Saving Failure", "Could not remove the solve from the session, "
                                 "because the file is missing.", parent=self.root)
        except ValueError:
            logging.error("Could not remove the solve, because the file is corrupted")
            messagebox.showerror("Saving Failure", "Could not remove the solve, because the file is corrupted.",
                                 parent=self.root)

    def rename_this_session(self):
        top_level = tk.Toplevel(self.root)
        SelectSession(top_level, self.rename_session, Mode.RENAME_SESSION)

    def rename_session(self, name: str):
        try:
            rename_session(self.session_data.name, name)
        except FileNotFoundError:
            messagebox.showerror("Rename Failure", "Could not rename the session, because the file is missing.",
                                 parent=self.root)
            return

        self.session_data.name = name
        self.var_session_name.set(name)
        logging.info(f'Renamed session to "{name}"')

    def delete_this_session(self):
        if self.session_data is None:
            messagebox.showerror("No Session", "There is no session selected.", parent=self.root)
            return

        if messagebox.askyesno("Delete Session", "Are you sure you want to delete this session?", parent=self.root):
            # Fill session name
            self.var_session_name.set("")

            # Clear first
            self.clear_left_UI()

            try:
                destroy_session(self.session_data.name)
            except FileNotFoundError:
                messagebox.showerror("Deletion Failure", "Could not delete this session, "
                                     "because the file is missing (it's already deleted).", parent=self.root)

            self.session_data = None

            try:
                remember_last_session("")  # Set last session as nothing
            except FileNotFoundError:
                messagebox.showerror("Saving Failure", "Could not remember last session, because the data file is missing.",
                                     parent=self.root)
            except ValueError:
                messagebox.showerror("Saving Failure", "Could not remember last session, "
                                     "because the data file is corrupted.", parent=self.root)

    def check_to_save_in_session(self):
        if src.globals.can_save_solve_now:
            self.save_solve_in_session(self.var_time.get())
            src.globals.can_save_solve_now = False

        self.after(700, self.check_to_save_in_session)

    def exit(self):
        if self.session_data is None:
            self.root.destroy()
            return

        try:
            remember_last_session(self.session_data.name)
        except FileNotFoundError:
            messagebox.showerror("Saving Failure", "Could not remember last session, because the data file is missing.",
                                 parent=self.root)
        except ValueError:
            messagebox.showerror("Saving Failure", "Could not remember last session, because the data file is corrupted.",
                                 parent=self.root)
        else:
            logging.debug(f'Session remembered is "{self.session_data.name}"')

        self.root.destroy()

    @staticmethod
    def calculate_ao5(list_5: list) -> float:
        smallest = min(list_5)
        largest = max(list_5)

        clone = copy.copy(list_5)
        clone.remove(smallest)
        clone.remove(largest)
        return sum(clone) / 3

    @staticmethod
    def calculate_ao12(list_12: list) -> float:
        smallest = min(list_12)
        largest = max(list_12)

        clone = copy.copy(list_12)
        clone.remove(smallest)
        clone.remove(largest)
        return sum(clone) / 10

    def update_statistics(self, session_data: SessionData):
        # Update mean
        mean = sum(session_data.solves) / len(session_data.solves)
        self.var_session_mean.set(format_time_seconds(mean))
        logging.debug(f"Mean is {mean}")

        # Update current time, current ao5 and current a012
        self.var_current_time.set(format_time_seconds(session_data.solves[-1]))

        ao5_list = session_data.solves[-5:]
        if len(ao5_list) >= 5:
            ao5 = MainApplication.calculate_ao5(ao5_list)
            self.var_current_ao5.set(format_time_seconds(ao5))
            logging.debug(f"ao5 is {ao5}")

        ao12_list = session_data.solves[-12:]
        if len(ao12_list) >= 12:
            ao12 = MainApplication.calculate_ao12(ao12_list)
            self.var_current_ao12.set(format_time_seconds(ao12))
            logging.debug(f"ao12 is {ao12}")

        # Update best time, best ao5 and best ao12
        best_time = min(session_data.solves)
        self.var_best_time.set(format_time_seconds(best_time))

        if len(ao5_list) >= 5:
            averages = []
            for i in range(len(session_data.solves) - 4):
                five = session_data.solves[0 + i:5 + i]
                averages.append(MainApplication.calculate_ao5(five))

            best_ao5 = min(averages)
            self.var_best_ao5.set(format_time_seconds(best_ao5))

        if len(ao12_list) >= 12:
            averages = []
            for i in range(len(session_data.solves) - 11):
                twelve = session_data.solves[0 + i:12 + i]
                averages.append(MainApplication.calculate_ao12(twelve))

            best_ao12 = min(averages)
            self.var_best_ao12.set(format_time_seconds(best_ao12))

    def load_last_session(self):
        try:
            last_session_name = get_last_session()
        except RuntimeError:  # There was no last session
            logging.info("Please select a session")
            messagebox.showinfo("No Session", "Please select or create a new session to use.", parent=self.root)
            return
        except ValueError:
            messagebox.showerror("Data Error", "The data file was corrupted.", parent=self.root)
            messagebox.showinfo("No Session", "Please select or create a new session to use.", parent=self.root)
            return
        except FileNotFoundError:
            messagebox.showerror("Data Error", "The data file was missing.", parent=self.root)
            messagebox.showinfo("No Session", "Please select or create a new session to use.", parent=self.root)
            return
        except KeyError:
            messagebox.showerror("Data Error", "Missing entry in data file.", parent=self.root)
            messagebox.showinfo("No Session", "Please select or create a new session to use.", parent=self.root)
            return

        self.load_session(last_session_name)

    def settings(self):
        top_level = tk.Toplevel(self.root)
        Settings(top_level, self.apply_settings)

    def about(self):
        top_level = tk.Toplevel(self.root)
        About(top_level)

    def new_session(self):
        top_level = tk.Toplevel(self.root)
        SelectSession(top_level, self.create_session, Mode.NEW_SESSION)

    def open_session(self):
        top_level = tk.Toplevel(self.root)
        SelectSession(top_level, self.load_session, Mode.OPEN_SESSION)

    def see_statistics(self):
        if self.session_data is None:
            messagebox.showinfo("No Session", "There is no session in use. Please select a session.", parent=self.root)
            return

        if not self.session_data.solves:
            messagebox.showinfo("No Solves", "There are no solves in this session.", parent=self.root)
            return

        plot(self.session_data)

    def clear_left_UI(self):
        # Only these must be reset
        for label in self.frm_canvas_frame.winfo_children():
            label.destroy()

        self.var_current_time.set("n/a")
        self.var_current_ao5.set("n/a")
        self.var_current_ao12.set("n/a")
        self.var_best_time.set("n/a")
        self.var_best_ao5.set("n/a")
        self.var_best_ao12.set("n/a")
        self.var_session_mean.set("n/a")

        self.solve_index = 1
        self.var_time.set("0.00")

    def create_session(self, name: str):
        try:
            self.session_data = create_new_session(name, True)
        except FileExistsError:
            if messagebox.askyesno("Session Already Exists", f'Session "{name}" already exists. '
                                   "Do you want to overwrite it?", parent=self.root):
                self.session_data = create_new_session(name, False)
            else:
                return

        # Fill session name
        self.var_session_name.set(name)

        self.clear_left_UI()

    def load_session(self, name: str):
        session_data = load_session_data(name + ".json")
        if session_data is None:
            messagebox.showerror("Loading Failure", f'Could not load session "{name}", because either it has missing data, '
                                 "or it is non-existent, or it is corrupted.", parent=self.root)
            return

        # Fill session name
        self.var_session_name.set(session_data.name)

        # Clear first
        self.clear_left_UI()

        # Fill left GUI list
        for solve in session_data.solves:
            tk.Label(self.frm_canvas_frame, text=f"{self.solve_index}. {format_time_seconds(solve)}", font="Times, 14") \
                .grid(row=self.MAX_SOLVES - self.solve_index, column=0, sticky="w")
            self.solve_index += 1

        # Fill statistics
        if session_data.solves:
            self.update_statistics(session_data)

        self.session_data = session_data

    def apply_settings(self, timer_size: int, scramble_size: int, enable_inspection: bool, background_color: str,
                       foreground_color: str):
        self.lbl_time.configure(font=f"Times, {timer_size}")
        self.lbl_scramble.configure(font=f"Times, {scramble_size}")
        self.timer.with_inspection = enable_inspection
        self.root.tk_setPalette(background=background_color, foreground=foreground_color)

    # Code copied from the internet and modified
    def kt_is_pressed(self):
        return time.time() - self.last_press_time < 0.1

    def kt_report_key_press(self, event):
        if not self.kt_is_pressed():
            self.on_key_press(event)  # The actual event
        self.last_press_time = time.time()

    def kt_report_key_release(self, event):
        timer = threading.Timer(0.1, self.kt_report_key_release_callback, args=(event,))
        timer.start()

    def kt_report_key_release_callback(self, event):
        if not self.kt_is_pressed():
            self.on_key_release(event)  # The actual event
        self.last_release_time = time.time()


def main():
    root = tk.Tk()
    MainApplication(root)
    root.mainloop()
