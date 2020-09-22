import tkinter as tk
from typing import Callable
from tkinter import messagebox

from src.session import session_exists


class SelectSession(tk.Frame):

    def __init__(self, top_level: tk.Toplevel, on_ok: Callable[[str], None], new: bool):
        super().__init__(top_level)
        self.top_level = top_level
        self.on_ok = on_ok
        self.new = new
        self.pack(padx=10, pady=10, expand=True)

        self.top_level.title("New Session" if self.new else "Open Session")

        frm_entry = tk.Frame(self)
        frm_entry.grid(row=0, column=0, columnspan=2, pady=16)

        tk.Label(frm_entry, text="Name").grid(row=0, column=0, padx=(0, 4))

        self.ent_session_name = tk.Entry(frm_entry, width=18)
        self.ent_session_name.grid(row=0, column=1)

        tk.Button(self, text="Ok", command=self.ok).grid(row=1, column=0)
        tk.Button(self, text="Cancel", command=self.top_level.destroy).grid(row=1, column=1)

        self.top_level.bind("<Return>", self.on_enter_press)
        self.ent_session_name.focus()

    def ok(self):
        session_name = self.ent_session_name.get()

        if not session_name:
            messagebox.showerror("Invalid Name", "Please insert a session name.", parent=self.top_level)
            return

        if not self.new:  # Only check for existence, if it's opening mode
            if not session_exists(session_name):
                messagebox.showerror("Invalid Name", f'There is no session called "{session_name}".', parent=self.top_level)
                return

        self.on_ok(session_name)
        self.top_level.destroy()

    def on_enter_press(self, event):
        self.ok()