import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox

from ui.common import BaseFrame, COLORS


class ProductsFrame(BaseFrame):
    def __init__(self, parent, db):
        super().__init__(parent, db)
        self._build()

    def _build(self):
        self.header("إدارة المنتجات", "📦")

        sf = self.card(self)
        sf.pack(fill="x", padx=10, pady=6)
        sff = tk.Frame(sf, bg=COLORS["white"], pady=6, padx=10)
        sff.pack(fill="x")
        tk.Label(sff, text="بحث:", font=("Arial", 9), bg=COLORS["white"]).pack(side="right")
        self.search_var = tk.StringVar()
        e = ttk.Entry(sff, textvariable=self.search_var, width=22)
        e.pack(side="right", padx=4)
        e.bind("<Return>", lambda _: self._load())
        self.btn(sff, "🔍", self._load, width=4).pack(side="right")

        card = self.card(self)
        card.pack(fill="both", expand=True, padx=10, pady=(0, 6))
        cols = ("ID", "الباركود", "الاسم", "القسم", "السعر", "التكلفة", "المخزون", "الوحدة")
        self.tree = ttk.Treeview(card, columns=cols, show="headings")
        widths = {"ID": 40, "الباركود": 80, "الاسم": 170, "القسم": 100,
                  "السعر": 70, "التكلفة": 70, "المخزون": 65, "الوحدة": 65}
        for c in cols:
            self.tree.heading(c, text=c)
            self.tree.column(c, width=widths.get(c, 80), anchor="center")
        vsb = ttk.Scrollbar(card, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")
        self.tree.tag_configure("low", foreground="red")

        btns = tk.Frame(self, bg=COLORS["bg"])
        btns.pack(fill="x", padx=10, pady=4)
        self.btn(btns, "➕ إضافة منتج",   self._add,    color=COLORS["success"]).pack(side="right", padx=4)
        self.btn(btns, "✏️ تعديل",         self._edit,   color=COLORS["warning"]).pack(side="right", padx=4)
        self.btn(btns, "🗑️ حذف",           self._delete, color=COLORS["danger"]).pack(side="right", padx=4)
        self.btn(btns, "⚠️ مخزون منخفض",   self._low_stock, color=COLORS["warning"]).pack(side="left", padx=4)

        self._load()

    def _load(self, search=None):
        s = search if search is not None else self.search_var.get().strip()
        prods = self.db.get_products(s)
        self.tree.delete(*self.tree.get_children())
        threshold = self.db.get_int_setting("low_stock_threshold", 10)
        for p in prods:
            tag = "low" if p["stock"] <= threshold else ""
            self.tree.insert("", "end", iid=p["id"],
                values=(p["id"], p["barcode"] or "", p["name"], p["cat_name"] or "",
                        f"{p['price']:.2f}", f"{p['cost']:.2f}", p["stock"], p["unit"]),
                tags=(tag,))

    def _product_form(self, title, data=None):
        win = tk.Toplevel(self)
        win.title(title)
        win.geometry("400x430")
        win.configure(bg=COLORS["bg"])
        win.resizable(False, False)

        tk.Label(win, text=title, font=("Arial", 12, "bold"), bg=COLORS["bg"],
                 fg=COLORS["header"]).pack(pady=8)

        fields = {}
        frame = tk.Frame(win, bg=COLORS["bg"])
        frame.pack(padx=20, fill="x")

        def field(lbl, key, default=""):
            r = tk.Frame(frame, bg=COLORS["bg"])
            r.pack(fill="x", pady=4)
            tk.Label(r, text=lbl, font=("Arial", 9), bg=COLORS["bg"], width=14, anchor="e").pack(side="right")
            var = tk.StringVar(value=str(data[key]) if data and data.get(key) is not None else default)
            e = ttk.Entry(r, textvariable=var, width=22)
            e.pack(side="right", padx=6)
            e.bind("<Return>", lambda _: save())
            fields[key] = var

        field("الباركود:", "barcode")
        field("الاسم:", "name")
        field("السعر:", "price", "0")
        field("التكلفة:", "cost", "0")
        field("المخزون:", "stock", "0")
        field("الوحدة:", "unit", "قطعة")

        r = tk.Frame(frame, bg=COLORS["bg"])
        r.pack(fill="x", pady=4)
        tk.Label(r, text="القسم:", font=("Arial", 9), bg=COLORS["bg"], width=14, anchor="e").pack(side="right")
        cats = self.db.get_categories()
        cat_names = [c["name"] for c in cats]
        cat_var = tk.StringVar(value=cat_names[0] if cat_names else "")
        if data:
            cat_row = self.db.conn.execute("SELECT name FROM categories WHERE id=?", (data["category_id"],)).fetchone()
            if cat_row:
                cat_var.set(cat_row["name"])
        ttk.Combobox(r, textvariable=cat_var, values=cat_names, width=20, state="readonly").pack(side="right", padx=6)

        result = {}

        def save():
            try:
                cat_id = next(c["id"] for c in cats if c["name"] == cat_var.get())
                result["data"] = {
                    "barcode":     fields["barcode"].get().strip() or None,
                    "name":        fields["name"].get().strip(),
                    "category_id": cat_id,
                    "price":       float(fields["price"].get()),
                    "cost":        float(fields["cost"].get()),
                    "stock":       int(fields["stock"].get()),
                    "unit":        fields["unit"].get().strip(),
                }
                if not result["data"]["name"]:
                    messagebox.showerror("خطأ", "اسم المنتج مطلوب", parent=win)
                    return
                win.destroy()
            except ValueError:
                messagebox.showerror("خطأ", "تحقق من صحة الأرقام", parent=win)

        tk.Button(win, text="💾 حفظ", command=save,
                  bg=COLORS["success"], fg="white", font=("Arial", 10, "bold"), pady=6).pack(pady=12)
        win.wait_window()
        return result.get("data")

    def _add(self):
        data = self._product_form("إضافة منتج جديد")
        if data:
            try:
                self.db.add_product(data)
                messagebox.showinfo("✅ تم", "تم إضافة المنتج بنجاح")
                self._load()
                try:
                    self.master.master.refresh_all_views()
                except Exception:
                    pass
            except sqlite3.IntegrityError:
                messagebox.showerror("خطأ", "الباركود مستخدم بالفعل")

    def _edit(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("تنبيه", "اختر منتجاً أولاً")
            return
        pid = int(sel[0])
        prod = self.db.conn.execute("SELECT * FROM products WHERE id=?", (pid,)).fetchone()
        data = self._product_form("تعديل المنتج", dict(prod))
        if data:
            try:
                self.db.update_product(pid, data)
                messagebox.showinfo("✅ تم", "تم تحديث المنتج")
                self._load()
                try:
                    self.master.master.refresh_all_views()
                except Exception:
                    pass
            except sqlite3.IntegrityError:
                messagebox.showerror("خطأ", "الباركود مستخدم بالفعل")

    def _delete(self):
        sel = self.tree.selection()
        if not sel:
            return
        if messagebox.askyesno("تأكيد", "هل تريد حذف هذا المنتج؟"):
            self.db.delete_product(int(sel[0]))
            self._load()
            try:
                self.master.master.refresh_all_views()
            except Exception:
                pass

    def _low_stock(self):
        threshold = self.db.get_int_setting("low_stock_threshold", 10)
        rows = self.db.low_stock(threshold)
        win = tk.Toplevel(self)
        win.title("المنتجات ذات المخزون المنخفض")
        win.geometry("450x350")
        win.configure(bg=COLORS["bg"])
        tk.Label(win, text=f"⚠️ مخزون منخفض (≤ {threshold})", font=("Arial", 12, "bold"),
                 bg=COLORS["bg"], fg=COLORS["danger"]).pack(pady=8)
        cols = ("الاسم", "المخزون", "الوحدة")
        tree = ttk.Treeview(win, columns=cols, show="headings", height=12)
        for c in cols:
            tree.heading(c, text=c)
            tree.column(c, width=130, anchor="center")
        tree.pack(fill="both", expand=True, padx=10)
        tree.tag_configure("zero", foreground="red", font=("Arial", 9, "bold"))
        for r in rows:
            tag = "zero" if r["stock"] == 0 else ""
            tree.insert("", "end", values=(r["name"], r["stock"], r["unit"]), tags=(tag,))
