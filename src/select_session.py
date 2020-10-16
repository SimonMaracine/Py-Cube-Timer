import os
from enum import Enum, auto
import tkinter as tk
from typing import Callable
from tkinter import messagebox
from tkinter import filedialog

from src.session import session_exists


class Mode(Enum):
    NEW_SESSION = auto(),
    OPEN_SESSION = auto(),
    RENAME_SESSION = auto()


class SelectSession(tk.Frame):

    def __init__(self, top_level: tk.Toplevel, on_ok: Callable[[str], None], mode: Mode, x: int, y: int):
        super().__init__(top_level)
        self.top_level = top_level
        self.on_ok = on_ok
        self.mode = mode
        self.pack(padx=10, pady=10, expand=True)

        if self.mode == Mode.NEW_SESSION:
            self.top_level.title("New Session")
        elif self.mode == Mode.OPEN_SESSION:
            self.top_level.title("Open Session")
        elif self.mode == Mode.RENAME_SESSION:
            self.top_level.title("Rename Session")

        self.top_level.geometry(f"+{x}+{y}")

        frm_entry = tk.Frame(self)
        if self.mode == Mode.OPEN_SESSION:
            frm_entry.grid(row=0, column=0, columnspan=2, pady=6)
        else:
            frm_entry.grid(row=0, column=0, columnspan=2, pady=16)

        tk.Label(frm_entry, text="Name").grid(row=0, column=0, padx=(0, 4))

        self.ent_session_name = tk.Entry(frm_entry, width=18)
        self.ent_session_name.grid(row=0, column=1)

        if self.mode == Mode.OPEN_SESSION:
            tk.Button(self, text="Open file", command=self.open_file).grid(row=1, column=0, columnspan=2, pady=(0, 16))

        tk.Button(self, text="Ok", command=self.ok).grid(row=2, column=0)
        tk.Button(self, text="Cancel", command=self.top_level.destroy).grid(row=2, column=1)

        self.top_level.bind("<Return>", self.on_enter_press)
        self.ent_session_name.focus()

    def ok(self):
        session_name = self.ent_session_name.get()

        if not session_name:
            messagebox.showerror("Invalid Name", "Please insert a session name.", parent=self.top_level)
            return

        if self.mode == Mode.OPEN_SESSION:  # Only check for existence, if it's opening mode
            if not session_exists(session_name):
                messagebox.showerror("Invalid Name", f'There is no session called "{session_name}".', parent=self.top_level)
                return

        self.on_ok(session_name)
        self.top_level.destroy()

    def on_enter_press(self, event):
        self.ok()

    # For opening mode
    def open_file(self):
        # It doesn't do anything, if it doesn't find the folder, which is annoying
        file_path: str = filedialog.askopenfilename(initialdir="data/sessions", parent=self.top_level)

        if file_path:  # Returned an empty tuple on cancel
            if not file_path.endswith(".json") or f"data{os.sep}sessions" not in file_path:
                messagebox.showerror("Invalid File", "Please choose a session file (json) from the sessions folder.",
                                     parent=self.top_level)
                return
        else:
            return

        file_name = file_path.split(os.sep)[-1].split(".")[0]

        self.on_ok(file_name)
        self.top_level.destroy()
