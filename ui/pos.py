import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from datetime import datetime

from database import PDF_DIR, Database, print_invoice_pdf
from ui.common import BaseFrame, COLORS


class POSFrame(BaseFrame):
    def __init__(self, parent, db):
        super().__init__(parent, db)
        self.cart = []
        self.held_sales = []
        self.customer_id = 1
        self.customer_name = "عميل نقدي"
        self._build()
        self.bind_all("<Shift-KeyPress>", self._save_invoice_shortcut)

    def _build(self):
        self.header("نقطة البيع - الكاشير", "🛒")

        body = tk.Frame(self, bg=COLORS["bg"])
        body.pack(fill="both", expand=True, padx=10, pady=4)
        body.columnconfigure(0, weight=5)
        body.columnconfigure(1, weight=5)
        body.rowconfigure(0, weight=1)

        left = self.card(body)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 6))

        sf = tk.Frame(left, bg=COLORS["white"], pady=4, padx=8)
        sf.pack(fill="x")
        tk.Label(sf, text="بحث / باركود:", font=("Arial", 10), bg=COLORS["white"]).pack(side="right")
        self.search_var = tk.StringVar()
        se = ttk.Entry(sf, textvariable=self.search_var, width=22)
        se.pack(side="right", padx=(0, 4))
        se.bind("<Return>", lambda e: self._search_products())
        self.btn(sf, "🔍 بحث", self._search_products, width=8).pack(side="right")

        cf = tk.Frame(left, bg=COLORS["white"], padx=8)
        cf.pack(fill="x")
        tk.Label(cf, text="القسم:", font=("Arial", 9), bg=COLORS["white"]).pack(side="right")
        self.cat_var = tk.StringVar(value="الكل")
        cats = ["الكل"] + [c["name"] for c in self.db.get_categories()]
        self.cat_cb = ttk.Combobox(cf, textvariable=self.cat_var, values=cats, width=18, state="readonly")
        self.cat_cb.pack(side="right", padx=4)
        self.cat_cb.bind("<<ComboboxSelected>>", lambda e: self._search_products())

        cols = ("الكود", "الاسم", "السعر", "المخزون")
        self.prod_tree = ttk.Treeview(left, columns=cols, show="headings", height=14)
        for c in cols:
            if c == "الكود":
                w = 120
            elif c == "الاسم":
                w = 280
            elif c == "السعر":
                w = 110
            else:
                w = 110
            self.prod_tree.heading(c, text=c)
            self.prod_tree.column(c, width=w, anchor="center")
        self.prod_tree.pack(fill="both", expand=True, padx=6, pady=6)
        self.prod_tree.tag_configure("low", foreground=COLORS["danger"], font=("Arial", 9, "bold"))
        self.prod_tree.bind("<Double-1>", lambda e: self._add_to_cart())
        sb = ttk.Scrollbar(left, orient="vertical", command=self.prod_tree.yview)
        self.prod_tree.configure(yscrollcommand=sb.set)

        self.btn(left, "➕ إضافة للسلة", self._add_to_cart, color=COLORS["success"]).pack(pady=2)
        self._search_products()

        right = tk.Frame(body, bg=COLORS["bg"])
        right.grid(row=0, column=1, sticky="nsew")
        right.rowconfigure(0, weight=1)

        cart_card = self.card(right)
        cart_card.pack(fill="both", expand=True, pady=(0, 6))

        cust_f = tk.Frame(cart_card, bg=COLORS["light"], pady=4, padx=8)
        cust_f.pack(fill="x")
        self.cust_lbl = tk.Label(cust_f, text=f"👤 {self.customer_name}",
                                  font=("Arial", 10, "bold"), bg=COLORS["light"])
        self.cust_lbl.pack(side="right")
        self.btn(cust_f, "تغيير العميل", self._change_customer, width=14).pack(side="left", pady=2)
        self.btn(cust_f, "عميل آخر", self._start_other_customer, width=12,
                 color=COLORS["warning"]).pack(side="left", padx=(4, 0), pady=2)

        tk.Label(cart_card, text="🛒 سلة المشتريات",
                 font=("Arial", 11, "bold"), bg=COLORS["white"]).pack(pady=4)

        ccols = ("الصنف", "الكمية", "السعر", "خصم%", "الإجمالي")
        self.cart_tree = ttk.Treeview(cart_card, columns=ccols, show="headings", height=7, selectmode="browse")
        widths = {"الصنف": 280, "الكمية": 70, "السعر": 110, "خصم%": 90, "الإجمالي": 110}
        for c in ccols:
            self.cart_tree.heading(c, text=c)
            self.cart_tree.column(c, width=widths.get(c, 80), anchor="center")
        self.cart_tree.pack(fill="both", expand=True, padx=6, pady=(4,2))
        self.cart_tree.tag_configure("odd", background="#f1f1f1")
        self.cart_tree.bind("<plus>", self._edit_qty_shortcut)
        self.cart_tree.bind("<KP_Add>", self._edit_qty_shortcut)
        self.cart_tree.bind("<Delete>", self._remove_item_shortcut)

        cb_btns = tk.Frame(cart_card, bg=COLORS["white"])
        cb_btns.pack(fill="x", padx=6, pady=(0,2))
        self.btn(cb_btns, "✏️ تعديل كمية", self._edit_qty, color=COLORS["warning"]).pack(side="right", padx=3, pady=1)
        self.btn(cb_btns, "🗑️ حذف صنف", self._remove_item, color=COLORS["danger"]).pack(side="right", padx=3, pady=1)
        self.btn(cb_btns, "🧹 مسح السلة", self._clear_cart, color=COLORS["danger"]).pack(side="left", padx=3, pady=1)

        tot_card = self.card(right)
        tot_card.pack(fill="x", pady=(0, 4))
        tf = tk.Frame(tot_card, bg=COLORS["white"], padx=12, pady=6)
        tf.pack(fill="x")

        def tot_row(lbl, var, bold=False):
            r = tk.Frame(tf, bg=COLORS["white"])
            r.pack(fill="x", pady=1)
            font = ("Arial", 11, "bold") if bold else ("Arial", 10)
            tk.Label(r, text=lbl, font=font, bg=COLORS["white"]).pack(side="right")
            tk.Label(r, textvariable=var, font=font, bg=COLORS["white"], fg=COLORS["accent"]).pack(side="left")

        self.subtotal_var = tk.StringVar(value="0.00 جنيه")
        self.disc_pct_var = tk.StringVar(value="0")
        self.disc_amt_var = tk.StringVar(value="0.00 جنيه")
        self.tax_var = tk.StringVar(value="0.00 جنيه")
        self.total_var = tk.StringVar(value="0.00 جنيه")
        self.paid_var = tk.StringVar(value="")
        self.change_var = tk.StringVar(value="0.00 جنيه")

        tot_row("المجموع الفرعي:", self.subtotal_var)

        disc_row = tk.Frame(tf, bg=COLORS["white"])
        disc_row.pack(fill="x", pady=2)
        tk.Label(disc_row, text="خصم %:", font=("Arial", 10), bg=COLORS["white"]).pack(side="right")
        disc_e = ttk.Entry(disc_row, textvariable=self.disc_pct_var, width=6)
        disc_e.pack(side="right", padx=4)
        disc_e.bind("<KeyRelease>", lambda e: self._recalc())
        tot_row("قيمة الخصم:", self.disc_amt_var)
        tot_row("الضريبة (14%):", self.tax_var)
        tot_row("الإجمالي النهائي:", self.total_var, bold=True)

        paid_row = tk.Frame(tf, bg=COLORS["white"])
        paid_row.pack(fill="x", pady=2)
        tk.Label(paid_row, text="المبلغ المدفوع:", font=("Arial", 10, "bold"), bg=COLORS["white"]).pack(side="right")
        paid_e = ttk.Entry(paid_row, textvariable=self.paid_var, width=10)
        paid_e.pack(side="right", padx=4)
        paid_e.bind("<KeyRelease>", lambda e: self._recalc())
        paid_e.bind("<Return>", lambda e: self._save_invoice())
        tot_row("الباقي / الزيادة:", self.change_var)

        notes_f = tk.Frame(tot_card, bg=COLORS["white"], padx=12)
        notes_f.pack(fill="x", pady=(0, 4))
        tk.Label(notes_f, text="ملاحظات:", font=("Arial", 9), bg=COLORS["white"]).pack(side="right")
        self.notes_var = tk.StringVar()
        ttk.Entry(notes_f, textvariable=self.notes_var, width=30).pack(side="right", padx=4)

        act = tk.Frame(right, bg=COLORS["bg"])
        act.pack(fill="x", pady=(0, 4))
        self.btn(act, "💾 حفظ الفاتورة", self._save_invoice,
                 color=COLORS["success"], font=("Arial", 12, "bold"), width=16).pack(side="right", padx=4, ipady=2, pady=4)

        self.last_inv_id = None

    def _search_products(self):
        search = self.search_var.get().strip()
        if search:
            barcode_product = self.db.get_product_by_barcode(search)
            if barcode_product:
                self._add_to_cart(barcode_product["id"])
                self.search_var.set("")
                return
        cat_name = self.cat_var.get()
        cat_id = None
        if cat_name != "الكل":
            cats = self.db.get_categories()
            for c in cats:
                if c["name"] == cat_name:
                    cat_id = c["id"]
                    break
        prods = self.db.get_products(search, cat_id)
        self.prod_tree.delete(*self.prod_tree.get_children())
        threshold = self.db.get_int_setting("low_stock_threshold", 10)
        for p in prods:
            tag = "low" if p["stock"] <= threshold else ""
            self.prod_tree.insert("", "end", iid=p["id"],
                values=(p["barcode"] or "", p["name"], f"{p['price']:.2f}", p["stock"]),
                tags=(tag,))

    def _add_to_cart(self, prod_id=None):
        if not prod_id:
            sel = self.prod_tree.selection()
            if not sel:
                messagebox.showwarning("تنبيه", "اختر صنفاً أولاً")
                return
            prod_id = int(sel[0])
        prod = self.db.conn.execute("SELECT * FROM products WHERE id=?", (prod_id,)).fetchone()
        if not prod:
            return
        current_qty = sum(item["qty"] for item in self.cart if item["product_id"] == prod_id)
        if prod["stock"] <= 0:
            messagebox.showerror("نفاد المخزون", f"الصنف '{prod['name']}' غير متوفر في المخزون")
            return
        if current_qty + 1 > prod["stock"]:
            messagebox.showerror("مخزون غير كافي", f"المتاح من '{prod['name']}' هو {prod['stock']} فقط")
            return
        for item in self.cart:
            if item["product_id"] == prod_id:
                item["qty"] += 1
                item["total"] = round(item["qty"] * item["unit_price"] * (1 - item["discount"]/100), 2)
                self._refresh_cart(self.cart.index(item))
                self._warn_low_stock(prod, item["qty"])
                return
        self.cart.append({
            "product_id": prod_id,
            "pname": prod["name"],
            "qty": 1,
            "unit_price": prod["price"],
            "discount": 0,
            "total": prod["price"],
        })
        self._refresh_cart(len(self.cart) - 1)
        self._warn_low_stock(prod, 1)

    def _warn_low_stock(self, product, cart_qty):
        threshold = self.db.get_int_setting("low_stock_threshold", 10)
        remaining = product["stock"] - cart_qty
        if remaining <= 0:
            messagebox.showwarning("تنبيه مخزون", f"الصنف '{product['name']}' وصل إلى صفر بعد هذه الفاتورة")
        elif remaining <= threshold:
            messagebox.showwarning("تنبيه مخزون", f"المتبقي من '{product['name']}': {remaining}")

    def _refresh_cart(self, selected_index=None):
        self.cart_tree.delete(*self.cart_tree.get_children())
        for i, it in enumerate(self.cart):
            self.cart_tree.insert("", "end", iid=i,
                values=(it["pname"], it["qty"], f"{it['unit_price']:.2f}",
                        f"{it['discount']:.0f}%", f"{it['total']:.2f}"),
                tags=("odd",) if i % 2 else ())
        self._select_cart_item(selected_index)
        self._recalc()

    def _select_cart_item(self, index):
        if index is None or not self.cart:
            return
        index = max(0, min(index, len(self.cart) - 1))
        iid = str(index)
        self.cart_tree.selection_set(iid)
        self.cart_tree.focus(iid)
        self.cart_tree.see(iid)
        self.cart_tree.focus_set()

    def _recalc(self):
        subtotal = sum(it["total"] for it in self.cart)
        try:
            disc_pct = float(self.disc_pct_var.get() or 0)
        except ValueError:
            disc_pct = 0
        disc_amt = round(subtotal * disc_pct / 100, 2)
        after_disc = subtotal - disc_amt
        tax_rate = self.db.get_float_setting("tax_rate", 14)
        tax = round(after_disc * tax_rate / 100, 2)
        total = round(after_disc + tax, 2)
        paid_text = self.paid_var.get().strip()
        if not paid_text:
            paid = total
        else:
            try:
                paid = float(paid_text)
            except ValueError:
                paid = 0
        change = round(paid - total, 2)

        currency = self.db.get_settings().get("currency", "جنيه")
        self.subtotal_var.set(f"{subtotal:.2f} {currency}")
        self.disc_amt_var.set(f"{disc_amt:.2f} {currency}")
        self.tax_var.set(f"{tax:.2f} {currency}")
        self.total_var.set(f"{total:.2f} {currency}")
        self.change_var.set(f"{change:.2f} {currency}")

        self._calc_cache = {"subtotal": subtotal, "disc_pct": disc_pct,
                            "disc_amt": disc_amt, "tax": tax, "total": total,
                            "paid": paid, "change": change}

    def _edit_qty(self):
        sel = self.cart_tree.selection()
        if not sel:
            messagebox.showwarning("تنبيه", "اختر صنفاً من السلة")
            return
        idx = int(sel[0])
        item = self.cart[idx]
        val = simpledialog.askfloat("تعديل الكمية", f"الكمية الجديدة لـ {item['pname']}:",
                                     initialvalue=item["qty"], minvalue=0.1)
        if val is not None:
            stock_row = self.db.conn.execute(
                "SELECT stock FROM products WHERE id=?", (item["product_id"],)
            ).fetchone()
            if stock_row and val > stock_row["stock"]:
                messagebox.showerror("مخزون غير كافي", f"المتاح من هذا الصنف هو {stock_row['stock']} فقط")
                return
            item["qty"] = val
            item["total"] = round(val * item["unit_price"] * (1 - item["discount"]/100), 2)
            self._refresh_cart(idx)

    def _edit_qty_shortcut(self, event=None):
        self._edit_qty()
        return "break"

    def _remove_item(self):
        sel = self.cart_tree.selection()
        if not sel:
            return
        idx = int(sel[0])
        self.cart.pop(idx)
        self._refresh_cart(idx if self.cart else None)

    def _remove_item_shortcut(self, event=None):
        self._remove_item()
        return "break"

    def _clear_cart(self):
        if self.cart and messagebox.askyesno("تأكيد", "مسح كل السلة؟"):
            self.cart.clear()
            self._refresh_cart()

    def _has_current_sale(self):
        return bool(
            self.cart
            or self.customer_id != 1
            or self.disc_pct_var.get().strip() not in ("", "0")
            or self.paid_var.get().strip()
            or self.notes_var.get().strip()
        )

    def _current_sale_state(self):
        return {
            "cart": [item.copy() for item in self.cart],
            "customer_id": self.customer_id,
            "customer_name": self.customer_name,
            "disc_pct": self.disc_pct_var.get(),
            "paid": self.paid_var.get(),
            "notes": self.notes_var.get(),
        }

    def _apply_sale_state(self, state):
        self.cart = [item.copy() for item in state["cart"]]
        self._set_customer(state["customer_id"], state["customer_name"])
        self.disc_pct_var.set(state["disc_pct"])
        self.paid_var.set(state["paid"])
        self.notes_var.set(state["notes"])
        self._refresh_cart(len(self.cart) - 1 if self.cart else None)

    def _clear_current_sale(self):
        self.cart.clear()
        self._set_customer(1, "عميل نقدي")
        self.disc_pct_var.set("0")
        self.paid_var.set("")
        self.notes_var.set("")
        self._refresh_cart()

    def _start_other_customer(self):
        if self._has_current_sale():
            self.held_sales.append(self._current_sale_state())
        self._clear_current_sale()

    def _restore_held_sale(self, index):
        if index < 0 or index >= len(self.held_sales):
            return
        state = self.held_sales.pop(index)
        if self._has_current_sale():
            self.held_sales.append(self._current_sale_state())
        self._apply_sale_state(state)

    def _set_customer(self, customer_id, customer_name):
        self.customer_id = customer_id
        self.customer_name = customer_name
        self.cust_lbl.config(text=f"👤 {self.customer_name}")

    def _change_customer(self):
        win = tk.Toplevel(self)
        win.title("اختيار عميل")
        win.geometry("560x560")
        win.configure(bg=COLORS["bg"])
        win.transient(self.winfo_toplevel())
        win.grab_set()

        header = tk.Frame(win, bg=COLORS["header"], pady=8)
        header.pack(fill="x")
        tk.Label(header, text="اختيار العميل للفاتورة", font=("Arial", 13, "bold"),
                 bg=COLORS["header"], fg="white").pack()
        tk.Label(header, text=f"العميل الحالي: {self.customer_name}", font=("Arial", 9),
                 bg=COLORS["header"], fg="#d6eaf8").pack()

        if self.held_sales:
            held_frame = tk.LabelFrame(win, text="فواتير معلقة", bg=COLORS["bg"],
                                       fg=COLORS["text"], padx=8, pady=6)
            held_frame.pack(fill="x", padx=10, pady=(8, 4))
            held_cols = ("#", "العميل", "الأصناف", "الإجمالي")
            held_tree = ttk.Treeview(held_frame, columns=held_cols, show="headings",
                                     height=min(4, len(self.held_sales)), selectmode="browse")
            widths = {"#": 40, "العميل": 230, "الأصناف": 80, "الإجمالي": 120}
            for col in held_cols:
                held_tree.heading(col, text=col)
                held_tree.column(col, width=widths[col], anchor="center")
            held_tree.pack(side="right", fill="x", expand=True)

            for index, state in enumerate(self.held_sales):
                total = sum(item["total"] for item in state["cart"])
                held_tree.insert("", "end", iid=str(index),
                                 values=(index + 1, state["customer_name"],
                                         len(state["cart"]), f"{total:.2f}"))

            def restore_selected():
                selected = held_tree.selection()
                if selected:
                    self._restore_held_sale(int(selected[0]))
                    win.destroy()

            tk.Button(held_frame, text="رجوع", command=restore_selected,
                      bg=COLORS["warning"], fg="white", font=("Arial", 10, "bold"),
                      width=8).pack(side="left", padx=6)
            held_tree.bind("<Double-1>", lambda _: restore_selected())
            held_tree.bind("<Return>", lambda _: restore_selected())

        search_frame = tk.Frame(win, bg=COLORS["bg"], pady=8, padx=10)
        search_frame.pack(fill="x")
        tk.Label(search_frame, text="بحث بالاسم أو الهاتف:", font=("Arial", 10),
                 bg=COLORS["bg"]).pack(side="right")
        search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=search_var, width=30)
        search_entry.pack(side="right", padx=6)

        cols = ("ID", "الاسم", "الهاتف")
        tree = ttk.Treeview(win, columns=cols, show="headings", height=10, selectmode="browse")
        widths = {"ID": 60, "الاسم": 240, "الهاتف": 160}
        for col in cols:
            tree.heading(col, text=col)
            tree.column(col, width=widths[col], anchor="center")
        tree.pack(fill="both", expand=True, padx=10, pady=(0, 8))

        def load(search=""):
            tree.delete(*tree.get_children())
            first_iid = None
            current_iid = None
            for customer in self.db.get_customers(search):
                iid = str(customer["id"])
                tree.insert("", "end", iid=iid,
                            values=(customer["id"], customer["name"], customer["phone"] or ""))
                first_iid = first_iid or iid
                if customer["id"] == self.customer_id:
                    current_iid = iid
            selected_iid = current_iid or first_iid
            if selected_iid:
                tree.selection_set(selected_iid)
                tree.focus(selected_iid)
                tree.see(selected_iid)

        def select():
            selected = tree.selection() or tree.get_children()[:1]
            if not selected:
                messagebox.showwarning("تنبيه", "لا يوجد عميل مطابق للبحث", parent=win)
                return
            customer_id = int(selected[0])
            row = self.db.conn.execute("SELECT * FROM customers WHERE id=?", (customer_id,)).fetchone()
            if row:
                self._set_customer(customer_id, row["name"])
            win.destroy()

        def use_cash_customer():
            self._set_customer(1, "عميل نقدي")
            win.destroy()

        buttons = tk.Frame(win, bg=COLORS["bg"], pady=8)
        buttons.pack(fill="x")
        tk.Button(buttons, text="اختيار", command=select,
                  bg=COLORS["success"], fg="white", font=("Arial", 10, "bold"),
                  width=12).pack(side="right", padx=6)
        tk.Button(buttons, text="عميل نقدي", command=use_cash_customer,
                  bg=COLORS["accent"], fg="white", font=("Arial", 10, "bold"),
                  width=12).pack(side="right", padx=6)
        tk.Button(buttons, text="إلغاء", command=win.destroy,
                  bg=COLORS["danger"], fg="white", font=("Arial", 10, "bold"),
                  width=10).pack(side="left", padx=6)

        search_var.trace_add("write", lambda *_: load(search_var.get().strip()))
        search_entry.bind("<Return>", lambda _: select())
        tree.bind("<Double-1>", lambda _: select())
        tree.bind("<Return>", lambda _: select())
        win.bind("<Escape>", lambda _: win.destroy())

        load()
        search_entry.focus_set()

    def _save_invoice(self):
        if not self.cart:
            messagebox.showwarning("تنبيه", "السلة فارغة!")
            return
        stock_errors = self.db.validate_stock(self.cart)
        if stock_errors:
            details = "\n".join(
                f"- {item['name']}: المطلوب {item['requested']}، المتاح {item['stock']}"
                for item in stock_errors
            )
            messagebox.showerror("مخزون غير كافي", f"لا يمكن حفظ الفاتورة:\n{details}")
            return
        if not self.paid_var.get().strip():
            self._recalc()
            self.paid_var.set(f"{self._calc_cache['total']:.2f}")
        self._recalc()
        c = self._calc_cache
        if c["paid"] < c["total"]:
            if not messagebox.askyesno("تحذير", f"المبلغ المدفوع ({c['paid']:.2f}) أقل من الإجمالي ({c['total']:.2f}).\nهل تريد المتابعة؟"):
                return
        inv_data = {
            "invoice_no":  self.db.next_invoice_no(),
            "customer_id": self.customer_id,
            "date":        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "subtotal":    c["subtotal"],
            "discount":    c["disc_amt"],
            "tax":         c["tax"],
            "total":       c["total"],
            "paid":        c["paid"],
            "change_amt":  c["change"],
            "notes":       self.notes_var.get(),
            "cashier":     "الكاشير",
        }
        try:
            self.last_inv_id = self.db.save_invoice(inv_data, self.cart)
        except ValueError as exc:
            messagebox.showerror("مخزون غير كافي", str(exc))
            return
        messagebox.showinfo("✅ تم", f"تم حفظ الفاتورة رقم {inv_data['invoice_no']} بنجاح!")
        if messagebox.askyesno("طباعة", "هل تريد طباعة الفاتورة؟"):
            self._print_last()
        self._reset_pos(restore_held=True)
        self._search_products()
        try:
            self.master.master.refresh_all_views()
        except Exception:
            pass

    def _save_invoice_shortcut(self, event=None):
        if event is None:
            self._save_invoice()
            return "break"

        char = getattr(event, "char", "") or ""
        key = char.lower()
        if key in ("s", "س"):
            self._save_invoice()
            return "break"

        keysym = getattr(event, "keysym", "").lower()
        if keysym in ("s", "arabic_seen", "arabic_sheen", "seen"):
            self._save_invoice()
            return "break"

        return None

    def _print_last(self):
        if not self.last_inv_id:
            messagebox.showwarning("تنبيه", "لا توجد فاتورة محفوظة حالياً")
            return
        inv, items = self.db.get_invoice(self.last_inv_id)
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
        except Exception:
            messagebox.showinfo("تنبيه", f"تم حفظ الفاتورة في:\n{result}\nيرجى طباعتها يدوياً.")

    def _reset_pos(self, restore_held=False):
        if restore_held and self.held_sales:
            self._apply_sale_state(self.held_sales.pop())
            return
        self._clear_current_sale()
