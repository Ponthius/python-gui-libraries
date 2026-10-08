"""
VoltPoint POS  -  plain tkinter / ttk edition (no extra installs)
Run:  python pos_tkinter.py
"""
import copy
import tkinter as tk
from datetime import datetime
from tkinter import messagebox, ttk

# ----------------------------------------------------------------- THEME ---
BG = "#0e121b"
PANEL = "#161c28"
CARD = "#1a2130"
BORDER = "#252d3f"
TEXT = "#e8ecf4"
MUTED = "#8b95ab"
ACCENT = "#3d8bff"
ACCENT_HOVER = "#2f74e0"
OK = "#22c55e"
WARN = "#f59e0b"
BAD = "#ef4444"

VAT_RATE = 0.18
CATEGORIES = ["All", "Laptops", "Phones", "Audio", "Accessories", "Networking"]

PRODUCTS = [
    (1, "MacBook Air M2", "Laptops", 4_850_000, 6),
    (2, "Dell XPS 13", "Laptops", 5_200_000, 4),
    (3, "HP Pavilion 15", "Laptops", 2_900_000, 9),
    (4, "iPhone 15", "Phones", 3_700_000, 10),
    (5, "Samsung Galaxy S24", "Phones", 3_300_000, 8),
    (6, "Tecno Camon 30", "Phones", 980_000, 15),
    (7, "AirPods Pro 2", "Audio", 950_000, 12),
    (8, "Sony WH-1000XM5", "Audio", 1_350_000, 5),
    (9, "JBL Flip 6", "Audio", 520_000, 3),
    (10, "USB-C Fast Charger 65W", "Accessories", 95_000, 40),
    (11, "Wireless Mouse", "Accessories", 65_000, 25),
    (12, "Mechanical Keyboard", "Accessories", 240_000, 7),
    (13, "Power Bank 20,000mAh", "Accessories", 150_000, 2),
    (14, "Wi-Fi 6 Router", "Networking", 320_000, 11),
    (15, "Ethernet Cable 10m", "Networking", 25_000, 60),
    (16, "128GB Flash Drive", "Accessories", 45_000, 0),
]


def money(n):
    return f"UGX {n:,.0f}"


class POSApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("VoltPoint POS")
        self.geometry("1380x800")
        self.minsize(1150, 680)
        self.configure(bg=BG)

        self.products = {
            p[0]: dict(id=p[0], name=p[1], cat=p[2], price=p[3], stock=p[4])
            for p in copy.deepcopy(PRODUCTS)
        }
        self.cart = {}
        self.revenue = 0
        self.tx_count = 0

        self.search_var = tk.StringVar()
        self.cat_var = tk.StringVar(value="All")
        self.discount_var = tk.StringVar(value="0")
        self.payment_var = tk.StringVar(value="Cash")
        self.search_var.trace_add("write", lambda *_: self.render_products())
        self.discount_var.trace_add("write", lambda *_: self.update_totals())

        self.setup_styles()
        self.build_ui()
        self.render_products()
        self.render_cart()
        self.refresh_stats()
        self.tick()

    # ------------------------------------------------------------- STYLES --
    def setup_styles(self):
        s = ttk.Style(self)
        s.theme_use("clam")  # the only built-in theme that accepts full recolouring
        s.configure("Treeview", background=CARD, fieldbackground=CARD, foreground=TEXT,
                    rowheight=36, borderwidth=0, font=("Segoe UI", 11))
        s.configure("Treeview.Heading", background=PANEL, foreground=MUTED,
                    font=("Segoe UI", 10, "bold"), relief="flat", padding=8)
        s.map("Treeview", background=[("selected", ACCENT)], foreground=[("selected", "white")])
        s.map("Treeview.Heading", background=[("active", PANEL)])
        s.configure("TCombobox", fieldbackground=CARD, background=CARD, foreground=TEXT,
                    arrowcolor=TEXT, bordercolor=BORDER, lightcolor=CARD, darkcolor=CARD)
        s.map("TCombobox", fieldbackground=[("readonly", CARD)], foreground=[("readonly", TEXT)])
        self.option_add("*TCombobox*Listbox.background", CARD)
        self.option_add("*TCombobox*Listbox.foreground", TEXT)
        s.configure("Vertical.TScrollbar", background=BORDER, troughcolor=PANEL,
                    bordercolor=PANEL, arrowcolor=MUTED)

    def button(self, parent, text, command, bg=CARD, fg=TEXT, hover=BORDER, **kw):
        b = tk.Button(parent, text=text, command=command, bg=bg, fg=fg, relief="flat",
                      activebackground=hover, activeforeground=fg, bd=0, cursor="hand2",
                      font=("Segoe UI", 11, "bold"), **kw)
        b.bind("<Enter>", lambda e: b.configure(bg=hover))
        b.bind("<Leave>", lambda e: b.configure(bg=bg))
        return b

    # ----------------------------------------------------------------- UI --
    def build_ui(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        # ---- left: catalog
        left = tk.Frame(self, bg=BG)
        left.grid(row=0, column=0, sticky="nsew", padx=(22, 10), pady=22)
        left.columnconfigure(0, weight=1)
        left.rowconfigure(3, weight=1)

        top = tk.Frame(left, bg=BG)
        top.grid(row=0, column=0, sticky="ew")
        tk.Label(top, text="⚡ VoltPoint", bg=BG, fg=ACCENT,
                 font=("Segoe UI", 22, "bold")).pack(side="left")
        self.clock = tk.Label(top, bg=BG, fg=MUTED, font=("Segoe UI", 11))
        self.clock.pack(side="right")

        stats = tk.Frame(left, bg=BG)
        stats.grid(row=1, column=0, sticky="ew", pady=14)
        self.stat_rev = self.stat_box(stats, "Sales today")
        self.stat_tx = self.stat_box(stats, "Transactions")
        self.stat_low = self.stat_box(stats, "Low / out of stock")

        filt = tk.Frame(left, bg=BG)
        filt.grid(row=2, column=0, sticky="ew", pady=(0, 10))
        filt.columnconfigure(0, weight=1)
        tk.Entry(filt, textvariable=self.search_var, bg=CARD, fg=TEXT, insertbackground=TEXT,
                 relief="flat", font=("Segoe UI", 13), highlightthickness=1,
                 highlightbackground=BORDER, highlightcolor=ACCENT
                 ).grid(row=0, column=0, sticky="ew", ipady=8, padx=(0, 10))
        cb = ttk.Combobox(filt, textvariable=self.cat_var, values=CATEGORIES,
                          state="readonly", width=16, font=("Segoe UI", 11))
        cb.grid(row=0, column=1)
        cb.bind("<<ComboboxSelected>>", lambda e: self.render_products())

        tree_wrap = tk.Frame(left, bg=BORDER)
        tree_wrap.grid(row=3, column=0, sticky="nsew")
        tree_wrap.columnconfigure(0, weight=1)
        tree_wrap.rowconfigure(0, weight=1)
        self.ptree = ttk.Treeview(tree_wrap, columns=("name", "cat", "price", "stock"),
                                  show="headings", selectmode="browse")
        for col, text, w, anchor in (("name", "Product", 300, "w"), ("cat", "Category", 120, "w"),
                                     ("price", "Price", 140, "e"), ("stock", "Stock", 80, "center")):
            self.ptree.heading(col, text=text)
            self.ptree.column(col, width=w, anchor=anchor)
        self.ptree.tag_configure("low", foreground=WARN)
        self.ptree.tag_configure("out", foreground=BAD)
        sb = ttk.Scrollbar(tree_wrap, orient="vertical", command=self.ptree.yview)
        self.ptree.configure(yscrollcommand=sb.set)
        self.ptree.grid(row=0, column=0, sticky="nsew", padx=1, pady=1)
        sb.grid(row=0, column=1, sticky="ns")
        self.ptree.bind("<Double-1>", lambda e: self.add_selected())

        self.button(left, "Add selected to cart  (or double-click)", self.add_selected,
                    bg=ACCENT, fg="white", hover=ACCENT_HOVER
                    ).grid(row=4, column=0, sticky="ew", pady=(10, 0), ipady=8)

        # ---- right: cart
        right = tk.Frame(self, bg=PANEL, width=430)
        right.grid(row=0, column=1, sticky="ns")
        right.grid_propagate(False)
        right.rowconfigure(1, weight=1)
        right.columnconfigure(0, weight=1)

        head = tk.Frame(right, bg=PANEL)
        head.grid(row=0, column=0, sticky="ew", padx=20, pady=(22, 10))
        tk.Label(head, text="Current sale", bg=PANEL, fg=TEXT,
                 font=("Segoe UI", 18, "bold")).pack(side="left")
        self.button(head, "Clear", self.clear_cart, bg=PANEL, hover=BORDER, fg=MUTED
                    ).pack(side="right", ipadx=8, ipady=2)

        cart_wrap = tk.Frame(right, bg=PANEL)
        cart_wrap.grid(row=1, column=0, sticky="nsew", padx=20)
        cart_wrap.columnconfigure(0, weight=1)
        cart_wrap.rowconfigure(0, weight=1)
        self.ctree = ttk.Treeview(cart_wrap, columns=("name", "qty", "total"),
                                  show="headings", selectmode="browse")
        for col, text, w, anchor in (("name", "Item", 190, "w"), ("qty", "Qty", 50, "center"),
                                     ("total", "Total", 130, "e")):
            self.ctree.heading(col, text=text)
            self.ctree.column(col, width=w, anchor=anchor)
        self.ctree.grid(row=0, column=0, sticky="nsew")

        qty_row = tk.Frame(right, bg=PANEL)
        qty_row.grid(row=2, column=0, sticky="ew", padx=20, pady=10)
        for i in range(3):
            qty_row.columnconfigure(i, weight=1, uniform="q")
        self.button(qty_row, "−", lambda: self.change_qty(-1)).grid(row=0, column=0, sticky="ew", padx=(0, 6), ipady=4)
        self.button(qty_row, "+", lambda: self.change_qty(1)).grid(row=0, column=1, sticky="ew", padx=6, ipady=4)
        self.button(qty_row, "Remove", self.remove_item, fg=BAD).grid(row=0, column=2, sticky="ew", padx=(6, 0), ipady=4)

        foot = tk.Frame(right, bg=PANEL)
        foot.grid(row=3, column=0, sticky="ew", padx=20, pady=(0, 20))
        foot.columnconfigure(1, weight=1)

        tk.Label(foot, text="Discount %", bg=PANEL, fg=MUTED, font=("Segoe UI", 11)
                 ).grid(row=0, column=0, sticky="w", pady=3)
        tk.Entry(foot, textvariable=self.discount_var, width=6, justify="center", bg=CARD,
                 fg=TEXT, insertbackground=TEXT, relief="flat", font=("Segoe UI", 11)
                 ).grid(row=0, column=1, sticky="e", ipady=3)
        self.lbl_sub = self.total_row(foot, 1, "Subtotal")
        self.lbl_disc = self.total_row(foot, 2, "Discount")
        self.lbl_vat = self.total_row(foot, 3, "VAT (18%)")
        tk.Frame(foot, bg=BORDER, height=1).grid(row=4, column=0, columnspan=2, sticky="ew", pady=8)
        tk.Label(foot, text="Total", bg=PANEL, fg=TEXT, font=("Segoe UI", 15, "bold")
                 ).grid(row=5, column=0, sticky="w")
        self.lbl_total = tk.Label(foot, bg=PANEL, fg=ACCENT, font=("Segoe UI", 20, "bold"))
        self.lbl_total.grid(row=5, column=1, sticky="e")

        ttk.Combobox(foot, textvariable=self.payment_var, state="readonly",
                     values=["Cash", "Mobile Money", "Card"], font=("Segoe UI", 11)
                     ).grid(row=6, column=0, columnspan=2, sticky="ew", pady=(14, 10), ipady=4)
        self.button(foot, "Charge customer", self.checkout, bg=OK, fg="#06210f", hover="#16a34a"
                    ).grid(row=7, column=0, columnspan=2, sticky="ew", ipady=12)

    def stat_box(self, parent, title):
        box = tk.Frame(parent, bg=CARD, highlightthickness=1, highlightbackground=BORDER)
        box.pack(side="left", fill="x", expand=True, padx=(0, 10))
        tk.Label(box, text=title, bg=CARD, fg=MUTED, font=("Segoe UI", 10)).pack(anchor="w", padx=14, pady=(10, 0))
        v = tk.Label(box, bg=CARD, fg=TEXT, font=("Segoe UI", 17, "bold"))
        v.pack(anchor="w", padx=14, pady=(0, 10))
        return v

    def total_row(self, parent, row, label):
        tk.Label(parent, text=label, bg=PANEL, fg=MUTED, font=("Segoe UI", 11)
                 ).grid(row=row, column=0, sticky="w", pady=2)
        v = tk.Label(parent, bg=PANEL, fg=TEXT, font=("Segoe UI", 11))
        v.grid(row=row, column=1, sticky="e", pady=2)
        return v

    def tick(self):
        self.clock.configure(text=datetime.now().strftime("%a %d %b %Y   %H:%M:%S"))
        self.after(1000, self.tick)

    # ------------------------------------------------------------ CATALOG --
    def render_products(self):
        self.ptree.delete(*self.ptree.get_children())
        q = self.search_var.get().strip().lower()
        cat = self.cat_var.get()
        for p in self.products.values():
            if (cat == "All" or p["cat"] == cat) and q in p["name"].lower():
                left = p["stock"] - self.cart.get(p["id"], 0)
                tag = "out" if left <= 0 else "low" if left <= 5 else ""
                self.ptree.insert("", "end", iid=str(p["id"]), tags=(tag,),
                                  values=(p["name"], p["cat"], money(p["price"]), left))

    def add_selected(self):
        sel = self.ptree.selection()
        if not sel:
            messagebox.showinfo("No product", "Select a product first.")
            return
        pid = int(sel[0])
        if self.cart.get(pid, 0) >= self.products[pid]["stock"]:
            messagebox.showwarning("Out of stock", "No more units available.")
            return
        self.cart[pid] = self.cart.get(pid, 0) + 1
        self.refresh_all()
        if self.ptree.exists(str(pid)):
            self.ptree.selection_set(str(pid))

    # --------------------------------------------------------------- CART --
    def selected_cart_id(self):
        sel = self.ctree.selection()
        return int(sel[0]) if sel else None

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
        if pid in self.cart:
            self.ctree.selection_set(str(pid))

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
        self.ctree.delete(*self.ctree.get_children())
        for pid, qty in self.cart.items():
            p = self.products[pid]
            self.ctree.insert("", "end", iid=str(pid), values=(p["name"], qty, money(p["price"] * qty)))
        self.update_totals()

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
        win = tk.Toplevel(self)
        win.title("Receipt")
        win.configure(bg=BG)
        win.geometry("430x600")
        win.transient(self)
        tk.Label(win, text="✅ Payment received", bg=BG, fg=OK,
                 font=("Segoe UI", 16, "bold")).pack(pady=(18, 8))
        box = tk.Text(win, bg=CARD, fg=TEXT, relief="flat", font=("Courier", 11), padx=14, pady=14)
        box.pack(fill="both", expand=True, padx=18, pady=6)
        box.insert("1.0", text)
        box.configure(state="disabled")
        self.button(win, "Done", win.destroy, bg=ACCENT, fg="white", hover=ACCENT_HOVER
                    ).pack(fill="x", padx=18, pady=(6, 18), ipady=8)

    def refresh_stats(self):
        self.stat_rev.configure(text=money(self.revenue))
        self.stat_tx.configure(text=str(self.tx_count))
        self.stat_low.configure(text=str(sum(1 for p in self.products.values() if p["stock"] <= 5)))


if __name__ == "__main__":
    POSApp().mainloop()
