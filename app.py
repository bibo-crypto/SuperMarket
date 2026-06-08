import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from database import Database
from ui import POSFrame, InvoicesFrame, ProductsFrame, CustomersFrame, ReportsFrame, SettingsFrame, COLORS


# ────────────────────────────────────────────────────────────
# app.py: application core and main windows
# ────────────────────────────────────────────────────────────


class LoginWindow(tk.Tk):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.result = None
        self.title("تسجيل الدخول - نور ماركت")
        self.geometry("350x400")
        self.configure(bg=COLORS["bg"])
        self.resizable(False, False)
        self._build()

    def _build(self):
        header = tk.Frame(self, bg=COLORS["header"], pady=20)
        header.pack(fill="x")
        tk.Label(header, text="🔐 دخول النظام", font=("Arial", 16, "bold"), bg=COLORS["header"], fg="white").pack()

        form = tk.Frame(self, bg=COLORS["bg"], pady=30)
        form.pack()

        tk.Label(form, text="اختر نوع المستخدم:", font=("Arial", 10, "bold"), bg=COLORS["bg"]).pack(anchor="e")
        self.role_var = tk.StringVar(value="cashier")
        role_cb = ttk.Combobox(form, textvariable=self.role_var, values=["cashier", "admin"], state="readonly", width=28)
        role_cb.pack(pady=(5, 15))
        role_cb.bind("<<ComboboxSelected>>", self._toggle_password)

        self.pass_lbl = tk.Label(form, text="كلمة المرور:", font=("Arial", 10, "bold"), bg=COLORS["bg"])
        self.p_var = tk.StringVar()
        self.p_ent = ttk.Entry(form, textvariable=self.p_var, show="*", width=30)
        self.p_ent.bind("<Return>", lambda e: self._login())

        self._toggle_password()

        btn = tk.Button(form, text="تسجيل الدخول", command=self._login,
                        bg=COLORS["success"], fg="white", font=("Arial", 11, "bold"),
                        relief="flat", width=25, pady=8, cursor="hand2")
        btn.pack()

    def _toggle_password(self, event=None):
        if self.role_var.get() == "admin":
            self.pass_lbl.pack(anchor="e")
            self.p_ent.pack(pady=(5, 20))
            self.p_ent.focus_set()
        else:
            self.p_ent.pack_forget()
            self.pass_lbl.pack_forget()
            self.p_var.set("")

    def _login(self):
        role = self.role_var.get()
        password = self.p_var.get().strip()

        if role == "cashier":
            user = self.db.conn.execute("SELECT * FROM users WHERE role='cashier'").fetchone()
        else:
            if password == "3620713":
                user = self.db.conn.execute("SELECT * FROM users WHERE role='admin'").fetchone()
            else:
                messagebox.showerror("خطأ", "كلمة المرور غير صحيحة!")
                return

        if user:
            self.result = dict(user)
            self.destroy()
        else:
            messagebox.showerror("خطأ", "بيانات الدخول غير صحيحة أو المستخدم غير موجود!")


class App(tk.Tk):
    def __init__(self, user_data):
        super().__init__()
        self.user = user_data
        self.title("🛒 نظام إدارة السوبر ماركت - نور")
        self.geometry("1150x720")
        self.state('zoomed')
        self.minsize(900, 600)
        self.configure(bg=COLORS["bg"])
        self.db = Database()
        self._setup_style()
        self._build_layout()

    def _setup_style(self):
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except Exception:
            pass
        style.configure("Treeview", rowheight=30, font=("Arial", 10), background=COLORS["white"])
        style.configure("Treeview.Heading", font=("Arial", 11, "bold"),
                        background=COLORS["header"], foreground="white")
        style.map("Treeview", background=[("selected", COLORS["accent"])])
        style.configure("TEntry", padding=6)
        style.configure("TCombobox", padding=6)

    def _build_layout(self):
        self.sidebar = tk.Frame(self, bg=COLORS["sidebar"], width=230)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        logo = tk.Frame(self.sidebar, bg=COLORS["header"], pady=18)
        logo.pack(fill="x")
        tk.Label(logo, text="🛒", font=("Arial", 26), bg=COLORS["header"], fg="white").pack()
        tk.Label(logo, text="نور ماركت", font=("Arial", 13, "bold"),
                 bg=COLORS["header"], fg="white").pack()
        tk.Label(logo, text="نظام المبيعات", font=("Arial", 9),
                 bg=COLORS["header"], fg="#aed6f1").pack()

        self.content = tk.Frame(self, bg=COLORS["bg"])
        self.content.pack(side="right", fill="both", expand=True)

        footer = tk.Frame(self.sidebar, bg=COLORS["sidebar"])
        footer.pack(side="bottom", fill="x", pady=8)
        tk.Label(footer, text=f"📅 {datetime.now().strftime('%A, %d %B %Y  |  %H:%M')}",
                 font=("Arial", 9), bg=COLORS["sidebar"], fg="white", anchor="w").pack(fill="x", padx=10)
        tk.Label(footer, text="v1.0 © نور ماركت", font=("Arial", 8),
                 bg=COLORS["sidebar"], fg="#566573", anchor="w").pack(fill="x", padx=10, pady=(4,0))

        role = self.user.get('role', 'cashier')
        
        self.pages = {}
        self.pages["pos"] = POSFrame(self.content, self.db)
        self.pages["customers"] = CustomersFrame(self.content, self.db)
        
        if role == 'admin':
            self.pages["invoices"] = InvoicesFrame(self.content, self.db)
            self.pages["products"] = ProductsFrame(self.content, self.db)
            self.pages["reports"] = ReportsFrame(self.content, self.db)
            self.pages["settings"] = SettingsFrame(self.content, self.db)

        for page in self.pages.values():
            page.place(relwidth=1, relheight=1)

        nav_items = [
            ("🛒", "نقطة البيع",    "pos"),
            ("👥", "العملاء",       "customers"),
        ]
        
        if role == 'admin':
            nav_items.insert(1, ("🧾", "الفواتير",      "invoices"))
            nav_items.insert(2, ("📦", "المنتجات",      "products"))
            nav_items.append(("📊", "التقارير",      "reports"))
            nav_items.append(("⚙️", "الإعدادات",     "settings"))

        self.nav_buttons = {}
        self.current_page = None
        for icon, label, key in nav_items:
            self._nav_btn(icon, label, key)

        tk.Frame(self.sidebar, bg=COLORS["sidebar"]).pack(expand=True)
        self.show_page("pos")

    def _nav_btn(self, icon, label, key):
        frm = tk.Frame(self.sidebar, bg=COLORS["sidebar"], cursor="hand2")
        frm.pack(fill="x", padx=8, pady=2)

        def hover_in(e):
            if self.current_page != key:
                frm.config(bg=COLORS["hover"])
                il.config(bg=COLORS["hover"])
                ll.config(bg=COLORS["hover"])

        def hover_out(e):
            if self.current_page != key:
                frm.config(bg=COLORS["sidebar"])
                il.config(bg=COLORS["sidebar"])
                ll.config(bg=COLORS["sidebar"])

        il = tk.Label(frm, text=icon, font=("Arial", 16), bg=COLORS["sidebar"], fg="white", width=3)
        il.pack(side="right", pady=8)
        ll = tk.Label(frm, text=label, font=("Arial", 12, "bold"), bg=COLORS["sidebar"], fg="white")
        ll.pack(side="right")

        for w in (frm, il, ll):
            w.bind("<Button-1>", lambda e, k=key: self.show_page(k))
            w.bind("<Enter>", hover_in)
            w.bind("<Leave>", hover_out)

        self.nav_buttons[key] = (frm, il, ll)

    def show_page(self, key):
        if self.current_page and self.current_page in self.nav_buttons:
            frm, il, ll = self.nav_buttons[self.current_page]
            for w in (frm, il, ll):
                w.config(bg=COLORS["sidebar"])
        self.current_page = key
        frm, il, ll = self.nav_buttons[key]
        for w in (frm, il, ll):
            w.config(bg=COLORS["accent"])
        self.pages[key].lift()

    def refresh_all_views(self):
        """Call available refresh/load/search methods on all pages to sync UI trees."""
        for page in list(self.pages.values()):
            try:
                # prefer common load methods
                if hasattr(page, "_load"):
                    page._load()
                elif hasattr(page, "_search_products"):
                    page._search_products()
                elif hasattr(page, "_refresh"):
                    page._refresh()
            except Exception:
                pass


def main():
    db = Database()
    login = LoginWindow(db)
    login.mainloop()

    if login.result:
        app = App(login.result)
        app.mainloop()


if __name__ == "__main__":
    main()
