import tkinter as tk
from tkinter import ttk, messagebox

from ui.common import BaseFrame, COLORS


class SettingsFrame(BaseFrame):
    def __init__(self, parent, db):
        super().__init__(parent, db)
        self.vars = {}
        self._build()

    def _build(self):
        self.header("إعدادات البرنامج", "⚙️")

        card = self.card(self)
        card.pack(fill="x", padx=20, pady=16)
        form = tk.Frame(card, bg=COLORS["white"], padx=20, pady=16)
        form.pack(fill="x")

        fields = [
            ("اسم المحل:", "store_name"),
            ("رقم الهاتف:", "store_phone"),
            ("العنوان:", "store_address"),
            ("نسبة الضريبة %:", "tax_rate"),
            ("العملة:", "currency"),
            ("رسالة آخر الفاتورة:", "receipt_footer"),
            ("حد تنبيه المخزون:", "low_stock_threshold"),
        ]

        settings = self.db.get_settings()
        for label, key in fields:
            row = tk.Frame(form, bg=COLORS["white"])
            row.pack(fill="x", pady=6)
            tk.Label(row, text=label, font=("Arial", 10, "bold"), bg=COLORS["white"],
                     width=18, anchor="e").pack(side="right")
            var = tk.StringVar(value=settings.get(key, ""))
            ttk.Entry(row, textvariable=var, width=36).pack(side="right", padx=8)
            self.vars[key] = var

        self.btn(form, "💾 حفظ الإعدادات", self._save, color=COLORS["success"],
                 width=18).pack(pady=12)

    def _save(self):
        try:
            tax_rate = float(self.vars["tax_rate"].get() or 0)
            low_stock = int(float(self.vars["low_stock_threshold"].get() or 0))
        except ValueError:
            messagebox.showerror("خطأ", "نسبة الضريبة وحد تنبيه المخزون يجب أن تكون أرقامًا")
            return
        if tax_rate < 0 or low_stock < 0:
            messagebox.showerror("خطأ", "الأرقام لا يمكن أن تكون سالبة")
            return

        self.db.save_settings({key: var.get().strip() for key, var in self.vars.items()})
        messagebox.showinfo("✅ تم", "تم حفظ الإعدادات بنجاح")
