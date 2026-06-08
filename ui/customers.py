import tkinter as tk
from tkinter import ttk, messagebox

from ui.common import BaseFrame, COLORS


class CustomersFrame(BaseFrame):
    def __init__(self, parent, db):
        super().__init__(parent, db)
        self._build()

    def _build(self):
        self.header("إدارة العملاء", "👥")

        sf = self.card(self)
        sf.pack(fill="x", padx=10, pady=6)
        sff = tk.Frame(sf, bg=COLORS["white"], pady=6, padx=10)
        sff.pack(fill="x")
        tk.Label(sff, text="بحث:", font=("Arial", 9), bg=COLORS["white"]).pack(side="right")
        self.sv = tk.StringVar()
        e = ttk.Entry(sff, textvariable=self.sv, width=22)
        e.pack(side="right", padx=4)
        e.bind("<Return>", lambda _: self._load())
        self.btn(sff, "🔍", self._load, width=4).pack(side="right")

        card = self.card(self)
        card.pack(fill="both", expand=True, padx=10, pady=(0, 6))
        cols = ("ID", "الاسم", "الهاتف", "النقاط", "الرصيد")
        self.tree = ttk.Treeview(card, columns=cols, show="headings")
        for c in cols:
            self.tree.heading(c, text=c)
            self.tree.column(c, width=110, anchor="center")
        vsb = ttk.Scrollbar(card, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        btns = tk.Frame(self, bg=COLORS["bg"])
        btns.pack(fill="x", padx=10, pady=4)
        self.btn(btns, "➕ إضافة", self._add, color=COLORS["success"]).pack(side="right", padx=4)
        self.btn(btns, "✏️ تعديل", self._edit, color=COLORS["warning"]).pack(side="right", padx=4)
        self.btn(btns, "📋 فواتير العميل", self._show_invoices, color=COLORS["accent"]).pack(side="left", padx=4)
        self._load()

    def _load(self):
        rows = self.db.get_customers(self.sv.get().strip())
        self.tree.delete(*self.tree.get_children())
        for r in rows:
            self.tree.insert("", "end", iid=r["id"],
                values=(r["id"], r["name"], r["phone"] or "", r["points"], f"{r['balance']:.2f}"))

    def _add(self):
        win = tk.Toplevel(self)
        win.title("إضافة عميل")
        win.geometry("320x200")
        win.configure(bg=COLORS["bg"])
        nv = tk.StringVar()
        pv = tk.StringVar()
        for lbl, var in [("الاسم:", nv), ("الهاتف:", pv)]:
            r = tk.Frame(win, bg=COLORS["bg"])
            r.pack(fill="x", padx=20, pady=6)
            tk.Label(r, text=lbl, font=("Arial", 9), bg=COLORS["bg"], width=8, anchor="e").pack(side="right")
            ent = ttk.Entry(r, textvariable=var, width=22)
            ent.pack(side="right")
            ent.bind("<Return>", lambda _: save())

        def save():
            name = nv.get().strip()
            if not name:
                messagebox.showerror("خطأ", "الاسم مطلوب", parent=win)
                return
            self.db.add_customer(name, pv.get().strip())
            win.destroy()
            self._load()
            try:
                self.master.master.refresh_all_views()
            except Exception:
                pass

        tk.Button(win, text="💾 حفظ", command=save,
                  bg=COLORS["success"], fg="white", font=("Arial", 10, "bold")).pack(pady=10)

    def _edit(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("تنبيه", "اختر عميلاً")
            return
        cid = int(sel[0])
        row = self.db.conn.execute("SELECT * FROM customers WHERE id=?", (cid,)).fetchone()
        win = tk.Toplevel(self)
        win.title("تعديل العميل")
        win.geometry("320x200")
        win.configure(bg=COLORS["bg"])
        nv = tk.StringVar(value=row["name"])
        pv = tk.StringVar(value=row["phone"] or "")
        for lbl, var in [("الاسم:", nv), ("الهاتف:", pv)]:
            r = tk.Frame(win, bg=COLORS["bg"])
            r.pack(fill="x", padx=20, pady=6)
            tk.Label(r, text=lbl, font=("Arial", 9), bg=COLORS["bg"], width=8, anchor="e").pack(side="right")
            ent = ttk.Entry(r, textvariable=var, width=22)
            ent.pack(side="right")
            ent.bind("<Return>", lambda _: save())

        def save():
            self.db.update_customer(cid, nv.get().strip(), pv.get().strip())
            win.destroy()
            self._load()
            try:
                self.master.master.refresh_all_views()
            except Exception:
                pass

        tk.Button(win, text="💾 حفظ", command=save,
                  bg=COLORS["success"], fg="white", font=("Arial", 10, "bold")).pack(pady=10)

    def _show_invoices(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("تنبيه", "اختر عميلاً")
            return
        cid = int(sel[0])
        name = self.tree.item(sel[0])["values"][1]
        invs = self.db.get_invoices()
        cust_invs = [i for i in invs if i["customer_id"] == cid]
        win = tk.Toplevel(self)
        win.title(f"فواتير: {name}")
        win.geometry("540x400")
        win.configure(bg=COLORS["bg"])
        tk.Label(win, text=f"فواتير العميل: {name}",
                 font=("Arial", 11, "bold"), bg=COLORS["bg"], fg=COLORS["header"]).pack(pady=8)
        cols = ("رقم الفاتورة", "التاريخ", "الإجمالي", "الحالة")
        tree = ttk.Treeview(win, columns=cols, show="headings", height=14)
        for c in cols:
            tree.heading(c, text=c)
            tree.column(c, width=120, anchor="center")
        tree.pack(fill="both", expand=True, padx=10)
        for i in cust_invs:
            tree.insert("", "end", values=(i["invoice_no"], i["date"][:16],
                                           f"{i['total']:.2f}", i["status"]))
