import os
import json
import hashlib
import tkinter as tk
from tkinter import ttk, messagebox
from abc import ABC, abstractmethod

DATA_DIR = "data"
USERS_FILE = os.path.join(DATA_DIR, "users.json")
ITEMS_FILE = os.path.join(DATA_DIR, "items.json")


def setup_files():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
    for path in [USERS_FILE, ITEMS_FILE]:
        if not os.path.exists(path):
            with open(path, "w") as f:
                json.dump([], f)


def read_data(path):
    try:
        with open(path, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return []


def write_data(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=4)


def hash_text(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


# ==========================================
# OOP MODELS
# ==========================================
class User(ABC):
    def __init__(self, user_id, name, password_hash):
        self._user_id = user_id
        self._name = name
        self.__password_hash = password_hash

    @property
    def user_id(self):
        return self._user_id

    @property
    def name(self):
        return self._name

    def verify_password(self, password):
        return self.__password_hash == hash_text(password)

    @abstractmethod
    def get_role(self):
        pass


class Student(User):
    def __init__(self, user_id, name, password_hash, department):
        super().__init__(user_id, name, password_hash)
        self.department = department

    def get_role(self):
        return "Student"


class Admin(User):
    def __init__(self, user_id, name, password_hash, admin_code):
        super().__init__(user_id, name, password_hash)
        self.admin_code = admin_code

    def get_role(self):
        return "Admin"


class Item(ABC):
    def __init__(self, item_id, title, category, description, location, reported_by, status="Open"):
        self.item_id = item_id
        self.title = title
        self.category = category
        self.description = description
        self.location = location
        self.reported_by = reported_by
        self.status = status

    @abstractmethod
    def get_details(self):
        pass


class LostItem(Item):
    def __init__(self, item_id, title, category, description, location, reported_by, status="Open", reward="None"):
        super().__init__(item_id, title, category, description, location, reported_by, status)
        self.reward = reward

    def get_details(self):
        return {
            "item_id": self.item_id,
            "type": "Lost",
            "title": self.title,
            "category": self.category,
            "description": self.description,
            "location": self.location,
            "reported_by": self.reported_by,
            "status": self.status,
            "reward": self.reward
        }


class FoundItem(Item):
    def __init__(self, item_id, title, category, description, location, reported_by, question, answer_hash, status="Open"):
        super().__init__(item_id, title, category, description, location, reported_by, status)
        self.question = question
        self.__answer_hash = answer_hash

    def check_answer(self, raw_answer):
        return self.__answer_hash == hash_text(raw_answer.strip().lower())

    def get_details(self):
        return {
            "item_id": self.item_id,
            "type": "Found",
            "title": self.title,
            "category": self.category,
            "description": self.description,
            "location": self.location,
            "reported_by": self.reported_by,
            "status": self.status,
            "question": self.question,
            "answer_hash": self.__answer_hash
        }


# ==========================================
# GUI APPLICATION CONTROLLER
# ==========================================
class LostAndFoundApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Campus Lost & Found System")
        self.geometry("980x620")
        self.minsize(850, 550)
        self.configure(bg="#F4F6F9")

        setup_files()
        self.current_user = None

        self.container = tk.Frame(self, bg="#F4F6F9")
        self.container.pack(fill="both", expand=True)

        self.show_login_screen()

    def clear_container(self):
        for widget in self.container.winfo_children():
            widget.destroy()

    # ------------------------------------------
    # AUTHENTICATION
    # ------------------------------------------
    def show_login_screen(self):
        self.clear_container()
        self.current_user = None

        card = tk.Frame(self.container, bg="#FFFFFF", padx=36, pady=32, relief="ridge", bd=1)
        card.place(relx=0.5, rely=0.5, anchor="center", width=420)

        tk.Label(card, text="Campus Lost & Found", font=("Helvetica", 16, "bold"), bg="#FFFFFF", fg="#1E293B").pack(pady=(0, 4))
        tk.Label(card, text="Sign in to your account", font=("Helvetica", 10), bg="#FFFFFF", fg="#64748B").pack(pady=(0, 20))

        tk.Label(card, text="Roll No / User ID", font=("Helvetica", 9, "bold"), bg="#FFFFFF", fg="#334155").pack(anchor="w")
        entry_user = ttk.Entry(card, font=("Helvetica", 10))
        entry_user.pack(fill="x", pady=(4, 12), ipady=3)
        entry_user.focus_set()

        tk.Label(card, text="Password", font=("Helvetica", 9, "bold"), bg="#FFFFFF", fg="#334155").pack(anchor="w")
        entry_pass = ttk.Entry(card, show="*", font=("Helvetica", 10))
        entry_pass.pack(fill="x", pady=(4, 20), ipady=3)

        def handle_login(event=None):
            uid = entry_user.get().strip()
            pwd = entry_pass.get().strip()

            if not uid or not pwd:
                messagebox.showwarning("Notice", "Please enter both User ID and password.")
                return

            users = read_data(USERS_FILE)
            account = next((u for u in users if u["user_id"].lower() == uid.lower()), None)

            if not account:
                messagebox.showerror("Failed", "User not found.")
                return

            if account["role"] == "Student":
                user_obj = Student(account["user_id"], account["name"], account["password_hash"], account.get("detail", ""))
            else:
                user_obj = Admin(account["user_id"], account["name"], account["password_hash"], account.get("detail", ""))

            if user_obj.verify_password(pwd):
                self.current_user = user_obj
                if user_obj.get_role() == "Student":
                    self.show_student_dashboard()
                else:
                    self.show_admin_dashboard()
            else:
                messagebox.showerror("Failed", "Incorrect password.")

        entry_pass.bind("<Return>", handle_login)

        tk.Button(card, text="Login", command=handle_login, bg="#2563EB", fg="#FFFFFF", font=("Helvetica", 10, "bold"), relief="flat", cursor="hand2").pack(fill="x", ipady=5, pady=(0, 10))
        tk.Button(card, text="Don't have an account? Register", command=self.show_register_screen, bg="#FFFFFF", fg="#2563EB", relief="flat", cursor="hand2").pack()

    def show_register_screen(self):
        self.clear_container()

        card = tk.Frame(self.container, bg="#FFFFFF", padx=36, pady=26, relief="ridge", bd=1)
        card.place(relx=0.5, rely=0.5, anchor="center", width=460)

        tk.Label(card, text="Create Account", font=("Helvetica", 15, "bold"), bg="#FFFFFF", fg="#1E293B").pack(pady=(0, 14))

        role_var = tk.StringVar(value="Student")
        role_frame = tk.Frame(card, bg="#FFFFFF")
        role_frame.pack(fill="x", pady=(0, 10))

        tk.Label(role_frame, text="Account Type:", font=("Helvetica", 9, "bold"), bg="#FFFFFF", fg="#334155").pack(side="left")
        rb_std = tk.Radiobutton(role_frame, text="Student", variable=role_var, value="Student", bg="#FFFFFF")
        rb_std.pack(side="left", padx=(10, 5))
        rb_adm = tk.Radiobutton(role_frame, text="Admin", variable=role_var, value="Admin", bg="#FFFFFF")
        rb_adm.pack(side="left")

        tk.Label(card, text="Roll No / ID", font=("Helvetica", 9, "bold"), bg="#FFFFFF", fg="#334155").pack(anchor="w")
        entry_uid = ttk.Entry(card)
        entry_uid.pack(fill="x", pady=(2, 6))

        tk.Label(card, text="Full Name", font=("Helvetica", 9, "bold"), bg="#FFFFFF", fg="#334155").pack(anchor="w")
        entry_name = ttk.Entry(card)
        entry_name.pack(fill="x", pady=(2, 6))

        lbl_dyn = tk.Label(card, text="Department", font=("Helvetica", 9, "bold"), bg="#FFFFFF", fg="#334155")
        lbl_dyn.pack(anchor="w")
        entry_dyn = ttk.Entry(card)
        entry_dyn.pack(fill="x", pady=(2, 6))

        def update_role_field():
            lbl_dyn.config(text="Department" if role_var.get() == "Student" else "Admin Passcode")

        rb_std.config(command=update_role_field)
        rb_adm.config(command=update_role_field)

        tk.Label(card, text="Password", font=("Helvetica", 9, "bold"), bg="#FFFFFF", fg="#334155").pack(anchor="w")
        entry_pwd = ttk.Entry(card, show="*")
        entry_pwd.pack(fill="x", pady=(2, 6))

        tk.Label(card, text="Confirm Password", font=("Helvetica", 9, "bold"), bg="#FFFFFF", fg="#334155").pack(anchor="w")
        entry_pwd_conf = ttk.Entry(card, show="*")
        entry_pwd_conf.pack(fill="x", pady=(2, 14))

        def handle_register():
            uid = entry_uid.get().strip()
            name = entry_name.get().strip()
            dyn = entry_dyn.get().strip()
            p1 = entry_pwd.get().strip()
            p2 = entry_pwd_conf.get().strip()
            role = role_var.get()

            if not uid or not name or not dyn or not p1:
                messagebox.showwarning("Incomplete", "All fields are required.")
                return
            if p1 != p2:
                messagebox.showerror("Error", "Passwords do not match.")
                return
            if role == "Admin" and dyn != "FUI-ADMIN-2026":
                messagebox.showerror("Unauthorized", "Invalid admin master passcode.")
                return

            users = read_data(USERS_FILE)
            if any(u["user_id"].lower() == uid.lower() for u in users):
                messagebox.showerror("Error", "User ID already exists.")
                return

            users.append({
                "user_id": uid,
                "name": name,
                "password_hash": hash_text(p1),
                "role": role,
                "detail": "Admin" if role == "Admin" else dyn
            })
            write_data(USERS_FILE, users)
            messagebox.showinfo("Success", f"{role} registered successfully.")
            self.show_login_screen()

        tk.Button(card, text="Register", command=handle_register, bg="#16A34A", fg="#FFFFFF", font=("Helvetica", 10, "bold"), relief="flat", cursor="hand2").pack(fill="x", ipady=4, pady=(0, 6))
        tk.Button(card, text="Back to Login", command=self.show_login_screen, bg="#FFFFFF", fg="#64748B", relief="flat", cursor="hand2").pack()

    # ------------------------------------------
    # DASHBOARD SHELL & TAB HANDLER
    # ------------------------------------------
    def build_dashboard_shell(self):
        self.clear_container()

        main_box = tk.Frame(self.container, bg="#F4F6F9")
        main_box.pack(fill="both", expand=True)

        sidebar = tk.Frame(main_box, bg="#1E293B", width=220)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        brand = tk.Frame(sidebar, bg="#1E293B", pady=16, padx=14)
        brand.pack(fill="x")
        tk.Label(brand, text="Campus L&F", font=("Helvetica", 13, "bold"), fg="#38BDF8", bg="#1E293B").pack(anchor="w")
        tk.Label(brand, text=f"{self.current_user.get_role()} Workspace", font=("Helvetica", 8), fg="#94A3B8", bg="#1E293B").pack(anchor="w")

        badge = tk.Frame(sidebar, bg="#0F172A", padx=10, pady=8)
        badge.pack(fill="x", padx=10, pady=(0, 12))
        tk.Label(badge, text=self.current_user.name, font=("Helvetica", 9, "bold"), fg="#F8FAFC", bg="#0F172A").pack(anchor="w")
        tk.Label(badge, text=f"ID: {self.current_user.user_id}", font=("Helvetica", 8), fg="#94A3B8", bg="#0F172A").pack(anchor="w")

        self.content_area = tk.Frame(main_box, bg="#F4F6F9", padx=20, pady=16)
        self.content_area.pack(side="right", fill="both", expand=True)

        return sidebar

    def clear_content(self):
        for widget in self.content_area.winfo_children():
            widget.destroy()

    # ------------------------------------------
    # STUDENT TABS
    # ------------------------------------------
    def show_student_dashboard(self):
        sidebar = self.build_dashboard_shell()

        tabs = [
            ("Dashboard", self.tab_student_home),
            ("Report Lost Item", self.tab_post_lost),
            ("Report Found Item", self.tab_post_found),
            ("Search & Filter", self.tab_search_items),
            ("Auto Matches", self.tab_view_matches),
            ("Submit Claim", self.tab_submit_claim),
        ]

        for label, func in tabs:
            tk.Button(
                sidebar,
                text=f"  {label}",
                anchor="w",
                font=("Helvetica", 9),
                bg="#1E293B",
                fg="#E2E8F0",
                activebackground="#334155",
                activeforeground="#FFFFFF",
                relief="flat",
                command=func,
                cursor="hand2"
            ).pack(fill="x", ipady=6)

        tk.Button(
            sidebar,
            text="  Logout",
            anchor="w",
            font=("Helvetica", 9),
            bg="#1E293B",
            fg="#F87171",
            activebackground="#334155",
            relief="flat",
            command=self.show_login_screen,
            cursor="hand2"
        ).pack(side="bottom", fill="x", ipady=8, pady=10)

        self.tab_student_home()

    def tab_student_home(self):
        self.clear_content()
        items = read_data(ITEMS_FILE)

        open_cnt = sum(1 for i in items if i.get("status") == "Open")
        pending_cnt = sum(1 for i in items if i.get("status") == "Claim Pending")
        ret_cnt = sum(1 for i in items if i.get("status") == "Returned")

        tk.Label(self.content_area, text=f"Welcome, {self.current_user.name}", font=("Helvetica", 15, "bold"), bg="#F4F6F9", fg="#0F172A").pack(anchor="w")
        tk.Label(self.content_area, text=f"Dept: {self.current_user.department}", font=("Helvetica", 9), bg="#F4F6F9", fg="#64748B").pack(anchor="w", pady=(1, 14))

        stats = tk.Frame(self.content_area, bg="#F4F6F9")
        stats.pack(fill="x", pady=(0, 16))

        for title, val, col in [("Items Open", open_cnt, "#2563EB"), ("Claims Pending", pending_cnt, "#EAB308"), ("Items Returned", ret_cnt, "#16A34A")]:
            c = tk.Frame(stats, bg="#FFFFFF", padx=14, pady=10, relief="ridge", bd=1)
            c.pack(side="left", fill="both", expand=True, padx=4)
            tk.Label(c, text=title, font=("Helvetica", 9), bg="#FFFFFF", fg="#64748B").pack(anchor="w")
            tk.Label(c, text=str(val), font=("Helvetica", 16, "bold"), bg="#FFFFFF", fg=col).pack(anchor="w", pady=(2, 0))

        tk.Label(self.content_area, text="Quick Shortcuts", font=("Helvetica", 11, "bold"), bg="#F4F6F9", fg="#1E293B").pack(anchor="w", pady=(6, 6))
        qf = tk.Frame(self.content_area, bg="#FFFFFF", padx=14, pady=14, relief="ridge", bd=1)
        qf.pack(fill="x")

        tk.Button(qf, text="+ Report Lost", bg="#2563EB", fg="#FFFFFF", font=("Helvetica", 9, "bold"), relief="flat", command=self.tab_post_lost, cursor="hand2").pack(side="left", padx=(0, 8))
        tk.Button(qf, text="+ Report Found", bg="#0D9488", fg="#FFFFFF", font=("Helvetica", 9, "bold"), relief="flat", command=self.tab_post_found, cursor="hand2").pack(side="left", padx=(0, 8))
        tk.Button(qf, text="🔍 Search Directory", bg="#475569", fg="#FFFFFF", font=("Helvetica", 9, "bold"), relief="flat", command=self.tab_search_items, cursor="hand2").pack(side="left")

    def tab_post_lost(self):
        self.clear_content()
        tk.Label(self.content_area, text="Report a Lost Item", font=("Helvetica", 14, "bold"), bg="#F4F6F9", fg="#0F172A").pack(anchor="w", pady=(0, 10))

        form = tk.Frame(self.content_area, bg="#FFFFFF", padx=20, pady=16, relief="ridge", bd=1)
        form.pack(fill="both", expand=True)

        tk.Label(form, text="Item Title (e.g., Black Dell Laptop)", bg="#FFFFFF", font=("Helvetica", 9, "bold")).pack(anchor="w")
        e_title = ttk.Entry(form)
        e_title.pack(fill="x", pady=(2, 8))

        tk.Label(form, text="Category", bg="#FFFFFF", font=("Helvetica", 9, "bold")).pack(anchor="w")
        cb_cat = ttk.Combobox(form, values=["Electronics", "Accessories", "Documents / Cards", "Books / Stationary", "Other"], state="readonly")
        cb_cat.set("Electronics")
        cb_cat.pack(fill="x", pady=(2, 8))

        tk.Label(form, text="Location Last Seen (e.g., Library 2nd Floor)", bg="#FFFFFF", font=("Helvetica", 9, "bold")).pack(anchor="w")
        e_loc = ttk.Entry(form)
        e_loc.pack(fill="x", pady=(2, 8))

        tk.Label(form, text="Description & Specific Marks", bg="#FFFFFF", font=("Helvetica", 9, "bold")).pack(anchor="w")
        e_desc = ttk.Entry(form)
        e_desc.pack(fill="x", pady=(2, 8))

        tk.Label(form, text="Optional Reward Note", bg="#FFFFFF", font=("Helvetica", 9, "bold")).pack(anchor="w")
        e_rew = ttk.Entry(form)
        e_rew.pack(fill="x", pady=(2, 12))

        def save_lost():
            t, loc, desc = e_title.get().strip(), e_loc.get().strip(), e_desc.get().strip()
            if not t or not loc or not desc:
                messagebox.showwarning("Notice", "Title, location, and description are required.")
                return

            items = read_data(ITEMS_FILE)
            item_id = f"LOST-{len(items) + 1:03d}"
            obj = LostItem(item_id, t, cb_cat.get(), desc, loc, self.current_user.user_id, "Open", e_rew.get().strip() or "None")
            items.append(obj.get_details())
            write_data(ITEMS_FILE, items)

            messagebox.showinfo("Success", f"Lost item registered with ID: {item_id}")
            self.tab_student_home()

        tk.Button(form, text="Publish Lost Item Post", bg="#2563EB", fg="#FFFFFF", font=("Helvetica", 10, "bold"), relief="flat", command=save_lost, cursor="hand2").pack(fill="x", ipady=4)

    def tab_post_found(self):
        self.clear_content()
        tk.Label(self.content_area, text="Report a Found Item", font=("Helvetica", 14, "bold"), bg="#F4F6F9", fg="#0F172A").pack(anchor="w", pady=(0, 10))

        form = tk.Frame(self.content_area, bg="#FFFFFF", padx=20, pady=16, relief="ridge", bd=1)
        form.pack(fill="both", expand=True)

        tk.Label(form, text="Item Title (e.g., Wireless Earbuds)", bg="#FFFFFF", font=("Helvetica", 9, "bold")).pack(anchor="w")
        e_title = ttk.Entry(form)
        e_title.pack(fill="x", pady=(2, 6))

        tk.Label(form, text="Category", bg="#FFFFFF", font=("Helvetica", 9, "bold")).pack(anchor="w")
        cb_cat = ttk.Combobox(form, values=["Electronics", "Accessories", "Documents / Cards", "Books / Stationary", "Other"], state="readonly")
        cb_cat.set("Electronics")
        cb_cat.pack(fill="x", pady=(2, 6))

        tk.Label(form, text="Location Found (e.g., Cafeteria Counter)", bg="#FFFFFF", font=("Helvetica", 9, "bold")).pack(anchor="w")
        e_loc = ttk.Entry(form)
        e_loc.pack(fill="x", pady=(2, 6))

        tk.Label(form, text="General Description", bg="#FFFFFF", font=("Helvetica", 9, "bold")).pack(anchor="w")
        e_desc = ttk.Entry(form)
        e_desc.pack(fill="x", pady=(2, 6))

        tk.Label(form, text="Verification Question (e.g., What color is the charging case?)", bg="#FFFFFF", font=("Helvetica", 9, "bold"), fg="#B91C1C").pack(anchor="w")
        e_q = ttk.Entry(form)
        e_q.pack(fill="x", pady=(2, 6))

        tk.Label(form, text="Secret Answer (Claimant must match this to verify)", bg="#FFFFFF", font=("Helvetica", 9, "bold"), fg="#B91C1C").pack(anchor="w")
        e_ans = ttk.Entry(form)
        e_ans.pack(fill="x", pady=(2, 12))

        def save_found():
            t, loc, desc, q, a = e_title.get().strip(), e_loc.get().strip(), e_desc.get().strip(), e_q.get().strip(), e_ans.get().strip()
            if not t or not loc or not desc or not q or not a:
                messagebox.showwarning("Notice", "All fields including question & answer are mandatory.")
                return

            items = read_data(ITEMS_FILE)
            item_id = f"FOUND-{len(items) + 1:03d}"
            obj = FoundItem(item_id, t, cb_cat.get(), desc, loc, self.current_user.user_id, q, hash_text(a.lower()), "Open")
            items.append(obj.get_details())
            write_data(ITEMS_FILE, items)

            messagebox.showinfo("Success", f"Found item posted with ID: {item_id}")
            self.tab_student_home()

        tk.Button(form, text="Publish Found Item Post", bg="#0D9488", fg="#FFFFFF", font=("Helvetica", 10, "bold"), relief="flat", command=save_found, cursor="hand2").pack(fill="x", ipady=4)

    def tab_search_items(self):
        self.clear_content()
        tk.Label(self.content_area, text="Search & Filter Items", font=("Helvetica", 14, "bold"), bg="#F4F6F9", fg="#0F172A").pack(anchor="w")

        filter_bar = tk.Frame(self.content_area, bg="#F4F6F9", pady=6)
        filter_bar.pack(fill="x")

        tk.Label(filter_bar, text="Keyword:", bg="#F4F6F9", font=("Helvetica", 9, "bold")).pack(side="left", padx=(0, 4))
        e_kw = ttk.Entry(filter_bar, width=18)
        e_kw.pack(side="left", padx=(0, 10))

        tk.Label(filter_bar, text="Type:", bg="#F4F6F9", font=("Helvetica", 9, "bold")).pack(side="left", padx=(0, 4))
        cb_type = ttk.Combobox(filter_bar, values=["All", "Lost", "Found"], width=10, state="readonly")
        cb_type.set("All")
        cb_type.pack(side="left", padx=(0, 10))

        tbl_frame = tk.Frame(self.content_area, bg="#FFFFFF", relief="ridge", bd=1)
        tbl_frame.pack(fill="both", expand=True, pady=6)

        cols = ("id", "type", "title", "category", "location", "status")
        tree = ttk.Treeview(tbl_frame, columns=cols, show="headings", height=12)
        for c in cols:
            tree.heading(c, text=c.upper())
            tree.column(c, width=110)

        tree.pack(fill="both", expand=True)

        def populate():
            tree.delete(*tree.get_children())
            kw = e_kw.get().strip().lower()
            t_filter = cb_type.get()
            for it in read_data(ITEMS_FILE):
                if t_filter != "All" and it.get("type") != t_filter:
                    continue
                full_text = f"{it.get('title', '')} {it.get('description', '')} {it.get('location', '')}".lower()
                if kw and kw not in full_text:
                    continue
                tree.insert("", "end", values=(it.get("item_id"), it.get("type"), it.get("title"), it.get("category"), it.get("location"), it.get("status")))

        tk.Button(filter_bar, text="Apply Filter", bg="#2563EB", fg="#FFFFFF", font=("Helvetica", 9, "bold"), relief="flat", command=populate, cursor="hand2").pack(side="left")
        populate()

    def tab_view_matches(self):
        self.clear_content()
        tk.Label(self.content_area, text="Automatic Match Suggestions", font=("Helvetica", 14, "bold"), bg="#F4F6F9", fg="#0F172A").pack(anchor="w")
        tk.Label(self.content_area, text="Correlating open Lost and Found records based on category and title keywords", font=("Helvetica", 9), bg="#F4F6F9", fg="#64748B").pack(anchor="w", pady=(0, 8))

        tbl_frame = tk.Frame(self.content_area, bg="#FFFFFF", relief="ridge", bd=1)
        tbl_frame.pack(fill="both", expand=True)

        cols = ("lost_id", "lost_title", "found_id", "found_title", "category")
        tree = ttk.Treeview(tbl_frame, columns=cols, show="headings", height=12)
        tree.heading("lost_id", text="LOST ID")
        tree.heading("lost_title", text="LOST TITLE")
        tree.heading("found_id", text="MATCHED FOUND ID")
        tree.heading("found_title", text="FOUND TITLE")
        tree.heading("category", text="CATEGORY")
        for c in cols:
            tree.column(c, width=130)

        tree.pack(fill="both", expand=True)

        items = read_data(ITEMS_FILE)
        losts = [i for i in items if i.get("type") == "Lost" and i.get("status") == "Open"]
        founds = [i for i in items if i.get("type") == "Found" and i.get("status") == "Open"]

        matches_found = False
        for l in losts:
            l_words = set(l.get("title", "").lower().split())
            for f in founds:
                f_words = set(f.get("title", "").lower().split())
                same_cat = l.get("category") == f.get("category")
                shared_words = l_words.intersection(f_words)

                if same_cat and (shared_words or len(l_words) == 0):
                    matches_found = True
                    tree.insert("", "end", values=(l.get("item_id"), l.get("title"), f.get("item_id"), f.get("title"), l.get("category")))

        if not matches_found:
            tk.Label(self.content_area, text="No strong matches detected between currently open items.", bg="#F4F6F9", fg="#64748B").pack(pady=8)

    def tab_submit_claim(self):
        self.clear_content()
        tk.Label(self.content_area, text="Claim Verification Portal", font=("Helvetica", 14, "bold"), bg="#F4F6F9", fg="#0F172A").pack(anchor="w", pady=(0, 6))

        card = tk.Frame(self.content_area, bg="#FFFFFF", padx=18, pady=16, relief="ridge", bd=1)
        card.pack(fill="both", expand=True)

        items = read_data(ITEMS_FILE)
        found_open = [i for i in items if i.get("type") == "Found" and i.get("status") == "Open"]

        if not found_open:
            tk.Label(card, text="There are currently no open found items available for claim.", bg="#FFFFFF", fg="#64748B").pack()
            return

        item_map = {f"{i['item_id']} - {i['title']}": i for i in found_open}

        tk.Label(card, text="Select Item to Claim:", bg="#FFFFFF", font=("Helvetica", 9, "bold")).pack(anchor="w")
        cb_items = ttk.Combobox(card, values=list(item_map.keys()), state="readonly", width=45)
        cb_items.set(list(item_map.keys())[0])
        cb_items.pack(anchor="w", pady=(2, 10))

        lbl_q = tk.Label(card, text="", bg="#FFFFFF", font=("Helvetica", 9, "bold"), fg="#B91C1C")
        lbl_q.pack(anchor="w")

        def update_question(event=None):
            selected = item_map[cb_items.get()]
            lbl_q.config(text=f"Verification Question: {selected.get('question', '')}")

        cb_items.bind("<<ComboboxSelected>>", update_question)
        update_question()

        tk.Label(card, text="Your Answer:", bg="#FFFFFF", font=("Helvetica", 9, "bold")).pack(anchor="w", pady=(8, 2))
        entry_ans = ttk.Entry(card, width=45)
        entry_ans.pack(anchor="w", pady=(0, 14))

        def verify():
            ans = entry_ans.get().strip()
            if not ans:
                messagebox.showwarning("Notice", "Please provide an answer.")
                return

            selected_dict = item_map[cb_items.get()]
            found_obj = FoundItem(
                selected_dict["item_id"],
                selected_dict["title"],
                selected_dict["category"],
                selected_dict["description"],
                selected_dict["location"],
                selected_dict["reported_by"],
                selected_dict["question"],
                selected_dict["answer_hash"],
                selected_dict["status"]
            )

            if found_obj.check_answer(ans):
                for it in items:
                    if it["item_id"] == selected_dict["item_id"]:
                        it["status"] = "Claim Pending"
                        it["claimed_by"] = self.current_user.user_id
                        break
                write_data(ITEMS_FILE, items)
                messagebox.showinfo("Claim Verified!", "Answer matched! Claim status changed to 'Claim Pending' for handover approval.")
                self.tab_student_home()
            else:
                messagebox.showerror("Verification Failed", "Incorrect answer. Verification unsuccessful.")

        tk.Button(card, text="Submit Claim Verification", bg="#16A34A", fg="#FFFFFF", font=("Helvetica", 9, "bold"), relief="flat", command=verify, cursor="hand2").pack(anchor="w", ipady=4)

    # ------------------------------------------
    # ADMIN DASHBOARD
    # ------------------------------------------
    def show_admin_dashboard(self):
        sidebar = self.build_dashboard_shell()

        tabs = [
            ("All Items & Moderate", self.tab_admin_items),
            ("Approve Claims", self.tab_admin_claims),
            ("Registered Users", self.tab_admin_users),
        ]

        for label, func in tabs:
            tk.Button(
                sidebar,
                text=f"  {label}",
                anchor="w",
                font=("Helvetica", 9),
                bg="#1E293B",
                fg="#E2E8F0",
                activebackground="#334155",
                activeforeground="#FFFFFF",
                relief="flat",
                command=func,
                cursor="hand2"
            ).pack(fill="x", ipady=6)

        tk.Button(
            sidebar,
            text="  Logout",
            anchor="w",
            font=("Helvetica", 9),
            bg="#1E293B",
            fg="#F87171",
            activebackground="#334155",
            relief="flat",
            command=self.show_login_screen,
            cursor="hand2"
        ).pack(side="bottom", fill="x", ipady=8, pady=10)

        self.tab_admin_items()

    def tab_admin_items(self):
        self.clear_content()
        tk.Label(self.content_area, text="Item Moderation Registry", font=("Helvetica", 14, "bold"), bg="#F4F6F9", fg="#0F172A").pack(anchor="w")

        bar = tk.Frame(self.content_area, bg="#F4F6F9", pady=6)
        bar.pack(fill="x")

        tbl_frame = tk.Frame(self.content_area, bg="#FFFFFF", relief="ridge", bd=1)
        tbl_frame.pack(fill="both", expand=True)

        cols = ("id", "type", "title", "category", "status", "reported_by")
        tree = ttk.Treeview(tbl_frame, columns=cols, show="headings", height=10)
        for c in cols:
            tree.heading(c, text=c.upper())
            tree.column(c, width=110)
        tree.pack(fill="both", expand=True)

        def refresh():
            tree.delete(*tree.get_children())
            for it in read_data(ITEMS_FILE):
                tree.insert("", "end", values=(it.get("item_id"), it.get("type"), it.get("title"), it.get("category"), it.get("status"), it.get("reported_by")))

        def delete_item():
            sel = tree.selection()
            if not sel:
                messagebox.showwarning("Notice", "Select an item to delete.")
                return
            item_id = tree.item(sel[0])["values"][0]
            items = [i for i in read_data(ITEMS_FILE) if i["item_id"] != item_id]
            write_data(ITEMS_FILE, items)
            messagebox.showinfo("Deleted", f"Item {item_id} removed.")
            refresh()

        tk.Button(bar, text="Delete Selected Post", bg="#DC2626", fg="#FFFFFF", font=("Helvetica", 9, "bold"), relief="flat", command=delete_item, cursor="hand2").pack(side="left")
        refresh()

    def tab_admin_claims(self):
        self.clear_content()
        tk.Label(self.content_area, text="Pending Claim Approvals", font=("Helvetica", 14, "bold"), bg="#F4F6F9", fg="#0F172A").pack(anchor="w")

        bar = tk.Frame(self.content_area, bg="#F4F6F9", pady=6)
        bar.pack(fill="x")

        tbl_frame = tk.Frame(self.content_area, bg="#FFFFFF", relief="ridge", bd=1)
        tbl_frame.pack(fill="both", expand=True)

        cols = ("id", "title", "claimed_by", "status")
        tree = ttk.Treeview(tbl_frame, columns=cols, show="headings", height=10)
        for c in cols:
            tree.heading(c, text=c.upper())
            tree.column(c, width=140)
        tree.pack(fill="both", expand=True)

        def refresh():
            tree.delete(*tree.get_children())
            for it in read_data(ITEMS_FILE):
                if it.get("status") == "Claim Pending":
                    tree.insert("", "end", values=(it.get("item_id"), it.get("title"), it.get("claimed_by", "-"), it.get("status")))

        def approve():
            sel = tree.selection()
            if not sel:
                messagebox.showwarning("Notice", "Select a claim to mark as Returned.")
                return
            item_id = tree.item(sel[0])["values"][0]
            items = read_data(ITEMS_FILE)
            for it in items:
                if it["item_id"] == item_id:
                    it["status"] = "Returned"
                    break
            write_data(ITEMS_FILE, items)
            messagebox.showinfo("Approved", f"Item {item_id} marked as 'Returned'.")
            refresh()

        tk.Button(bar, text="Approve & Mark as Returned", bg="#16A34A", fg="#FFFFFF", font=("Helvetica", 9, "bold"), relief="flat", command=approve, cursor="hand2").pack(side="left")
        refresh()

    def tab_admin_users(self):
        self.clear_content()
        tk.Label(self.content_area, text="Registered Users", font=("Helvetica", 14, "bold"), bg="#F4F6F9", fg="#0F172A").pack(anchor="w", pady=(0, 8))

        tbl_frame = tk.Frame(self.content_area, bg="#FFFFFF", relief="ridge", bd=1)
        tbl_frame.pack(fill="both", expand=True)

        cols = ("user_id", "name", "role", "detail")
        tree = ttk.Treeview(tbl_frame, columns=cols, show="headings", height=12)
        for c in cols:
            tree.heading(c, text=c.upper())
            tree.column(c, width=140)
        tree.pack(fill="both", expand=True)

        for u in read_data(USERS_FILE):
            tree.insert("", "end", values=(u["user_id"], u["name"], u["role"], u.get("detail", "-")))


if __name__ == "__main__":
    app = LostAndFoundApp()
    app.mainloop()