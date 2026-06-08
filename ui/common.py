import tkinter as tk
from tkinter import ttk

from database import Database

COLORS = {
    "bg":       "#f0f4f8",
    "sidebar":  "#1a3a5c",
    "header":   "#1e4d8c",
    "accent":   "#2e86c1",
    "success":  "#27ae60",
    "danger":   "#e74c3c",
    "warning":  "#f39c12",
    "white":    "#ffffff",
    "text":     "#2c3e50",
    "light":    "#ecf0f1",
    "hover":    "#154360",
}


class ZebraTreeview(ttk.Treeview):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tag_configure("even", background=COLORS["white"])
        self.tag_configure("odd", background="#f1f1f1")

    def insert(self, parent, index, iid=None, **kwargs):
        tags = kwargs.get("tags", ())
        if isinstance(tags, str):
            tags = (tags,)
        tags = tuple(tag for tag in tags if tag)

        if "even" not in tags and "odd" not in tags:
            row_tag = "odd" if len(self.get_children(parent)) % 2 else "even"
            tags = (*tags, row_tag)

        kwargs["tags"] = tags
        return super().insert(parent, index, iid=iid, **kwargs)


ttk.Treeview = ZebraTreeview


class BaseFrame(tk.Frame):
    def __init__(self, parent, db: Database, **kw):
        super().__init__(parent, bg=COLORS["bg"], **kw)
        self.db = db

    def header(self, text, icon=""):
        frm = tk.Frame(self, bg=COLORS["header"], pady=8)
        frm.pack(fill="x")
        tk.Label(frm, text=f"{icon}  {text}", font=("Arial", 18, "bold"),
                 bg=COLORS["header"], fg="white").pack()

    def card(self, parent, **kw):
        f = tk.Frame(parent, bg=COLORS["white"], relief="flat",
                     highlightthickness=1, highlightbackground="#dde1e7", **kw)
        return f

    def btn(self, parent, text, cmd, color=None, **kw):
        color = color or COLORS["accent"]
        font = kw.pop("font", ("Arial", 13, "bold"))
        b = tk.Button(parent, text=text, command=cmd,
                      bg=color, fg="white", relief="flat",
                      font=font, cursor="hand2",
                      activebackground=COLORS["hover"], activeforeground="white",
                      padx=14, pady=6, **kw)
        return b

    def lbl(self, parent, text, size=10, bold=False, color=None):
        font = ("Arial", size, "bold" if bold else "normal")
        return tk.Label(parent, text=text, font=font,
                        bg=parent["bg"] if hasattr(parent, "__getitem__") else COLORS["bg"],
                        fg=color or COLORS["text"])

    def entry(self, parent, var, width=20, **kw):
        return ttk.Entry(parent, textvariable=var, width=width, **kw)
