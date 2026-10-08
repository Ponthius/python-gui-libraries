"""
VoltPoint POS  -  CustomTkinter edition (modern UI)
Run:  pip install customtkinter
      python pos_customtkinter.py
"""
import copy
from datetime import datetime
from tkinter import messagebox

import customtkinter as ctk

# ----------------------------------------------------------------- THEME ---
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# (light, dark) colour pairs so the app works in both modes
BG = ("#eef1f6", "#0e121b")
PANEL = ("#ffffff", "#161c28")
CARD = ("#ffffff", "#1a2130")
BORDER = ("#dde2ec", "#252d3f")
TEXT = ("#111827", "#e8ecf4")
MUTED = ("#6b7280", "#8b95ab")
ACCENT = ("#2563eb", "#3d8bff")
ACCENT_HOVER = ("#1d4ed8", "#2f74e0")
OK = "#22c55e"
WARN = "#f59e0b"
BAD = "#ef4444"

FONT = "Segoe UI"  # falls back automatically on Linux/macOS
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


def money(n):
    return f"UGX {n:,.0f}"


# ------------------------------------------------------------------- APP ---
class POSApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("VoltPoint POS")
        self.geometry("1440x860")
        self.minsize(1200, 720)
        self.configure(fg_color=BG)

        self.products = {
            p[0]: dict(id=p[0], name=p[1], cat=p[2], price=p[3], stock=p[4], icon=p[5])
            for p in copy.deepcopy(PRODUCTS)
        }
        self.cart = {}  # product id -> quantity
        self.category = "All"
        self.revenue = 0
        self.tx_count = 0

        self.search_var = ctk.StringVar()
        self.discount_var = ctk.StringVar(value="0")
        self.payment_var = ctk.StringVar(value="Cash")
        self.search_var.trace_add("write", lambda *_: self.render_products())
        self.discount_var.trace_add("write", lambda *_: self.update_totals())

        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)

        self.build_sidebar()
        self.build_catalog()
        self.build_cart()

        self.build_cards()
        self.render_products()
        self.render_cart()
        self.refresh_stats()
        self.tick()

    # ------------------------------------------------------------ SIDEBAR --
    def build_sidebar(self):
        bar = ctk.CTkFrame(self, width=230, corner_radius=0, fg_color=PANEL)
        bar.grid(row=0, column=0, sticky="nsew")
        bar.grid_propagate(False)

        ctk.CTkLabel(bar, text="⚡ VoltPoint", font=(FONT, 26, "bold"),
                     text_color=ACCENT).pack(anchor="w", padx=24, pady=(28, 0))
        ctk.CTkLabel(bar, text="Tech store checkout", font=(FONT, 13),
                     text_color=MUTED).pack(anchor="w", padx=24, pady=(0, 24))

        self.clock = ctk.CTkLabel(bar, text="", font=(FONT, 13), text_color=MUTED,
                                  justify="left")
        self.clock.pack(anchor="w", padx=24)

        user = ctk.CTkFrame(bar, fg_color=BG, corner_radius=14)
        user.pack(fill="x", padx=18, pady=22)
        ctk.CTkLabel(user, text="👤", font=(FONT, 24)).grid(row=0, column=0, rowspan=2,
                                                            padx=(14, 10), pady=12)
        ctk.CTkLabel(user, text="Cashier 01", font=(FONT, 14, "bold"),
                     text_color=TEXT).grid(row=0, column=1, sticky="w", pady=(12, 0))
        ctk.CTkLabel(user, text="Main counter", font=(FONT, 12),
                     text_color=MUTED).grid(row=1, column=1, sticky="w", pady=(0, 12))

        ctk.CTkLabel(bar, text="Running low", font=(FONT, 14, "bold"),
                     text_color=TEXT).pack(anchor="w", padx=24, pady=(6, 6))
        self.low_label = ctk.CTkLabel(bar, text="", font=(FONT, 13), text_color=WARN,
                                      justify="left", anchor="w", wraplength=185)
        self.low_label.pack(anchor="w", padx=24)

        switch = ctk.CTkSwitch(bar, text="Dark mode", font=(FONT, 13), text_color=TEXT,
                               command=self.toggle_theme)
        switch.select()
        switch.pack(side="bottom", anchor="w", padx=24, pady=26)

    def toggle_theme(self):
        ctk.set_appearance_mode("light" if ctk.get_appearance_mode() == "Dark" else "dark")

    def tick(self):
        self.clock.configure(text=datetime.now().strftime("%A, %d %b %Y\n%H:%M:%S"))
        self.after(1000, self.tick)

    # ------------------------------------------------------------ CATALOG --
    def build_catalog(self):
        main = ctk.CTkFrame(self, fg_color="transparent")
        main.grid(row=0, column=1, sticky="nsew", padx=24, pady=24)
        main.columnconfigure(0, weight=1)
        main.rowconfigure(3, weight=1)

        # stats row
        stats = ctk.CTkFrame(main, fg_color="transparent")
        stats.grid(row=0, column=0, sticky="ew")
        for i in range(3):
            stats.columnconfigure(i, weight=1, uniform="stat")
        self.stat_rev = self.make_stat(stats, 0, "Sales today")
        self.stat_tx = self.make_stat(stats, 1, "Transactions")
        self.stat_stock = self.make_stat(stats, 2, "Units in stock")

        # search
        search = ctk.CTkEntry(main, textvariable=self.search_var, height=48,
                              corner_radius=14, border_width=1, border_color=BORDER,
                              fg_color=PANEL, font=(FONT, 15),
                              placeholder_text="🔍  Search products…")
        search.grid(row=1, column=0, sticky="ew", pady=(20, 12))

        # category pills
        self.pills = ctk.CTkSegmentedButton(
            main, values=CATEGORIES, command=self.set_category, height=38,
            font=(FONT, 13, "bold"), corner_radius=12, fg_color=PANEL,
            selected_color=ACCENT, selected_hover_color=ACCENT_HOVER,
            unselected_color=PANEL, unselected_hover_color=BORDER, text_color=TEXT)
        self.pills.set("All")
        self.pills.grid(row=2, column=0, sticky="w", pady=(0, 14))

        self.grid_frame = ctk.CTkScrollableFrame(main, fg_color="transparent")
        self.grid_frame.grid(row=3, column=0, sticky="nsew")
        for c in range(3):
            self.grid_frame.columnconfigure(c, weight=1, uniform="card")

    def make_stat(self, parent, col, title):
        box = ctk.CTkFrame(parent, fg_color=CARD, corner_radius=16,
                           border_width=1, border_color=BORDER)
        box.grid(row=0, column=col, sticky="ew", padx=(0 if col == 0 else 8, 0 if col == 2 else 8))
        ctk.CTkLabel(box, text=title, font=(FONT, 13), text_color=MUTED).pack(
            anchor="w", padx=18, pady=(14, 0))
        value = ctk.CTkLabel(box, text="–", font=(FONT, 24, "bold"), text_color=TEXT)
        value.pack(anchor="w", padx=18, pady=(0, 14))
        return value

    def set_category(self, value):
        self.category = value
        self.render_products()

    def build_cards(self):
        self.cards = {}
        for p in self.products.values():
            self.cards[p["id"]] = self.product_card(p)
        self.empty_lbl = ctk.CTkLabel(self.grid_frame, text="No products match. Try another search.",
                                      font=(FONT, 15), text_color=MUTED)

    def render_products(self):
        q = self.search_var.get().strip().lower()
        for c in self.cards.values():
            c.grid_forget()
        self.empty_lbl.grid_forget()
        items = [p for p in self.products.values()
                 if (self.category == "All" or p["cat"] == self.category)
                 and q in p["name"].lower()]
        if not items:
            self.empty_lbl.grid(row=0, column=0, columnspan=3, pady=60)
        for i, p in enumerate(items):
            self.cards[p["id"]].grid(row=i // 3, column=i % 3, padx=7, pady=7, sticky="nsew")
        self.update_cards()

    def update_cards(self):
        """Update stock text/button state in place (no widget rebuilding)."""
        for pid, card in self.cards.items():
            p = self.products[pid]
            left = p["stock"] - self.cart.get(pid, 0)
            if left <= 0:
                note, color = "Out of stock", BAD
            elif left <= 5:
                note, color = f"Only {left} left", WARN
            else:
                note, color = f"{left} in stock", OK
            if card.stock_lbl.cget("text") != note:
                card.stock_lbl.configure(text=note, text_color=color)
            state = "normal" if left > 0 else "disabled"
            if card.btn.cget("state") != state:
                card.btn.configure(state=state)

    def product_card(self, p):
        card = ctk.CTkFrame(self.grid_frame, fg_color=CARD, corner_radius=18,
                            border_width=1, border_color=BORDER)
        ctk.CTkLabel(card, text=p["icon"], font=(FONT, 40)).pack(anchor="w", padx=18, pady=(16, 0))
        ctk.CTkLabel(card, text=p["name"], font=(FONT, 15, "bold"), text_color=TEXT,
                     anchor="w", wraplength=200, justify="left").pack(fill="x", padx=18, pady=(6, 0))
        ctk.CTkLabel(card, text=p["cat"], font=(FONT, 12), text_color=MUTED,
                     anchor="w").pack(fill="x", padx=18)
        ctk.CTkLabel(card, text=money(p["price"]), font=(FONT, 17, "bold"),
                     text_color=ACCENT, anchor="w").pack(fill="x", padx=18, pady=(8, 0))
        card.stock_lbl = ctk.CTkLabel(card, text="", font=(FONT, 12), anchor="w")
        card.stock_lbl.pack(fill="x", padx=18)
        card.btn = ctk.CTkButton(card, text="Add to cart", height=36, corner_radius=10,
                                 font=(FONT, 13, "bold"), fg_color=ACCENT, hover_color=ACCENT_HOVER,
                                 command=lambda pid=p["id"]: self.add(pid))
        card.btn.pack(fill="x", padx=18, pady=(10, 16))
        return card

    # --------------------------------------------------------------- CART --
    def build_cart(self):
        panel = ctk.CTkFrame(self, width=420, corner_radius=0, fg_color=PANEL)
        panel.grid(row=0, column=2, sticky="nsew")
        panel.grid_propagate(False)
        panel.rowconfigure(1, weight=1)
        panel.columnconfigure(0, weight=1)

        head = ctk.CTkFrame(panel, fg_color="transparent")
        head.grid(row=0, column=0, sticky="ew", padx=22, pady=(24, 8))
        ctk.CTkLabel(head, text="Current sale", font=(FONT, 22, "bold"),
                     text_color=TEXT).pack(side="left")
        ctk.CTkButton(head, text="Clear", width=64, height=30, corner_radius=8,
                      fg_color="transparent", border_width=1, border_color=BORDER,
                      text_color=MUTED, hover_color=BORDER,
                      command=self.clear_cart).pack(side="right")

        self.cart_frame = ctk.CTkScrollableFrame(panel, fg_color="transparent")
        self.cart_frame.grid(row=1, column=0, sticky="nsew", padx=10)

        foot = ctk.CTkFrame(panel, fg_color="transparent")
        foot.grid(row=2, column=0, sticky="ew", padx=22, pady=(8, 22))
        foot.columnconfigure(1, weight=1)

        ctk.CTkLabel(foot, text="Discount %", font=(FONT, 13), text_color=MUTED).grid(
            row=0, column=0, sticky="w", pady=4)
        ctk.CTkEntry(foot, textvariable=self.discount_var, width=80, height=32,
                     justify="center", corner_radius=8).grid(row=0, column=1, sticky="e")

        self.lbl_sub = self.total_row(foot, 1, "Subtotal")
        self.lbl_disc = self.total_row(foot, 2, "Discount")
        self.lbl_vat = self.total_row(foot, 3, "VAT (18%)")

        ctk.CTkFrame(foot, height=1, fg_color=BORDER).grid(
            row=4, column=0, columnspan=2, sticky="ew", pady=10)
        ctk.CTkLabel(foot, text="Total", font=(FONT, 18, "bold"), text_color=TEXT).grid(
            row=5, column=0, sticky="w")
        self.lbl_total = ctk.CTkLabel(foot, text="", font=(FONT, 24, "bold"), text_color=ACCENT)
        self.lbl_total.grid(row=5, column=1, sticky="e")

        self.pay = ctk.CTkSegmentedButton(
            foot, values=["Cash", "Mobile Money", "Card"], variable=self.payment_var,
            height=36, font=(FONT, 12, "bold"), selected_color=ACCENT,
            selected_hover_color=ACCENT_HOVER, unselected_color=BG)
        self.pay.grid(row=6, column=0, columnspan=2, sticky="ew", pady=(16, 10))

        ctk.CTkButton(foot, text="Charge customer", height=52, corner_radius=14,
                      font=(FONT, 17, "bold"), fg_color=OK, hover_color="#16a34a",
                      text_color="#06210f", command=self.checkout
                      ).grid(row=7, column=0, columnspan=2, sticky="ew")

    def total_row(self, parent, row, label):
        ctk.CTkLabel(parent, text=label, font=(FONT, 13), text_color=MUTED).grid(
            row=row, column=0, sticky="w", pady=2)
        value = ctk.CTkLabel(parent, text="", font=(FONT, 14), text_color=TEXT)
        value.grid(row=row, column=1, sticky="e", pady=2)
        return value

    def add(self, pid):
        if self.cart.get(pid, 0) >= self.products[pid]["stock"]:
            return
        self.cart[pid] = self.cart.get(pid, 0) + 1
        self.refresh_all()

    def change_qty(self, pid, delta):
        new = self.cart.get(pid, 0) + delta
        if new <= 0:
            self.cart.pop(pid, None)
        elif new <= self.products[pid]["stock"]:
            self.cart[pid] = new
        self.refresh_all()

    def clear_cart(self):
        self.cart.clear()
        self.refresh_all()

    def refresh_all(self):
        self.render_cart()
        self.update_cards()

    def render_cart(self):
        if not hasattr(self, "cart_rows"):
            self.cart_rows = {}
            self.cart_empty = ctk.CTkLabel(
                self.cart_frame, text="🛒\nCart is empty.\nTap “Add to cart” on a product.",
                font=(FONT, 14), text_color=MUTED, justify="center")
        for pid in [i for i in self.cart_rows if i not in self.cart]:
            self.cart_rows.pop(pid)["frame"].destroy()
        for pid, qty in self.cart.items():
            if pid not in self.cart_rows:
                self.cart_rows[pid] = self.make_cart_row(pid)
            r = self.cart_rows[pid]
            r["qty"].configure(text=str(qty))
            r["total"].configure(text=money(self.products[pid]["price"] * qty))
        if self.cart:
            self.cart_empty.pack_forget()
        elif not self.cart_empty.winfo_ismapped():
            self.cart_empty.pack(pady=80)
        self.update_totals()

    def make_cart_row(self, pid):
        p = self.products[pid]
        row = ctk.CTkFrame(self.cart_frame, fg_color=CARD, corner_radius=14,
                           border_width=1, border_color=BORDER)
        row.pack(fill="x", padx=6, pady=5)
        row.columnconfigure(0, weight=1)
        ctk.CTkLabel(row, text=p["name"], font=(FONT, 14, "bold"), text_color=TEXT,
                     anchor="w").grid(row=0, column=0, sticky="w", padx=14, pady=(10, 0))
        ctk.CTkLabel(row, text=f"{money(p['price'])} each", font=(FONT, 12),
                     text_color=MUTED, anchor="w").grid(row=1, column=0, sticky="w", padx=14, pady=(0, 10))
        total = ctk.CTkLabel(row, text="", font=(FONT, 14, "bold"), text_color=TEXT)
        total.grid(row=0, column=1, columnspan=3, sticky="e", padx=14, pady=(10, 0))
        ctk.CTkButton(row, text="−", width=28, height=28, corner_radius=8, fg_color=BG,
                      hover_color=BORDER, text_color=TEXT,
                      command=lambda: self.change_qty(pid, -1)).grid(row=1, column=1, pady=(0, 10))
        qty = ctk.CTkLabel(row, text="", width=26, font=(FONT, 14, "bold"), text_color=TEXT)
        qty.grid(row=1, column=2, pady=(0, 10))
        ctk.CTkButton(row, text="+", width=28, height=28, corner_radius=8, fg_color=BG,
                      hover_color=BORDER, text_color=TEXT,
                      command=lambda: self.change_qty(pid, 1)).grid(row=1, column=3, pady=(0, 10), padx=(0, 14))
        return dict(frame=row, qty=qty, total=total)

    def totals(self):
        sub = sum(self.products[i]["price"] * q for i, q in self.cart.items())
        try:
            pct = min(max(float(self.discount_var.get() or 0), 0), 100)
        except ValueError:
            pct = 0
        disc = sub * pct / 100
        vat = (sub - disc) * VAT_RATE
        return sub, disc, vat, sub - disc + vat

    def update_totals(self):
        sub, disc, vat, total = self.totals()
        self.lbl_sub.configure(text=money(sub))
        self.lbl_disc.configure(text="– " + money(disc))
        self.lbl_vat.configure(text=money(vat))
        self.lbl_total.configure(text=money(total))

    # ----------------------------------------------------------- CHECKOUT --
    def checkout(self):
        if not self.cart:
            messagebox.showinfo("Empty cart", "Add at least one product before charging.")
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
            f"{'Paid by':<20}{self.payment_var.get():>20}",
            "-" * 40,
            "      Thank you for shopping with us!",
        ]
        self.cart.clear()
        self.discount_var.set("0")
        self.refresh_all()
        self.refresh_stats()
        self.show_receipt("\n".join(lines))

    def show_receipt(self, text):
        win = ctk.CTkToplevel(self)
        win.title("Receipt")
        win.geometry("440x620")
        win.after(150, win.lift)
        ctk.CTkLabel(win, text="✅ Payment received", font=(FONT, 20, "bold"),
                     text_color=OK).pack(pady=(20, 8))
        box = ctk.CTkTextbox(win, font=("Courier", 13), corner_radius=12)
        box.pack(fill="both", expand=True, padx=20, pady=8)
        box.insert("1.0", text)
        box.configure(state="disabled")
        ctk.CTkButton(win, text="Done", height=42, corner_radius=12,
                      command=win.destroy).pack(fill="x", padx=20, pady=(4, 20))

    def refresh_stats(self):
        self.stat_rev.configure(text=money(self.revenue))
        self.stat_tx.configure(text=str(self.tx_count))
        self.stat_stock.configure(text=str(sum(p["stock"] for p in self.products.values())))
        low = [p for p in self.products.values() if p["stock"] <= 5]
        self.low_label.configure(
            text="\n".join(f"• {p['name']} ({p['stock']})" for p in low) or "Everything is stocked ✓")


if __name__ == "__main__":
    POSApp().mainloop()