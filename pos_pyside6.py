"""
VoltPoint POS  -  PySide6 edition (Qt, styled with QSS)
Run:  pip install PySide6
      python pos_pyside6.py
"""
import copy
import sys
from datetime import datetime

from PySide6.QtCore import QTimer, Qt, Signal
from PySide6.QtWidgets import (
    QApplication, QButtonGroup, QDialog, QDoubleSpinBox, QComboBox, QFrame,
    QGridLayout, QHBoxLayout, QHeaderView, QLabel, QLineEdit, QMainWindow,
    QMessageBox, QPushButton, QScrollArea, QTableWidget, QTableWidgetItem,
    QTextEdit, QVBoxLayout, QWidget, QAbstractItemView,
)

VAT_RATE = 0.18
CATEGORIES = ["All", "Laptops", "Phones", "Audio", "Accessories", "Networking"]

PRODUCTS = [
    (1, "MacBook Air M2", "Laptops", 4_850_000, 6, "💻"),
    (2, "Dell XPS 13", "Laptops", 5_200_000, 4, "💻"),
    (3, "HP Pavilion 15", "Laptops", 2_900_000, 9, "💻"),
    (4, "iPhone 15", "Phones", 3_700_000, 10, "📱"),
    (5, "Samsung Galaxy S24", "Phones", 3_300_000, 8, "📱"),
    (6, "Tecno Camon 30", "Phones", 980_000, 15, "📱"),
    (7, "AirPods Pro 2", "Audio", 950_000, 12, "🎧"),
    (8, "Sony WH-1000XM5", "Audio", 1_350_000, 5, "🎧"),
    (9, "JBL Flip 6", "Audio", 520_000, 3, "🔊"),
    (10, "USB-C Fast Charger 65W", "Accessories", 95_000, 40, "🔌"),
    (11, "Wireless Mouse", "Accessories", 65_000, 25, "🖱️"),
    (12, "Mechanical Keyboard", "Accessories", 240_000, 7, "⌨️"),
    (13, "Power Bank 20,000mAh", "Accessories", 150_000, 2, "🔋"),
    (14, "Wi-Fi 6 Router", "Networking", 320_000, 11, "📡"),
    (15, "Ethernet Cable 10m", "Networking", 25_000, 60, "🔗"),
    (16, "128GB Flash Drive", "Accessories", 45_000, 0, "💾"),
]

QSS = """
* { font-family: "Segoe UI", "Inter", "Noto Sans", sans-serif; color: #e8ecf4; font-size: 14px; }
QMainWindow, #root { background: #0e121b; }
#cartPanel { background: #161c28; }
#brand { font-size: 26px; font-weight: 700; color: #3d8bff; }
#muted { color: #8b95ab; font-size: 13px; }
#h2 { font-size: 22px; font-weight: 700; }

#stat, #card { background: #1a2130; border: 1px solid #252d3f; border-radius: 16px; }
#card:hover { border: 1px solid #3d8bff; }
#statValue { font-size: 22px; font-weight: 700; background: transparent; }
#cardPrice { font-size: 17px; font-weight: 700; color: #3d8bff; background: transparent; }
#cardName { font-size: 15px; font-weight: 700; background: transparent; }
#cardIcon { font-size: 38px; background: transparent; }
#ok { color: #22c55e; background: transparent; }
#warn { color: #f59e0b; background: transparent; }
#bad { color: #ef4444; background: transparent; }

QLabel { background: transparent; }
QLineEdit, QDoubleSpinBox, QComboBox {
    background: #161c28; border: 1px solid #252d3f; border-radius: 12px; padding: 10px 14px;
}
QLineEdit:focus, QDoubleSpinBox:focus, QComboBox:focus { border: 1px solid #3d8bff; }
QComboBox QAbstractItemView { background: #1a2130; selection-background-color: #3d8bff; border: 0; }

QPushButton { background: #1a2130; border: 1px solid #252d3f; border-radius: 10px; padding: 8px 14px; font-weight: 600; }
QPushButton:hover { background: #252d3f; }
QPushButton#pill { background: #161c28; border-radius: 12px; padding: 8px 18px; }
QPushButton#pill:checked { background: #3d8bff; border-color: #3d8bff; color: white; }
QPushButton#primary { background: #3d8bff; border: 0; color: white; }
QPushButton#primary:hover { background: #2f74e0; }
QPushButton#primary:disabled { background: #252d3f; color: #6b7280; }
QPushButton#charge { background: #22c55e; border: 0; border-radius: 14px; color: #06210f; font-size: 17px; font-weight: 700; padding: 15px; }
QPushButton#charge:hover { background: #16a34a; }
QPushButton#danger { color: #ef4444; }

QTableWidget { background: transparent; border: 0; gridline-color: transparent; outline: 0; }
QTableWidget::item { border-bottom: 1px solid #252d3f; padding: 6px; }
QTableWidget::item:selected { background: #22304d; color: white; }
QHeaderView::section { background: transparent; color: #8b95ab; border: 0; padding: 8px; font-weight: 600; }

QScrollArea { border: 0; background: transparent; }
QScrollBar:vertical { background: transparent; width: 10px; }
QScrollBar::handle:vertical { background: #252d3f; border-radius: 5px; min-height: 30px; }
QScrollBar::add-line, QScrollBar::sub-line { height: 0; }
QTextEdit { background: #1a2130; border: 0; border-radius: 12px; padding: 12px; font-family: "Courier New", monospace; }
QDialog { background: #0e121b; }
"""


def money(n):
    return f"UGX {n:,.0f}"


class ProductCard(QFrame):
    clicked = Signal(int)

    def __init__(self, p, left):
        super().__init__()
        self.pid = p["id"]
        self.available = left > 0
        self.setObjectName("card")
        self.setCursor(Qt.PointingHandCursor if self.available else Qt.ForbiddenCursor)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(18, 16, 18, 16)
        lay.setSpacing(3)

        icon = QLabel(p["icon"])
        icon.setObjectName("cardIcon")
        name = QLabel(p["name"])
        name.setObjectName("cardName")
        name.setWordWrap(True)
        cat = QLabel(p["cat"])
        cat.setObjectName("muted")
        price = QLabel(money(p["price"]))
        price.setObjectName("cardPrice")

        if left <= 0:
            note, kind = "Out of stock", "bad"
        elif left <= 5:
            note, kind = f"Only {left} left", "warn"
        else:
            note, kind = f"{left} in stock", "ok"
        stock = QLabel(note)
        stock.setObjectName(kind)

        for w in (icon, name, cat, price, stock):
            lay.addWidget(w)
        if not self.available:
            self.setToolTip("Out of stock")

    def mousePressEvent(self, event):
        if self.available and event.button() == Qt.LeftButton:
            self.clicked.emit(self.pid)


class POSWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("VoltPoint POS")
        self.resize(1440, 860)
        self.setMinimumSize(1200, 700)

        self.products = {
            p[0]: dict(id=p[0], name=p[1], cat=p[2], price=p[3], stock=p[4], icon=p[5])
            for p in copy.deepcopy(PRODUCTS)
        }
        self.cart = {}
        self.category = "All"
        self.revenue = 0
        self.tx_count = 0

        root = QWidget()
        root.setObjectName("root")
        self.setCentralWidget(root)
        row = QHBoxLayout(root)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(0)
        row.addWidget(self.build_catalog(), 1)
        row.addWidget(self.build_cart())

        self.render_products()
        self.render_cart()
        self.refresh_stats()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.tick)
        self.timer.start(1000)
        self.tick()

    # ------------------------------------------------------------ CATALOG --
    def build_catalog(self):
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(24, 22, 14, 22)
        lay.setSpacing(14)

        head = QHBoxLayout()
        brand = QLabel("⚡ VoltPoint")
        brand.setObjectName("brand")
        self.clock = QLabel()
        self.clock.setObjectName("muted")
        head.addWidget(brand)
        head.addStretch()
        head.addWidget(self.clock)
        lay.addLayout(head)

        stats = QHBoxLayout()
        self.stat_rev = self.stat_box(stats, "Sales today")
        self.stat_tx = self.stat_box(stats, "Transactions")
        self.stat_low = self.stat_box(stats, "Low / out of stock")
        lay.addLayout(stats)

        self.search = QLineEdit()
        self.search.setPlaceholderText("🔍  Search products…")
        self.search.textChanged.connect(self.render_products)
        lay.addWidget(self.search)

        pills = QHBoxLayout()
        pills.setSpacing(8)
        self.group = QButtonGroup(self)
        for name in CATEGORIES:
            b = QPushButton(name)
            b.setObjectName("pill")
            b.setCheckable(True)
            b.setChecked(name == "All")
            b.setCursor(Qt.PointingHandCursor)
            b.clicked.connect(lambda _, n=name: self.set_category(n))
            self.group.addButton(b)
            pills.addWidget(b)
        pills.addStretch()
        lay.addLayout(pills)

        self.grid_host = QWidget()
        self.grid = QGridLayout(self.grid_host)
        self.grid.setContentsMargins(0, 0, 8, 0)
        self.grid.setSpacing(14)
        for c in range(3):
            self.grid.setColumnStretch(c, 1)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self.grid_host)
        lay.addWidget(scroll, 1)
        return page

    def stat_box(self, parent_layout, title):
        box = QFrame()
        box.setObjectName("stat")
        v = QVBoxLayout(box)
        v.setContentsMargins(18, 12, 18, 12)
        v.setSpacing(0)
        t = QLabel(title)
        t.setObjectName("muted")
        val = QLabel("–")
        val.setObjectName("statValue")
        v.addWidget(t)
        v.addWidget(val)
        parent_layout.addWidget(box)
        return val

    def set_category(self, name):
        self.category = name
        self.render_products()

    def tick(self):
        self.clock.setText(datetime.now().strftime("%a %d %b %Y   %H:%M:%S"))

    def render_products(self):
        while self.grid.count():
            w = self.grid.takeAt(0).widget()
            if w:
                w.deleteLater()
        q = self.search.text().strip().lower()
        items = [p for p in self.products.values()
                 if (self.category == "All" or p["cat"] == self.category) and q in p["name"].lower()]
        if not items:
            empty = QLabel("No products match. Try another search.")
            empty.setObjectName("muted")
            empty.setAlignment(Qt.AlignCenter)
            self.grid.addWidget(empty, 0, 0, 1, 3)
        for i, p in enumerate(items):
            card = ProductCard(p, p["stock"] - self.cart.get(p["id"], 0))
            card.clicked.connect(self.add)
            self.grid.addWidget(card, i // 3, i % 3)
        self.grid.setRowStretch(len(items) // 3 + 1, 1)

    # --------------------------------------------------------------- CART --
    def build_cart(self):
        panel = QFrame()
        panel.setObjectName("cartPanel")
        panel.setFixedWidth(430)
        lay = QVBoxLayout(panel)
        lay.setContentsMargins(22, 24, 22, 22)
        lay.setSpacing(10)

        head = QHBoxLayout()
        title = QLabel("Current sale")
        title.setObjectName("h2")
        clear = QPushButton("Clear")
        clear.clicked.connect(self.clear_cart)
        head.addWidget(title)
        head.addStretch()
        head.addWidget(clear)
        lay.addLayout(head)

        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["Item", "Qty", "Total"])
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.verticalHeader().setDefaultSectionSize(44)
        hh = self.table.horizontalHeader()
        hh.setSectionResizeMode(0, QHeaderView.Stretch)
        hh.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        lay.addWidget(self.table, 1)

        qty = QHBoxLayout()
        for text, fn, name in (("−", lambda: self.change_qty(-1), ""),
                               ("+", lambda: self.change_qty(1), ""),
                               ("Remove", self.remove_item, "danger")):
            b = QPushButton(text)
            if name:
                b.setObjectName(name)
            b.clicked.connect(fn)
            qty.addWidget(b)
        lay.addLayout(qty)

        disc_row = QHBoxLayout()
        disc_row.addWidget(self.muted_label("Discount %"))
        disc_row.addStretch()
        self.discount = QDoubleSpinBox()
        self.discount.setRange(0, 100)
        self.discount.setDecimals(1)
        self.discount.setFixedWidth(100)
        self.discount.valueChanged.connect(self.update_totals)
        disc_row.addWidget(self.discount)
        lay.addLayout(disc_row)

        self.lbl_sub = self.total_row(lay, "Subtotal")
        self.lbl_disc = self.total_row(lay, "Discount")
        self.lbl_vat = self.total_row(lay, "VAT (18%)")

        line = QFrame()
        line.setFixedHeight(1)
        line.setStyleSheet("background:#252d3f;")
        lay.addWidget(line)

        tot = QHBoxLayout()
        label = QLabel("Total")
        label.setStyleSheet("font-size:18px; font-weight:700;")
        self.lbl_total = QLabel()
        self.lbl_total.setStyleSheet("font-size:24px; font-weight:700; color:#3d8bff;")
        tot.addWidget(label)
        tot.addStretch()
        tot.addWidget(self.lbl_total)
        lay.addLayout(tot)

        self.payment = QComboBox()
        self.payment.addItems(["Cash", "Mobile Money", "Card"])
        lay.addWidget(self.payment)

        charge = QPushButton("Charge customer")
        charge.setObjectName("charge")
        charge.setCursor(Qt.PointingHandCursor)
        charge.clicked.connect(self.checkout)
        lay.addWidget(charge)
        return panel

    def muted_label(self, text):
        l = QLabel(text)
        l.setObjectName("muted")
        return l

    def total_row(self, parent_layout, label):
        row = QHBoxLayout()
        value = QLabel()
        row.addWidget(self.muted_label(label))
        row.addStretch()
        row.addWidget(value)
        parent_layout.addLayout(row)
        return value

    def add(self, pid):
        if self.cart.get(pid, 0) >= self.products[pid]["stock"]:
            return
        self.cart[pid] = self.cart.get(pid, 0) + 1
        self.refresh_all()

    def selected_cart_id(self):
        r = self.table.currentRow()
        if r < 0:
            return None
        return self.table.item(r, 0).data(Qt.UserRole)

    def change_qty(self, delta):
        pid = self.selected_cart_id()
        if pid is None:
            return
        new = self.cart[pid] + delta
        if new <= 0:
            del self.cart[pid]
        elif new <= self.products[pid]["stock"]:
            self.cart[pid] = new
        self.refresh_all()
        self.reselect(pid)

    def reselect(self, pid):
        for r in range(self.table.rowCount()):
            if self.table.item(r, 0).data(Qt.UserRole) == pid:
                self.table.selectRow(r)

    def remove_item(self):
        pid = self.selected_cart_id()
        if pid is not None:
            del self.cart[pid]
            self.refresh_all()

    def clear_cart(self):
        self.cart.clear()
        self.refresh_all()

    def refresh_all(self):
        self.render_cart()
        self.render_products()

    def render_cart(self):
        self.table.setRowCount(0)
        for pid, qty in self.cart.items():
            p = self.products[pid]
            r = self.table.rowCount()
            self.table.insertRow(r)
            name = QTableWidgetItem(p["name"])
            name.setData(Qt.UserRole, pid)
            q = QTableWidgetItem(str(qty))
            q.setTextAlignment(Qt.AlignCenter)
            t = QTableWidgetItem(money(p["price"] * qty))
            t.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            for col, item in enumerate((name, q, t)):
                self.table.setItem(r, col, item)
        self.update_totals()

    def totals(self):
        sub = sum(self.products[i]["price"] * q for i, q in self.cart.items())
        disc = sub * self.discount.value() / 100
        vat = (sub - disc) * VAT_RATE
        return sub, disc, vat, sub - disc + vat

    def update_totals(self, *_):
        sub, disc, vat, total = self.totals()
        self.lbl_sub.setText(money(sub))
        self.lbl_disc.setText("– " + money(disc))
        self.lbl_vat.setText(money(vat))
        self.lbl_total.setText(money(total))

    # ----------------------------------------------------------- CHECKOUT --
    def checkout(self):
        if not self.cart:
            QMessageBox.information(self, "Empty cart", "Add at least one product before charging.")
            return
        sub, disc, vat, total = self.totals()
        self.tx_count += 1
        self.revenue += total
        lines = [
            "        VOLTPOINT TECH STORE",
            "     Kampala, Uganda  |  Tel 0700 000 000",
            "-" * 40,
            f"Receipt #{self.tx_count:04d}",
            datetime.now().strftime("%d %b %Y  %H:%M"),
            "-" * 40,
        ]
        for pid, qty in self.cart.items():
            p = self.products[pid]
            lines.append(p["name"][:40])
            lines.append(f"  {qty} x {p['price']:,.0f}".ljust(24) + f"{p['price'] * qty:>16,.0f}")
            p["stock"] -= qty
        lines += [
            "-" * 40,
            f"{'Subtotal':<20}{sub:>20,.0f}",
            f"{'Discount':<20}{-disc:>20,.0f}",
            f"{'VAT 18%':<20}{vat:>20,.0f}",
            f"{'TOTAL (UGX)':<20}{total:>20,.0f}",
            f"{'Paid by':<20}{self.payment.currentText():>20}",
            "-" * 40,
            "      Thank you for shopping with us!",
        ]
        self.cart.clear()
        self.discount.setValue(0)
        self.refresh_all()
        self.refresh_stats()
        self.show_receipt("\n".join(lines))

    def show_receipt(self, text):
        dlg = QDialog(self)
        dlg.setWindowTitle("Receipt")
        dlg.resize(440, 620)
        v = QVBoxLayout(dlg)
        v.setContentsMargins(20, 20, 20, 20)
        title = QLabel("✅ Payment received")
        title.setStyleSheet("font-size:20px; font-weight:700; color:#22c55e;")
        box = QTextEdit()
        box.setReadOnly(True)
        box.setPlainText(text)
        done = QPushButton("Done")
        done.setObjectName("primary")
        done.clicked.connect(dlg.accept)
        v.addWidget(title)
        v.addWidget(box, 1)
        v.addWidget(done)
        dlg.exec()

    def refresh_stats(self):
        self.stat_rev.setText(money(self.revenue))
        self.stat_tx.setText(str(self.tx_count))
        self.stat_low.setText(str(sum(1 for p in self.products.values() if p["stock"] <= 5)))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet(QSS)
    win = POSWindow()
    win.show()
    sys.exit(app.exec())
