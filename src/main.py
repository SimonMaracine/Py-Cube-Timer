import logging
import time
import threading
import datetime
import tkinter as tk
from tkinter import messagebox
from typing import Optional

import src.globals
from src.timer import Timer
from src.scramble import generate_scramble
from src.session import create_new_session, dump_data, SessionData, Solve, remember_last_session, \
    get_last_session, load_session_data
from src.select_session import SelectSession

logging.basicConfig(level=logging.DEBUG)


def TWODEC(n: float) -> str:
    return "{:.2f}".format(n)


class MainApplication(tk.Frame):

    def __init__(self, root: tk.Tk):
        super().__init__(root, bg="black", relief="ridge", bd=6)
        self.root = root
        self.pack(fill="both", expand=True)
        self.columnconfigure(0, weight=0)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=0)
        self.rowconfigure(1, weight=1)

        self.root.option_add("*tearOff", False)
        self.root.title("Py-Cube-Timer")
        self.root.wm_protocol("WM_DELETE_WINDOW", self.exit)

        # Main menu
        men_file = tk.Menu(self)
        men_file.add_command(label="New Session", command=self.new_session)
        men_file.add_command(label="Open Session", command=self.open_session)
        men_file.add_command(label="Exit", command=self.exit)

        men_edit = tk.Menu(self)
        men_edit.add_command(label="Settings")

        men_help = tk.Menu(self)
        men_help.add_command(label="Info")
        men_help.add_command(label="About")

        men_main = tk.Menu(self)
        men_main.add_cascade(label="File", menu=men_file)
        men_main.add_cascade(label="Edit", menu=men_edit)
        men_main.add_cascade(label="Help", menu=men_help)
        self.root.configure(menu=men_main)

        # Main frames
        frm_left_side = tk.Frame(self, bg="red", relief="ridge", bd=2)
        frm_left_side.grid(row=0, column=0, rowspan=2, sticky="wns")
        frm_left_side.rowconfigure(3, weight=1)

        frm_scramble = tk.Frame(self, bg="purple", relief="ridge", bd=2)
        frm_scramble.grid(row=0, column=1, sticky="wen")

        frm_timer = tk.Frame(self, bg="blue", relief="ridge", bd=2)
        frm_timer.grid(row=1, column=1)

        # Scramble area
        self.var_scramble = tk.StringVar(frm_scramble, value=generate_scramble())
        lbl_scramble = tk.Label(frm_scramble, textvariable=self.var_scramble, font="Times, 20")
        lbl_scramble.pack()

        # Left side area
        # Session name
        self.var_session_name = tk.StringVar(frm_left_side, value="")
        lbl_session_name = tk.Label(frm_left_side, textvariable=self.var_session_name)
        lbl_session_name.grid(row=0, column=0)

        # Statistics
        frm_statistics = tk.Frame(frm_left_side)
        frm_statistics.grid(row=1, column=0)

        lbl_current = tk.Label(frm_statistics, text="current")
        lbl_current.grid(row=0, column=1)

        lbl_best = tk.Label(frm_statistics, text="best")
        lbl_best.grid(row=0, column=2)

        lbl_time = tk.Label(frm_statistics, text="time")
        lbl_time.grid(row=1, column=0)

        lbl_ao5 = tk.Label(frm_statistics, text="ao5")
        lbl_ao5.grid(row=2, column=0)

        lbl_ao12 = tk.Label(frm_statistics, text="ao12")
        lbl_ao12.grid(row=3, column=0)

        self.var_current_time = tk.DoubleVar(frm_statistics, value="0.00")
        lbl_current_time = tk.Label(frm_statistics, textvariable=self.var_current_time)
        lbl_current_time.grid(row=1, column=1)

        self.var_current_ao5 = tk.DoubleVar(frm_statistics, value="0.00")
        lbl_current_ao5 = tk.Label(frm_statistics, textvariable=self.var_current_ao5)
        lbl_current_ao5.grid(row=2, column=1)

        self.var_current_ao12 = tk.DoubleVar(frm_statistics, value="0.00")
        lbl_current_ao12 = tk.Label(frm_statistics, textvariable=self.var_current_ao12)
        lbl_current_ao12.grid(row=3, column=1)

        self.var_best_time = tk.DoubleVar(frm_statistics, value="0.00")
        lbl_best_time = tk.Label(frm_statistics, textvariable=self.var_best_time)
        lbl_best_time.grid(row=1, column=2)

        self.var_best_ao5 = tk.DoubleVar(frm_statistics, value="0.00")
        lbl_best_ao5 = tk.Label(frm_statistics, textvariable=self.var_best_ao5)
        lbl_best_ao5.grid(row=2, column=2)

        self.var_best_ao12 = tk.DoubleVar(frm_statistics, value="0.00")
        lbl_best_ao12 = tk.Label(frm_statistics, textvariable=self.var_best_ao12)
        lbl_best_ao12.grid(row=3, column=2)

        # Session mean
        self.var_session_mean = tk.StringVar(frm_left_side, value="0.00")
        lbl_session_mean = tk.Label(frm_left_side, textvariable=self.var_session_mean, font="Times, 18")

        lbl_session_mean.grid(row=2, column=0)

        # Times
        frm_times = tk.Frame(frm_left_side)
        frm_times.grid(row=3, column=0, sticky="ns")

        bar_times = tk.Scrollbar(frm_times, orient="vertical")
        bar_times.pack(side="right", fill="y")

        canvas_times = tk.Canvas(frm_times, width=140, borderwidth=0, yscrollcommand=bar_times.set)
        canvas_times.pack(side="left", fill="both", expand=True)

        bar_times.configure(command=canvas_times.yview)

        self.frm_canvas_frame = tk.Frame(frm_times)
        canvas_times.create_window((0, 0), window=self.frm_canvas_frame, anchor="nw")
        self.frm_canvas_frame.bind("<Configure>", lambda event: self.on_frame_configure(canvas_times))

        # for i in range(25):
        #     tk.Label(frm_canvas_frame, text=f"{i}. 0.00").grid(row=i, column=0)

        self.solve_index = 0

        # Timer area
        self.var_time = tk.StringVar(frm_timer, value="0.00")
        lbl_time = tk.Label(frm_timer, textvariable=self.var_time, font="Times, 90")
        lbl_time.pack()

        self.check_to_save_in_session()

        self.timer = Timer(self.var_time)
        self.timer.with_inspection = True
        self.root.bind("<KeyPress>", self.kt_report_key_press)
        self.root.bind("<KeyRelease>", self.kt_report_key_release)

        # Flag to handle timer start
        self.stopped_timer = False

        # Variables to fix the key repeating functionality
        # There is still the bug that there are two key presses registered, if holding down a key
        self.last_press_time = 0
        self.last_release_time = 0

        # Load session
        self.session_data: Optional[SessionData] = None
        self.load_last_session()

    def on_frame_configure(self, canvas):
        canvas.configure(scrollregion=canvas.bbox("all"))

    def on_key_press(self, event):
        print("KEY PRESSED")
        if self.timer.is_running() and not self.timer.is_inspecting():
            self.timer.stop()
            self.stopped_timer = True

            logging.debug("Timer STOP")

    def on_key_release(self, event):
        print("KEY RELEASED")
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

    def save_solve_in_session(self, solve_time: str):
        assert self.session_data is not None

        # Update left GUI list
        tk.Label(self.frm_canvas_frame, text=f"{self.solve_index}. {solve_time}") \
            .grid(row=self.solve_index, column=0, sticky="W")
        self.solve_index += 1

        # Update list
        self.session_data.solves.append(float(solve_time))

        self.update_statistics(self.session_data)

        assert self.session_data.name
        try:
            dump_data(self.session_data.name + ".json",
                      solve=Solve(self.session_data.solves[-1], self.var_scramble.get(), str(datetime.datetime.now())),
                      mean=TWODEC(self.session_data.mean),
                      best_time=TWODEC(self.session_data.best_time),
                      best_ao5=TWODEC(self.session_data.best_ao5),
                      best_ao12=TWODEC(self.session_data.best_ao12))
        except FileNotFoundError as err:
            logging.error(err)
            exit(1)

        # Generate new scramble
        self.var_scramble.set(generate_scramble())

    def check_to_save_in_session(self):
        if src.globals.can_save_solve_now:
            self.save_solve_in_session(self.var_time.get())
            logging.info("Saved solve")
            src.globals.can_save_solve_now = False

        self.after(700, self.check_to_save_in_session)

    def exit(self):
        if self.session_data is None:
            self.root.destroy()
            return

        remember_last_session(self.session_data.name)
        logging.debug(f"Session remembered is '{self.session_data.name}'")
        self.root.destroy()

    def update_statistics(self, session_data: SessionData):
        # Update mean
        session_data.mean = sum(session_data.solves) / len(session_data.solves)
        self.var_session_mean.set(TWODEC(session_data.mean))
        logging.debug(f"Mean is {session_data.mean}")

        # Update current time, current ao5 and current a012
        self.var_current_time.set(TWODEC(session_data.solves[-1]))

        ao5_list = session_data.solves[-5:]
        ao5 = sum(ao5_list) / len(ao5_list)
        if len(ao5_list) >= 5:
            self.var_current_ao5.set(TWODEC(ao5))
            logging.debug(f"ao5 is {ao5}")

        ao12_list = session_data.solves[-12:]
        ao12 = sum(ao12_list) / len(ao12_list)
        if len(ao12_list) >= 12:
            self.var_current_ao12.set(TWODEC(ao12))
            logging.debug(f"ao12 is {ao12}")

        # Update best time, best ao5 and best ao12
        session_data.best_time = min(session_data.best_time, session_data.solves[-1])
        self.var_best_time.set(TWODEC(session_data.best_time))

        if len(ao5_list) >= 5:
            session_data.best_ao5 = min(session_data.best_ao5, ao5)
            self.var_best_ao5.set(TWODEC(session_data.best_ao5))

        if len(ao12_list) >= 12:
            session_data.best_ao12 = min(session_data.best_ao12, ao12)
            self.var_best_ao12.set(TWODEC(session_data.best_ao12))

    def load_last_session(self):
        try:
            last_session_name = get_last_session()
        except AssertionError:  # There was no last session
            logging.info("Please select a session")
            messagebox.showinfo("No Session", "Please select or create a new session to use.", parent=self.root)
            return

        self.load_session(last_session_name)

    def new_session(self):
        top_level = tk.Toplevel(self.root)
        SelectSession(top_level, self.create_session, True)

    def open_session(self):
        top_level = tk.Toplevel(self.root)
        SelectSession(top_level, self.load_session, False)

    def create_session(self, name: str):
        self.session_data = create_new_session(name)

        # Fill session name
        self.var_session_name.set(name)

        # Clear first
        # Only these must be reset
        for label in self.frm_canvas_frame.winfo_children():
            label.destroy()

        self.var_current_time.set("0.00")
        self.var_current_ao5.set("0.00")
        self.var_current_ao12.set("0.00")
        self.var_best_time.set("0.00")
        self.var_best_ao5.set("0.00")
        self.var_best_ao12.set("0.00")
        self.var_session_mean.set("0.00")

        self.solve_index = 0

        # TODO maybe clear timer too

    def load_session(self, name: str):
        session_data = load_session_data(name + ".json")
        if session_data is None:
            messagebox.showerror("Loading Failure",
                                 (f'Could not load session "{name}", because either it has missing data, or '
                                  "it is non-existent, or it is corrupted."), parent=self.root)
            return

        # Fill session name
        self.var_session_name.set(session_data.name)

        # Clear first
        # Only these must be reset
        for label in self.frm_canvas_frame.winfo_children():
            label.destroy()

        self.var_current_time.set("0.00")
        self.var_current_ao5.set("0.00")
        self.var_current_ao12.set("0.00")
        self.var_best_time.set("0.00")
        self.var_best_ao5.set("0.00")
        self.var_best_ao12.set("0.00")
        self.var_session_mean.set("0.00")

        self.solve_index = 0
        # Yeah, not very DRY...

        # TODO maybe clear timer too

        # Fill left GUI list
        for i in range(len(session_data.solves)):
            tk.Label(self.frm_canvas_frame, text=f"{i}. {TWODEC(session_data.solves[i])}") \
                .grid(row=i, column=0, sticky="W")
            self.solve_index += 1

        # Fill statistics
        if session_data.solves:
            self.update_statistics(session_data)

        self.session_data = session_data

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
