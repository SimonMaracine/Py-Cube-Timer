import logging
import time
import threading
import datetime
import copy
import webbrowser
import tkinter as tk
from tkinter import messagebox
from typing import Optional, List
from os.path import join

import src.globals
from src.timer import Timer, interpret_time_in_seconds, format_time_seconds, DEFAULT_READY_COLOR, DEFAULT_INSPECTION_COLOR
from src.scramble import generate_3x3x3_scramble, generate_4x4x4_scramble, generate_2x2x2_scramble
from src.session import create_new_session, dump_data, SessionData, Solve, remember_last_session, get_last_session, \
    load_session_data, remove_solve_out_of_session, rename_session, destroy_session, backup_session, \
    FileCorruptedError, SameFileError, change_type
from src.select_session import SelectSession, Mode
from src.settings import Settings, get_settings
from src.data import data_folder_exists, recreate_data_folder, DEFAULT_BACKGROUND_COLOR, DEFAULT_TIMER_SIZE, \
    DEFAULT_SCRAMBLE_SIZE
from src.about import About
from src.plot import plot
from src.inspect_solve import InspectSolve

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
        self.rowconfigure(2, weight=0)

        self.root.option_add("*tearOff", False)
        self.root.title("Py-Cube-Timer")
        self.root.wm_protocol("WM_DELETE_WINDOW", self.exit)
        self.root.geometry("1024x576")

        try:
            self.icon = tk.PhotoImage(file=join("data", "icon.png"), master=self.root)
        except tk.TclError:
            logging.error("Icon not found")
        else:
            self.root.iconphoto(True, self.icon)

        # Main menu
        men_file = tk.Menu(self)
        men_file.add_command(label="New Session", command=self.new_session)
        men_file.add_command(label="Open Session", command=self.open_session)
        men_file.add_command(label="See Statistics", command=self.see_statistics)
        men_file.add_command(label="Backup Session Now", command=self.backup_session_now)
        men_file.add_command(label="Exit", command=self.exit)

        men_edit = tk.Menu(self)
        men_edit.add_command(label="Remove Last Solve", command=self.remove_last_solve_out_of_session)
        men_edit.add_command(label="Rename This Session", command=self.rename_this_session)
        men_edit.add_command(label="Delete This Session", command=self.delete_this_session)
        men_edit.add_command(label="Settings", command=self.settings)

        men_help = tk.Menu(self)
        men_help.add_command(label="Info", command=self.info)
        men_help.add_command(label="About", command=self.about)

        men_main = tk.Menu(self)
        men_main.add_cascade(label="File", menu=men_file)
        men_main.add_cascade(label="Edit", menu=men_edit)
        men_main.add_cascade(label="Help", menu=men_help)
        self.root.configure(menu=men_main)

        # Main frames
        frm_left_side = tk.Frame(self, relief="ridge", bd=3)
        frm_left_side.grid(row=0, column=0, rowspan=3, sticky="wns")
        frm_left_side.rowconfigure(3, weight=1)

        frm_scramble = tk.Frame(self, relief="ridge", bd=3)
        frm_scramble.grid(row=0, column=1, sticky="wen")

        frm_timer = tk.Frame(self)
        frm_timer.grid(row=1, column=1)

        self.frm_event = tk.Frame(self, relief="ridge", bd=3, height=33)
        self.frm_event.grid(row=2, column=1, sticky="wes")

        # Get settings from data
        error = False

        try:
            timer_size, scramble_size, enable_inspection, background_color, self.foreground_color, \
                enable_backup, backup_path, ready_color, inspection_color = get_settings()
        except FileNotFoundError:
            messagebox.showerror("Data Error", "The data file is missing.", parent=self.root)
            error = True
        except FileCorruptedError:
            messagebox.showerror("Data Error", "The data file is corrupted.", parent=self.root)
            error = True
        except KeyError:
            messagebox.showerror("Data Error", "Missing entry in data file.", parent=self.root)
            error = True

        if error:
            timer_size = DEFAULT_TIMER_SIZE
            scramble_size = DEFAULT_SCRAMBLE_SIZE
            enable_inspection = True
            background_color = DEFAULT_BACKGROUND_COLOR
            self.foreground_color = "#000000"
            enable_backup = False
            backup_path = ""
            ready_color = DEFAULT_READY_COLOR
            inspection_color = DEFAULT_INSPECTION_COLOR

        self.root.tk_setPalette(background=background_color, foreground=self.foreground_color)

        # Scramble area
        frm_scramble_buttons = tk.Frame(frm_scramble)
        frm_scramble_buttons.pack()

        # Needed by the OptionMenu below
        self.var_scrtype = tk.StringVar(frm_scramble_buttons, value="3x3x3")  # Default is this, but it may be set after load

        tk.OptionMenu(frm_scramble_buttons, self.var_scrtype, "3x3x3", "4x4x4", "2x2x2",
                      command=self.on_scramble_type_change).grid(row=0, column=0)

        tk.Button(frm_scramble_buttons, text="Generate Next", command=self.generate_next_scramble).grid(row=0, column=1)

        self.var_scramble = tk.StringVar(frm_scramble, value=generate_3x3x3_scramble())  # It may be set later after load
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
        frm_statistics.grid(row=1, column=0, padx=(10, 10))

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

        self.frm_indices = tk.Frame(self.frm_canvas_frame)
        self.frm_indices.grid(row=0, column=0)
        self.frm_solves = tk.Frame(self.frm_canvas_frame)
        self.frm_solves.grid(row=0, column=1)
        # self.frm_ao5 = tk.Frame(self.frm_canvas_frame)
        # self.frm_ao5.grid(row=0, column=2)
        # self.frm_ao12 = tk.Frame(self.frm_canvas_frame)
        # self.frm_ao12.grid(row=0, column=3)

        self.solve_index = 1  # Next solve index to be added (last one in the list + 1)
        self.MAX_SOLVES = 9997

        # These two are used in the logic for loading more solves; they don't need to be updated when a solve is removed
        self.solves_loaded = 0
        self.SOLVES_ON_LOAD: Optional[List[Solve]] = None

        self.btn_more: Optional[tk.Button] = None

        # Timer area
        self.var_time = tk.StringVar(frm_timer, value="0.00")
        self.lbl_time = tk.Label(frm_timer, textvariable=self.var_time, font=f"Times, {timer_size}")
        self.lbl_time.pack()

        self.check_to_save_in_session()

        self.timer = Timer(self.var_time)
        self.timer.with_inspection = enable_inspection
        self.root.bind("<KeyPress>", self.kt_report_key_press)
        self.root.bind("<KeyRelease>", self.kt_report_key_release)
        self.root.bind("<Alt-z>", self.on_alt_z_key_press)
        self.root.bind("<Escape>", self.on_escape_press)

        self.timer_ready_color = ready_color
        self.timer_inspection_color = inspection_color

        # Flag to handle timer start
        self.stopped_timer = False

        # Variables to fix the key repeating functionality
        # There is still the bug that there are two key presses registered, if holding down a key
        self.last_press_time = 0.0
        self.last_release_time = 0.0

        # Data class to hold a session
        self.session_data: Optional[SessionData] = None

        # Backup settings
        self.enable_backup = enable_backup
        self.backup_path = backup_path

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

        if not self.timer.is_running() or self.timer.is_inspecting():
            if event.char == " ":
                if self.session_data is not None:
                    if not self.stopped_timer:
                        self.change_timer_color(self.timer_ready_color)

    def on_key_release(self, event):
        if event.char == " ":
            if self.session_data is None:
                messagebox.showerror("No Session", "Please select or create a new session to use the timer.",
                                     parent=self.root)
                return
            if not self.stopped_timer:
                if not self.timer.is_running():
                    self.timer.start()
                    if self.timer.with_inspection:  # This is to handle the case when there is no inspection
                        self.change_timer_color(self.timer_inspection_color)
                    else:
                        self.change_timer_color(self.foreground_color)
                    logging.debug("Timer START")
                elif self.timer.is_inspecting():
                    self.timer.start()
                    self.change_timer_color(self.foreground_color)
                    logging.debug("Timer START")
            else:
                self.stopped_timer = False

    def on_alt_z_key_press(self, _event):
        self.remove_last_solve_out_of_session()

    def on_escape_press(self, _event):
        if self.timer.is_running():
            src.globals.pressed_escape = True
            self.timer.stop()
        self.var_time.set("0.00")
        self.change_timer_color(self.foreground_color)

    def on_scramble_type_change(self, value: str):
        if value == "3x3x3":
            self.var_scramble.set(generate_3x3x3_scramble())
        elif value == "4x4x4":
            self.var_scramble.set(generate_4x4x4_scramble())
        elif value == "2x2x2":
            self.var_scramble.set(generate_2x2x2_scramble())

        try:
            self.session_data.scramble_type = value
        except AttributeError:  # It is None
            return

        try:
            change_type(self.session_data.name + ".json", value)
        except FileCorruptedError:
            logging.error("Could not save the scramble type, because the session file is corrupted")
            messagebox.showerror("Saving Failure", "Could not save the scramble type, "
                                 "because the session file is corrupted.", parent=self.root)

    def show_event(self, text: str):
        label = tk.Label(self.frm_event, text=text, font="Times, 14")
        label.pack()

        threading.Timer(5.0, lambda l=label: self.delete_event(l)).start()

    def delete_event(self, label: tk.Label):
        label.destroy()
        self.frm_event.configure(height=33)

    def generate_next_scramble(self):
        if self.var_scrtype.get() == "3x3x3":  # var_scrtype cannot be empty
            self.var_scramble.set(generate_3x3x3_scramble())
        elif self.var_scrtype.get() == "4x4x4":
            self.var_scramble.set(generate_4x4x4_scramble())
        elif self.var_scrtype.get() == "2x2x2":
            self.var_scramble.set(generate_2x2x2_scramble())

    def change_timer_color(self, color: str):
        self.lbl_time.configure(foreground=color)

    def save_solve_in_session(self, solve_time: str):  # solve_time is already formatted
        assert self.session_data is not None

        if self.solve_index >= self.MAX_SOLVES:
            messagebox.showerror("Saving Failure", "Could not save the solve, because the "
                                 "amount of solves per session was exceeded.", parent=self.root)
            return

        # Update left GUI list
        tk.Label(self.frm_indices, text=f"{self.solve_index}. ", font="Times, 14") \
            .grid(row=self.MAX_SOLVES - self.solve_index, column=0, sticky="w")

        lbl_solve = tk.Label(self.frm_solves, text=f"{solve_time}", font="Times, 14")
        lbl_solve.grid(row=self.MAX_SOLVES - self.solve_index, column=0, sticky="w")
        lbl_solve.bind("<Button-1>", lambda event, index=self.solve_index: self.inspect_solve(index))  # A bit hacky

        self.solve_index += 1

        if self.solve_index >= self.MAX_SOLVES:
            messagebox.showinfo("Session Ended", "The maximum amount of solves per session has exceeded. "
                                "This session is done.", parent=self.root)
            return

        date = str(datetime.datetime.now())
        scramble = self.var_scramble.get()

        # Update list
        self.session_data.solves.append(Solve(time=solve_time, scramble=scramble, date=date,
                                              raw_time=interpret_time_in_seconds(solve_time)))

        self.update_statistics(self.session_data, True)

        assert self.session_data.name
        try:
            dump_data(self.session_data.name + ".json",
                      Solve(solve_time, scramble, date, 0.0))  # dump_data doesn't care about raw_time anyway
        except FileNotFoundError:
            messagebox.showerror("Saving Failure", "Could not save the solve in session, because the file is missing.",
                                 parent=self.root)
        except FileCorruptedError:
            messagebox.showerror("Saving Failure", "Could not save the solve, because the file is corrupted.",
                                 parent=self.root)
        except KeyError:
            messagebox.showerror("Saving Failure", "Could not save the solve, because there is a missing key in the file.",
                                 parent=self.root)
        else:
            logging.info("Saved solve")

        # Generate new scramble
        self.generate_next_scramble()

        # Backup the session, if appropriate
        if len(self.session_data.solves) % 5 == 0:  # Magic number :O
            if self.enable_backup:
                self.backup_session()

    def remove_last_solve_out_of_session(self):
        self.remove_solve_out_of_session(-1)

    def remove_solve_out_of_session(self, index: int, parent: tk.Toplevel = None) -> bool:
        """
        index is from 1 to 9997.
        -1 is handled separately; don't put negative numbers except for -1.

        """
        assert self.session_data is not None

        if not self.session_data.solves:
            messagebox.showinfo("No Solves", "There are no solves in this session.", parent=self.root)
            return False

        if not messagebox.askyesno("Remove Last Solve" if index == -1 else "Remove Solve",
                                   "Are you sure you want to remove the last solve in the session?" if index == -1 else
                                   "Are you sure you want to remove this solve?",
                                   parent=self.root if parent is None else parent):
            return False

        # Update left GUI list
        # Search for the last widget in the list (the lowest row) and destroy it
        time_labels = self.frm_solves.winfo_children()
        index_labels = self.frm_indices.winfo_children()
        assert time_labels
        assert index_labels

        rows = map(lambda widget: widget.grid_info()["row"], time_labels)
        time_row_widget_dict = {row: widget for row, widget in zip(rows, time_labels)}
        time_lowest_widget_row = min(time_row_widget_dict.keys())

        rows = map(lambda widget: widget.grid_info()["row"], index_labels)
        index_row_widget_dict = {row: widget for row, widget in zip(rows, index_labels)}
        index_lowest_widget_row = min(index_row_widget_dict.keys())

        if index == -1:
            time_row_widget_dict[time_lowest_widget_row].destroy()
            index_row_widget_dict[index_lowest_widget_row].destroy()
        else:
            time_row_widget_dict[self.MAX_SOLVES - index].destroy()
            index_row_widget_dict[self.MAX_SOLVES - index].destroy()

        # Delete these, so that we don't get confused
        del index_row_widget_dict, time_row_widget_dict, rows, index_lowest_widget_row, time_lowest_widget_row, \
            index_labels, time_labels

        self.solve_index -= 1

        # Update list
        if index == -1:
            del self.session_data.solves[-1]
        else:
            del self.session_data.solves[index - 1]

        if self.session_data.solves:
            self.update_statistics(self.session_data, False)

        # Fix indexing when deleting a solve from the middle
        if index != -1:
            index_labels = self.frm_indices.winfo_children()
            rows = map(lambda widget: widget.grid_info()["row"], index_labels)
            row_widget_dict = {row: widget for row, widget in zip(rows, index_labels)}
            for i in range(0, len(self.session_data.solves) - index + 1):
                label: tk.Label = row_widget_dict[self.MAX_SOLVES - index - i - 1]

                number_str = label["text"].rstrip(". ")
                index_text = str(int(number_str) - 1) + ". "
                label.configure(text=index_text)

                current_row = label.grid_info()["row"]
                current_column = label.grid_info()["column"]
                label.grid(row=current_row + 1, column=current_column)

            time_labels = self.frm_solves.winfo_children()
            rows = map(lambda widget: widget.grid_info()["row"], time_labels)
            row_widget_dict = {row: widget for row, widget in zip(rows, time_labels)}
            actual_index = index
            for i in range(0, len(self.session_data.solves) - index + 1):
                label: tk.Label = row_widget_dict[self.MAX_SOLVES - index - i - 1]

                label.bind("<Button-1>", lambda event, ind=actual_index: self.inspect_solve(ind))
                actual_index += 1

                current_row = label.grid_info()["row"]
                current_column = label.grid_info()["column"]
                label.grid(row=current_row + 1, column=current_column)

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
            remove_solve_out_of_session(self.session_data.name + ".json", index)
        except FileNotFoundError:
            messagebox.showerror("Saving Failure", "Could not remove the solve from the session, "
                                 "because the file is missing.", parent=self.root)
        except FileCorruptedError:
            messagebox.showerror("Saving Failure", "Could not remove the solve, because the file is corrupted.",
                                 parent=self.root)
        except KeyError:
            messagebox.showerror("Saving Failure", "Could not remove the solve, because there is a missing key in the file.",
                                 parent=self.root)

        return True

    def rename_this_session(self):
        top_level = tk.Toplevel(self.root)
        SelectSession(top_level, self.rename_session, Mode.RENAME_SESSION, self.root.winfo_x() + 50,
                      self.root.winfo_y() + 50)

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
            except FileCorruptedError:
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
        except FileCorruptedError:
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

    def update_statistics(self, session_data: SessionData, from_save: bool):
        solves_raw = list(map(lambda solve: solve.raw_time, session_data.solves))

        # Update mean
        mean = sum(solves_raw) / len(session_data.solves)
        self.var_session_mean.set(format_time_seconds(mean))
        logging.debug(f"Mean is {mean}")

        # Update current time, current ao5 and current ao12
        self.var_current_time.set(session_data.solves[-1].time)

        ao5_list = solves_raw[-5:]
        if len(ao5_list) >= 5:
            ao5 = MainApplication.calculate_ao5(ao5_list)
            self.var_current_ao5.set(format_time_seconds(ao5))
            logging.debug(f"ao5 is {ao5}")

        ao12_list = solves_raw[-12:]
        if len(ao12_list) >= 12:
            ao12 = MainApplication.calculate_ao12(ao12_list)
            self.var_current_ao12.set(format_time_seconds(ao12))
            logging.debug(f"ao12 is {ao12}")

        # Update best time, best ao5 and best ao12
        best_time = min(solves_raw)
        if from_save:
            if self.var_best_time.get() != "n/a":
                if best_time < interpret_time_in_seconds(self.var_best_time.get()):
                    logging.debug(f"New PB of {format_time_seconds(best_time)}!")
                    self.show_event(f"New PB of {format_time_seconds(best_time)}!")
        self.var_best_time.set(format_time_seconds(best_time))

        if len(ao5_list) >= 5:
            averages = []
            for i in range(len(solves_raw) - 4):
                five = solves_raw[0 + i:5 + i]
                averages.append(MainApplication.calculate_ao5(five))

            best_ao5 = min(averages)
            if from_save:
                if self.var_best_ao5.get() != "n/a":
                    if best_ao5 < interpret_time_in_seconds(self.var_best_ao5.get()):
                        logging.debug(f"New ao5 best of {format_time_seconds(best_ao5)}!")
                        self.show_event(f"New ao5 best of {format_time_seconds(best_ao5)}!")
            self.var_best_ao5.set(format_time_seconds(best_ao5))
            session_data.all_ao5 = averages  # Write to session data
        else:
            session_data.all_ao5.clear()

        if len(ao12_list) >= 12:
            averages = []
            for i in range(len(solves_raw) - 11):
                twelve = solves_raw[0 + i:12 + i]
                averages.append(MainApplication.calculate_ao12(twelve))

            best_ao12 = min(averages)
            if from_save:
                if self.var_best_ao12.get() != "n/a":
                    if best_ao12 < interpret_time_in_seconds(self.var_best_ao12.get()):
                        logging.debug(f"New ao12 best of {format_time_seconds(best_ao12)}!")
                        self.show_event(f"New ao12 best of {format_time_seconds(best_ao12)}!")
            self.var_best_ao12.set(format_time_seconds(best_ao12))
            session_data.all_ao12 = averages  # Write to session data
        else:
            session_data.all_ao12.clear()

    def load_last_session(self):
        try:
            last_session_name = get_last_session()
        except RuntimeError:  # There was no last session
            messagebox.showinfo("No Session", "Please select or create a new session to use.", parent=self.root)
            return
        except FileCorruptedError:
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
        Settings(top_level, self.apply_settings,  self.root.winfo_x() + 50, self.root.winfo_y() + 50)

    def about(self):
        top_level = tk.Toplevel(self.root)
        About(top_level, self.root.winfo_x() + 50, self.root.winfo_y() + 50)

    @staticmethod
    def info():
        webbrowser.open(join("info", "index.html"))

    def new_session(self):
        top_level = tk.Toplevel(self.root)
        SelectSession(top_level, self.create_session, Mode.NEW_SESSION, self.root.winfo_x() + 50, self.root.winfo_y() + 50)

    def open_session(self):
        top_level = tk.Toplevel(self.root)
        SelectSession(top_level, self.load_session, Mode.OPEN_SESSION, self.root.winfo_x() + 50, self.root.winfo_y() + 50)

    def see_statistics(self):
        if self.session_data is None:
            messagebox.showinfo("No Session", "There is no session in use. Please select a session.", parent=self.root)
            return

        if not self.session_data.solves:
            messagebox.showinfo("No Solves", "There are no solves in this session.", parent=self.root)
            return

        plot(self.session_data)

    def backup_session_now(self):
        if self.enable_backup:
            self.backup_session()
        else:
            logging.info("Couldn't backup the session, because it is disabled in the settings")
            messagebox.showinfo("Backup Disbaled", "Couldn't backup the session, because it is disabled in the settings.",
                                parent=self.root)

    def backup_session(self):
        if self.backup_path:
            try:
                backup_session(self.session_data.name + ".json", self.backup_path)
            except FileNotFoundError:
                messagebox.showerror("Backup Failure", "Couldn't backup the session, because the session file "
                                     "is missing.", parent=self.root)
                return
            except SameFileError:
                messagebox.showerror("Backup Failure", "Couldn't backup the session, because the backup folder "
                                     "is the sessions folder.", parent=self.root)  # TODO maybe avoid this completely
                return
            except OSError:
                messagebox.showerror("Backup Failure", "Couldn't backup the session, because the backup folder "
                                     "is not writable (permission denied).", parent=self.root)
                return
            except AttributeError:  # It is None
                messagebox.showerror("Backup Failure", "There is no session in use. Please select a session.",
                                     parent=self.root)

            logging.info(f"Session backed up in {self.backup_path}")
            self.show_event(f"Session backed up in {self.backup_path}.")
            return  # Success, so don't continue messaging that backup is disabled
        else:  # The string was empty
            logging.error("Couldn't backup the session, because the path is not specified")
            messagebox.showerror("No Backup Folder", "Couldn't backup the session, because "
                                 "the path is not specified.", parent=self.root)
            return

    def clear_left_UI(self):
        # Only these must be reset
        for label in self.frm_indices.winfo_children():
            label.destroy()

        for label in self.frm_solves.winfo_children():
            label.destroy()

        self.var_current_time.set("n/a")
        self.var_current_ao5.set("n/a")
        self.var_current_ao12.set("n/a")
        self.var_best_time.set("n/a")
        self.var_best_ao5.set("n/a")
        self.var_best_ao12.set("n/a")
        self.var_session_mean.set("n/a")

        self.solve_index = 1
        self.solves_loaded = 0  # Technically not necessary
        self.var_time.set("0.00")

    def create_session(self, name: str):
        try:
            self.session_data = create_new_session(name, check_first=True)
        except FileExistsError:
            if messagebox.askyesno("Session Already Exists", f'Session "{name}" already exists. '
                                   "Do you want to overwrite it?", parent=self.root):
                self.session_data = create_new_session(name, check_first=False)
            else:
                return

        # Fill session name
        self.var_session_name.set(name)

        self.clear_left_UI()
        self.on_scramble_type_change(self.var_scrtype.get())  # Call this manually to write to the file and to session_data

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

        if len(session_data.solves) > 40:
            self.solve_index = len(session_data.solves) - 40 + 1
            self.solves_loaded = 40

            self.btn_more = tk.Button(self.frm_canvas_frame, text="More", command=self.load_more_solves)
            self.btn_more.grid(row=1, column=0, columnspan=2)
        else:
            # This is useless, because you can't load more solves anyway
            self.solves_loaded = len(session_data.solves)

            # Do this, because btn_more might stick from the previous session list
            if self.btn_more is not None:
                self.btn_more.destroy()
                self.btn_more = None

        self.SOLVES_ON_LOAD = copy.copy(session_data.solves)  # Only a shallow copy needed

        # Fill left GUI list
        solve: Solve
        for solve in session_data.solves[-40:]:
            tk.Label(self.frm_indices, text=f"{self.solve_index}. ", font="Times, 14") \
                .grid(row=self.MAX_SOLVES - self.solve_index, column=0, sticky="w")  # TODO maybe should be -1

            lbl_solve = tk.Label(self.frm_solves, text=f"{solve.time}", font="Times, 14")
            lbl_solve.grid(row=self.MAX_SOLVES - self.solve_index, column=0, sticky="w")  # TODO maybe should be -1
            lbl_solve.bind("<Button-1>", lambda event, index=self.solve_index: self.inspect_solve(index))  # A bit hacky

            self.solve_index += 1

        # Fill statistics
        if session_data.solves:
            self.update_statistics(session_data, False)

        # Set this, so that it displays the correct scramble type on load
        self.var_scrtype.set(session_data.scramble_type)
        if session_data.scramble_type == "4x4x4":
            self.var_scramble.set(generate_4x4x4_scramble())
        elif session_data.scramble_type == "2x2x2":
            self.var_scramble.set(generate_2x2x2_scramble())
        else:  # It may be any string...
            self.var_scramble.set(generate_3x3x3_scramble())

        self.session_data = session_data

    def load_more_solves(self):
        solve_index = len(self.SOLVES_ON_LOAD) - self.solves_loaded

        solves_loaded_now = 0
        solve: Solve
        for solve in reversed(self.SOLVES_ON_LOAD[-self.solves_loaded - 40:-self.solves_loaded]):
            tk.Label(self.frm_indices, text=f"{solve_index}. ", font="Times, 14") \
                .grid(row=self.MAX_SOLVES - solve_index, column=0, sticky="w")

            lbl_solve = tk.Label(self.frm_solves, text=f"{format_time_seconds(solve.raw_time)}", font="Times, 14")
            lbl_solve.grid(row=self.MAX_SOLVES - solve_index, column=0, sticky="w")
            lbl_solve.bind("<Button-1>", lambda event, index=solve_index: self.inspect_solve(index))  # A bit hacky

            solve_index -= 1
            solves_loaded_now += 1

        self.solves_loaded += solves_loaded_now

        if self.solves_loaded == len(self.SOLVES_ON_LOAD):
            self.btn_more.destroy()
            self.btn_more = None

    def apply_settings(self, timer_size: int, scramble_size: int, enable_inspection: bool, background_color: str,
                       foreground_color: str, enable_backup: bool, backup_path: str, ready_color: str,
                       inspection_color: str):
        self.lbl_time.configure(font=f"Times, {timer_size}")
        self.lbl_scramble.configure(font=f"Times, {scramble_size}")
        self.timer.with_inspection = enable_inspection
        self.root.tk_setPalette(background=background_color, foreground=foreground_color)
        self.foreground_color = foreground_color
        self.enable_backup = enable_backup
        self.backup_path = backup_path
        self.timer_ready_color = ready_color
        self.timer_inspection_color = inspection_color

    def inspect_solve(self, index: int):
        top_level = tk.Toplevel(self.root)
        InspectSolve(top_level, index, self.session_data.solves[index - 1], self.remove_solve_out_of_session,
                     self.root.winfo_x() + 50, self.root.winfo_y() + 50)

    # Code copied from the internet and modified
    def kt_is_pressed(self) -> float:
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
