import sqlite3
import customtkinter as ctk
from tkinter import messagebox, ttk
from datetime import datetime, timedelta
import calendar

import os
import sys
import shutil

import hashlib
import secrets
import re

APP_NAME = "Study Scheduler"

def get_app_data_dir():
    app_support = os.path.expanduser("~/Library/Application Support")
    app_dir = os.path.join(app_support, APP_NAME)
    os.makedirs(app_dir, exist_ok=True)
    return app_dir

APP_DATA_DIR = get_app_data_dir()

DATABASE_DIR = os.path.join(APP_DATA_DIR, "database")
os.makedirs(DATABASE_DIR, exist_ok=True)

DB_PATH = os.path.join(DATABASE_DIR, "study_scheduler.db")
SESSION_PATH = os.path.join(APP_DATA_DIR, "session.txt")

current_user_id = None

# App settings
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

app = ctk.CTk()
app.title("Study Scheduler")
app.geometry("1400x800")


# ---------- Helper Functions ----------
def clear_main_area():
    for widget in content_frame.winfo_children():
        widget.destroy()

def save_login_session(user_id):
    try:
        with open(SESSION_PATH, "w") as file:
            file.write(str(user_id))
    except Exception as e:
        messagebox.showerror("Session Error", str(e))


def load_login_session():
    try:
        with open(SESSION_PATH, "r") as file:
            user_id = file.read().strip()
            if user_id:
                return int(user_id)
    except:
        return None

    return None


def clear_login_session():
    try:
        with open(SESSION_PATH, "w") as file:
            file.write("")
    except Exception as e:
        messagebox.showerror("Session Error", str(e))

def create_tables():
    print("Creating database tables...")
    try:
        connection = sqlite3.connect(DB_PATH)
        cursor = connection.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                task_name TEXT NOT NULL,
                deadline TEXT NOT NULL,
                difficulty INTEGER NOT NULL,
                study_hours INTEGER NOT NULL,
                status TEXT DEFAULT 'Pending'
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS weekly_schedule (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                task_id INTEGER,
                day_name TEXT NOT NULL,
                task_name TEXT NOT NULL,
                session_hours INTEGER NOT NULL,
                deadline TEXT,
                is_completed INTEGER DEFAULT 0
            )
        """)

        cursor.execute("PRAGMA table_info(weekly_schedule)")
        columns = [col[1] for col in cursor.fetchall()]

        if "task_id" not in columns:
            cursor.execute("ALTER TABLE weekly_schedule ADD COLUMN task_id INTEGER")

        connection.commit()
        connection.close()

    except Exception as e:
        messagebox.showerror("Database Error", str(e))

def show_task_reminders():
    global current_user_id

    try:
        today = datetime.today().date()

        connection = sqlite3.connect(DB_PATH)
        cursor = connection.cursor()

        cursor.execute("""
            SELECT task_name, deadline, status
            FROM tasks
            WHERE user_id = ?
              AND status = 'Pending'
            ORDER BY deadline ASC
        """, (current_user_id,))

        tasks = cursor.fetchall()
        connection.close()

        reminders = []

        for task_name, deadline, status in tasks:
            deadline_date = datetime.strptime(deadline, "%Y-%m-%d").date()
            days_left = (deadline_date - today).days

            if days_left < 0:
                reminders.append(f"⚠️ {task_name} is overdue! Due: {deadline}")
            elif days_left == 0:
                reminders.append(f"📌 {task_name} is due today!")
            elif days_left <= 2:
                reminders.append(f"⏰ {task_name} is due in {days_left} day(s).")

        if reminders:
            messagebox.showinfo(
                "Task Reminders",
                "\n\n".join(reminders)
            )

    except Exception as e:
        messagebox.showerror("Reminder Error", str(e))

def update_overdue_tasks():
    global current_user_id

    try:
        today = datetime.today().date()

        connection = sqlite3.connect(DB_PATH)
        cursor = connection.cursor()

        cursor.execute("""
            SELECT id, deadline, status
            FROM tasks
            WHERE user_id = ?
        """, (current_user_id,))

        tasks = cursor.fetchall()

        for task_id, deadline, status in tasks:

            if status == "Completed":
                continue

            deadline_date = datetime.strptime(deadline, "%Y-%m-%d").date()

            if deadline_date < today:
                cursor.execute("""
                    UPDATE tasks
                    SET status = 'Overdue'
                    WHERE id = ?
                """, (task_id,))

            else:
                cursor.execute("""
                    UPDATE tasks
                    SET status = 'Pending'
                    WHERE id = ?
                """, (task_id,))

        connection.commit()
        connection.close()

    except Exception as e:
        messagebox.showerror("Overdue Error", str(e))        

def save_weekly_schedule(schedule_data):
    global current_user_id

    try:
        connection = sqlite3.connect(DB_PATH)
        cursor = connection.cursor()

        cursor.execute("DELETE FROM weekly_schedule WHERE user_id = ?", (current_user_id,))

        for day, sessions in schedule_data.items():
            for session in sessions:
                cursor.execute("""
                    INSERT INTO weekly_schedule (
                        user_id, task_id, day_name, task_name, session_hours, deadline, is_completed
                    )
                    VALUES (?, ?, ?, ?, ?, ?, 0)
                """, (
                    current_user_id,
                    session.get("task_id"),
                    day,
                    session["task_name"],
                    session["session_hours"],
                    session["deadline"]
                ))

        connection.commit()
        connection.close()

    except Exception as e:
        messagebox.showerror("Save Schedule Error", str(e))

def load_saved_weekly_schedule():
    global current_user_id

    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    schedule = {day: [] for day in days}

    try:
        connection = sqlite3.connect(DB_PATH)
        cursor = connection.cursor()

        cursor.execute("""
            SELECT id, task_id, day_name, task_name, session_hours, deadline, is_completed
            FROM weekly_schedule
            WHERE user_id = ?
            ORDER BY id ASC
        """, (current_user_id,))

        rows = cursor.fetchall()
        connection.close()

        for session_id, task_id, day_name, task_name, session_hours, deadline, is_completed in rows:
            if day_name in schedule:
                schedule[day_name].append({
                    "id": session_id,
                    "task_id": task_id,
                    "task_name": task_name,
                    "session_hours": session_hours,
                    "deadline": deadline,
                    "is_completed": is_completed
                })

    except Exception as e:
        messagebox.showerror("Load Schedule Error", str(e))

    return schedule

def has_saved_weekly_schedule():
    global current_user_id

    try:
        connection = sqlite3.connect(DB_PATH)
        cursor = connection.cursor()

        cursor.execute("""
            SELECT COUNT(*)
            FROM weekly_schedule
            WHERE user_id = ?
        """, (current_user_id,))

        count = cursor.fetchone()[0]
        connection.close()

        return count > 0

    except Exception as e:
        messagebox.showerror("Schedule Check Error", str(e))
        return False
    
def clear_saved_weekly_schedule():
    global current_user_id

    try:
        connection = sqlite3.connect(DB_PATH)
        cursor = connection.cursor()

        cursor.execute("""
            DELETE FROM weekly_schedule
            WHERE user_id = ?
        """, (current_user_id,))

        connection.commit()
        connection.close()

    except Exception as e:
        messagebox.showerror("Clear Schedule Error", str(e))

def mark_session_completed(session_id):
    global current_user_id

    try:
        connection = sqlite3.connect(DB_PATH)
        cursor = connection.cursor()

        cursor.execute("""
            UPDATE weekly_schedule
            SET is_completed = 1
            WHERE id = ? AND user_id = ?
        """, (session_id, current_user_id))

        cursor.execute("""
            SELECT task_id
            FROM weekly_schedule
            WHERE id = ? AND user_id = ?
        """, (session_id, current_user_id))
        row = cursor.fetchone()

        if row and row[0] is not None:
            task_id = row[0]

            cursor.execute("""
                SELECT COUNT(*)
                FROM weekly_schedule
                WHERE user_id = ? AND task_id = ? AND is_completed = 0
            """, (current_user_id, task_id))
            remaining_sessions = cursor.fetchone()[0]

            if remaining_sessions == 0:
                cursor.execute("""
                    UPDATE tasks
                    SET status = 'Completed'
                    WHERE id = ? AND user_id = ?
                """, (task_id, current_user_id))

        connection.commit()
        connection.close()

    except Exception as e:
        messagebox.showerror("Session Update Error", str(e))

def undo_session_completed(session_id):
    global current_user_id

    try:
        connection = sqlite3.connect(DB_PATH)
        cursor = connection.cursor()

        cursor.execute("""
            UPDATE weekly_schedule
            SET is_completed = 0
            WHERE id = ? AND user_id = ?
        """, (session_id, current_user_id))

        cursor.execute("""
            SELECT task_id
            FROM weekly_schedule
            WHERE id = ? AND user_id = ?
        """, (session_id, current_user_id))
        row = cursor.fetchone()

        if row and row[0] is not None:
            task_id = row[0]

            cursor.execute("""
                UPDATE tasks
                SET status = 'Pending'
                WHERE id = ? AND user_id = ?
            """, (task_id, current_user_id))

        connection.commit()
        connection.close()

    except Exception as e:
        messagebox.showerror("Session Update Error", str(e))

def get_tasks_for_month(year, month):
    global current_user_id

    tasks_by_date = {}

    try:
        connection = sqlite3.connect(DB_PATH)
        cursor = connection.cursor()

        month_start = f"{year}-{month:02d}-01"

        if month == 12:
            next_month_start = f"{year + 1}-01-01"
        else:
            next_month_start = f"{year}-{month + 1:02d}-01"

        cursor.execute("""
            SELECT task_name, deadline, status
            FROM tasks
            WHERE user_id = ?
              AND deadline >= ?
              AND deadline < ?
            ORDER BY deadline ASC
        """, (current_user_id, month_start, next_month_start))

        rows = cursor.fetchall()
        connection.close()

        for task_name, deadline, status in rows:
            if deadline not in tasks_by_date:
                tasks_by_date[deadline] = []

            tasks_by_date[deadline].append({
                "task_name": task_name,
                "status": status
            })

    except Exception as e:
        messagebox.showerror("Calendar Error", str(e))

    return tasks_by_date

def get_task_stats():
    global current_user_id

    total_tasks = 0
    completed_tasks = 0
    pending_tasks = 0
    progress = 0

    try:
        connection = sqlite3.connect(DB_PATH)
        cursor = connection.cursor()

        cursor.execute("""
            SELECT COUNT(*)
            FROM tasks
            WHERE user_id = ?
        """, (current_user_id,))
        total_tasks = cursor.fetchone()[0]

        cursor.execute("""
            SELECT COUNT(*)
            FROM tasks
            WHERE user_id = ? AND status = 'Completed'
        """, (current_user_id,))
        completed_tasks = cursor.fetchone()[0]

        cursor.execute("""
            SELECT COUNT(*)
            FROM tasks
            WHERE user_id = ? AND status = 'Pending'
        """, (current_user_id,))
        pending_tasks = cursor.fetchone()[0]

        connection.close()

        if total_tasks > 0:
            progress = completed_tasks / total_tasks
        else:
            progress = 0

    except Exception as e:
        messagebox.showerror("Stats Error", str(e))

    return total_tasks, completed_tasks, pending_tasks, progress

def get_schedule_completion_stats():
    global current_user_id

    try:
        connection = sqlite3.connect(DB_PATH)
        cursor = connection.cursor()

        cursor.execute("""
            SELECT COUNT(*), SUM(is_completed)
            FROM weekly_schedule
            WHERE user_id = ?
        """, (current_user_id,))

        row = cursor.fetchone()
        connection.close()

        total_sessions = row[0] if row and row[0] is not None else 0
        completed_sessions = row[1] if row and row[1] is not None else 0

        if total_sessions == 0:
            return 0, 0, 0

        schedule_progress = completed_sessions / total_sessions
        return total_sessions, completed_sessions, schedule_progress

    except Exception as e:
        messagebox.showerror("Schedule Stats Error", str(e))
        return 0, 0, 0
    
def get_task_progress(task_id):
    try:
        connection = sqlite3.connect(DB_PATH)
        cursor = connection.cursor()

        # total sessions
        cursor.execute("""
            SELECT COUNT(*)
            FROM weekly_schedule
            WHERE user_id = ? AND task_id = ?
        """, (current_user_id, task_id))
        total = cursor.fetchone()[0]

        # completed sessions
        cursor.execute("""
            SELECT COUNT(*)
            FROM weekly_schedule
            WHERE user_id = ? AND task_id = ? AND is_completed = 1
        """, (current_user_id, task_id))
        completed = cursor.fetchone()[0]

        connection.close()

        if total == 0:
            return "No schedule"

        return f"{completed}/{total} sessions"

    except Exception:
        return "Error"

def search_tasks_into_tree(tree, search_text):
    global current_user_id

    try:
        for item in tree.get_children():
            tree.delete(item)

        if search_text.strip() == "":
            load_tasks_into_tree(tree)
            return

        connection = sqlite3.connect(DB_PATH)
        cursor = connection.cursor()

        cursor.execute("""
            SELECT id, task_name, deadline, difficulty, study_hours, status
            FROM tasks
            WHERE user_id = ?
              AND task_name LIKE ? COLLATE NOCASE
            ORDER BY id DESC
        """, (current_user_id, f"%{search_text.strip()}%"))

        tasks = cursor.fetchall()
        connection.close()

        for task in tasks:
            task_id = task[0]
            progress = get_task_progress(task_id)

            tree.insert("", "end", values=(
                task[0],
                task[1],
                task[2],
                task[3],
                task[4],
                progress,
                task[5]
            ))

    except Exception as e:
        messagebox.showerror("Search Error", str(e))

def load_tasks_into_tree(tree):
    global current_user_id

    try:
        for item in tree.get_children():
            tree.delete(item)

        connection = sqlite3.connect(DB_PATH)
        cursor = connection.cursor()

        cursor.execute("""
            SELECT id, task_name, deadline, difficulty, study_hours, status
            FROM tasks
            WHERE user_id = ?
            ORDER BY id ASC
        """, (current_user_id,))

        tasks = cursor.fetchall()
        connection.close()

        for index, task in enumerate(tasks, start=1):
            real_task_id = task[0]

            progress = get_task_progress(real_task_id)

            new_row = (
                index,  # Display row number 
                task[1],  # Name
                task[2],  # Deadline
                task[3],  # Difficulty
                task[4],  # Hours
                progress, # NEW COLUMN
                task[5]   # Status
            )

            tree.insert("", "end", iid=str(real_task_id), values=new_row)

    except Exception as e:
        messagebox.showerror("Load Error", str(e))


def sidebar_button(parent, text, command):
    return ctk.CTkButton(
        parent,
        text=text,
        width=220,
        height=42,
        corner_radius=10,
        fg_color="#374151",
        hover_color="#4b5563",
        anchor="w",
        command=command
    )


def get_pending_tasks():
    global current_user_id

    try:
        connection = sqlite3.connect(DB_PATH)
        cursor = connection.cursor()

        cursor.execute("""
            SELECT id, task_name, deadline, difficulty, study_hours, status
            FROM tasks
            WHERE user_id = ? AND status = 'Pending'
            ORDER BY deadline ASC, difficulty DESC
        """, (current_user_id,))

        tasks = cursor.fetchall()
        connection.close()
        return tasks

    except Exception as e:
        messagebox.showerror("Schedule Error", str(e))
        return []


def calculate_task_priority(task):
    task_id, task_name, deadline, difficulty, study_hours, status = task

    try:
        deadline_date = datetime.strptime(deadline, "%Y-%m-%d").date()
        today = datetime.today().date()
        days_left = (deadline_date - today).days

        if days_left < 0:
            days_left = 0

        urgency_score = 10 / (days_left + 1)
        difficulty_score = float(difficulty)
        hours_score = float(study_hours) / 2

        priority_score = urgency_score + difficulty_score + hours_score
        return priority_score

    except Exception:
        return 0


def generate_weekly_schedule_data(excluded_days=None):
    global current_user_id

    MAX_DAILY_HOURS = 6

    try:
        connection = sqlite3.connect(DB_PATH)
        cursor = connection.cursor()

        cursor.execute("""
            SELECT id, task_name, deadline, difficulty, study_hours
            FROM tasks
            WHERE user_id = ?
                        AND status IN ('Pending', 'Overdue')
        """, (current_user_id,))

        tasks = cursor.fetchall()
        connection.close()

    except Exception as e:
        messagebox.showerror("Schedule Error", str(e))
        return {
            "Monday": [],
            "Tuesday": [],
            "Wednesday": [],
            "Thursday": [],
            "Friday": [],
            "Saturday": [],
            "Sunday": []
        }

    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

    if excluded_days is None:
        excluded_days = []

    days = [day for day in days if day not in excluded_days]

    if not days:
        messagebox.showwarning("Schedule Error", "You must allow at least one study day.")
        return {
            "Monday": [],
            "Tuesday": [],
            "Wednesday": [],
            "Thursday": [],
            "Friday": [],
            "Saturday": [],
            "Sunday": []
        }
    all_days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    schedule = {day: [] for day in all_days}
    daily_hours = {day: 0 for day in all_days}

    today = datetime.today().date()

    def priority_score(task):
        task_id, task_name, deadline, difficulty, study_hours = task

        try:
            deadline_date = datetime.strptime(deadline, "%Y-%m-%d").date()
            days_left = (deadline_date - today).days

            if days_left < 0:
                days_left = 0

            urgency = 100 / (days_left + 1)
            difficulty_score = int(difficulty) * 5
            hours_score = int(study_hours) * 2

            return urgency + difficulty_score + hours_score

        except Exception:
            return 0

    sorted_tasks = sorted(tasks, key=priority_score, reverse=True)

    for task_id, task_name, deadline, difficulty, study_hours in sorted_tasks:
        remaining_hours = int(study_hours)

        while remaining_hours > 0:
            placed = False

            for day in days:
                if daily_hours[day] < MAX_DAILY_HOURS:
                    session_hours = min(2, remaining_hours, MAX_DAILY_HOURS - daily_hours[day])

                    if session_hours > 0:
                        schedule[day].append({
                            "task_id": task_id,
                            "task_name": task_name,
                            "session_hours": session_hours,
                            "deadline": deadline,
                            "is_completed": 0
                        })
                        daily_hours[day] += session_hours
                        remaining_hours -= session_hours
                        placed = True

                    if remaining_hours <= 0:
                        break

            if not placed:
                break

    return schedule

def show_dashboard_page():
    clear_main_area()

    total_tasks, completed_tasks, pending_tasks, progress = get_task_stats()

    title = ctk.CTkLabel(
        content_frame,
        text="Dashboard",
        font=ctk.CTkFont(size=28, weight="bold")
    )
    title.pack(anchor="w", padx=30, pady=(30, 10))

    subtitle = ctk.CTkLabel(
        content_frame,
        text="Welcome to your study planner dashboard",
        font=ctk.CTkFont(size=16),
        text_color="gray"
    )
    subtitle.pack(anchor="w", padx=30, pady=(0, 20))

    cards_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
    cards_frame.pack(padx=30, pady=20, fill="x")

    card1 = ctk.CTkFrame(cards_frame, width=220, height=130, fg_color="#1f2937", corner_radius=15)
    card1.grid(row=0, column=0, padx=15, pady=10)
    card1.grid_propagate(False)
    ctk.CTkLabel(
        card1,
        text=f"📋 Total Tasks\n{total_tasks}",
        font=ctk.CTkFont(size=22, weight="bold")
    ).place(relx=0.5, rely=0.5, anchor="center")

    card2 = ctk.CTkFrame(cards_frame, width=220, height=130, fg_color="#1f2937", corner_radius=15)
    card2.grid(row=0, column=1, padx=15, pady=10)
    card2.grid_propagate(False)
    ctk.CTkLabel(
        card2,
        text=f"✅ Completed\n{completed_tasks}",
        font=ctk.CTkFont(size=22, weight="bold")
    ).place(relx=0.5, rely=0.5, anchor="center")

    card3 = ctk.CTkFrame(cards_frame, width=220, height=130, fg_color="#1f2937", corner_radius=15)
    card3.grid(row=0, column=2, padx=15, pady=10)
    card3.grid_propagate(False)
    ctk.CTkLabel(
        card3,
        text=f"⏳ Pending\n{pending_tasks}",
        font=ctk.CTkFont(size=22, weight="bold")
    ).place(relx=0.5, rely=0.5, anchor="center")

    progress_title = ctk.CTkLabel(
        content_frame,
        text="Overall Progress",
        font=ctk.CTkFont(size=20, weight="bold")
    )
    progress_title.pack(anchor="w", padx=30, pady=(30, 10))

    progress_bar = ctk.CTkProgressBar(content_frame, width=500)
    progress_bar.pack(anchor="w", padx=30, pady=10)
    progress_bar.set(progress)

    progress_text = ctk.CTkLabel(
        content_frame,
        text=f"{round(progress * 100, 1)}% Completed",
        font=ctk.CTkFont(size=14)
    )
    progress_text.pack(anchor="w", padx=30, pady=5)


def show_tasks_page():
    clear_main_area()

    page_frame = ctk.CTkScrollableFrame(content_frame, fg_color="transparent")
    page_frame.pack(fill="both", expand=True)

    title = ctk.CTkLabel(
        page_frame,
        text="Task Management",
        font=ctk.CTkFont(size=28, weight="bold")
    )
    title.pack(anchor="w", padx=30, pady=(30, 20))

    # ---------- FORM ----------
    form_frame = ctk.CTkFrame(page_frame, fg_color="#2b2b2b", corner_radius=15)
    form_frame.pack(padx=30, pady=10, fill="x")

    ctk.CTkLabel(form_frame, text="Task Name").grid(row=0, column=0, padx=20, pady=15, sticky="w")
    task_entry = ctk.CTkEntry(form_frame, width=250, placeholder_text="Enter task name")
    task_entry.grid(row=0, column=1, padx=20, pady=15)

    ctk.CTkLabel(form_frame, text="Deadline").grid(row=1, column=0, padx=20, pady=15, sticky="w")
    deadline_entry = ctk.CTkEntry(form_frame, width=250, placeholder_text="YYYY-MM-DD")
    deadline_entry.grid(row=1, column=1, padx=20, pady=15)

    ctk.CTkLabel(form_frame, text="Difficulty").grid(row=2, column=0, padx=20, pady=15, sticky="w")
    difficulty_entry = ctk.CTkEntry(form_frame, width=250, placeholder_text="1 - 5")
    difficulty_entry.grid(row=2, column=1, padx=20, pady=15)

    ctk.CTkLabel(form_frame, text="Study Hours").grid(row=3, column=0, padx=20, pady=15, sticky="w")
    hours_entry = ctk.CTkEntry(form_frame, width=250, placeholder_text="Enter study hours")
    hours_entry.grid(row=3, column=1, padx=20, pady=15)

    # ---------- BUTTON ROW ----------
    button_row = ctk.CTkFrame(form_frame, fg_color="transparent")
    button_row.grid(row=4, column=0, columnspan=2, pady=10)

    # ---------- SEARCH BAR ----------
    search_frame = ctk.CTkFrame(page_frame, fg_color="transparent")
    search_frame.pack(padx=30, pady=(5, 5), fill="x")

    search_entry = ctk.CTkEntry(
        search_frame,
        width=300,
        placeholder_text="Search task by name"
    )
    search_entry.pack(side="left", padx=(0, 10))

    # ---------- TABLE ----------
    table_frame = ctk.CTkFrame(page_frame, corner_radius=15)
    table_frame.pack(padx=30, pady=10, fill="both", expand=True)

    columns = ("No.", "Task Name", "Deadline", "Difficulty", "Hours", "Progress", "Status")
    tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=12)

    for col in columns:
        tree.heading(col, text=col)

    tree.column("No.", width=60, anchor="center")
    tree.column("Task Name", width=240, anchor="center")
    tree.column("Deadline", width=140, anchor="center")
    tree.column("Difficulty", width=100, anchor="center")
    tree.column("Hours", width=100, anchor="center")
    tree.column("Progress", width=140, anchor="center")
    tree.column("Status", width=120, anchor="center")

    tree.pack(fill="both", expand=True, padx=10, pady=10)

    search_button = ctk.CTkButton(
        search_frame,
        text="Search",
        width=120,
        command=lambda: search_tasks_into_tree(tree, search_entry.get().strip())
    )
    search_button.pack(side="left", padx=5)

    clear_search_button = ctk.CTkButton(
        search_frame,
        text="Clear",
        width=120,
        fg_color="#4b5563",
        hover_color="#374151",
        command=lambda: [
            search_entry.delete(0, "end"),
            load_tasks_into_tree(tree)
        ]
    )
    clear_search_button.pack(side="left", padx=5)

    def add_task_v2():
        global current_user_id

        task_name = task_entry.get().strip()
        deadline = deadline_entry.get().strip()
        difficulty = difficulty_entry.get().strip()
        hours = hours_entry.get().strip()

        if task_name == "" or deadline == "" or difficulty == "" or hours == "":
            messagebox.showwarning("Missing Information", "Please fill in all fields.")
            return

        try:
            datetime.strptime(deadline, "%Y-%m-%d")
        except ValueError:
            messagebox.showwarning("Invalid Date", "Please enter the deadline in YYYY-MM-DD format.")
            return

        if not difficulty.isdigit() or not (1 <= int(difficulty) <= 5):
            messagebox.showwarning("Invalid Difficulty", "Difficulty must be a number between 1 and 5.")
            return

        if not hours.isdigit():
            messagebox.showwarning("Invalid Study Hours", "Study hours must be a number.")
            return

        try:
            connection = sqlite3.connect(DB_PATH)
            cursor = connection.cursor()

            cursor.execute("""
                INSERT INTO tasks (user_id, task_name, deadline, difficulty, study_hours, status)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (current_user_id, task_name, deadline, int(difficulty), int(hours), "Pending"))

            connection.commit()
            connection.close()

            messagebox.showinfo("Success", "Task added successfully.")

            task_entry.delete(0, "end")
            deadline_entry.delete(0, "end")
            difficulty_entry.delete(0, "end")
            hours_entry.delete(0, "end")

            load_tasks_into_tree(tree)

        except Exception as e:
            messagebox.showerror("Database Error", str(e))

    def edit_selected_task_v2():
        selected_item = tree.focus()

        if not selected_item:
            selected = tree.selection()
            if selected:
                selected_item = selected[0]
   
        if not selected_item:
            messagebox.showwarning("No Selection", "Please select a task first.")
            return

        task_id = selected_item
        task_values = tree.item(selected_item, "values")

        if not task_values:
            messagebox.showwarning("No Selection", "Please select a valid task row.")
            return

        current_task_name = task_values[1]
        current_deadline = task_values[2]
        current_difficulty = task_values[3]
        current_hours = task_values[4]

        edit_window = ctk.CTkToplevel(app)
        edit_window.title("Edit Task")
        edit_window.geometry("420x500")
        edit_window.transient(app)
        edit_window.lift()
        edit_window.focus()

        ctk.CTkLabel(
            edit_window,
            text="Edit Task",
            font=ctk.CTkFont(size=22, weight="bold")
        ).pack(pady=(25, 15))

        ctk.CTkLabel(
            edit_window,
            text="Task Name",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", padx=80, pady=(8, 3))

        task_name_entry = ctk.CTkEntry(edit_window, width=260)
        task_name_entry.pack(pady=(0, 10))
        task_name_entry.insert(0, str(current_task_name))

        ctk.CTkLabel(
            edit_window,
            text="Deadline (YYYY-MM-DD)",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", padx=80, pady=(8, 3))

        deadline_entry = ctk.CTkEntry(edit_window, width=260)
        deadline_entry.pack(pady=(0, 10))
        deadline_entry.insert(0, str(current_deadline))

        ctk.CTkLabel(
            edit_window,
            text="Difficulty (1 - 5)",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", padx=80, pady=(8, 3))

        difficulty_entry = ctk.CTkEntry(edit_window, width=260)
        difficulty_entry.pack(pady=(0, 10))
        difficulty_entry.insert(0, str(current_difficulty))

        ctk.CTkLabel(
            edit_window,
            text="Study Hours",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", padx=80, pady=(8, 3))

        hours_entry = ctk.CTkEntry(edit_window, width=260)
        hours_entry.pack(pady=(0, 15))
        hours_entry.insert(0, str(current_hours))

        def save_task_changes():
            new_task_name = task_name_entry.get().strip()
            new_deadline = deadline_entry.get().strip()
            new_difficulty = difficulty_entry.get().strip()
            new_hours = hours_entry.get().strip()

            if not new_task_name or not new_deadline or not new_difficulty or not new_hours:
                messagebox.showwarning("Missing Information", "Please fill in all fields.")
                return

            try:
                datetime.strptime(new_deadline, "%Y-%m-%d")
            except ValueError:
                messagebox.showwarning("Invalid Date", "Deadline must be in YYYY-MM-DD format.")
                return

            if not new_difficulty.isdigit() or not (1 <= int(new_difficulty) <= 5):
                messagebox.showwarning("Invalid Difficulty", "Difficulty must be between 1 and 5.")
                return

            if not new_hours.isdigit() or int(new_hours) <= 0:
                messagebox.showwarning("Invalid Hours", "Study hours must be a positive number.")
                return

            try:
                connection = sqlite3.connect(DB_PATH)
                cursor = connection.cursor()

                cursor.execute("""
                    UPDATE tasks
                    SET task_name = ?,
                        deadline = ?,
                        difficulty = ?,
                        study_hours = ?
                    WHERE id = ? AND user_id = ?
                """, (
                    new_task_name,
                    new_deadline,
                    int(new_difficulty),
                    int(new_hours),
                    task_id,
                    current_user_id
                ))

                connection.commit()
                connection.close()

                clear_saved_weekly_schedule()
                update_overdue_tasks()

                messagebox.showinfo(
                    "Task Updated",
                    "Task updated successfully. Your weekly schedule was cleared. Please generate a new schedule."
                )

                edit_window.destroy()
                load_tasks_into_tree(tree)

            except Exception as e:
                messagebox.showerror("Update Error", str(e))

        ctk.CTkButton(
            edit_window,
            text="Save Changes",
            width=220,
            command=save_task_changes
        ).pack(pady=20)

    def delete_selected_task_v2():
        selected_item = tree.selection()
        if not selected_item:
            messagebox.showwarning("No Selection", "Please select a task first.")
            return

        task_values = tree.item(selected_item[0], "values")
        task_id = tree.focus()

        try:
            connection = sqlite3.connect(DB_PATH)
            cursor = connection.cursor()
            cursor.execute(
                "DELETE FROM tasks WHERE id = ? AND user_id = ?",
                (task_id, current_user_id)
            )
            connection.commit()
            connection.close()

            messagebox.showinfo("Delete Task", "Task deleted successfully.")
            load_tasks_into_tree(tree)

        except Exception as e:
            messagebox.showerror("Delete Error", str(e))
    
    def mark_completed_v2():
        selected_item = tree.selection()
        if not selected_item:
            messagebox.showwarning("No Selection", "Please select a task first.")
            return

        task_values = tree.item(selected_item[0], "values")
        task_id = tree.focus()
        task_name = task_values[1]

        try:
            connection = sqlite3.connect(DB_PATH)
            cursor = connection.cursor()

            # 🔍 Check if this task has any incomplete sessions
            cursor.execute("""
                SELECT COUNT(*)
                FROM weekly_schedule
                WHERE user_id = ?
                  AND task_id = ?
                  AND is_completed = 0
            """, (current_user_id, task_id))

            remaining_sessions = cursor.fetchone()[0]

            #  If sessions still pending then, block completion
            if remaining_sessions > 0:
                messagebox.showwarning(
                    "Cannot Complete Task",
                    f"You must complete all study sessions for '{task_name}' before marking it as completed."
                )
                connection.close()
                return

            # Otherwise allow completion
            cursor.execute("""
                UPDATE tasks
                SET status = 'Completed'
                WHERE id = ? AND user_id = ?
            """, (task_id, current_user_id))

            connection.commit()
            connection.close()

            messagebox.showinfo("Task Status", "Task marked as completed.")

            load_tasks_into_tree(tree)

        except Exception as e:
            messagebox.showerror("Update Error", str(e))

    button_row = ctk.CTkFrame(form_frame, fg_color="transparent")
    button_row.grid(row=4, column=0, columnspan=2, pady=20)

    add_button = ctk.CTkButton(button_row, text="Add Task", width=160, command=add_task_v2)
    add_button.pack(side="left", padx=10)

    refresh_button = ctk.CTkButton(
        button_row,
        text="Refresh Table",
        width=160,
        command=lambda: load_tasks_into_tree(tree)
    )
    refresh_button.pack(side="left", padx=10)

    complete_button = ctk.CTkButton(
        button_row,
        text="Mark Completed",
        width=160,
        fg_color="#16a34a",
        hover_color="#15803d",
        command=mark_completed_v2
    )
    complete_button.pack(side="left", padx=10)

    delete_button = ctk.CTkButton(
        button_row,
        text="Delete Selected",
        width=160,
        fg_color="red",
        hover_color="darkred",
        command=delete_selected_task_v2
    )
    delete_button.pack(side="left", padx=10)

    edit_button = ctk.CTkButton(
        button_row,
        text="Edit Task",
        width=160,
        fg_color="#f59e0b",
        hover_color="#d97706",
        command=edit_selected_task_v2
    )
    edit_button.pack(side="left", padx=10)

    load_tasks_into_tree(tree)

def show_schedule_page():
    clear_main_area()

    title = ctk.CTkLabel(
        content_frame,
        text="Weekly Schedule",
        font=ctk.CTkFont(size=28, weight="bold")
    )
    title.pack(anchor="w", padx=30, pady=(30, 20))

    subtitle = ctk.CTkLabel(
        content_frame,
        text="Your weekly plan is generated from pending tasks, deadlines, and difficulty",
        font=ctk.CTkFont(size=14),
        text_color="gray"
    )
    subtitle.pack(anchor="w", padx=30, pady=(0, 15))

    button_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
    button_frame.pack(anchor="w", padx=30, pady=10)

    schedule_frame = ctk.CTkFrame(content_frame, corner_radius=15)
    schedule_frame.pack(padx=30, pady=20, fill="both", expand=True)

    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

    availability_frame = ctk.CTkFrame(content_frame, fg_color="#1f2937", corner_radius=12)
    availability_frame.pack(anchor="w", padx=30, pady=(5, 10), fill="x")

    ctk.CTkLabel(
        availability_frame,
        text="Select days you do NOT want study sessions:",
        font=ctk.CTkFont(size=14, weight="bold")
    ).pack(anchor="w", padx=15, pady=(10, 5))

    day_vars = {}

    checkbox_row = ctk.CTkFrame(availability_frame, fg_color="transparent")
    checkbox_row.pack(anchor="w", padx=15, pady=(0, 10))

    for day in days:
        var = ctk.BooleanVar(value=False)
        day_vars[day] = var

        ctk.CTkCheckBox(
            checkbox_row,
            text=day,
            variable=var
        ).pack(side="left", padx=8)

    def render_schedule(schedule_data):
        for widget in schedule_frame.winfo_children():
            widget.destroy()

        for i, day in enumerate(days):
            day_box = ctk.CTkFrame(
                schedule_frame,
                width=150,
                height=420,
                fg_color="#1f2937",
                corner_radius=15
            )
            day_box.grid(row=0, column=i, padx=8, pady=10, sticky="n")
            day_box.grid_propagate(False)

            ctk.CTkLabel(
                day_box,
                text=day,
                font=ctk.CTkFont(size=16, weight="bold")
            ).pack(pady=10)

            sessions = schedule_data.get(day, [])

            if sessions:
                for session in sessions:
                    bg_color = "#14532d" if session.get("is_completed") else "#27374d"
                    session_card = ctk.CTkFrame(day_box, fg_color=bg_color, corner_radius=8)
                    session_card.pack(fill="x", padx=8, pady=5)

                    session_text = (
                        f"{session['task_name']} ({session['session_hours']}h)\n"
                        f"Due: {session['deadline']}"
                    )

                    if session.get("is_completed"):
                        session_text += "\n✅ Completed"

                    session_label = ctk.CTkLabel(
                        session_card,
                        text=session_text,
                        wraplength=115,
                        justify="left",
                        anchor="w",
                        font=ctk.CTkFont(size=11)
                    )
                    session_label.pack(anchor="w", padx=8, pady=(6, 4))

                    if not session.get("is_completed") and "id" in session:
                        done_button = ctk.CTkButton(
                            session_card,
                            text="Mark Done",
                            width=100,
                            height=28,         
                            fg_color="#16a34a",
                            hover_color="#15803d",
                            command=lambda sid=session["id"]: complete_session_action(sid)
                        )
                        done_button.pack(padx=8, pady=(0, 6))

                    elif session.get("is_completed") and "id" in session:
                        undo_button = ctk.CTkButton(
                            session_card,
                            text="Undo",
                            width=100, 
                            height=28,
                            fg_color="#f59e0b",
                            hover_color="#d97706",
                            command=lambda sid=session["id"]: undo_session_action(sid)
                        )
                        undo_button.pack(padx=8, pady=(0, 6))
                    else:
                         ctk.CTkLabel(
                             session_card,
                             text="✔ Completed",
                             text_color="lightgreen",
                             font=ctk.CTkFont(size=10)
                         ).pack(pady=(0,6))

                    
            else:
                ctk.CTkLabel(
                    day_box,
                    text="No sessions",
                    font=ctk.CTkFont(size=12),
                    text_color="gray"
                ).pack(pady=20)

    def generate_schedule_action(show_popup=True):
        excluded_days = [day for day, var in day_vars.items() if var.get()]
        schedule_data = generate_weekly_schedule_data(excluded_days) 
        save_weekly_schedule(schedule_data)
        saved_schedule = load_saved_weekly_schedule()
        render_schedule(saved_schedule)

        total_sessions = sum(len(v) for v in saved_schedule.values())

        if show_popup:
            if total_sessions == 0:
                messagebox.showwarning(
                    "No Tasks",
                    "You have no pending tasks.\nAdd tasks first to generate a schedule."
                )
            else:
                messagebox.showinfo(
                    "Weekly Schedule",
                    "Smart weekly schedule generated and saved successfully."
                )

    def clear_schedule_action():
        clear_saved_weekly_schedule()
        empty_schedule = {day: [] for day in days}
        render_schedule(empty_schedule)

        messagebox.showinfo(
            "Weekly Schedule",
            "Saved schedule cleared successfully."
        )

    def complete_session_action(session_id):
        mark_session_completed(session_id)
        updated_schedule = load_saved_weekly_schedule()
        render_schedule(updated_schedule)

    def undo_session_action(session_id):
        undo_session_completed(session_id)
        updated_schedule = load_saved_weekly_schedule()
        render_schedule(updated_schedule)

    generate_button = ctk.CTkButton(
        button_frame,
        text="Generate Weekly Schedule",
        width=220,
        command=lambda: generate_schedule_action(True)
    )
    generate_button.pack(side="left", padx=(0, 10))

    clear_button = ctk.CTkButton(
        button_frame,
        text="Clear Saved Schedule",
        width=180,
        fg_color="red",
        hover_color="darkred",
        command=clear_schedule_action
    )
    clear_button.pack(side="left")

    if has_saved_weekly_schedule():
        saved_schedule = load_saved_weekly_schedule()
        render_schedule(saved_schedule)
    else:
        empty_schedule = {day: [] for day in days}
        render_schedule(empty_schedule)

def show_calendar_page():
    clear_main_area()

    current_month = datetime.now().month
    current_year = datetime.now().year
    today_date = datetime.now().date()
    selected_date = None

    title = ctk.CTkLabel(
        content_frame,
        text="Calendar View",
        font=ctk.CTkFont(size=28, weight="bold")
    )
    title.pack(anchor="w", padx=30, pady=(30, 10))

    subtitle = ctk.CTkLabel(
        content_frame,
        text="View your tasks by deadline in a monthly calendar",
        font=ctk.CTkFont(size=14),
        text_color="gray"
    )
    subtitle.pack(anchor="w", padx=30, pady=(0, 20))

    nav_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
    nav_frame.pack(anchor="w", padx=30, pady=(0, 10))

    main_calendar_area = ctk.CTkFrame(content_frame, fg_color="transparent")
    main_calendar_area.pack(padx=20, pady=10, fill="both", expand=True)

    left_frame = ctk.CTkFrame(main_calendar_area, corner_radius=15, fg_color="#2b2b2b")
    left_frame.pack(side="left", fill="both", expand=True, padx=(0, 10))

    month_label = ctk.CTkLabel(
        left_frame,
        text="",
        font=ctk.CTkFont(size=24, weight="bold")
    )
    month_label.pack(pady=(18, 10))

    header_frame = ctk.CTkFrame(left_frame, fg_color="transparent")
    header_frame.pack(padx=10, pady=(0, 8), fill="x")

    grid_frame = ctk.CTkFrame(left_frame, fg_color="transparent")
    grid_frame.pack(padx=10, pady=(0, 15), fill="both", expand=True)

    details_panel = ctk.CTkFrame(
        main_calendar_area,
        width=260,
        corner_radius=15,
        fg_color="#1f2937"
    )
    details_panel.pack(side="right", fill="y")
    details_panel.pack_propagate(False)

    details_title = ctk.CTkLabel(
        details_panel,
        text="Task Details",
        font=ctk.CTkFont(size=20, weight="bold")
    )
    details_title.pack(anchor="w", padx=15, pady=(20, 10))

    selected_date_label = ctk.CTkLabel(
        details_panel,
        text="Select a date",
        font=ctk.CTkFont(size=13),
        text_color="gray"
    )
    selected_date_label.pack(anchor="w", padx=15, pady=(0, 10))

    details_scroll = ctk.CTkScrollableFrame(details_panel, width=220, height=600)
    details_scroll.pack(padx=10, pady=(0, 15), fill="both", expand=True)

    def clear_details_panel():
        for widget in details_scroll.winfo_children():
            widget.destroy()

    def get_task_color(task_status, date_key):
        try:
            deadline_date = datetime.strptime(date_key, "%Y-%m-%d").date()
        except Exception:
            deadline_date = None

        if task_status == "Completed":
            return "lightgreen"
        elif deadline_date and deadline_date < today_date:
            return "#ef4444"
        else:
            return "#facc15"

    def show_tasks_in_panel(date_key, tasks_for_day):
        nonlocal selected_date
        selected_date = date_key

        selected_date_label.configure(text=f"Selected: {date_key}")
        clear_details_panel()

        if not tasks_for_day:
            ctk.CTkLabel(
                details_scroll,
                text="No tasks for this date",
                font=ctk.CTkFont(size=13),
                text_color="gray"
            ).pack(anchor="w", padx=8, pady=10)

            render_calendar(current_month, current_year)
            return

        for task in tasks_for_day:
            task_name = task["task_name"]
            status = task["status"]
            status_color = get_task_color(status, date_key)

            task_card = ctk.CTkFrame(details_scroll, fg_color="#111827", corner_radius=12)
            task_card.pack(fill="x", padx=6, pady=6)

            ctk.CTkLabel(
                task_card,
                text=task_name,
                font=ctk.CTkFont(size=14, weight="bold"),
                wraplength=190,
                justify="left"
            ).pack(anchor="w", padx=10, pady=(10, 4))

            ctk.CTkLabel(
                task_card,
                text=f"Deadline: {date_key}",
                font=ctk.CTkFont(size=11),
                text_color="gray"
            ).pack(anchor="w", padx=10, pady=(0, 2))

            ctk.CTkLabel(
                task_card,
                text=f"Status: {status}",
                font=ctk.CTkFont(size=11),
                text_color=status_color
            ).pack(anchor="w", padx=10, pady=(0, 10))

        render_calendar(current_month, current_year)

    def bind_click(widget, date_key, tasks_for_day):
        def handle_click(event=None):
            show_tasks_in_panel(date_key, tasks_for_day)
            render_calendar(current_month, current_year) 
        widget.bind("<Button-1>", handle_click)

    def render_calendar(month, year):
        month_label.configure(text=f"{calendar.month_name[month]} {year}")

        for widget in header_frame.winfo_children():
            widget.destroy()

        for widget in grid_frame.winfo_children():
            widget.destroy()

        short_day_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

        for col, day_name in enumerate(short_day_names):
            header = ctk.CTkLabel(
                header_frame,
                text=day_name,
                font=ctk.CTkFont(size=16, weight="bold")
            )
            header.grid(row=0, column=col, padx=4, pady=4, sticky="nsew")
            header_frame.grid_columnconfigure(col, weight=1, uniform="header")

        month_matrix = calendar.monthcalendar(year, month)
        tasks_by_date = get_tasks_for_month(year, month)

        CELL_WIDTH = 115
        CELL_HEIGHT = 95

        for row_index, week in enumerate(month_matrix):
            for col_index, day in enumerate(week):
                if day == 0:
                    empty = ctk.CTkFrame(
                        grid_frame,
                        fg_color="transparent",
                        width=CELL_WIDTH,
                        height=CELL_HEIGHT
                    )
                    empty.grid(row=row_index, column=col_index, padx=4, pady=4)
                    empty.grid_propagate(False)
                    continue

                date_key = f"{year}-{month:02d}-{day:02d}"
                tasks_for_day = tasks_by_date.get(date_key, [])
                cell_date = datetime(year, month, day).date()

                fg_color = "#17263c"
                border_width = 0
                border_color = None

                if cell_date == today_date:
                    fg_color = "#1d3557"
                    border_width = 2
                    border_color = "#3b82f6"

                if selected_date == date_key:
                    border_width = 2
                    border_color = "#facc15"

                day_box = ctk.CTkFrame(
                    grid_frame,
                    fg_color=fg_color,
                    corner_radius=10,
                    width=CELL_WIDTH,
                    height=CELL_HEIGHT,
                    border_width=border_width,
                    border_color=border_color
                )
                original_color = fg_color

                def on_enter(e):
                    # don't override selected or today styles
                    if border_width == 0:
                        day_box.configure(fg_color="#223a5e")

                def on_leave(e):
                    day_box.configure(fg_color=original_color)

                day_box.bind("<Enter>", on_enter)
                day_box.bind("<Leave>", on_leave)

                day_box.grid(row=row_index, column=col_index, padx=4, pady=4, sticky="nsew")
                day_box.grid_propagate(False)

                top_row = ctk.CTkFrame(day_box, fg_color="transparent")
                top_row.pack(fill="x", padx=6, pady=(6, 2))

                date_label = ctk.CTkLabel(
                    top_row,
                    text=str(day),
                    font=ctk.CTkFont(size=16, weight="bold")
                )
                date_label.pack(anchor="e")

                if cell_date == today_date:
                    today_label = ctk.CTkLabel(
                        top_row,
                        text="Today",
                        font=ctk.CTkFont(size=9, weight="bold"),
                        text_color="#93c5fd"
                    )
                    today_label.pack(anchor="w")

                body_frame = ctk.CTkFrame(day_box, fg_color="transparent")
                body_frame.pack(fill="both", expand=True, padx=6, pady=(0, 6))

                if tasks_for_day:
                    count_label = ctk.CTkLabel(
                        body_frame,
                        text=f"{len(tasks_for_day)} task(s)",
                        font=ctk.CTkFont(size=9),
                        text_color="gray"
                    )
                    count_label.pack(anchor="w", pady=(0, 3))
                    bind_click(count_label, date_key, tasks_for_day)

                    for task in tasks_for_day[:2]:
                        task_color = get_task_color(task["status"], date_key)

                        task_label = ctk.CTkLabel(
                            body_frame,
                            text=f"• {task['task_name']}",
                            text_color=task_color,
                            font=ctk.CTkFont(size=10),
                            wraplength=95,
                            justify="left",
                            anchor="w"
                        )
                        task_label.pack(anchor="w", pady=1)
                        bind_click(task_label, date_key, tasks_for_day)

                    if len(tasks_for_day) > 2:
                        more_label = ctk.CTkLabel(
                            body_frame,
                            text=f"+{len(tasks_for_day) - 2} more",
                            text_color="#9ca3af",
                            font=ctk.CTkFont(size=9)
                        )
                        more_label.pack(anchor="w", pady=(2, 0))
                        bind_click(more_label, date_key, tasks_for_day)
                else:
                    empty_label = ctk.CTkLabel(
                        body_frame,
                        text="No tasks",
                        text_color="gray",
                        font=ctk.CTkFont(size=10)
                    )
                    empty_label.pack(anchor="w", pady=(6, 0))
                    bind_click(empty_label, date_key, tasks_for_day)

                bind_click(day_box, date_key, tasks_for_day)
                bind_click(top_row, date_key, tasks_for_day)
                bind_click(date_label, date_key, tasks_for_day)
                bind_click(body_frame, date_key, tasks_for_day)

        for col in range(7):
            grid_frame.grid_columnconfigure(col, weight=1, uniform="calendar")

    def prev_month():
        nonlocal current_month, current_year
        current_month -= 1
        if current_month == 0:
            current_month = 12
            current_year -= 1
        render_calendar(current_month, current_year)

    def next_month():
        nonlocal current_month, current_year
        current_month += 1
        if current_month == 13:
            current_month = 1
            current_year += 1
        render_calendar(current_month, current_year)

    prev_button = ctk.CTkButton(
        nav_frame,
        text="⬅ Prev",
        width=100,
        command=prev_month
    )
    prev_button.pack(side="left", padx=(0, 10))

    next_button = ctk.CTkButton(
        nav_frame,
        text="Next ➡",
        width=100,
        command=next_month
    )
    next_button.pack(side="left")

    render_calendar(current_month, current_year)

def show_progress_page():
    clear_main_area()

    total_tasks, completed_tasks, pending_tasks, task_progress = get_task_stats()
    total_sessions, completed_sessions, schedule_progress = get_schedule_completion_stats()

    if total_tasks > 0 and total_sessions > 0:
        overall_progress = (task_progress + schedule_progress) / 2
    elif total_tasks > 0:
        overall_progress = task_progress
    elif total_sessions > 0:
        overall_progress = schedule_progress
    else:
        overall_progress = 0

    title = ctk.CTkLabel(
        content_frame,
        text="Progress Overview",
        font=ctk.CTkFont(size=28, weight="bold")
    )
    title.pack(anchor="w", padx=30, pady=(30, 20))

    ctk.CTkLabel(
        content_frame,
        text="Completion Progress",
        font=ctk.CTkFont(size=18, weight="bold")
    ).pack(anchor="w", padx=30, pady=10)

    progress_bar = ctk.CTkProgressBar(content_frame, width=500)
    progress_bar.pack(anchor="w", padx=30, pady=10)
    progress_bar.set(overall_progress)

    ctk.CTkLabel(
        content_frame,
        text=f"{round(overall_progress * 100, 1)}% overall progress",
        font=ctk.CTkFont(size=14)
    ).pack(anchor="w", padx=30, pady=5)

    stats_box = ctk.CTkFrame(content_frame, fg_color="#1f2937", corner_radius=15)
    stats_box.pack(padx=30, pady=25, fill="x")

    ctk.CTkLabel(
        stats_box,
        text=f"📋 Total Tasks: {total_tasks}",
        font=ctk.CTkFont(size=16)
    ).pack(anchor="w", padx=20, pady=10)

    ctk.CTkLabel(
        stats_box,
        text=f"✅ Completed Tasks: {completed_tasks}",
        font=ctk.CTkFont(size=16)
    ).pack(anchor="w", padx=20, pady=10)

    ctk.CTkLabel(
        stats_box,
        text=f"⏳ Pending Tasks: {pending_tasks}",
        font=ctk.CTkFont(size=16)
    ).pack(anchor="w", padx=20, pady=10)

    ctk.CTkLabel(
        stats_box,
        text=f"🗓 Total Schedule Sessions: {total_sessions}",
        font=ctk.CTkFont(size=16)
    ).pack(anchor="w", padx=20, pady=10)

    ctk.CTkLabel(
        stats_box,
        text=f"✔ Completed Sessions: {completed_sessions}",
        font=ctk.CTkFont(size=16)
    ).pack(anchor="w", padx=20, pady=10)

    ctk.CTkLabel(
        stats_box,
        text=f"📈 Task Progress: {round(task_progress * 100, 1)}%",
        font=ctk.CTkFont(size=16)
    ).pack(anchor="w", padx=20, pady=10)

    ctk.CTkLabel(
        stats_box,
        text=f"📊 Schedule Progress: {round(schedule_progress * 100, 1)}%",
        font=ctk.CTkFont(size=16)
    ).pack(anchor="w", padx=20, pady=10)

def validate_password(password):
    if len(password) < 8:
        return "Password must be at least 8 characters long."
    if not re.search(r"[A-Z]", password):
        return "Password must contain at least one uppercase letter."
    if not re.search(r"[a-z]", password):
        return "Password must contain at least one lowercase letter."
    if not re.search(r"[0-9]", password):
        return "Password must contain at least one number."
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return "Password must contain at least one special character."
    return None


def hash_password(password):
    salt = secrets.token_hex(16)
    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode(),
        salt.encode(),
        100000
    ).hex()
    return f"{salt}${password_hash}"


def verify_password(password, stored_password):
    try:
        if "$" not in stored_password:
            return password == stored_password

        salt, saved_hash = stored_password.split("$")
        password_hash = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode(),
            salt.encode(),
            100000
        ).hex()

        return password_hash == saved_hash
    except Exception:
        return False

def show_register():
    register_window = ctk.CTkToplevel(app)
    register_window.title("Register")
    register_window.geometry("400x350")

    title_label = ctk.CTkLabel(
        register_window,
        text="Create Account",
        font=ctk.CTkFont(size=24, weight="bold")
    )
    title_label.pack(pady=(30, 20))

    username_entry = ctk.CTkEntry(
        register_window,
        width=260,
        height=40,
        placeholder_text="New Username"
    )
    username_entry.pack(pady=10)

    password_entry = ctk.CTkEntry(
        register_window,
        width=260,
        height=40,
        placeholder_text="New Password",
        show="*"
    )
    password_entry.pack(pady=10)

    def register_user():
        username = username_entry.get().strip()
        password = password_entry.get().strip()

        password_error = validate_password(password)
        if password_error:
            messagebox.showwarning("Weak Password", password_error)
            return
   
        hashed_password = hash_password(password)

        if username == "" or password == "":
            messagebox.showwarning("Missing Information", "Please fill in all fields.")
            return

        try:
            connection = sqlite3.connect(DB_PATH)
            cursor = connection.cursor()

            cursor.execute(
                "INSERT INTO users (username, password) VALUES (?, ?)",
                (username, hashed_password)
            )

            connection.commit()
            connection.close()

            messagebox.showinfo("Success", "User registered successfully.")
            register_window.destroy()

        except sqlite3.IntegrityError:
            messagebox.showerror("Register Error", "Username already exists.")
        except Exception as e:
            messagebox.showerror("Register Error", str(e))

    register_button = ctk.CTkButton(
        register_window,
        text="Register",
        width=260,
        height=40,
        command=register_user
    )
    register_button.pack(pady=20)

def show_forgot_password():
    forgot_window = ctk.CTkToplevel(app)
    forgot_window.title("Forgot Password")
    forgot_window.geometry("420x420")
    forgot_window.transient(app)
    forgot_window.lift()
    forgot_window.focus()

    ctk.CTkLabel(
        forgot_window,
        text="Reset Password",
        font=ctk.CTkFont(size=24, weight="bold")
    ).pack(pady=(30, 20))

    username_entry = ctk.CTkEntry(
        forgot_window,
        width=280,
        height=40,
        placeholder_text="Username"
    )
    username_entry.pack(pady=10)

    new_password_entry = ctk.CTkEntry(
        forgot_window,
        width=280,
        height=40,
        placeholder_text="New Password",
        show="*"
    )
    new_password_entry.pack(pady=10)

    confirm_password_entry = ctk.CTkEntry(
        forgot_window,
        width=280,
        height=40,
        placeholder_text="Confirm New Password",
        show="*"
    )
    confirm_password_entry.pack(pady=10)

    def reset_password():
        username = username_entry.get().strip()
        new_password = new_password_entry.get().strip()
        confirm_password = confirm_password_entry.get().strip()

        if not username or not new_password or not confirm_password:
            messagebox.showwarning("Missing Information", "Please fill in all fields.")
            return

        if new_password != confirm_password:
            messagebox.showwarning("Password Error", "Passwords do not match.")
            return

        password_error = validate_password(new_password)
        if password_error:
            messagebox.showwarning("Weak Password", password_error)
            return

        try:
            connection = sqlite3.connect(DB_PATH)
            cursor = connection.cursor()

            cursor.execute(
                "SELECT id FROM users WHERE username = ?",
                (username,)
            )
            user = cursor.fetchone()

            if not user:
                messagebox.showerror("User Not Found", "No account found with this username.")
                connection.close()
                return

            hashed_new_password = hash_password(new_password)

            cursor.execute(
                "UPDATE users SET password = ? WHERE id = ?",
                (hashed_new_password, user[0])
            )

            connection.commit()
            connection.close()

            messagebox.showinfo("Success", "Password reset successfully. You can now login.")
            forgot_window.destroy()

        except Exception as e:
            messagebox.showerror("Reset Error", str(e))

    ctk.CTkButton(
        forgot_window,
        text="Reset Password",
        width=280,
        height=40,
        command=reset_password
    ).pack(pady=20)

def show_login():
    for widget in app.winfo_children():
        widget.destroy()

    login_frame = ctk.CTkFrame(app, width=420, height=430, corner_radius=20)
    login_frame.place(relx=0.5, rely=0.5, anchor="center")

    title_label = ctk.CTkLabel(
        login_frame,
        text="Study Scheduler",
        font=ctk.CTkFont(size=30, weight="bold")
    )
    title_label.pack(pady=(35, 15))

    subtitle_label = ctk.CTkLabel(
        login_frame,
        text="Plan Smart. Study Better.",
        font=ctk.CTkFont(size=15),
        text_color="gray"
    )
    subtitle_label.pack(pady=(0, 20))

    username_entry = ctk.CTkEntry(login_frame, width=300, height=42, placeholder_text="Username")
    username_entry.pack(pady=10)

    password_entry = ctk.CTkEntry(login_frame, width=300, height=42, placeholder_text="Password", show="*")
    password_entry.pack(pady=10)

    def login_user():
        username = username_entry.get().strip()
        password = password_entry.get().strip()

        if username == "" or password == "":
            messagebox.showwarning("Missing Information", "Please enter username and password.")
            return

        try:
            connection = sqlite3.connect(DB_PATH)
            cursor = connection.cursor()

            cursor.execute(
                "SELECT * FROM users WHERE username = ?",
                (username,)
            )

            user = cursor.fetchone()
            connection.close()

            if user and verify_password(password, user[2]):
                global current_user_id
                current_user_id = user[0]
                save_login_session(current_user_id)
                show_main_app()
            else:
                messagebox.showerror("Login Failed", "Invalid username or password.")

        except Exception as e:
            messagebox.showerror("Login Error", str(e))

    login_button = ctk.CTkButton(
        login_frame,
        text="Login",
        width=300,
        height=42,
        fg_color="#3b82f6",
        hover_color="#2563eb",
        command=login_user
    )
    login_button.pack(pady=(20, 10))

    forgot_button = ctk.CTkButton(
        login_frame,
        text="Forgot Password?",
        width=300,
        height=36,
        fg_color="transparent",
        hover_color="#374151",
        text_color="#60a5fa",
        command=show_forgot_password
    )
    forgot_button.pack(pady=(0, 10)) 

    register_button = ctk.CTkButton(
        login_frame,
        text="Register",
        width=300,
        height=42,
        fg_color="#4b5563",
        hover_color="#374151",
        command=show_register
    )
    register_button.pack(pady=10)

def show_change_password_page():
    clear_main_area()

    title = ctk.CTkLabel(
        content_frame,
        text="Change Password",
        font=ctk.CTkFont(size=28, weight="bold")
    )
    title.pack(anchor="w", padx=30, pady=(30, 20))

    form_frame = ctk.CTkFrame(content_frame, fg_color="#2b2b2b", corner_radius=15)
    form_frame.pack(padx=30, pady=20, fill="x")

    old_password_entry = ctk.CTkEntry(
        form_frame,
        width=300,
        placeholder_text="Current Password",
        show="*"
    )
    old_password_entry.pack(pady=15)

    new_password_entry = ctk.CTkEntry(
        form_frame,
        width=300,
        placeholder_text="New Password",
        show="*"
    )
    new_password_entry.pack(pady=15)

    confirm_password_entry = ctk.CTkEntry(
        form_frame,
        width=300,
        placeholder_text="Confirm New Password",
        show="*"
    )
    confirm_password_entry.pack(pady=15)

    def change_password():
        old_password = old_password_entry.get().strip()
        new_password = new_password_entry.get().strip()
        confirm_password = confirm_password_entry.get().strip()

        if not old_password or not new_password or not confirm_password:
            messagebox.showwarning("Missing Information", "Please fill in all fields.")
            return

        if new_password != confirm_password:
            messagebox.showwarning("Password Error", "New passwords do not match.")
            return

        password_error = validate_password(new_password)
        if password_error:
            messagebox.showwarning("Weak Password", password_error)
            return

        try:
            connection = sqlite3.connect(DB_PATH)
            cursor = connection.cursor()

            cursor.execute(
                "SELECT password FROM users WHERE id = ?",
                (current_user_id,)
            )
            row = cursor.fetchone()

            if not row or not verify_password(old_password, row[0]):
                messagebox.showerror("Password Error", "Current password is incorrect.")
                connection.close()
                return

            new_hashed_password = hash_password(new_password)

            cursor.execute(
                "UPDATE users SET password = ? WHERE id = ?",
                (new_hashed_password, current_user_id)
            )

            connection.commit()
            connection.close()

            messagebox.showinfo("Success", "Password changed successfully.")

            old_password_entry.delete(0, "end")
            new_password_entry.delete(0, "end")
            confirm_password_entry.delete(0, "end")

        except Exception as e:
            messagebox.showerror("Password Error", str(e))

    ctk.CTkButton(
        form_frame,
        text="Change Password",
        width=220,
        fg_color="#3b82f6",
        hover_color="#2563eb",
        command=change_password
    ).pack(pady=20)

def show_main_app():
    global content_frame

    for widget in app.winfo_children():
        widget.destroy()

    sidebar = ctk.CTkFrame(app, width=280, corner_radius=0, fg_color="#111827")
    sidebar.pack(side="left", fill="y")
    sidebar.pack_propagate(False)

    logo_frame = ctk.CTkFrame(sidebar, fg_color="transparent")
    logo_frame.pack(pady=(30, 20))

    logo_icon = ctk.CTkLabel(
        logo_frame,
        text="📚",
        font=ctk.CTkFont(size=32)
    )
    logo_icon.pack()

    logo_label = ctk.CTkLabel(
        logo_frame,
        text="Study Scheduler",
        font=ctk.CTkFont(size=20, weight="bold")
    )
    logo_label.pack()

    tagline = ctk.CTkLabel(
        logo_frame,
        text="Plan Smart. Study Better.",
        font=ctk.CTkFont(size=12),
        text_color="gray"
    )
    tagline.pack(pady=(5, 10))

    dashboard_button = sidebar_button(sidebar, "📊 Dashboard", show_dashboard_page)
    dashboard_button.pack(pady=8)

    tasks_button = sidebar_button(sidebar, "📝 Task Management", show_tasks_page)
    tasks_button.pack(pady=8)

    schedule_button = sidebar_button(sidebar, "📅 Weekly Schedule", show_schedule_page)
    schedule_button.pack(pady=8)

    calendar_button = sidebar_button(sidebar, "🗓 Calendar View", show_calendar_page)
    calendar_button.pack(pady=8)

    progress_button = sidebar_button(sidebar, "📈 Progress", show_progress_page)
    progress_button.pack(pady=8)

    def logout_user():
        global current_user_id
        current_user_id = None
        clear_login_session()
        show_login()

    logout_button = ctk.CTkButton(
        sidebar,
        text="Logout",
        width=220,
        height=42,
        corner_radius=10,
        fg_color="#ef4444",
        hover_color="#dc2626",
        command=logout_user
    )
    logout_button.pack(side="bottom", pady=30)

    content_frame = ctk.CTkFrame(app, corner_radius=0)
    content_frame.pack(side="right", fill="both", expand=True)

    update_overdue_tasks()
    show_dashboard_page()
    app.after(500, show_task_reminders)


# Start app
create_tables()

saved_user_id = load_login_session()

if saved_user_id:
    current_user_id = saved_user_id
    show_main_app()
else:
    show_login()

app.mainloop()