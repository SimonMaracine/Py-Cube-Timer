from typing import Callable

import tkinter as tk

from src.session import Solve


class InspectSolve(tk.Frame):

    def __init__(self, top_level: tk.Toplevel, index: int, solve: Solve, delete_solve: Callable[[int], None], x: int, y: int):
        super().__init__(top_level)
        self.top_level = top_level
        self.index = index
        self.delete_solve = delete_solve
        self.pack(padx=10, pady=10, expand=True)

        self.top_level.title("Inspect Solve")
        self.top_level.geometry(f"+{x}+{y}")

        tk.Label(self, text=f"Solve number {index}", font="Times, 18").grid(row=0, column=0)
        tk.Label(self, text=solve.time, font="Times, 13").grid(row=1, column=0)
        tk.Label(self, text=solve.scramble, font="Times, 13").grid(row=2, column=0)
        tk.Label(self, text=solve.date, font="Times, 13").grid(row=3, column=0)

        self.frm_buttons = tk.Frame(self)
        self.frm_buttons.grid(row=4, column=0)

        tk.Button(self.frm_buttons, text="Ok", command=self.top_level.destroy).grid(row=0, column=0)
        tk.Button(self.frm_buttons, text="Delete", command=self.delete).grid(row=0, column=1, padx=(100, 0))

    def delete(self):
        self.delete_solve(self.index)
        self.top_level.destroy()
