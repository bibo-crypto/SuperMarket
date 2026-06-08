import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
from datetime import datetime

from database import PDF_DIR, print_invoice_pdf
from ui.common import BaseFrame, COLORS


class EditInvoiceWindow(tk.Toplevel):
    def __init__(self, parent, db, inv_id, inv, items, callback):
        super().__init__(parent)
        self.db = db
        self.inv_id = inv_id
        self.inv = inv
        self.callback = callback
        self.cart = [{"product_id": it["product_id"], "pname": it["pname"],
                      "qty": it["qty"], "unit_price": it["unit_price"],
                      "discount": it["discount"], "total": it["total"]} for it in items]
        self.title(f"تعديل فاتورة {inv['invoice_no']}")
        self.geometry("700x560")
        self.configure(bg=COLORS["bg"])
        self._build()

    def _build(self):
        tk.Label(self, text=f"تعديل الفاتورة: {self.inv['invoice_no']}",
                 font=("Arial", 13, "bold"), bg=COLORS["bg"], fg=COLORS["header"]).pack(pady=8)

        add_f = tk.Frame(self, bg=COLORS["white"], pady=6, padx=10)
        add_f.pack(fill="x", padx=10)
        tk.Label(add_f, text="اسم الصنف للإضافة:", font=("Arial", 9), bg=COLORS["white"]).pack(side="right")
        self.add_var = tk.StringVar()
        ent_add = ttk.Entry(add_f, textvariable=self.add_var, width=24)
        ent_add.pack(side="right", padx=4)
        ent_add.bind("<Return>", lambda e: self._find_and_add())
        tk.Button(add_f, text="بحث وإضافة", command=self._find_and_add,
                  bg=COLORS["success"], fg="white", font=("Arial", 9)).pack(side="right")

        cols = ("الصنف", "الكمية", "السعر", "الإجمالي")
        self.tree = ttk.Treeview(self, columns=cols, show="headings", height=10)
        for c in cols:
            self.tree.heading(c, text=c)
            self.tree.column(c, width=140, anchor="center")
        self.tree.pack(fill="both", expand=True, padx=10, pady=6)
        self.tree.tag_configure("odd", background="#f1f1f1")

        btns = tk.Frame(self, bg=COLORS["bg"])
        btns.pack(fill="x", padx=10)
        tk.Button(btns, text="✏️ تعديل كمية", command=self._edit_qty,
                  bg=COLORS["warning"], fg="white", font=("Arial", 10, "bold"), width=14, pady=8).pack(side="right", padx=8)
        tk.Button(btns, text="🗑️ حذف", command=self._remove,
                  bg=COLORS["danger"], fg="white", font=("Arial", 10, "bold"), width=10, pady=8).pack(side="right", padx=8)

        disc_f = tk.Frame(self, bg=COLORS["bg"], pady=4)
        disc_f.pack(fill="x", padx=10)
        tk.Label(disc_f, text="خصم %:", font=("Arial", 9), bg=COLORS["bg"]).pack(side="right")
        self.disc_var = tk.StringVar(value="0")
        ent_disc = ttk.Entry(disc_f, textvariable=self.disc_var, width=6)
        ent_disc.pack(side="right", padx=4)
        ent_disc.bind("<Return>", lambda e: self._save())

        tk.Button(self, text="💾 حفظ التعديلات", command=self._save,
                  bg=COLORS["success"], fg="white",
                  font=("Arial", 11, "bold"), pady=6).pack(pady=8)

        self._refresh()

    def _refresh(self):
        self.tree.delete(*self.tree.get_children())
        for i, it in enumerate(self.cart):
            self.tree.insert("", "end", iid=i,
                values=(it["pname"], it["qty"], f"{it['unit_price']:.2f}", f"{it['total']:.2f}"),
                tags=("odd",) if i % 2 else ())

    def _find_and_add(self):
        name = self.add_var.get().strip()
        if not name:
            return
        prods = self.db.get_products(name)
        if not prods:
            messagebox.showwarning("تنبيه", "لم يتم العثور على صنف")
            return
        p = prods[0]
        self.cart.append({"product_id": p["id"], "pname": p["name"],
                          "qty": 1, "unit_price": p["price"],
                          "discount": 0, "total": p["price"]})
        self._refresh()

    def _edit_qty(self):
        sel = self.tree.selection()
        if not sel:
            return
        idx = int(sel[0])
        val = simpledialog.askfloat("تعديل", "الكمية الجديدة:", initialvalue=self.cart[idx]["qty"], minvalue=0.1)
        if val is not None:
            self.cart[idx]["qty"] = val
            self.cart[idx]["total"] = round(
                val * self.cart[idx]["unit_price"] * (1 - self.cart[idx]["discount"] / 100),
                2,
            )
            self._refresh()

    def _remove(self):
        sel = self.tree.selection()
        if sel:
            self.cart.pop(int(sel[0]))
            self._refresh()

    def _save(self):
        if not self.cart:
            messagebox.showwarning("تنبيه", "السلة فارغة")
            return
        try:
            disc_pct = float(self.disc_var.get() or 0)
        except ValueError:
            disc_pct = 0
        subtotal = sum(it["total"] for it in self.cart)
        disc_amt = round(subtotal * disc_pct / 100, 2)
        tax_rate = self.db.get_float_setting("tax_rate", 14)
        tax = round((subtotal - disc_amt) * tax_rate / 100, 2)
        total = round(subtotal - disc_amt + tax, 2)
        new_inv = {
            "customer_id": self.inv["customer_id"],
            "subtotal": subtotal, "discount": disc_amt,
            "tax": tax, "total": total,
            "paid": self.inv["paid"],
            "change_amt": round(self.inv["paid"] - total, 2),
            "notes": self.inv["notes"],
        }
        try:
            updated = self.db.update_invoice(self.inv_id, new_inv, self.cart)
        except ValueError as exc:
            messagebox.showerror("مخزون غير كافي", str(exc), parent=self)
            return
        if not updated:
            messagebox.showerror("خطأ", "تعذر تحديث الفاتورة", parent=self)
            return
        messagebox.showinfo("✅ تم", "تم تحديث الفاتورة بنجاح")
        self.callback()
        app = self._find_app()
        if app:
            app.refresh_all_views()
        self.destroy()

    def _find_app(self):
        widget = self
        while widget is not None:
            if hasattr(widget, "refresh_all_views"):
                return widget
            widget = getattr(widget, "master", None)
        return None


class InvoicesFrame(BaseFrame):
    def __init__(self, parent, db):
        super().__init__(parent, db)
        self._auto_refresh_interval = 3000  # milliseconds
        self._auto_refresh_running = True
        self._build()
        self._start_auto_refresh()

    def _build(self):
        self.header("إدارة الفواتير", "🧾")

        fb = self.card(self)
        fb.pack(fill="x", padx=10, pady=6)
        ff = tk.Frame(fb, bg=COLORS["white"], pady=6, padx=10)
        ff.pack(fill="x")

        tk.Label(ff, text="بحث:", font=("Arial", 9), bg=COLORS["white"]).pack(side="right")
        self.search_var = tk.StringVar()
        ent_s = ttk.Entry(ff, textvariable=self.search_var, width=20)
        ent_s.pack(side="right", padx=4)
        ent_s.bind("<Return>", lambda e: self._load())

        tk.Label(ff, text="الحالة:", font=("Arial", 9), bg=COLORS["white"]).pack(side="right", padx=(10, 0))
        self.status_var = tk.StringVar(value="الكل")
        ttk.Combobox(ff, textvariable=self.status_var,
                     values=["الكل", "active", "cancelled", "edited", "returned"],
                     width=10, state="readonly").pack(side="right", padx=4)

        self.btn(ff, "🔍 بحث", self._load, color=COLORS["accent"], width=8).pack(side="right", padx=6)

        card = self.card(self)
        card.pack(fill="both", expand=True, padx=10, pady=(0, 6))
        cols = ("ID", "رقم الفاتورة", "العميل", "التاريخ", "الإجمالي", "المدفوع", "الحالة")
        self.tree = ttk.Treeview(card, columns=cols, show="headings")
        widths = {"ID": 40, "رقم الفاتورة": 140, "العميل": 130, "التاريخ": 140,
                  "الإجمالي": 80, "المدفوع": 80, "الحالة": 70}
        for c in cols:
            self.tree.heading(c, text=c)
            self.tree.column(c, width=widths.get(c, 100), anchor="center")
        vsb = ttk.Scrollbar(card, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        self.tree.tag_configure("cancelled", foreground="red")
        self.tree.tag_configure("edited",    foreground="#e67e22")
        self.tree.tag_configure("active",    foreground=COLORS["success"])

        btns = tk.Frame(self, bg=COLORS["bg"])
        btns.pack(fill="x", padx=10, pady=4)
        self.btn(btns, "👁️ عرض التفاصيل", self._view_details, color=COLORS["accent"]).pack(side="right", padx=4)
        self.btn(btns, "✏️ تعديل الفاتورة", self._edit_invoice, color=COLORS["warning"]).pack(side="right", padx=4)
        self.btn(btns, "❌ إلغاء الفاتورة", self._cancel_invoice, color=COLORS["danger"]).pack(side="right", padx=4)
        self.btn(btns, "💾 حفظ PDF",      self._save_pdf, color="#16a085").pack(side="left", padx=4)
        self.btn(btns, "🖨️ طباعة",         self._print_invoice, color=COLORS["success"]).pack(side="left", padx=4)

        self._load()

    def _start_auto_refresh(self):
        try:
            self.after(self._auto_refresh_interval, self._auto_refresh_loop)
        except Exception:
            pass

    def _auto_refresh_loop(self):
        try:
            if self.winfo_ismapped():
                focused = self.focus_get()
                busy = False
                if focused is not None:
                    w = focused
                    while w is not None:
                        if w is self.tree:
                            busy = True
                            break
                        w = getattr(w, 'master', None)
                if not busy:
                    self._load()
        except Exception:
            pass
        if getattr(self, "_auto_refresh_running", False):
            try:
                self.after(self._auto_refresh_interval, self._auto_refresh_loop)
            except Exception:
                pass

    def _stop_auto_refresh(self):
        self._auto_refresh_running = False

    def _load(self):
        s = self.search_var.get().strip()
        st = self.status_var.get()
        status = None if st == "الكل" else st

        try:
            prev_selected = set(self.tree.selection())
        except Exception:
            prev_selected = set()
        try:
            prev_focus = self.tree.focus()
        except Exception:
            prev_focus = None

        rows = self.db.get_invoices(s, status)
        new_ids = [str(r["id"]) for r in rows]
        cur_ids = list(self.tree.get_children())
        if cur_ids == new_ids:
            for r in rows:
                iid = str(r["id"])
                try:
                    self.tree.item(iid, values=(r["id"], r["invoice_no"], r["cust_name"] or "عميل نقدي",
                                                 r["date"][:16], f"{r['total']:.2f}", f"{r['paid']:.2f}", r["status"]))
                    self.tree.item(iid, tags=(r["status"],))
                except Exception:
                    pass
            return

        self.tree.delete(*cur_ids)
        for r in rows:
            tag = r["status"]
            iid = str(r["id"])
            self.tree.insert("", "end", iid=iid,
                values=(r["id"], r["invoice_no"], r["cust_name"] or "عميل نقدي",
                        r["date"][:16], f"{r['total']:.2f}", f"{r['paid']:.2f}",
                        r["status"]),
                tags=(tag,))

        try:
            to_select = [iid for iid in prev_selected if iid in self.tree.get_children()]
            if to_select:
                self.tree.selection_set(to_select)
                self.tree.focus(to_select[0])
                self.tree.see(to_select[0])
            elif prev_focus and prev_focus in self.tree.get_children():
                self.tree.focus(prev_focus)
                self.tree.see(prev_focus)
        except Exception:
            pass

    def _selected_id(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("تنبيه", "اختر فاتورة أولاً")
            return None
        return int(sel[0])

    def _view_details(self):
        inv_id = self._selected_id()
        if not inv_id:
            return
        inv, items = self.db.get_invoice(inv_id)
        win = tk.Toplevel(self)
        win.title(f"تفاصيل فاتورة {inv['invoice_no']}")
        win.geometry("600x500")
        win.configure(bg=COLORS["bg"])

        tk.Label(win, text=f"فاتورة: {inv['invoice_no']}",
                 font=("Arial", 13, "bold"), bg=COLORS["bg"],
                 fg=COLORS["header"]).pack(pady=8)

        info = tk.Frame(win, bg=COLORS["white"], pady=8, padx=12)
        info.pack(fill="x", padx=10)
        for label, val in [("العميل", inv["cust_name"] or "عميل نقدي"),
                            ("التاريخ", inv["date"]),
                            ("الكاشير", inv["cashier"]),
                            ("الحالة", inv["status"]),
                            ("ملاحظات", inv["notes"] or "")]:
            r = tk.Frame(info, bg=COLORS["white"])
            r.pack(fill="x", pady=2)
            tk.Label(r, text=f"{label}:", font=("Arial", 9, "bold"), bg=COLORS["white"], width=10, anchor="e").pack(side="right")
            tk.Label(r, text=str(val), font=("Arial", 9), bg=COLORS["white"]).pack(side="right", padx=6)

        cols = ("الصنف", "الكمية", "الوحدة", "السعر", "خصم%", "الإجمالي")
        tree = ttk.Treeview(win, columns=cols, show="headings", height=10)
        for c in cols:
            tree.heading(c, text=c)
            tree.column(c, width=90, anchor="center")
        tree.pack(fill="both", expand=True, padx=10, pady=6)
        for it in items:
            tree.insert("", "end", values=(it["pname"], it["qty"], it["unit"],
                                           f"{it['unit_price']:.2f}",
                                           f"{it['discount']:.0f}%", f"{it['total']:.2f}"))

        tot_f = tk.Frame(win, bg=COLORS["white"], pady=6, padx=12)
        tot_f.pack(fill="x", padx=10, pady=4)
        for lbl, val in [("المجموع الفرعي", f"{inv['subtotal']:.2f} جنيه"),
                          ("الخصم", f"{inv['discount']:.2f} جنيه"),
                          ("الضريبة", f"{inv['tax']:.2f} جنيه"),
                          ("الإجمالي", f"{inv['total']:.2f} جنيه"),
                          ("المدفوع", f"{inv['paid']:.2f} جنيه"),
                          ("الباقي", f"{inv['change_amt']:.2f} جنيه")]:
            r = tk.Frame(tot_f, bg=COLORS["white"])
            r.pack(fill="x", pady=1)
            tk.Label(r, text=f"{lbl}:", font=("Arial", 9, "bold"), width=14, anchor="e", bg=COLORS["white"]).pack(side="right")
            tk.Label(r, text=val, font=("Arial", 9), bg=COLORS["white"]).pack(side="right", padx=6)

    def _cancel_invoice(self):
        inv_id = self._selected_id()
        if not inv_id:
            return
        inv, _ = self.db.get_invoice(inv_id)
        if inv["status"] == "cancelled":
            messagebox.showinfo("تنبيه", "الفاتورة ملغاة بالفعل")
            return
        if messagebox.askyesno("تأكيد الإلغاء",
                                f"هل تريد إلغاء الفاتورة {inv['invoice_no']}؟\nسيتم استرداد المخزون."):
            self.db.cancel_invoice(inv_id)
            messagebox.showinfo("✅ تم", "تم إلغاء الفاتورة واسترداد المخزون.")
            self._load()
            try:
                self.master.master.refresh_all_views()
            except Exception:
                pass

    def _edit_invoice(self):
        inv_id = self._selected_id()
        if not inv_id:
            return
        inv, items = self.db.get_invoice(inv_id)
        if inv["status"] == "cancelled":
            messagebox.showerror("خطأ", "لا يمكن تعديل فاتورة ملغاة")
            return
        EditInvoiceWindow(self, self.db, inv_id, inv, items, self._load)

    def _print_invoice(self):
        inv_id = self._selected_id()
        if not inv_id:
            return
        inv, items = self.db.get_invoice(inv_id)
        path = os.path.join(PDF_DIR, f"{inv['invoice_no']}.pdf")
        inv_dict = dict(inv)
        inv_dict["settings"] = self.db.get_settings()
        result = print_invoice_pdf(inv_dict, [dict(i) for i in items], path)
        try:
            if sys.platform == "win32":
                os.startfile(result, "print")
            elif sys.platform == "darwin":
                os.system(f"lp '{result}'")
            else:
                os.system(f"lpr '{result}'")
            messagebox.showinfo("✅ تم", "تم إرسال الفاتورة للطابعة")
        except Exception:
            messagebox.showinfo("تم الحفظ", f"تعذر الاتصال بالطابعة. تم حفظ الملف في:\n{result}")

    def _save_pdf(self):
        inv_id = self._selected_id()
        if not inv_id:
            return
        inv, items = self.db.get_invoice(inv_id)

        file_path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            initialfile=f"{inv['invoice_no']}.pdf",
            filetypes=[("PDF Files", "*.pdf"), ("All Files", "*.*")],
            title="حفظ فاتورة PDF"
        )

        if not file_path:
            return

        inv_dict = dict(inv)
        inv_dict["settings"] = self.db.get_settings()
        result = print_invoice_pdf(inv_dict, [dict(i) for i in items], file_path)
        messagebox.showinfo("✅ تم", f"تم حفظ الفاتورة في:\n{result}")
