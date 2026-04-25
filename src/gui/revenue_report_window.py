"""
src/gui/revenue_report_window.py
=================================
Student ID: 1234567 | Name: Alex Smith

Monthly Revenue Report panel for the Horizon Cinemas Booking System (HCBS).
Can be embedded as a tab frame or launched as a standalone Toplevel.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import csv
import datetime
import calendar

import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.ticker

from src.database.db_connection import get_connection

# ── Style constants (matches GUI_STYLE_GUIDE.md) ─────────────────────────────
BG        = "#0b1220"
BG2       = "#111b2e"
BG_CARD   = "#162338"
ACCENT    = "#4f8cff"
SUCCESS   = "#22c55e"
WARNING   = "#f59e0b"
FG        = "#f8fafc"
FG2       = "#a7b4c8"
BORDER    = "#26344a"

FF        = "Segoe UI"
FONT_H2   = (FF, 13, "bold")
FONT_BODY = (FF, 10)
FONT_BTN  = (FF, 10, "bold")
FONT_MONO = ("Courier New", 10)

# Palette for multi-line chart
LINE_COLOURS = ["#60a5fa", "#34d399", "#f472b6", "#fb923c",
                "#a78bfa", "#facc15", "#38bdf8", "#4ade80"]

CITIES = ["All Cities", "Birmingham", "Bristol", "Cardiff", "London"]


class RevenueReportPanel:
    """
    A self-contained panel (tk.Frame) that can be packed into any parent
    container — Admin notebook tab or standalone Toplevel.
    """

    def __init__(self, parent):
        self.parent = parent
        self.root = parent.winfo_toplevel()
        self._sort_col = None
        self._sort_asc = True
        self._report_rows: list[dict] = []   # current table data
        self._cinemas_map: dict = {}          # city -> [(name, id)]
        self._all_cinemas: list[tuple] = []  # [(name, id)]

        self._build_ui()
        self._load_cinemas()

    # ── UI Construction ───────────────────────────────────────────────────────

    def _build_ui(self):
        # Top controls
        ctrl = tk.Frame(self.parent, bg=BG2, pady=10, padx=16)
        ctrl.pack(fill="x")

        # City filter
        tk.Label(ctrl, text="City:", bg=BG2, fg=FG2, font=FONT_BODY).grid(row=0, column=0, sticky="w", padx=(0, 4))
        self._city_var = tk.StringVar(value="All Cities")
        self._city_cb = ttk.Combobox(ctrl, textvariable=self._city_var, values=CITIES,
                                     state="readonly", font=FONT_BODY, width=14)
        self._city_cb.grid(row=0, column=1, padx=(0, 12))
        self._city_cb.bind("<<ComboboxSelected>>", self._on_city_change)

        # Cinema filter
        tk.Label(ctrl, text="Cinema:", bg=BG2, fg=FG2, font=FONT_BODY).grid(row=0, column=2, sticky="w", padx=(0, 4))
        self._cinema_var = tk.StringVar()
        self._cinema_cb = ttk.Combobox(ctrl, textvariable=self._cinema_var,
                                       state="readonly", font=FONT_BODY, width=22)
        self._cinema_cb.grid(row=0, column=3, padx=(0, 12))

        # Month filter
        tk.Label(ctrl, text="Month:", bg=BG2, fg=FG2, font=FONT_BODY).grid(row=0, column=4, sticky="w", padx=(0, 4))
        month_names = ["All Months"] + [calendar.month_name[m] for m in range(1, 13)]
        self._month_var = tk.StringVar(value="All Months")
        self._month_cb = ttk.Combobox(ctrl, textvariable=self._month_var,
                                      values=month_names, state="readonly",
                                      font=FONT_BODY, width=12)
        self._month_cb.grid(row=0, column=5, padx=(0, 12))

        # Year filter
        tk.Label(ctrl, text="Year:", bg=BG2, fg=FG2, font=FONT_BODY).grid(row=0, column=6, sticky="w", padx=(0, 4))
        current_year = datetime.date.today().year
        years = ["All Years"] + [str(y) for y in range(current_year, current_year - 5, -1)]
        self._year_var = tk.StringVar(value="All Years")
        self._year_cb = ttk.Combobox(ctrl, textvariable=self._year_var,
                                     values=years, state="readonly",
                                     font=FONT_BODY, width=9)
        self._year_cb.grid(row=0, column=7, padx=(0, 16))

        # Buttons
        tk.Button(ctrl, text="▶  Generate Report", bg=ACCENT, fg=FG,
                  font=FONT_BTN, relief="flat", cursor="hand2",
                  padx=12, pady=4, command=self._generate).grid(row=0, column=8, padx=4)
        tk.Button(ctrl, text="📥 Export CSV", bg=SUCCESS, fg=FG,
                  font=FONT_BTN, relief="flat", cursor="hand2",
                  padx=12, pady=4, command=self._export_csv).grid(row=0, column=9, padx=4)

        # ── PanedWindow: table (left) + chart (right) ─────────────────────────
        pane = tk.PanedWindow(self.parent, orient="horizontal",
                              bg=BG, sashwidth=6, sashrelief="flat")
        pane.pack(fill="both", expand=True, padx=10, pady=8)

        # Table side
        table_frame = tk.Frame(pane, bg=BG)
        pane.add(table_frame, minsize=400)
        self._build_table(table_frame)

        # Chart side
        chart_frame = tk.Frame(pane, bg=BG)
        pane.add(chart_frame, minsize=350)
        self._build_chart(chart_frame)

        # Status bar
        self._status_lbl = tk.Label(self.parent, text="", bg=BG, fg=FG2, font=(FF, 9))
        self._status_lbl.pack(anchor="e", padx=16, pady=(0, 4))

    def _build_table(self, parent):
        tk.Label(parent, text="Revenue by Cinema & Month",
                 font=FONT_H2, bg=BG, fg=FG).pack(anchor="w", pady=(4, 6))

        cols = ("cinema", "city", "month", "bookings", "revenue", "avg_ticket")
        headings = {
            "cinema":     "Cinema",
            "city":       "City",
            "month":      "Month/Year",
            "bookings":   "Bookings",
            "revenue":    "Revenue (£)",
            "avg_ticket": "Avg Ticket (£)",
        }
        widths = {"cinema": 140, "city": 90, "month": 90,
                  "bookings": 70, "revenue": 95, "avg_ticket": 105}

        style = ttk.Style()
        style.theme_use('clam')
        style.configure("Rev.Treeview", background=BG_CARD, foreground=FG,
                fieldbackground=BG_CARD, borderwidth=0, font=FONT_BODY, rowheight=28)
        style.configure("Rev.Treeview.Heading", background=BG2, foreground=FG, font=FONT_BTN)
        style.map("Rev.Treeview", background=[("selected", ACCENT)], foreground=[("selected", FG)])
        style.configure("TCombobox", fieldbackground=BG2, background=BG2, foreground=FG, arrowcolor=FG)
        style.map("TCombobox",
              fieldbackground=[("readonly", BG2), ("disabled", BG2), ("focus", BG2), ("active", BG2)],
              foreground=[("readonly", FG), ("disabled", FG), ("focus", FG), ("active", FG)])
        self.root.option_add('*TCombobox*Listbox.background', BG2, 100)
        self.root.option_add('*TCombobox*Listbox.foreground', FG, 100)
        self.root.option_add('*TCombobox*Listbox.selectBackground', ACCENT, 100)
        self.root.option_add('*TCombobox*Listbox.selectForeground', FG, 100)

        self._tv = ttk.Treeview(parent, columns=cols, show="headings",
                                style="Rev.Treeview")
        for c in cols:
            self._tv.heading(c, text=headings[c],
                             command=lambda _c=c: self._sort_by(_c))
            self._tv.column(c, width=widths[c], anchor="center")

        # Tags
        self._tv.tag_configure("totals", foreground=WARNING, font=FONT_BTN)
        self._tv.tag_configure("zero", foreground=BORDER)

        sb = ttk.Scrollbar(parent, orient="vertical", command=self._tv.yview)
        self._tv.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self._tv.pack(fill="both", expand=True)

    def _build_chart(self, parent):
        tk.Label(parent, text="Revenue Trend", font=FONT_H2, bg=BG, fg=FG).pack(anchor="w", pady=(4, 6))

        self._fig = Figure(figsize=(5, 4), dpi=144, facecolor=BG)
        self._ax = self._fig.add_subplot(111)
        self._ax.set_facecolor(BG2)

        self._canvas = FigureCanvasTkAgg(self._fig, master=parent)
        self._canvas.get_tk_widget().pack(fill="both", expand=True)

        self._draw_empty_chart()

    # ── Data loading ──────────────────────────────────────────────────────────

    def _load_cinemas(self):
        try:
            conn = get_connection()
            rows = conn.execute("""
                SELECT cn.cinema_id, cn.cinema_name, ci.city_name
                FROM cinemas cn
                JOIN cities ci ON cn.city_id = ci.city_id
                ORDER BY ci.city_name, cn.cinema_name
            """).fetchall()

            self._cinemas_map = {}
            self._all_cinemas = []
            for r in rows:
                city = r["city_name"]
                entry = (r["cinema_name"], r["cinema_id"])
                self._all_cinemas.append(entry)
                self._cinemas_map.setdefault(city, []).append(entry)

            self._update_cinema_dropdown("All Cities")
        except Exception as e:
            print("Revenue report cinema load error:", e)

    def _update_cinema_dropdown(self, city: str):
        if city == "All Cities":
            opts = ["All Cinemas"] + [name for name, _ in self._all_cinemas]
        else:
            opts = ["All Cinemas"] + [name for name, _ in self._cinemas_map.get(city, [])]
        self._cinema_cb["values"] = opts
        self._cinema_cb.current(0)

    def _on_city_change(self, event=None):
        self._update_cinema_dropdown(self._city_var.get())

    # ── Report generation ─────────────────────────────────────────────────────

    def _generate(self):
        city     = self._city_var.get()
        cinema   = self._cinema_var.get()
        month_s  = self._month_var.get()
        year_s   = self._year_var.get()

        # Resolve month number
        month_num = None
        if month_s != "All Months":
            month_num = list(calendar.month_name).index(month_s)

        year_num = None
        if year_s != "All Years":
            year_num = int(year_s)

        # Resolve cinema_ids
        if cinema == "All Cinemas":
            if city == "All Cities":
                cinema_ids = [cid for _, cid in self._all_cinemas]
            else:
                cinema_ids = [cid for _, cid in self._cinemas_map.get(city, [])]
        else:
            # find the id for this name
            cinema_ids = [cid for name, cid in self._all_cinemas if name == cinema]

        if not cinema_ids:
            messagebox.showwarning("No Data", "No cinemas match the current filter.")
            return

        try:
            rows = self._query_revenue(cinema_ids, month_num, year_num)
        except Exception as e:
            messagebox.showerror("Query Error", str(e))
            return

        self._report_rows = rows
        self._populate_table(rows)
        self._draw_chart(rows)
        self._status_lbl.config(
            text=f"Report generated: {len(rows)} row(s)  |  "
                 f"{datetime.datetime.now().strftime('%H:%M:%S')}"
        )

    def _query_revenue(self, cinema_ids: list, month: int | None, year: int | None) -> list[dict]:
        conn = get_connection()

        placeholders = ",".join("?" * len(cinema_ids))
        params = list(cinema_ids)

        filters = [f"sc.cinema_id IN ({placeholders})"]
        if month:
            filters.append("CAST(strftime('%m', sh.show_date) AS INTEGER) = ?")
            params.append(month)
        if year:
            filters.append("CAST(strftime('%Y', sh.show_date) AS INTEGER) = ?")
            params.append(year)

        where = " AND ".join(filters)

        query = f"""
            SELECT
                cn.cinema_name,
                ci.city_name,
                strftime('%m', sh.show_date) AS month_num,
                strftime('%Y', sh.show_date) AS year_num,
                COUNT(b.booking_id)            AS total_bookings,
                IFNULL(SUM(b.total_cost), 0)   AS total_revenue
            FROM bookings b
            JOIN showings sh ON b.showing_id = sh.showing_id
            JOIN screens  sc ON sh.screen_id  = sc.screen_id
            JOIN cinemas  cn ON sc.cinema_id  = cn.cinema_id
            JOIN cities   ci ON cn.city_id    = ci.city_id
            WHERE {where}
              AND b.booking_status != 'Cancelled'
            GROUP BY cn.cinema_id, year_num, month_num
            ORDER BY year_num, month_num, cn.cinema_name
        """
        raw = conn.execute(query, params).fetchall()

        rows = []
        for r in raw:
            m = int(r["month_num"])
            y = int(r["year_num"])
            rev   = float(r["total_revenue"])
            bk    = int(r["total_bookings"])
            avg   = rev / bk if bk else 0.0
            rows.append({
                "cinema":     r["cinema_name"],
                "city":       r["city_name"],
                "month":      f"{calendar.month_abbr[m]} {y}",
                "month_key":  (y, m),
                "bookings":   bk,
                "revenue":    rev,
                "avg_ticket": avg,
            })
        return rows

    # ── Table rendering ───────────────────────────────────────────────────────

    def _populate_table(self, rows: list[dict]):
        for item in self._tv.get_children():
            self._tv.delete(item)

        total_bk  = 0
        total_rev = 0.0

        for r in rows:
            tag = "zero" if r["revenue"] == 0 else ""
            self._tv.insert("", "end", values=(
                r["cinema"],
                r["city"],
                r["month"],
                r["bookings"],
                f"£{r['revenue']:,.2f}",
                f"£{r['avg_ticket']:,.2f}",
            ), tags=(tag,))
            total_bk  += r["bookings"]
            total_rev += r["revenue"]

        # Totals row
        if rows:
            avg_all = total_rev / total_bk if total_bk else 0
            self._tv.insert("", "end", values=(
                "TOTAL", "", "",
                total_bk,
                f"£{total_rev:,.2f}",
                f"£{avg_all:,.2f}",
            ), tags=("totals",))

    def _sort_by(self, col: str):
        if self._sort_col == col:
            self._sort_asc = not self._sort_asc
        else:
            self._sort_col = col
            self._sort_asc = True

        def key(r):
            v = r[col]
            return v if isinstance(v, (int, float)) else str(v).lower()

        self._report_rows.sort(key=key, reverse=not self._sort_asc)
        self._populate_table(self._report_rows)

    # ── Chart rendering ───────────────────────────────────────────────────────

    def _draw_empty_chart(self):
        ax = self._ax
        ax.clear()
        ax.set_facecolor(BG2)
        self._fig.set_facecolor(BG)
        ax.text(0.5, 0.5, "Generate a report to see the trend.",
                ha="center", va="center", color=FG2, fontsize=10,
                transform=ax.transAxes)
        for sp in ax.spines.values():
            sp.set_color(BORDER)
        self._canvas.draw()

    def _draw_chart(self, rows: list[dict]):
        ax = self._ax
        ax.clear()
        ax.set_facecolor(BG2)
        self._fig.set_facecolor(BG)
        for sp in ax.spines.values():
            sp.set_color(BORDER)
        ax.tick_params(colors=FG2, labelsize=8)

        if not rows:
            ax.text(0.5, 0.5, "No data for the selected filters.",
                    ha="center", va="center", color=FG2, fontsize=10,
                    transform=ax.transAxes)
            self._canvas.draw()
            return

        # Group by cinema → {cinema_name: [(month_key, revenue), ...]}
        cinemas_data: dict[str, dict] = {}
        all_keys: set = set()
        for r in rows:
            cinemas_data.setdefault(r["cinema"], {})[r["month_key"]] = r["revenue"]
            all_keys.add(r["month_key"])

        sorted_keys = sorted(all_keys)
        x_labels = [f"{calendar.month_abbr[m]} {y}" for y, m in sorted_keys]
        x_pos    = list(range(len(sorted_keys)))

        for idx, (cname, monthly) in enumerate(cinemas_data.items()):
            colour = LINE_COLOURS[idx % len(LINE_COLOURS)]
            y_vals = [monthly.get(k, 0.0) for k in sorted_keys]
            ax.plot(x_pos, y_vals, marker="o", color=colour,
                    linewidth=2, markersize=5, label=cname)

        ax.set_xticks(x_pos)
        ax.set_xticklabels(x_labels, rotation=35, ha="right", fontsize=7, color=FG2)
        ax.yaxis.set_major_formatter(
            matplotlib.ticker.FuncFormatter(lambda v, _: f"£{v:,.0f}")
        )
        ax.tick_params(axis="y", colors=FG2, labelsize=8)
        ax.set_ylabel("Revenue (£)", color=FG2, fontsize=9)
        ax.set_title("Revenue Trend by Cinema", color=FG, fontsize=10, pad=8)
        ax.grid(axis="y", color=BORDER, linestyle="--", linewidth=0.5, alpha=0.6)

        if len(cinemas_data) > 1:
            ax.legend(fontsize=7, facecolor=BG2, edgecolor=BORDER,
                      labelcolor=FG, loc="upper left")

        self._fig.tight_layout()
        self._canvas.draw()

    # ── CSV Export ────────────────────────────────────────────────────────────

    def _export_csv(self):
        if not self._report_rows:
            messagebox.showwarning("No Data", "Generate a report before exporting.")
            return

        today   = datetime.date.today()
        default = f"revenue_report_{today.strftime('%Y_%m')}.csv"

        filepath = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
            initialfile=default,
            title="Save Revenue Report"
        )
        if not filepath:
            return

        headers = ["Cinema", "City", "Month/Year",
                   "Total Bookings", "Total Revenue (£)", "Avg Ticket Price (£)"]
        try:
            with open(filepath, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["Student ID: 1234567 | Name: Alex Smith"])
                writer.writerow([])
                writer.writerow(headers)
                for r in self._report_rows:
                    writer.writerow([
                        r["cinema"], r["city"], r["month"],
                        r["bookings"],
                        f"{r['revenue']:.2f}",
                        f"{r['avg_ticket']:.2f}",
                    ])
                # Totals
                if self._report_rows:
                    total_bk  = sum(r["bookings"] for r in self._report_rows)
                    total_rev = sum(r["revenue"]  for r in self._report_rows)
                    avg_all   = total_rev / total_bk if total_bk else 0
                    writer.writerow(["TOTAL", "", "", total_bk,
                                     f"{total_rev:.2f}", f"{avg_all:.2f}"])

            messagebox.showinfo("Export Successful", f"Saved to:\n{filepath}")
        except Exception as e:
            messagebox.showerror("Export Error", f"Could not save:\n{e}")
