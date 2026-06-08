import tkinter as tk
from tkinter import ttk
from datetime import datetime

from ui.common import BaseFrame, COLORS


class ReportsFrame(BaseFrame):
    def __init__(self, parent, db):
        super().__init__(parent, db)
        self._build()

    def _build(self):
        self.header("التقارير والإحصائيات", "📊")

        tabs = ttk.Notebook(self)
        tabs.pack(fill="both", expand=True, padx=10, pady=8)

        self._daily_tab(tabs)
        self._products_tab(tabs)
        self._stock_tab(tabs)

    def _daily_tab(self, nb):
        frm = tk.Frame(nb, bg=COLORS["bg"])
        nb.add(frm, text="📅 الملخص اليومي")

        ctrl = tk.Frame(frm, bg=COLORS["bg"], pady=8)
        ctrl.pack(fill="x", padx=10)
        tk.Label(ctrl, text="التاريخ (YYYY-MM-DD):", font=("Arial", 9), bg=COLORS["bg"]).pack(side="right")
        self.date_var = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        ent_d = ttk.Entry(ctrl, textvariable=self.date_var, width=14)
        ent_d.pack(side="right", padx=6)
        ent_d.bind("<Return>", lambda e: self._show_daily())
        tk.Button(ctrl, text="عرض", command=self._show_daily,
                  bg=COLORS["accent"], fg="white", font=("Arial", 9)).pack(side="right")

        self.daily_frame = tk.Frame(frm, bg=COLORS["white"], pady=12, padx=20)
        self.daily_frame.pack(fill="x", padx=10, pady=6)

        tk.Label(frm, text="آخر الفواتير:", font=("Arial", 10, "bold"),
                 bg=COLORS["bg"]).pack(padx=10, anchor="e", pady=4)
        card = tk.Frame(frm, bg=COLORS["white"])
        card.pack(fill="both", expand=True, padx=10)
        cols = ("الفاتورة", "العميل", "التاريخ", "الإجمالي", "الحالة")
        self.daily_tree = ttk.Treeview(card, columns=cols, show="headings", height=8)
        for c in cols:
            self.daily_tree.heading(c, text=c)
            self.daily_tree.column(c, width=110, anchor="center")
        self.daily_tree.pack(fill="both", expand=True)
        self._show_daily()

    def _show_daily(self):
        date = self.date_var.get().strip()
        row = self.db.daily_summary(date)
        for w in self.daily_frame.winfo_children():
            w.destroy()
        stats = [
            ("عدد الفواتير", str(row["cnt"] or 0)),
            ("إجمالي المبيعات", f"{(row['total'] or 0):.2f} جنيه"),
            ("إجمالي الخصومات", f"{(row['disc'] or 0):.2f} جنيه"),
        ]
        for lbl, val in stats:
            r = tk.Frame(self.daily_frame, bg=COLORS["white"])
            r.pack(fill="x", pady=3)
            tk.Label(r, text=f"{lbl}:", font=("Arial", 10, "bold"), bg=COLORS["white"], width=18, anchor="e").pack(side="right")
            tk.Label(r, text=val, font=("Arial", 11), bg=COLORS["white"],
                     fg=COLORS["accent"]).pack(side="right", padx=8)

        invs = self.db.get_invoices(date_from=date, date_to=date + " 23:59:59")
        self.daily_tree.delete(*self.daily_tree.get_children())
        for i in invs:
            self.daily_tree.insert("", "end", values=(i["invoice_no"], i["cust_name"] or "",
                                                      i["date"][:16], f"{i['total']:.2f}", i["status"]))

    def _refresh_top_products(self):
        if not hasattr(self, "top_products_tree"):
            return
        tree = self.top_products_tree
        tree.delete(*tree.get_children())
        for i, p in enumerate(self.db.top_products()):
            tree.insert("", "end", values=(i + 1, p["name"], f"{p['qty']:.0f}", f"{p['revenue']:.2f} جنيه"),
                        tags=("odd",) if i % 2 else ())

    def _refresh_stock(self):
        if not hasattr(self, "stock_tree"):
            return
        tree = self.stock_tree
        tree.delete(*tree.get_children())
        total_val = 0
        for i, p in enumerate(self.db.get_products()):
            val = p["stock"] * p["cost"]
            total_val += val
            tree.insert("", "end", values=(p["name"], p["stock"], p["unit"],
                                           f"{p['price']:.2f}", f"{p['cost']:.2f}", f"{val:.2f}"),
                        tags=("odd",) if i % 2 else ())
        if hasattr(self, "stock_total_var"):
            self.stock_total_var.set(f"إجمالي قيمة المخزون: {total_val:.2f} جنيه")

    def _products_tab(self, nb):
        frm = tk.Frame(nb, bg=COLORS["bg"])
        nb.add(frm, text="🏆 أفضل المنتجات")
        tk.Label(frm, text="أعلى 10 منتجات مبيعاً", font=("Arial", 11, "bold"),
                 bg=COLORS["bg"], fg=COLORS["header"]).pack(pady=8)
        card = tk.Frame(frm, bg=COLORS["white"])
        card.pack(fill="both", expand=True, padx=10, pady=6)
        cols = ("#", "الصنف", "الكمية المباعة", "الإيرادات")
        tree = ttk.Treeview(card, columns=cols, show="headings")
        for c in cols:
            tree.heading(c, text=c)
            tree.column(c, width=130, anchor="center")
        tree.pack(fill="both", expand=True)
        tree.tag_configure("odd", background="#f1f1f1")
        self.top_products_tree = tree
        self._refresh_top_products()

    def _stock_tab(self, nb):
        frm = tk.Frame(nb, bg=COLORS["bg"])
        nb.add(frm, text="📦 تقرير المخزون")
        tk.Label(frm, text="قيمة المخزون الكاملة", font=("Arial", 11, "bold"),
                 bg=COLORS["bg"], fg=COLORS["header"]).pack(pady=8)
        card = tk.Frame(frm, bg=COLORS["white"])
        card.pack(fill="both", expand=True, padx=10, pady=6)
        cols = ("الصنف", "المخزون", "الوحدة", "سعر البيع", "التكلفة", "قيمة المخزون")
        tree = ttk.Treeview(card, columns=cols, show="headings")
        for c in cols:
            tree.heading(c, text=c)
            tree.column(c, width=100, anchor="center")
        tree.pack(fill="both", expand=True)
        tree.tag_configure("odd", background="#f1f1f1")
        self.stock_tree = tree
        self.stock_total_var = tk.StringVar()
        tk.Label(frm, textvariable=self.stock_total_var,
                 font=("Arial", 11, "bold"), bg=COLORS["bg"],
                 fg=COLORS["success"]).pack(pady=6)
        self._refresh_stock()

    def _refresh(self):
        self._show_daily()
        self._refresh_top_products()
        self._refresh_stock()
