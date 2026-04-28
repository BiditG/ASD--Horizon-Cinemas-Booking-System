import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import csv
import datetime
import os
import shutil
import uuid
from src.database.db_connection import get_connection
from src.gui.login_window import SessionManager
from src.models.film import Film
from src.models.showing import Showing

import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

BG = "#0f172a"
BG2 = "#1e293b"
ACCENT = "#1e40af"
FG = "#f8fafc"
TEXT2 = "#94a3b8"
SUCCESS = "#16a34a"
DANGER = "#dc2626"
WARNING = "#ca8a04"

from src.utils.rbac import require_role

@require_role('admin')
class AdminWindow:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        
        session = SessionManager.get_instance()
        self.user = session.get_current_user()

        self.root.title("HCBS — Admin Dashboard")
        self.root.configure(bg=BG)
        self.root.geometry("1100x750")
        
        self._build_topbar()
        self._build_notebook()
        
    def _build_topbar(self):
        bar = tk.Frame(self.root, bg=BG2, pady=10, padx=20)
        bar.pack(fill="x", side="top")
        
        tk.Label(bar, text=f"🎬 Admin Dashboard — {self.user.full_name}", font=("Helvetica", 16, "bold"), bg=BG2, fg=FG).pack(side="left")
        
        tk.Button(bar, text="Logout", bg=DANGER, fg=FG, relief="flat", padx=10, command=self._logout).pack(side="right", padx=5)
        tk.Button(bar, text="Cancel Booking", bg="#b91c1c", fg=FG, relief="flat", padx=10, command=self._open_cancellation).pack(side="right", padx=5)
        tk.Button(bar, text="📊 Live Dashboard", bg="#0f766e", fg=FG, relief="flat", padx=10, command=self._open_dashboard).pack(side="right", padx=5)

    def _build_notebook(self):
        style = ttk.Style()
        style.theme_use("default")
        style.configure("TNotebook", background=BG, borderwidth=0)
        style.configure("TNotebook.Tab", background=BG2, foreground=FG, padding=[15, 8], font=("Helvetica", 11))
        style.map("TNotebook.Tab", background=[("selected", ACCENT)])
        
        # Customize treeview style
        style.configure("Treeview", background=BG, foreground=FG, fieldbackground=BG, rowheight=25)
        style.map("Treeview", background=[("selected", ACCENT)])
        style.configure("Treeview.Heading", background=BG2, foreground=FG, font=("Helvetica", 10, "bold"))
        
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=20, pady=20)
        
        self.tab_films = tk.Frame(self.notebook, bg=BG)
        self.tab_showings = tk.Frame(self.notebook, bg=BG)
        self.tab_reports = tk.Frame(self.notebook, bg=BG)
        self.tab_chart = tk.Frame(self.notebook, bg=BG)
        self.tab_revenue = tk.Frame(self.notebook, bg=BG)
        self.tab_heatmap = tk.Frame(self.notebook, bg=BG)
        self.tab_leaderboard = tk.Frame(self.notebook, bg=BG)
        self.tab_waitlist = tk.Frame(self.notebook, bg=BG)

        self.notebook.add(self.tab_films,   text="Films")
        self.notebook.add(self.tab_showings, text="Showings")
        self.notebook.add(self.tab_reports,  text="Reports")
        self.notebook.add(self.tab_chart,    text="📊 Revenue Chart")
        self.notebook.add(self.tab_revenue,  text="📅 Monthly Revenue")
        self.notebook.add(self.tab_heatmap,  text="🔥 Occupancy Heatmap")
        self.notebook.add(self.tab_leaderboard, text="🏆 Staff Leaderboard")
        self.notebook.add(self.tab_waitlist, text="⏳ Waitlist")

        self._build_films_tab()
        self._build_showings_tab()
        self._build_reports_tab()
        self._build_chart_tab()
        self._build_revenue_tab()
        self._build_heatmap_tab()
        self._build_leaderboard_tab()
        self._build_waitlist_tab()
        
    # --- FILMS TAB ---
    def _build_films_tab(self):
        top = tk.Frame(self.tab_films, bg=BG, pady=10)
        top.pack(fill="x")
        
        tk.Button(top, text="+ Add Film", bg=SUCCESS, fg=FG, command=self._open_add_film).pack(side="left", padx=5)
        tk.Button(top, text="✎ Edit Film", bg=ACCENT, fg=FG, command=self._open_edit_film).pack(side="left", padx=5)
        tk.Button(top, text="✕ Remove Film", bg=WARNING, fg="#000", command=self._remove_film).pack(side="left", padx=5)
        tk.Button(top, text="↻ Refresh", bg=BG2, fg=FG, command=self._refresh_films).pack(side="right", padx=5)
        
        cols = ("ID", "Title", "Genre", "Age Rating", "Duration", "Active")
        self.films_tree = ttk.Treeview(self.tab_films, columns=cols, show="headings", height=15)
        
        for c in cols:
            self.films_tree.heading(c, text=c)
            self.films_tree.column(c, anchor="center")
        self.films_tree.column("ID", width=50)
        self.films_tree.column("Title", width=250, anchor="w")
        self.films_tree.column("Active", width=80)
        
        # Scrollbar
        sb = ttk.Scrollbar(self.tab_films, orient="vertical", command=self.films_tree.yview)
        self.films_tree.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self.films_tree.pack(fill="both", expand=True, pady=10)
        
        self._refresh_films()
        
    def _refresh_films(self):
        for row in self.films_tree.get_children():
            self.films_tree.delete(row)
        try:
            conn = get_connection()
            cursor = conn.execute("SELECT film_id, title, genre, age_rating, duration_mins, is_active FROM films ORDER BY title")
            for row in cursor.fetchall():
                active_str = "Yes" if row["is_active"] else "No"
                self.films_tree.insert("", "end", values=(row["film_id"], row["title"], row["genre"], row["age_rating"], f"{row['duration_mins']}m", active_str))
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _open_add_film(self):
        self._open_film_form("Add Film")

    def _open_edit_film(self):
        sel = self.films_tree.selection()
        if not sel:
            messagebox.showwarning("Warning", "Select a film to edit.")
            return
        film_id = self.films_tree.item(sel[0])["values"][0]
        self._open_film_form("Edit Film", film_id)

    def _open_film_form(self, mode, film_id=None):
        win = tk.Toplevel(self.root)
        win.title(mode)
        win.geometry("500x550")
        win.configure(bg=BG)
        win.grab_set()
        
        fields = [
            ("Title", "entry"),
            ("Genre", "combo", ["Action", "Animation", "Comedy", "Documentary", "Drama", "Horror", "Romance", "Sci-Fi", "Thriller"]),
            ("Age Rating", "combo", ["U", "PG", "12", "12A", "15", "18", "R"]),
            ("Duration (mins)", "entry"),
            ("Description", "text"),
            ("Cast Members", "entry"),
            ("Poster Path", "poster"),
        ]

        _project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        posters_dir = os.path.join(_project_root, "assets", "posters")

        inputs = {}
        for idx, field in enumerate(fields):
            name, ftype = field[0], field[1]
            tk.Label(win, text=name + ":", bg=BG, fg=TEXT2, font=("Helvetica", 10)).grid(row=idx, column=0, pady=10, padx=15, sticky="e")

            if ftype == "poster":
                pf = tk.Frame(win, bg=BG)
                pf.grid(row=idx, column=1, pady=10, padx=10, sticky="w")
                w = tk.Entry(pf, width=34, font=("Helvetica", 10))
                w.pack(side=tk.LEFT)
                inputs[name] = w

                def browse_poster(fid=film_id):
                    src = filedialog.askopenfilename(
                        parent=win,
                        title="Select poster image",
                        filetypes=[
                            ("Images", "*.png *.jpg *.jpeg *.webp *.gif"),
                            ("All files", "*.*"),
                        ],
                    )
                    if not src:
                        return
                    try:
                        os.makedirs(posters_dir, exist_ok=True)
                        _, ext = os.path.splitext(src)
                        ext = ext.lower() if ext else ".jpg"
                        if ext not in (".png", ".jpg", ".jpeg", ".webp", ".gif"):
                            ext = ".jpg"
                        if fid is not None:
                            dest_name = f"poster_film_{fid}{ext}"
                        else:
                            dest_name = f"poster_{uuid.uuid4().hex[:12]}{ext}"
                        dest_abs = os.path.join(posters_dir, dest_name)
                        shutil.copy2(src, dest_abs)
                        rel = f"assets/posters/{dest_name}"
                        inputs["Poster Path"].delete(0, tk.END)
                        inputs["Poster Path"].insert(0, rel)
                    except OSError as ex:
                        messagebox.showerror("Copy failed", str(ex), parent=win)

                tk.Button(
                    pf,
                    text="Browse…",
                    bg=BG2,
                    fg=FG,
                    command=browse_poster,
                ).pack(side=tk.LEFT, padx=(8, 0))
            elif ftype == "entry":
                w = tk.Entry(win, width=40, font=("Helvetica", 10))
                w.grid(row=idx, column=1, pady=10, padx=10, sticky="w")
                inputs[name] = w
            elif ftype == "combo":
                w = ttk.Combobox(win, values=field[2], state="readonly", width=37)
                w.grid(row=idx, column=1, pady=10, padx=10, sticky="w")
                if field[2]:
                    w.current(0)
                inputs[name] = w
            elif ftype == "text":
                w = tk.Text(win, width=40, height=4, font=("Helvetica", 10))
                w.grid(row=idx, column=1, pady=10, padx=10, sticky="w")
                inputs[name] = w
                
        if film_id:
            try:
                conn = get_connection()
                row = conn.execute("SELECT * FROM films WHERE film_id=?", (film_id,)).fetchone()
                inputs["Title"].insert(0, row["title"])
                inputs["Genre"].set(row["genre"])
                inputs["Age Rating"].set(row["age_rating"])
                inputs["Duration (mins)"].insert(0, str(row["duration_mins"]))
                inputs["Description"].insert("1.0", row["description"] or "")
                inputs["Cast Members"].insert(0, row["cast_members"] or "")
                inputs["Poster Path"].insert(0, row["poster_path"] or "")
            except Exception as e:
                messagebox.showerror("Error", str(e))
                win.destroy()
                return

        def save():
            try:
                t = inputs["Title"].get().strip()
                g = inputs["Genre"].get()
                a = inputs["Age Rating"].get()
                d_str = inputs["Duration (mins)"].get().strip()
                d = int(d_str) if d_str.isdigit() else 0
                desc = inputs["Description"].get("1.0", "end-1c").strip()
                c = inputs["Cast Members"].get().strip()
                p = inputs["Poster Path"].get().strip()
                
                if not t or d <= 0:
                    messagebox.showwarning("Validation Error", "Valid title and duration (>0) are required.")
                    return
                
                if mode == "Add Film":
                    Film.create(title=t, genre=g, age_rating=a, duration_mins=d, description=desc, cast_members=c, poster_path=p)
                else:
                    Film.update(film_id, title=t, genre=g, age_rating=a, duration_mins=d, description=desc, cast_members=c, poster_path=p)
                win.destroy()
                self._refresh_films()
                messagebox.showinfo("Success", f"Film '{t}' saved.")
            except Exception as e:
                messagebox.showerror("Error", str(e))
                
        tk.Button(win, text="Save Film", bg=SUCCESS, fg=FG, font=("Helvetica", 11, "bold"), command=save).grid(row=len(fields), column=1, pady=20, sticky="e", padx=10)

    def _remove_film(self):
        sel = self.films_tree.selection()
        if not sel:
            messagebox.showwarning("Warning", "Select a film to remove.")
            return
            
        film_id = self.films_tree.item(sel[0])["values"][0]
        title = self.films_tree.item(sel[0])["values"][1]
        active = self.films_tree.item(sel[0])["values"][5]
        
        if active == "No":
            messagebox.showinfo("Info", "Film is already inactive.")
            return
        
        if messagebox.askyesno("Confirm Remove", f"Are you sure you want to deactivate '{title}'?\nThis will hide it from future listings."):
            try:
                Film.deactivate(film_id)
                self._refresh_films()
                messagebox.showinfo("Success", "Film deactivated.")
            except Exception as e:
                messagebox.showerror("Error", str(e))

    # --- SHOWINGS TAB ---
    def _build_showings_tab(self):
        top = tk.Frame(self.tab_showings, bg=BG, pady=10)
        top.pack(fill="x")
        
        tk.Button(top, text="+ Add Showing", bg=SUCCESS, fg=FG, command=self._open_add_showing).pack(side="left", padx=5)
        tk.Button(top, text="✎ Edit Showing", bg=ACCENT, fg=FG, command=self._open_edit_showing).pack(side="left", padx=5)
        tk.Button(top, text="✕ Cancel Showing", bg=DANGER, fg=FG, command=self._cancel_showing).pack(side="left", padx=5)
        tk.Button(top, text="↻ Refresh", bg=BG2, fg=FG, command=self._refresh_showings).pack(side="right", padx=5)
        
        cols = ("ID", "Film", "Cinema", "Screen", "Date", "Time", "Type", "Seats", "Status")
        self.shows_tree = ttk.Treeview(self.tab_showings, columns=cols, show="headings", height=15)
        
        for c in cols:
            self.shows_tree.heading(c, text=c)
            self.shows_tree.column(c, width=100, anchor="center")
        self.shows_tree.column("Film", width=220, anchor="w")
        self.shows_tree.column("Cinema", width=150, anchor="w")
        self.shows_tree.column("Screen", width=70)
        self.shows_tree.column("ID", width=50)
        
        sb = ttk.Scrollbar(self.tab_showings, orient="vertical", command=self.shows_tree.yview)
        self.shows_tree.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self.shows_tree.pack(fill="both", expand=True, pady=10)
        
        self._refresh_showings()
        
    def _refresh_showings(self):
        for row in self.shows_tree.get_children():
            self.shows_tree.delete(row)
        try:
            conn = get_connection()
            q = '''SELECT s.showing_id, f.title, c.cinema_name, s.screen_id, s.show_date, s.show_time, s.show_type, s.seats_remaining, s.is_cancelled
                   FROM showings s
                   JOIN films f ON s.film_id = f.film_id
                   JOIN screens sc ON s.screen_id = sc.screen_id
                   JOIN cinemas c ON sc.cinema_id = c.cinema_id
                   ORDER BY s.show_date DESC, s.show_time DESC
                   LIMIT 200''' # limit to avoid hanging
            for row in conn.execute(q).fetchall():
                status = "Cancelled" if row["is_cancelled"] else "Active"
                self.shows_tree.insert("", "end", values=(
                    row["showing_id"], row["title"], row["cinema_name"], 
                    row["screen_id"], row["show_date"], row["show_time"], 
                    row["show_type"].capitalize(), row["seats_remaining"], status
                ))
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _open_add_showing(self):
        win = tk.Toplevel(self.root)
        win.title("Add Showing")
        win.geometry("450x450")
        win.configure(bg=BG)
        win.grab_set()
        
        conn = get_connection()
        films = conn.execute("SELECT film_id, title FROM films WHERE is_active=1 ORDER BY title").fetchall()
        cinemas = conn.execute("SELECT cinema_id, cinema_name FROM cinemas ORDER BY cinema_name").fetchall()
        
        if not films or not cinemas:
            messagebox.showerror("Error", "Need active films and cinemas to create showings.")
            win.destroy()
            return
            
        tk.Label(win, text="Film:", bg=BG, fg=TEXT2).grid(row=0, column=0, pady=15, padx=15, sticky="e")
        f_cb = ttk.Combobox(win, values=[f"{f['film_id']} - {f['title']}" for f in films], state="readonly", width=35)
        f_cb.grid(row=0, column=1)
        f_cb.current(0)
        
        tk.Label(win, text="Cinema:", bg=BG, fg=TEXT2).grid(row=1, column=0, pady=15, padx=15, sticky="e")
        c_cb = ttk.Combobox(win, values=[f"{c['cinema_id']} - {c['cinema_name']}" for c in cinemas], state="readonly", width=35)
        c_cb.grid(row=1, column=1)
        c_cb.current(0)
        
        tk.Label(win, text="Screen ID:", bg=BG, fg=TEXT2).grid(row=2, column=0, pady=15, padx=15, sticky="e")
        s_cb = ttk.Combobox(win, state="readonly", width=35)
        s_cb.grid(row=2, column=1)
        
        def update_screens(*args):
            c_val = c_cb.get()
            if not c_val: return
            c_id = int(c_val.split(" - ")[0])
            screens = conn.execute("SELECT screen_id, total_capacity FROM screens WHERE cinema_id=?", (c_id,)).fetchall()
            s_cb['values'] = [f"{s['screen_id']} (Cap: {s['total_capacity']})" for s in screens]
            if screens: s_cb.current(0)
            
        c_cb.bind("<<ComboboxSelected>>", update_screens)
        update_screens()
        
        tk.Label(win, text="Date (YYYY-MM-DD):", bg=BG, fg=TEXT2).grid(row=3, column=0, pady=15, padx=15, sticky="e")
        d_ent = tk.Entry(win, width=37)
        d_ent.insert(0, datetime.date.today().isoformat())
        d_ent.grid(row=3, column=1)
        
        tk.Label(win, text="Time:", bg=BG, fg=TEXT2).grid(row=4, column=0, pady=15, padx=15, sticky="e")
        t_cb = ttk.Combobox(win, values=["10:00", "14:30", "19:00"], state="readonly", width=35)
        t_cb.grid(row=4, column=1)
        t_cb.current(0)
        
        def save():
            try:
                f_id = int(f_cb.get().split(" - ")[0])
                c_id = int(c_cb.get().split(" - ")[0])
                sc_id = int(s_cb.get().split(" ")[0])
                d = d_ent.get().strip()
                t = t_cb.get()
                
                type_map = {"10:00": "morning", "14:30": "afternoon", "19:00": "evening"}
                stype = type_map.get(t, "evening")
                
                # Check valid date
                datetime.date.fromisoformat(d)
                
                Showing.create(cinema_id=c_id, screen_id=sc_id, film_id=f_id, date=d, show_type=stype)
                win.destroy()
                self._refresh_showings()
                messagebox.showinfo("Success", "Showing created.")
            except ValueError as ve:
                messagebox.showerror("Validation Error", str(ve))
            except Exception as e:
                messagebox.showerror("Error", str(e))
                
        tk.Button(win, text="Create Showing", bg=SUCCESS, fg=FG, font=("Helvetica", 10, "bold"), command=save).grid(row=5, column=1, pady=20, sticky="e")

    def _open_edit_showing(self):
        sel = self.shows_tree.selection()
        if not sel:
            messagebox.showwarning("Warning", "Select a showing to edit.")
            return
            
        sid = self.shows_tree.item(sel[0])["values"][0]
        
        win = tk.Toplevel(self.root)
        win.title("Edit Showing")
        win.geometry("400x300")
        win.configure(bg=BG)
        win.grab_set()
        
        try:
            conn = get_connection()
            showing = conn.execute("SELECT screen_id, show_time, show_date FROM showings WHERE showing_id=?", (sid,)).fetchone()
        except Exception as e:
            messagebox.showerror("Error", str(e))
            win.destroy()
            return
            
        tk.Label(win, text="New Screen ID:", bg=BG, fg=TEXT2).grid(row=0, column=0, pady=15, padx=15, sticky="e")
        s_ent = tk.Entry(win)
        s_ent.insert(0, str(showing["screen_id"]))
        s_ent.grid(row=0, column=1)
        
        tk.Label(win, text="New Time:", bg=BG, fg=TEXT2).grid(row=1, column=0, pady=15, padx=15, sticky="e")
        t_cb = ttk.Combobox(win, values=["10:00", "14:30", "19:00"], state="readonly")
        t_cb.set(showing["show_time"])
        t_cb.grid(row=1, column=1)
        
        def save():
            try:
                new_s = int(s_ent.get().strip())
                new_t = t_cb.get()
                
                type_map = {"10:00": "morning", "14:30": "afternoon", "19:00": "evening"}
                new_stype = type_map.get(new_t, "evening")
                
                conn.execute("UPDATE showings SET screen_id=?, show_time=?, show_type=? WHERE showing_id=?", (new_s, new_t, new_stype, sid))
                conn.commit()
                win.destroy()
                self._refresh_showings()
                messagebox.showinfo("Success", "Showing updated.")
            except Exception as e:
                messagebox.showerror("Error", str(e))
                
        tk.Button(win, text="Save Changes", bg=SUCCESS, fg=FG, command=save).grid(row=2, column=1, pady=20, sticky="e")

    def _cancel_showing(self):
        sel = self.shows_tree.selection()
        if not sel:
            messagebox.showwarning("Warning", "Select a showing to cancel.")
            return
            
        sid = self.shows_tree.item(sel[0])["values"][0]
        status = self.shows_tree.item(sel[0])["values"][8]
        
        if status == "Cancelled":
            messagebox.showinfo("Info", "Showing is already cancelled.")
            return
            
        if messagebox.askyesno("Confirm Cancel", f"Are you sure you want to cancel showing ID {sid}?\nActive bookings may need refunds."):
            try:
                conn = get_connection()
                conn.execute("UPDATE showings SET is_cancelled=1 WHERE showing_id=?", (sid,))
                conn.commit()
                self._refresh_showings()
                messagebox.showinfo("Success", "Showing cancelled.")
            except Exception as e:
                messagebox.showerror("Error", str(e))

    # --- MONTHLY REVENUE TAB ---
    def _build_revenue_tab(self):
        try:
            from src.gui.revenue_report_window import RevenueReportPanel
            self.revenue_panel = RevenueReportPanel(self.tab_revenue)
        except Exception as e:
            tk.Label(self.tab_revenue, text=f"Error loading Revenue Report Panel:\n{e}", fg="red", bg=BG).pack(pady=20)

    # --- HEATMAP TAB ---
    def _build_heatmap_tab(self):
        try:
            from src.gui.occupancy_heatmap_window import OccupancyHeatmapPanel
            self.heatmap_panel = OccupancyHeatmapPanel(self.tab_heatmap)
        except Exception as e:
            tk.Label(self.tab_heatmap, text=f"Error loading Occupancy Heatmap Panel:\n{e}", fg="red", bg=BG).pack(pady=20)

    # --- STAFF LEADERBOARD TAB ---
    def _build_leaderboard_tab(self):
        try:
            from src.gui.staff_leaderboard_window import StaffLeaderboardPanel
            self.leaderboard_panel = StaffLeaderboardPanel(self.tab_leaderboard)
        except Exception as e:
            tk.Label(self.tab_leaderboard, text=f"Error loading Staff Leaderboard Panel:\n{e}", fg="red", bg=BG).pack(pady=20)

    # --- REVENUE CHART TAB ---
    def _build_chart_tab(self):
        """Embedded horizontal bar chart: Top 10 films by revenue."""
        # ── Controls row ──────────────────────────────────────────────────
        ctrl = tk.Frame(self.tab_chart, bg=BG2, pady=12, padx=16)
        ctrl.pack(fill="x")

        tk.Label(ctrl, text="Time Period:", bg=BG2, fg=FG,
                 font=("Helvetica", 10, "bold")).pack(side="left", padx=(0, 8))

        self._chart_period = tk.StringVar(value="month")
        for label, val in [("This Week", "week"), ("This Month", "month"), ("All Time", "all")]:
            tk.Radiobutton(
                ctrl, text=label, variable=self._chart_period, value=val,
                bg=BG2, fg=FG, selectcolor=ACCENT, activebackground=BG2,
                activeforeground=FG, font=("Helvetica", 10),
                command=self._refresh_revenue_chart
            ).pack(side="left", padx=4)

        tk.Label(ctrl, text="Cinema:", bg=BG2, fg=FG,
                 font=("Helvetica", 10, "bold")).pack(side="left", padx=(20, 6))
        self._chart_cinema_var = tk.StringVar()
        self._chart_cinema_cb = ttk.Combobox(
            ctrl, textvariable=self._chart_cinema_var,
            state="readonly", font=("Helvetica", 10), width=22
        )
        self._chart_cinema_cb.pack(side="left")
        self._chart_cinema_cb.bind("<<ComboboxSelected>>",
                                   lambda e: self._refresh_revenue_chart())

        tk.Button(
            ctrl, text="📥 Export CSV", bg=SUCCESS, fg=FG,
            font=("Helvetica", 10, "bold"), relief="flat", cursor="hand2",
            padx=12, pady=4, command=self._export_chart_csv
        ).pack(side="right", padx=8)

        tk.Button(
            ctrl, text="↻ Refresh", bg=BG, fg=FG,
            font=("Helvetica", 10, "bold"), relief="flat", cursor="hand2",
            padx=12, pady=4, command=self._refresh_revenue_chart
        ).pack(side="right", padx=4)

        # ── Matplotlib canvas ─────────────────────────────────────────────
        chart_frame = tk.Frame(self.tab_chart, bg=BG)
        chart_frame.pack(fill="both", expand=True, padx=16, pady=12)

        self._rev_figure = Figure(figsize=(9, 5.5), dpi=100, facecolor=BG)
        self._rev_ax = self._rev_figure.add_subplot(111)
        self._rev_ax.set_facecolor(BG2)

        self._rev_canvas = FigureCanvasTkAgg(self._rev_figure, master=chart_frame)
        self._rev_canvas.get_tk_widget().pack(fill="both", expand=True)

        # ── Status label ──────────────────────────────────────────────────
        self._chart_status = tk.Label(
            self.tab_chart, text="", bg=BG, fg="#94a3b8", font=("Helvetica", 9)
        )
        self._chart_status.pack(anchor="e", padx=16, pady=(0, 6))

        # Initialise cinema dropdown then draw first chart
        self._chart_cinemas = {}   # name -> id
        self._chart_data = []      # list of dicts for CSV export
        self._load_chart_cinemas()

    def _load_chart_cinemas(self):
        try:
            conn = get_connection()
            rows = conn.execute(
                "SELECT cinema_id, cinema_name FROM cinemas ORDER BY cinema_name"
            ).fetchall()
            self._chart_cinemas = {r['cinema_name']: r['cinema_id'] for r in rows}
            opts = ["All Cinemas"] + list(self._chart_cinemas.keys())
            self._chart_cinema_cb['values'] = opts
            self._chart_cinema_cb.current(0)
        except Exception as e:
            print("Chart cinema load error:", e)
        finally:
            self._refresh_revenue_chart()

    def _refresh_revenue_chart(self):
        today = datetime.date.today()
        period = self._chart_period.get()

        if period == "week":
            since = (today - datetime.timedelta(days=7)).isoformat()
            until = today.isoformat()
            period_label = "This Week"
        elif period == "month":
            since = today.replace(day=1).isoformat()
            until = today.isoformat()
            period_label = "This Month"
        else:
            since = "2000-01-01"
            until = today.isoformat()
            period_label = "All Time"

        cinema_name = self._chart_cinema_var.get()
        cinema_id = self._chart_cinemas.get(cinema_name)  # None = all

        try:
            conn = get_connection()

            cinema_filter = " AND sc.cinema_id = ? " if cinema_id else ""
            params = [since, until]
            if cinema_id:
                params.append(cinema_id)

            query = f"""
                SELECT f.title AS film_title,
                       COUNT(b.booking_id) AS booking_count,
                       IFNULL(SUM(b.total_cost), 0) AS total_revenue
                FROM bookings b
                JOIN showings sh  ON b.showing_id  = sh.showing_id
                JOIN screens  sc  ON sh.screen_id  = sc.screen_id
                JOIN films    f   ON sh.film_id     = f.film_id
                WHERE sh.show_date BETWEEN ? AND ?
                  AND b.booking_status != 'Cancelled'
                  {cinema_filter}
                GROUP BY f.film_id
                ORDER BY total_revenue DESC
                LIMIT 10
            """
            rows = conn.execute(query, params).fetchall()
            self._chart_data = [
                {"film_title": r["film_title"],
                 "total_revenue": r["total_revenue"],
                 "booking_count": r["booking_count"]}
                for r in rows
            ]
        except Exception as e:
            messagebox.showerror("Chart Error", f"Failed to load revenue data:\n{e}")
            return

        # ── Draw chart ────────────────────────────────────────────────────
        ax = self._rev_ax
        ax.clear()
        ax.set_facecolor(BG2)
        self._rev_figure.set_facecolor(BG)

        for spine in ax.spines.values():
            spine.set_color("#334155")
        ax.tick_params(colors="#94a3b8")
        ax.xaxis.label.set_color("#94a3b8")
        ax.yaxis.label.set_color("#94a3b8")

        if not self._chart_data:
            ax.text(0.5, 0.5, "No revenue data for this period.",
                    ha="center", va="center", color="#94a3b8",
                    fontsize=12, transform=ax.transAxes)
        else:
            titles  = [d["film_title"] for d in self._chart_data]
            revenues = [d["total_revenue"] for d in self._chart_data]

            # Horizontal bars — longest bar at top
            titles   = titles[::-1]
            revenues = revenues[::-1]

            bars = ax.barh(titles, revenues, color=ACCENT, height=0.55)

            # Value labels
            for bar, val in zip(bars, revenues):
                ax.text(
                    bar.get_width() + max(revenues) * 0.01,
                    bar.get_y() + bar.get_height() / 2,
                    f"£{val:,.0f}",
                    va="center", ha="left",
                    color="#f8fafc", fontsize=9
                )

            ax.set_xlabel("Revenue (£)", color="#94a3b8")
            ax.xaxis.set_major_formatter(
                matplotlib.ticker.FuncFormatter(lambda x, _: f"£{x:,.0f}")
            )
            ax.tick_params(axis="y", labelsize=9, colors="#f8fafc")
            ax.tick_params(axis="x", labelsize=8, colors="#94a3b8")

        cinema_label = cinema_name if cinema_name and cinema_name != "All Cinemas" else "All Cinemas"
        ax.set_title(
            f"Top 10 Films by Revenue — {period_label} · {cinema_label}",
            color="#f8fafc", fontsize=11, pad=10
        )

        self._rev_figure.tight_layout()
        self._rev_canvas.draw()
        self._chart_status.config(
            text=f"Last updated: {datetime.datetime.now().strftime('%H:%M:%S')}  |  "
                 f"{len(self._chart_data)} film(s) found"
        )

    def _export_chart_csv(self):
        if not self._chart_data:
            messagebox.showwarning("No Data", "Generate the chart first before exporting.")
            return

        filepath = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
            initialfile=f"revenue_chart_{datetime.date.today().isoformat()}.csv"
        )
        if not filepath:
            return

        try:
            with open(filepath, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(
                    f, fieldnames=["film_title", "total_revenue", "booking_count"]
                )
                writer.writeheader()
                writer.writerows(self._chart_data)
            messagebox.showinfo("Export Successful", f"Saved to:\n{filepath}")
        except Exception as e:
            messagebox.showerror("Export Error", f"Could not save CSV:\n{e}")

    # --- REPORTS TAB ---
    def _build_reports_tab(self):
        top = tk.Frame(self.tab_reports, bg=BG, pady=15)
        top.pack(fill="x")
        
        tk.Label(top, text="Select Report:", bg=BG, fg=TEXT2, font=("Helvetica", 11)).pack(side="left", padx=10)
        
        self.report_var = tk.StringVar(value="Bookings per Listing")
        rep_cb = ttk.Combobox(top, textvariable=self.report_var, values=[
            "Bookings per Listing", 
            "Monthly Revenue", 
            "Top Revenue Film", 
            "Staff Leaderboard"
        ], state="readonly", width=30, font=("Helvetica", 11))
        rep_cb.pack(side="left", padx=5)
        
        tk.Button(top, text="📊 Generate", bg=ACCENT, fg=FG, font=("Helvetica", 10, "bold"), command=self._generate_report).pack(side="left", padx=15)
        tk.Button(top, text="📥 CSV Export", bg=SUCCESS, fg=FG, font=("Helvetica", 10, "bold"), command=self._export_csv).pack(side="right", padx=15)
        
        self.rep_tree = ttk.Treeview(self.tab_reports, show="headings", height=20)
        
        sb = ttk.Scrollbar(self.tab_reports, orient="vertical", command=self.rep_tree.yview)
        self.rep_tree.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self.rep_tree.pack(fill="both", expand=True, pady=10)
        
    def _generate_report(self):
        rtype = self.report_var.get()
        conn = get_connection()
        for row in self.rep_tree.get_children():
            self.rep_tree.delete(row)
            
        try:
            from src.models.reports import ReportManager
            cinema_id = self.user.cinema_id or 1 # Fallback to 1 if admin has no cinema assigned
            
            # Using current month/year for those that require it
            now = datetime.datetime.now()
            y, m = now.year, now.month
            
            data = []
            
            if rtype == "Bookings per Listing":
                cols = ("Film Title", "Date", "Time", "Active Bookings", "Total Revenue (£)")
                self.rep_tree["columns"] = cols
                for c in cols:
                    self.rep_tree.heading(c, text=c)
                    self.rep_tree.column(c, width=150, anchor="center")
                
                raw_data = ReportManager.bookings_per_listing(cinema_id, conn)
                for r in raw_data:
                    self.rep_tree.insert("", "end", values=(r["film_title"], r["show_date"], r["show_time"], r["total_bookings"], f"£{r['total_revenue']:.2f}"))
                data = raw_data
                    
            elif rtype == "Monthly Revenue":
                cols = ("Total Bookings", "Total Revenue (£)", "Avg Occupancy (%)", "Morning Revenue (£)", "Afternoon Revenue (£)", "Evening Revenue (£)")
                self.rep_tree["columns"] = cols
                for c in cols:
                    self.rep_tree.heading(c, text=c)
                    self.rep_tree.column(c, width=150, anchor="center")
                
                stats = ReportManager.monthly_revenue(cinema_id, y, m, conn)
                self.rep_tree.insert("", "end", values=(
                    stats["total_bookings"], 
                    f"£{stats['total_revenue']:.2f}", 
                    f"{stats['average_occupancy_percent']:.1f}%",
                    f"£{stats['revenue_by_show_type'].get('morning', 0):.2f}",
                    f"£{stats['revenue_by_show_type'].get('afternoon', 0):.2f}",
                    f"£{stats['revenue_by_show_type'].get('evening', 0):.2f}"
                ))
                data = [stats]
                
            elif rtype == "Top Revenue Film":
                cols = ("Film Title", "Active Bookings", "Total Revenue (£)")
                self.rep_tree["columns"] = cols
                for c in cols:
                    self.rep_tree.heading(c, text=c)
                    self.rep_tree.column(c, width=150, anchor="center")
                
                raw_data = ReportManager.top_revenue_films(cinema_id, 10, conn)
                for r in raw_data:
                    self.rep_tree.insert("", "end", values=(r["film_title"], r["total_bookings"], f"£{r['total_revenue']:.2f}"))
                data = raw_data
                
            elif rtype == "Staff Leaderboard":
                cols = ("Rank", "Staff Name", "Active Bookings", "Total Revenue (£)")
                self.rep_tree["columns"] = cols
                for c in cols:
                    self.rep_tree.heading(c, text=c)
                    self.rep_tree.column(c, width=150, anchor="center")
                
                raw_data = ReportManager.staff_booking_leaderboard(cinema_id, y, m, conn)
                for r in raw_data:
                    self.rep_tree.insert("", "end", values=(r["rank"], r["staff_full_name"], r["total_bookings"], f"£{r['total_revenue']:.2f}"))
                data = raw_data
                
            self.current_report_data = data
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate report: {e}")

    def _export_csv(self):
        if not hasattr(self, 'current_report_data') or not self.current_report_data:
            messagebox.showwarning("Warning", "No data to export. Generate a report first.")
            return
            
        f = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")], initialfile=f"report_{datetime.datetime.now().strftime('%Y%m%d')}.csv")
        if not f: return
        
        try:
            from src.models.reports import ReportManager
            filepath = ReportManager.export_to_csv(self.current_report_data, os.path.basename(f))
            # Move the generated file to the user's chosen location if they picked somewhere else, 
            # since ReportManager forces it into 'exports/' folder.
            import shutil
            if os.path.abspath(f) != os.path.abspath(filepath):
                shutil.copy2(filepath, f)
            messagebox.showinfo("Success", f"Export successful!\nSaved to {f}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export CSV: {e}")

    def _open_cancellation(self):
        try:
            from src.gui.cancellation_window import CancellationWindow
            CancellationWindow(tk.Toplevel(self.root))
        except Exception as e:
            messagebox.showerror("Error", f"Could not open cancellation window: {e}")

    def _open_dashboard(self):
        try:
            from src.gui.dashboard_window import DashboardWindow
            DashboardWindow(tk.Toplevel(self.root))
        except Exception as e:
            messagebox.showerror("Error", f"Could not open dashboard: {e}")

    def _logout(self):
        from src.gui.login_window import _logout_and_return
        _logout_and_return(self.root)

    def _build_waitlist_tab(self):
        top = tk.Frame(self.tab_waitlist, bg=BG, pady=10)
        top.pack(fill="x")
        
        tk.Label(top, text="Showing ID:", bg=BG, fg=FG).pack(side="left", padx=5)
        self.waitlist_showing_ent = tk.Entry(top, font=("Helvetica", 11), width=10)
        self.waitlist_showing_ent.pack(side="left", padx=5)
        
        tk.Button(top, text="🔍 Load", bg=ACCENT, fg=FG, command=self._refresh_waitlist).pack(side="left", padx=5)
        tk.Button(top, text="✅ Promote", bg=SUCCESS, fg=FG, command=self._promote_waitlist).pack(side="right", padx=5)
        tk.Button(top, text="✕ Remove", bg=WARNING, fg="#000", command=self._remove_waitlist).pack(side="right", padx=5)
        
        cols = ("ID", "Customer", "Email", "Phone", "Tickets", "Status", "Joined")
        self.waitlist_tree = ttk.Treeview(self.tab_waitlist, columns=cols, show="headings", height=15)
        
        for c in cols:
            self.waitlist_tree.heading(c, text=c)
            self.waitlist_tree.column(c, anchor="center")
        self.waitlist_tree.column("Customer", width=150, anchor="w")
        self.waitlist_tree.column("Email", width=150, anchor="w")
        self.waitlist_tree.column("Joined", width=150)
        
        sb = ttk.Scrollbar(self.tab_waitlist, orient="vertical", command=self.waitlist_tree.yview)
        self.waitlist_tree.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self.waitlist_tree.pack(fill="both", expand=True, pady=10)

    def _refresh_waitlist(self):
        for row in self.waitlist_tree.get_children():
            self.waitlist_tree.delete(row)
        
        sh_id = self.waitlist_showing_ent.get().strip()
        if not sh_id.isdigit():
            return
            
        try:
            conn = get_connection()
            cursor = conn.execute("SELECT * FROM waitlist WHERE showing_id = ? ORDER BY joined_at ASC", (sh_id,))
            for r in cursor.fetchall():
                self.waitlist_tree.insert("", "end", values=(
                    r["waitlist_id"], r["customer_name"], r["customer_email"], 
                    r["customer_phone"], r["num_tickets"], r["status"], r["joined_at"]
                ))
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _promote_waitlist(self):
        sel = self.waitlist_tree.selection()
        if not sel: return
        w_id = self.waitlist_tree.item(sel[0])["values"][0]
        import datetime
        try:
            conn = get_connection()
            conn.execute("UPDATE waitlist SET status = 'offered', offered_at = ? WHERE waitlist_id = ?", 
                         (datetime.datetime.now().isoformat(), w_id))
            conn.commit()
            self._refresh_waitlist()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _remove_waitlist(self):
        sel = self.waitlist_tree.selection()
        if not sel: return
        w_id = self.waitlist_tree.item(sel[0])["values"][0]
        try:
            conn = get_connection()
            conn.execute("DELETE FROM waitlist WHERE waitlist_id = ?", (w_id,))
            conn.commit()
            self._refresh_waitlist()
        except Exception as e:
            messagebox.showerror("Error", str(e))
