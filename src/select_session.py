import tkinter as tk
from typing import Callable

from src.session import session_exists


class SelectSession(tk.Frame):

    def __init__(self, top_level: tk.Toplevel, on_ok: Callable[[str], None], new: bool):
        super().__init__(top_level)
        self.top_level = top_level
        self.on_ok = on_ok
        self.new = new
        self.pack(padx=10, pady=10, expand=True)

        self.top_level.title("New Session" if self.new else "Open Session")

        self.ent_session_name = tk.Entry(self)
        self.ent_session_name.grid(row=0, column=0, columnspan=2, pady=16)

        tk.Button(self, text="Ok", command=self.ok).grid(row=1, column=0)
        tk.Button(self, text="Cancel", command=self.top_level.destroy).grid(row=1, column=1)

        self.top_level.bind("<Return>", self.on_enter_press)
        self.ent_session_name.focus()

    def ok(self):
        session_name = self.ent_session_name.get()

        # TODO show a message here
        if not session_name:
            return

        if not self.new:  # Only check for existence, if it's opening mode
            if not session_exists(session_name):
                return

        self.on_ok(session_name)
        self.top_level.destroy()

    def on_enter_press(self, event):
        self.ok()
