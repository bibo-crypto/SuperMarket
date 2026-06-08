import os
import sys
import sqlite3
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def _runtime_root():
    if getattr(sys, "frozen", False):
        return os.path.dirname(os.path.abspath(sys.executable))
    return BASE_DIR


def _desktop_dir():
    desktop = os.path.join(os.path.expanduser("~"), "Desktop")
    return desktop if os.path.isdir(desktop) else os.path.expanduser("~")


DATA_DIR = _runtime_root()
DB_PATH = os.path.join(DATA_DIR, "supermarket.db")
PDF_DIR = os.path.join(_desktop_dir(), "NoorMarket", "Invoices")
os.makedirs(PDF_DIR, exist_ok=True)


class Database:
    def __init__(self):
        self.conn = sqlite3.connect(DB_PATH)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        self._create_tables()
        self._seed()

    def _create_tables(self):
        self.conn.executescript("""
        CREATE TABLE IF NOT EXISTS categories (
            id   INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        );

        CREATE TABLE IF NOT EXISTS products (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            barcode     TEXT UNIQUE,
            name        TEXT NOT NULL,
            category_id INTEGER REFERENCES categories(id),
            price       REAL NOT NULL CHECK(price >= 0),
            cost        REAL NOT NULL DEFAULT 0 CHECK(cost >= 0),
            stock       INTEGER NOT NULL DEFAULT 0 CHECK(stock >= 0),
            unit        TEXT DEFAULT 'قطعة',
            active      INTEGER DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS customers (
            id      INTEGER PRIMARY KEY AUTOINCREMENT,
            name    TEXT NOT NULL,
            phone   TEXT,
            points  INTEGER DEFAULT 0,
            balance REAL DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS invoices (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_no   TEXT NOT NULL UNIQUE,
            customer_id  INTEGER REFERENCES customers(id),
            date         TEXT NOT NULL,
            subtotal     REAL NOT NULL DEFAULT 0,
            discount     REAL NOT NULL DEFAULT 0,
            tax          REAL NOT NULL DEFAULT 0,
            total        REAL NOT NULL DEFAULT 0,
            paid         REAL NOT NULL DEFAULT 0,
            change_amt   REAL NOT NULL DEFAULT 0,
            status       TEXT DEFAULT 'active',
            notes        TEXT,
            cashier      TEXT DEFAULT 'الكاشير'
        );

        CREATE TABLE IF NOT EXISTS invoice_items (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_id  INTEGER NOT NULL REFERENCES invoices(id),
            product_id  INTEGER NOT NULL REFERENCES products(id),
            qty         REAL NOT NULL,
            unit_price  REAL NOT NULL,
            discount    REAL DEFAULT 0,
            total       REAL NOT NULL
        );

        CREATE TABLE IF NOT EXISTS expenses (
            id      INTEGER PRIMARY KEY AUTOINCREMENT,
            date    TEXT NOT NULL,
            desc    TEXT NOT NULL,
            amount  REAL NOT NULL,
            cat     TEXT
        );

        CREATE TABLE IF NOT EXISTS settings (
            key   TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS users (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            role     TEXT NOT NULL
        );
        """)
        self.conn.commit()

    def _seed(self):
        cats = ["مواد غذائية", "مشروبات", "منظفات", "خضروات وفواكه", "ألبان وأجبان", "مخبوزات", "أخرى"]
        for c in cats:
            self.conn.execute("INSERT OR IGNORE INTO categories(name) VALUES(?)", (c,))

        products = [
            ("P001", "أرز بسمتي 5 كيلو",   1, 28.50, 22.0, 100, "كيس"),
            ("P002", "زيت ذرة 1.5 لتر",     1, 18.00, 13.0,  80, "زجاجة"),
            ("P003", "سكر أبيض 1 كيلو",     1, 8.50,  6.0,  150, "كيس"),
            ("P004", "ماء معدني 6×1.5",     2, 14.00, 10.0, 200, "كرتون"),
            ("P005", "عصير برتقال 1 لتر",   2, 12.00,  9.0,  60, "كرتون"),
            ("P006", "مسحوق غسيل 3 كيلو",  3, 35.00, 27.0,  40, "كيس"),
            ("P007", "منظف أرضيات 1 لتر",  3, 15.00, 11.0,  55, "زجاجة"),
            ("P008", "طماطم",               4,  4.50,  3.0, 500, "كيلو"),
            ("P009", "تفاح أحمر",           4,  9.00,  7.0, 300, "كيلو"),
            ("P010", "جبن رومي",            5, 55.00, 42.0,  30, "كيلو"),
            ("P011", "لبن كامل 1 لتر",      5,  9.00,  7.0, 120, "كرتون"),
            ("P012", "خبز عيش بلدي",        6,  3.50,  2.5, 200, "رغيف"),
        ]
        for p in products:
            self.conn.execute(
                "INSERT OR IGNORE INTO products(barcode,name,category_id,price,cost,stock,unit) VALUES(?,?,?,?,?,?,?)", p)
        self.conn.execute("INSERT OR IGNORE INTO customers(id,name,phone) VALUES(1,'عميل نقدي','')")
        defaults = {
            "store_name": "سوبر ماركت نور",
            "store_phone": "",
            "store_address": "",
            "tax_rate": "14",
            "currency": "جنيه",
            "receipt_footer": "شكراً لتسوقكم معنا",
            "low_stock_threshold": "10",
        }
        for key, value in defaults.items():
            self.conn.execute("INSERT OR IGNORE INTO settings(key,value) VALUES(?,?)", (key, value))

        users = [
            ('admin', '3620713', 'admin'),
            ('cashier', '1234', 'cashier')
        ]
        for u in users:
            self.conn.execute("INSERT OR IGNORE INTO users(username, password, role) VALUES(?,?,?)", u)
        self.conn.commit()

    def verify_user(self, username, password):
        return self.conn.execute(
            "SELECT * FROM users WHERE username=? AND password=?", (username, password)
        ).fetchone()

    def get_settings(self):
        rows = self.conn.execute("SELECT key,value FROM settings").fetchall()
        settings = {row["key"]: row["value"] for row in rows}
        settings.setdefault("store_name", "سوبر ماركت نور")
        settings.setdefault("store_phone", "")
        settings.setdefault("store_address", "")
        settings.setdefault("tax_rate", "14")
        settings.setdefault("currency", "جنيه")
        settings.setdefault("receipt_footer", "شكراً لتسوقكم معنا")
        settings.setdefault("low_stock_threshold", "10")
        return settings

    def save_settings(self, settings):
        for key, value in settings.items():
            self.conn.execute(
                "INSERT INTO settings(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                (key, str(value)),
            )
        self.conn.commit()

    def get_float_setting(self, key, default=0):
        try:
            return float(self.get_settings().get(key, default))
        except (TypeError, ValueError):
            return default

    def get_int_setting(self, key, default=0):
        try:
            return int(float(self.get_settings().get(key, default)))
        except (TypeError, ValueError):
            return default

    def get_products(self, search="", cat_id=None):
        q = """SELECT p.*, c.name cat_name FROM products p
               LEFT JOIN categories c ON p.category_id=c.id
               WHERE p.active=1"""
        args = []
        if search:
            q += " AND (p.name LIKE ? OR p.barcode LIKE ?)"
            args += [f"%{search}%", f"%{search}%"]
        if cat_id:
            q += " AND p.category_id=?"
            args.append(cat_id)
        q += " ORDER BY p.name"
        return self.conn.execute(q, args).fetchall()

    def get_product_by_barcode(self, bc):
        return self.conn.execute("SELECT * FROM products WHERE barcode=? AND active=1", (bc,)).fetchone()

    def add_product(self, data):
        self.conn.execute(
            "INSERT INTO products(barcode,name,category_id,price,cost,stock,unit) VALUES(:barcode,:name,:category_id,:price,:cost,:stock,:unit)", data)
        self.conn.commit()

    def update_product(self, pid, data):
        self.conn.execute(
            "UPDATE products SET barcode=:barcode,name=:name,category_id=:category_id,price=:price,cost=:cost,stock=:stock,unit=:unit WHERE id=:id",
            {**data, "id": pid})
        self.conn.commit()

    def delete_product(self, pid):
        self.conn.execute("UPDATE products SET active=0 WHERE id=?", (pid,))
        self.conn.commit()

    def get_categories(self):
        return self.conn.execute("SELECT * FROM categories ORDER BY name").fetchall()

    def get_customers(self, search=""):
        q = "SELECT * FROM customers WHERE 1"
        args = []
        if search:
            q += " AND (name LIKE ? OR phone LIKE ?)"
            args += [f"%{search}%", f"%{search}%"]
        return self.conn.execute(q, args).fetchall()

    def add_customer(self, name, phone):
        self.conn.execute("INSERT INTO customers(name,phone) VALUES(?,?)", (name, phone))
        self.conn.commit()

    def update_customer(self, cid, name, phone):
        self.conn.execute("UPDATE customers SET name=?,phone=? WHERE id=?", (name, phone, cid))
        self.conn.commit()

    def next_invoice_no(self):
        row = self.conn.execute("SELECT COUNT(*) n FROM invoices").fetchone()
        return f"INV-{row['n']+1:04d}"

    def save_invoice(self, inv, items):
        stock_errors = self.validate_stock(items)
        if stock_errors:
            raise ValueError("\n".join(
                f"{item['name']}: المطلوب {item['requested']}, المتاح {item['stock']}"
                for item in stock_errors
            ))
        with self.conn:
            cur = self.conn.cursor()
            cur.execute("""INSERT INTO invoices
                (invoice_no,customer_id,date,subtotal,discount,tax,total,paid,change_amt,notes,cashier)
                VALUES(:invoice_no,:customer_id,:date,:subtotal,:discount,:tax,:total,:paid,:change_amt,:notes,:cashier)""", inv)
            inv_id = cur.lastrowid
            for it in items:
                cur.execute(
                    "INSERT INTO invoice_items(invoice_id,product_id,qty,unit_price,discount,total) VALUES(?,?,?,?,?,?)",
                    (inv_id, it["product_id"], it["qty"], it["unit_price"], it.get("discount", 0), it["total"]))
                cur.execute("UPDATE products SET stock=stock-? WHERE id=?", (it["qty"], it["product_id"]))
        return inv_id

    def validate_stock(self, items):
        requested = {}
        for item in items:
            requested[item["product_id"]] = requested.get(item["product_id"], 0) + item["qty"]

        errors = []
        for product_id, qty in requested.items():
            row = self.conn.execute(
                "SELECT name,stock FROM products WHERE id=? AND active=1", (product_id,)
            ).fetchone()
            if not row or qty > row["stock"]:
                errors.append({
                    "product_id": product_id,
                    "name": row["name"] if row else f"#{product_id}",
                    "requested": qty,
                    "stock": row["stock"] if row else 0,
                })
        return errors

    def get_invoices(self, search="", status=None, date_from=None, date_to=None):
        q = """SELECT i.*, c.name cust_name FROM invoices i
               LEFT JOIN customers c ON i.customer_id=c.id WHERE 1"""
        args = []
        if search:
            q += " AND (i.invoice_no LIKE ? OR c.name LIKE ?)"
            args += [f"%{search}%", f"%{search}%"]
        if status:
            q += " AND i.status=?"
            args.append(status)
        if date_from:
            q += " AND i.date >= ?"
            args.append(date_from)
        if date_to:
            q += " AND i.date <= ?"
            args.append(date_to)
        q += " ORDER BY i.id DESC"
        return self.conn.execute(q, args).fetchall()

    def get_invoice(self, inv_id):
        inv = self.conn.execute("SELECT i.*,c.name cust_name FROM invoices i LEFT JOIN customers c ON i.customer_id=c.id WHERE i.id=?", (inv_id,)).fetchone()
        items = self.conn.execute("""SELECT ii.*,p.name pname,p.unit FROM invoice_items ii
                                     JOIN products p ON ii.product_id=p.id WHERE ii.invoice_id=?""", (inv_id,)).fetchall()
        return inv, items

    def cancel_invoice(self, inv_id):
        inv, items = self.get_invoice(inv_id)
        if inv["status"] == "cancelled":
            return False
        for it in items:
            self.conn.execute("UPDATE products SET stock=stock+? WHERE id=?", (it["qty"], it["product_id"]))
        self.conn.execute("UPDATE invoices SET status='cancelled' WHERE id=?", (inv_id,))
        self.conn.commit()
        return True

    def update_invoice(self, inv_id, new_inv, new_items):
        inv, old_items = self.get_invoice(inv_id)
        if inv["status"] == "cancelled":
            return False

        with self.conn:
            for it in old_items:
                self.conn.execute("UPDATE products SET stock=stock+? WHERE id=?", (it["qty"], it["product_id"]))

            stock_errors = self.validate_stock(new_items)
            if stock_errors:
                raise ValueError("\n".join(
                    f"{item['name']}: المطلوب {item['requested']}, المتاح {item['stock']}"
                    for item in stock_errors
                ))

            self.conn.execute("DELETE FROM invoice_items WHERE invoice_id=?", (inv_id,))
            self.conn.execute("""UPDATE invoices SET customer_id=:customer_id,subtotal=:subtotal,discount=:discount,
                tax=:tax,total=:total,paid=:paid,change_amt=:change_amt,notes=:notes,status='edited' WHERE id=:id""",
                {**new_inv, "id": inv_id})
            for it in new_items:
                self.conn.execute(
                    "INSERT INTO invoice_items(invoice_id,product_id,qty,unit_price,discount,total) VALUES(?,?,?,?,?,?)",
                    (inv_id, it["product_id"], it["qty"], it["unit_price"], it.get("discount", 0), it["total"]))
                self.conn.execute("UPDATE products SET stock=stock-? WHERE id=?", (it["qty"], it["product_id"]))
        return True

    def daily_summary(self, date=None):
        date = date or datetime.now().strftime("%Y-%m-%d")
        return self.conn.execute("""
            SELECT COUNT(*) cnt, SUM(total) total, SUM(discount) disc
            FROM invoices WHERE date LIKE ? AND status!='cancelled'
        """, (f"{date}%",)).fetchone()

    def top_products(self, limit=10):
        return self.conn.execute("""
            SELECT p.name, SUM(ii.qty) qty, SUM(ii.total) revenue
            FROM invoice_items ii JOIN products p ON ii.product_id=p.id
            JOIN invoices inv ON ii.invoice_id=inv.id
            WHERE inv.status!='cancelled'
            GROUP BY p.id ORDER BY revenue DESC LIMIT ?
        """, (limit,)).fetchall()

    def low_stock(self, threshold=None):
        if threshold is None:
            threshold = self.get_int_setting("low_stock_threshold", 10)
        return self.conn.execute(
            "SELECT * FROM products WHERE stock<=? AND active=1 ORDER BY stock", (threshold,)).fetchall()


def _text_receipt(inv, items):
    lines = [
        "=" * 40,
        "       سوبر ماركت نور",
        "=" * 40,
        f"رقم الفاتورة : {inv['invoice_no']}",
        f"التاريخ      : {inv['date']}",
        f"العميل       : {inv.get('cust_name','عميل نقدي')}",
        "-" * 40,
        f"{'الصنف':<20} {'كمية':>4} {'سعر':>6} {'إجمالي':>7}",
        "-" * 40,
    ]
    for it in items:
        lines.append(f"{it['pname'][:20]:<20} {it['qty']:>4.0f} {it['unit_price']:>6.2f} {it['total']:>7.2f}")
    lines += [
        "-" * 40,
        f"{'المجموع الفرعي':<25} {inv['subtotal']:>7.2f}",
        f"{'الضريبة':<25} {inv['tax']:>7.2f}",
        f"{'الإجمالي':<25} {inv['total']:>7.2f}",
        f"{'المدفوع':<25} {inv['paid']:>7.2f}",
        f"{'الباقي':<25} {inv['change_amt']:>7.2f}",
        "=" * 40,
        "     شكراً لتسوقكم معنا",
        "=" * 40,
    ]
    return "\n".join(lines)


def print_invoice_pdf(inv, items, filepath):
    # المكتبات الأساسية للـ PDF (مطلوبة)
    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib import colors
        from reportlab.lib.units import mm
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
    except ImportError:
        # إذا لم تكن مكتبة reportlab مثبتة، يتم العودة لطباعة ملف نصي
        txt_path = filepath.replace(".pdf", ".txt")
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(_text_receipt(inv, items))
        return txt_path

    # مكتبات دعم اللغة العربية (اختيارية)
    arabic_lib_available = False
    try:
        import arabic_reshaper
        from bidi.algorithm import get_display
        arabic_lib_available = True
    except ImportError:
        pass

    # مكتبات الـ QR Code (اختيارية)
    qr_path = None
    try:
        import qrcode
        from PIL import Image
        qr = qrcode.QRCode(version=1, box_size=3, border=1)
        qr.add_data(inv["invoice_no"])
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color="black", back_color="white")
        qr_path = filepath.replace(".pdf", "_qr.png")
        qr_img.save(qr_path)
    except ImportError:
        pass

    font_name = "Helvetica"
    arabic_available = False
    for fp in ["/usr/share/fonts/truetype/arabeyes/ae_AlArabiya.ttf",
               "C:/Windows/Fonts/arial.ttf", "C:/Windows/Fonts/Arial.ttf",
               "/Library/Fonts/Arial.ttf", "/System/Library/Fonts/Arial.ttf",
               "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]:
        if os.path.exists(fp):
            try:
                pdfmetrics.registerFont(TTFont("Arabic", fp))
                font_name = "Arabic"
                arabic_available = True
            except Exception:
                pass
            break

    def ar(text):
        if arabic_available and arabic_lib_available:
            try:
                reshaped = arabic_reshaper.reshape(str(text))
                return get_display(reshaped)
            except Exception:
                return str(text)
        return str(text)

    settings = inv.get("settings") or {}
    store_name = settings.get("store_name", "سوبر ماركت نور")
    store_phone = settings.get("store_phone", "")
    store_address = settings.get("store_address", "")
    currency = settings.get("currency", "جنيه")
    footer = settings.get("receipt_footer", "شكراً لتسوقكم معنا")

    w = 80 * mm
    h = max(150, 95 + len(items) * 9 + (8 if inv.get("notes") else 0)) * mm
    c = canvas.Canvas(filepath, pagesize=(w, h))

    c.setFillColor(colors.HexColor("#1a5276"))
    c.rect(0, h-24*mm, w, 24*mm, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont(font_name, 13)
    c.drawCentredString(w/2, h-9*mm, ar(store_name))
    c.setFont(font_name, 8)
    c.drawCentredString(w/2, h-15*mm, ar("فاتورة مبيعات"))
    if store_phone:
        c.drawCentredString(w/2, h-20*mm, ar(store_phone))

    if qr_path and os.path.exists(qr_path):
        try:
            c.drawImage(qr_path, 4*mm, h-22*mm, width=16*mm, height=16*mm)
        except Exception:
            pass

    y = h - 30*mm
    c.setFillColor(colors.black)
    c.setFont(font_name, 8)

    def row(label, val, bold=False):
        nonlocal y
        if bold:
            c.setFont(font_name, 9)
        c.drawString(4*mm, y, ar(val))
        c.drawRightString(w-4*mm, y, ar(label))
        c.setFont(font_name, 8)
        y -= 4.5*mm

    row("رقم الفاتورة:", inv["invoice_no"], bold=True)
    row("التاريخ:", inv["date"])
    row("العميل:", inv.get("cust_name") or "عميل نقدي")
    row("الكاشير:", inv.get("cashier") or "")
    if store_address:
        row("العنوان:", store_address)

    y -= 2*mm
    c.setStrokeColor(colors.HexColor("#aab7b8"))
    c.line(4*mm, y, w-4*mm, y)
    y -= 5*mm

    c.setFillColor(colors.HexColor("#d5dbdb"))
    c.rect(4*mm, y-4*mm, w-8*mm, 7*mm, fill=1, stroke=0)
    c.setFillColor(colors.black)
    c.setFont(font_name, 7)
    c.drawString(4*mm, y, ar("الإجمالي"))
    c.drawString(23*mm, y, ar("السعر"))
    c.drawString(39*mm, y, ar("كمية"))
    c.drawRightString(w-4*mm, y, ar("الصنف"))
    y -= 7*mm

    c.setFont(font_name, 7)
    for it in items:
        c.drawString(4*mm, y, f"{it['total']:.2f}")
        c.drawString(23*mm, y, f"{it['unit_price']:.2f}")
        c.drawString(40*mm, y, f"{it['qty']:.0f}")
        c.drawRightString(w-4*mm, y, ar(str(it["pname"])[:18]))
        y -= 4.5*mm

    y -= 2*mm
    c.line(4*mm, y, w-4*mm, y)
    y -= 5*mm

    c.setFont(font_name, 8)
    row("المجموع الفرعي:", f"{inv['subtotal']:.2f} {currency}", bold=True)
    if inv["tax"] > 0:
        row("الضريبة:", f"{inv['tax']:.2f} {currency}")
    c.setFont(font_name, 10)
    row("الإجمالي:", f"{inv['total']:.2f} {currency}", bold=True)
    c.setFont(font_name, 8)
    row("المدفوع:", f"{inv['paid']:.2f} {currency}")
    row("الباقي:", f"{inv['change_amt']:.2f} {currency}")

    if inv.get("notes"):
        y -= 3*mm
        c.drawRightString(w-4*mm, y, ar(f"ملاحظات: {inv['notes']}"))

    y -= 8*mm
    c.setFont(font_name, 7)
    c.setFillColor(colors.grey)
    c.drawCentredString(w/2, y, ar(footer))

    c.save()
    
    # تنظيف صورة الـ QR المؤقتة
    if qr_path and os.path.exists(qr_path):
        try:
            os.remove(qr_path)
        except Exception:
            pass
    
    return filepath
