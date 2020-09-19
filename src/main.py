import logging
import time
import threading
import tkinter as tk

import src.globals
from src.timer import Timer
from src.scramble import generate_scramble
from src.session import create_new_session, dump_data

logging.basicConfig(level=logging.DEBUG)


class MainApplication(tk.Frame):

    def __init__(self, root: tk.Tk):
        super().__init__(root,  bg="black", relief="ridge", bd=6)
        self.root = root
        self.pack(fill="both", expand=True)
        self.columnconfigure(0, weight=0)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=0)
        self.rowconfigure(1, weight=1)

        self.root.option_add("*tearOff", False)
        self.root.title("Py-Cube-Timer")

        # Main menu
        men_file = tk.Menu(self)
        men_file.add_command(label="New")
        men_file.add_command(label="Open")

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
        self.var_session_name = tk.StringVar(frm_left_side, value="Session name")
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

        self.var_current_time = tk.DoubleVar(frm_statistics, value=0.0)
        lbl_current_time = tk.Label(frm_statistics, textvariable=self.var_current_time)
        lbl_current_time.grid(row=1, column=1)

        self.var_current_ao5 = tk.DoubleVar(frm_statistics, value=0.0)
        lbl_current_ao5 = tk.Label(frm_statistics, textvariable=self.var_current_ao5)
        lbl_current_ao5.grid(row=2, column=1)

        self.var_current_ao12 = tk.DoubleVar(frm_statistics, value=0.0)
        lbl_current_ao12 = tk.Label(frm_statistics, textvariable=self.var_current_ao12)
        lbl_current_ao12.grid(row=3, column=1)

        self.var_best_time = tk.DoubleVar(frm_statistics, value=0.0)
        lbl_best_time = tk.Label(frm_statistics, textvariable=self.var_best_time)
        lbl_best_time.grid(row=1, column=2)

        self.var_best_ao5 = tk.DoubleVar(frm_statistics, value=0.0)
        lbl_best_ao5 = tk.Label(frm_statistics, textvariable=self.var_best_ao5)
        lbl_best_ao5.grid(row=2, column=2)

        self.var_best_ao12 = tk.DoubleVar(frm_statistics, value=0.0)
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
        if event.char == " ":
            if not self.stopped_timer:
                if not self.timer.is_running() or self.timer.is_inspecting():
                    self.timer.start()

                    logging.debug("Timer START")
            else:
                self.stopped_timer = False

    def save_solve_in_session(self):
        self.var_scramble.set(generate_scramble())

        tk.Label(self.frm_canvas_frame, text=f"{self.solve_index}. {self.var_time.get()}").grid(row=self.solve_index, column=0)
        self.solve_index += 1

    def check_to_save_in_session(self):
        if src.globals.can_save_solve_now:
            self.save_solve_in_session()
            logging.info("Saved solve")
            src.globals.can_save_solve_now = False

        self.after(800, self.check_to_save_in_session)

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
