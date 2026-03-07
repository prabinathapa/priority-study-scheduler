import sqlite3
import customtkinter as ctk
from tkinter import messagebox, ttk 
from datetime import datetime

current_user_id = None

# App settings
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

app = ctk.CTk()
app.title("Priority-Based Study Scheduler - Version 2")
app.geometry("1400x800")


# ---------- Page Functions ----------
def clear_main_area():
    for widget in content_frame.winfo_children():
        widget.destroy()


def show_dashboard_page():
    clear_main_area()

    title = ctk.CTkLabel(
        content_frame,
        text="Dashboard",
        font=ctk.CTkFont(size=28, weight="bold")
    )
    title.pack(anchor="w", padx=30, pady=(30, 10))

    subtitle = ctk.CTkLabel(
        content_frame,
        text="Welcome to your study planner dashboard",
        font=ctk.CTkFont(size=16)
    )
    subtitle.pack(anchor="w", padx=30, pady=(0, 20))

    cards_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
    cards_frame.pack(padx=30, pady=20, fill="x")

    card1 = ctk.CTkFrame(cards_frame, width=220, height=130, fg_color="#374151")
    card1.grid(row=0, column=0, padx=15, pady=10)
    ctk.CTkLabel(card1, text="Total Tasks\n0", font=ctk.CTkFont(size=22, weight="bold")).place(relx=0.5, rely=0.5, anchor="center")

    card2 = ctk.CTkFrame(cards_frame, width=220, height=130, fg_color="#374151")
    card2.grid(row=0, column=1, padx=15, pady=10)
    ctk.CTkLabel(card2, text="Completed\n0", font=ctk.CTkFont(size=22, weight="bold")).place(relx=0.5, rely=0.5, anchor="center")

    card3 = ctk.CTkFrame(cards_frame, width=220, height=130, fg_color="#374151")
    card3.grid(row=0, column=2, padx=15, pady=10)
    ctk.CTkLabel(card3, text="Pending\n0", font=ctk.CTkFont(size=22, weight="bold")).place(relx=0.5, rely=0.5, anchor="center")

    progress_title = ctk.CTkLabel(
        content_frame,
        text="Overall Progress",
        font=ctk.CTkFont(size=20, weight="bold")
    )
    progress_title.pack(anchor="w", padx=30, pady=(30, 10))

    progress_bar = ctk.CTkProgressBar(content_frame, width=450)
    progress_bar.pack(anchor="w", padx=30, pady=10)
    progress_bar.set(0.4)

    progress_text = ctk.CTkLabel(
        content_frame,
        text="40% Completed",
        font=ctk.CTkFont(size=14)
    )
    progress_text.pack(anchor="w", padx=30, pady=5)

def load_tasks_into_tree(tree):
    global current_user_id

    try:
        for item in tree.get_children():
            tree.delete(item)

        connection = sqlite3.connect("database/study_scheduler.db")
        cursor = connection.cursor()

        cursor.execute("""
            SELECT id, task_name, deadline, difficulty, study_hours, status
            FROM tasks
            WHERE user_id = ?
            ORDER BY id DESC
        """, (current_user_id,))

        tasks = cursor.fetchall()
        connection.close()

        for task in tasks:
            tree.insert("", "end", values=task)

    except Exception as e:
        messagebox.showerror("Load Error", str(e))

def show_tasks_page():
    clear_main_area()

    title = ctk.CTkLabel(
        content_frame,
        text="Task Management",
        font=ctk.CTkFont(size=28, weight="bold")
    )
    title.pack(anchor="w", padx=30, pady=(30, 20))

    form_frame = ctk.CTkFrame(content_frame, fg_color="#2b2b2b")
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

    # Table frame
    table_frame = ctk.CTkFrame(content_frame)
    table_frame.pack(padx=30, pady=25, fill="both", expand=True)

    columns = ("ID", "Task Name", "Deadline", "Difficulty", "Hours", "Status")
    tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=12)

    for col in columns:
        tree.heading(col, text=col)

    tree.column("ID", width=50, anchor="center")
    tree.column("Task Name", width=220, anchor="center")
    tree.column("Deadline", width=140, anchor="center")
    tree.column("Difficulty", width=100, anchor="center")
    tree.column("Hours", width=100, anchor="center")
    tree.column("Status", width=120, anchor="center")

    tree.pack(fill="both", expand=True, padx=10, pady=10)

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

        if not difficulty.isdigit():
            messagebox.showwarning("Invalid Difficulty", "Difficulty must be a number.")
            return

        if not hours.isdigit():
            messagebox.showwarning("Invalid Study Hours", "Study hours must be a number.")
            return

        try:
            connection = sqlite3.connect("database/study_scheduler.db")
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

    def delete_selected_task_v2():
        selected_item = tree.selection()
        if not selected_item:
            messagebox.showwarning("No Selection", "Please select a task first.")
            return

        task_values = tree.item(selected_item[0], "values")
        task_id = task_values[0]

        try:
            connection = sqlite3.connect("database/study_scheduler.db")
            cursor = connection.cursor()
            cursor.execute("DELETE FROM tasks WHERE id = ? AND user_id = ?", (task_id, current_user_id))
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
        task_id = task_values[0]

        try:
            connection = sqlite3.connect("database/study_scheduler.db")
            cursor = connection.cursor()
            cursor.execute(
                "UPDATE tasks SET status = 'Completed' WHERE id = ? AND user_id = ?",
                (task_id, current_user_id)
            )
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

    refresh_button = ctk.CTkButton(button_row, text="Refresh Table", width=160, command=lambda: load_tasks_into_tree(tree))
    refresh_button.pack(side="left", padx=10)

    complete_button = ctk.CTkButton(button_row, text="Mark Completed", width=160, command=mark_completed_v2)
    complete_button.pack(side="left", padx=10)

    delete_button = ctk.CTkButton(button_row, text="Delete Selected", width=160, fg_color="red", hover_color="darkred", command=delete_selected_task_v2)
    delete_button.pack(side="left", padx=10)

    load_tasks_into_tree(tree)

def show_schedule_page():
    clear_main_area()

    title = ctk.CTkLabel(
        content_frame,
        text="Weekly Schedule",
        font=ctk.CTkFont(size=28, weight="bold")
    )
    title.pack(anchor="w", padx=30, pady=(30, 20))

    ctk.CTkButton(content_frame, text="Generate Weekly Schedule", width=220).pack(anchor="w", padx=30, pady=10)

    schedule_frame = ctk.CTkFrame(content_frame)
    schedule_frame.pack(padx=30, pady=20, fill="both", expand=True)

    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

    for i, day in enumerate(days):
        day_box = ctk.CTkFrame(schedule_frame, width=140, height=400, fg_color="#374151")
        day_box.grid(row=0, column=i, padx=8, pady=10, sticky="n")
        ctk.CTkLabel(day_box, text=day, font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)
        ctk.CTkLabel(day_box, text="No sessions yet", font=ctk.CTkFont(size=12)).pack(pady=20)


def show_progress_page():
    clear_main_area()

    title = ctk.CTkLabel(
        content_frame,
        text="Progress Overview",
        font=ctk.CTkFont(size=28, weight="bold")
    )
    title.pack(anchor="w", padx=30, pady=(30, 20))

    ctk.CTkLabel(content_frame, text="Completion Progress", font=ctk.CTkFont(size=18, weight="bold")).pack(anchor="w", padx=30, pady=10)

    progress_bar = ctk.CTkProgressBar(content_frame, width=500)
    progress_bar.pack(anchor="w", padx=30, pady=10)
    progress_bar.set(0.6)

    ctk.CTkLabel(content_frame, text="60% of tasks completed", font=ctk.CTkFont(size=14)).pack(anchor="w", padx=30, pady=5)

    stats_box = ctk.CTkFrame(content_frame, fg_color="#374151")
    stats_box.pack(padx=30, pady=25, fill="x")

    ctk.CTkLabel(stats_box, text="Total Tasks: 10", font=ctk.CTkFont(size=16)).pack(anchor="w", padx=20, pady=10)
    ctk.CTkLabel(stats_box, text="Completed Tasks: 6", font=ctk.CTkFont(size=16)).pack(anchor="w", padx=20, pady=10)
    ctk.CTkLabel(stats_box, text="Pending Tasks: 4", font=ctk.CTkFont(size=16)).pack(anchor="w", padx=20, pady=10)

def show_register():
    register_window = ctk.CTkToplevel(app)
    register_window.title("Register")
    register_window.geometry("400x350")

    title_label = ctk.CTkLabel(
        register_window,
        text="Register New User",
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

        if username == "" or password == "":
            messagebox.showwarning("Missing Information", "Please fill in all fields.")
            return

        try:
            connection = sqlite3.connect("database/study_scheduler.db")
            cursor = connection.cursor()

            cursor.execute(
                "INSERT INTO users (username, password) VALUES (?, ?)",
                (username, password)
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

def show_login():
    for widget in app.winfo_children():
        widget.destroy()

    login_frame = ctk.CTkFrame(app, width=420, height=430, corner_radius=20)
    login_frame.place(relx=0.5, rely=0.5, anchor="center")

    title_label = ctk.CTkLabel(
        login_frame,
        text="Login",
        font=ctk.CTkFont(size=30, weight="bold")
    )
    title_label.pack(pady=(35, 15))

    subtitle_label = ctk.CTkLabel(
        login_frame,
        text="Priority-Based Study Scheduler",
        font=ctk.CTkFont(size=15)
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
            connection = sqlite3.connect("database/study_scheduler.db")
            cursor = connection.cursor()

            cursor.execute(
                "SELECT * FROM users WHERE username = ? AND password = ?",
                (username, password)
            )

            user = cursor.fetchone()
            connection.close()

            if user:
                global current_user_id
                current_user_id = user[0]   # user id from database
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


def show_main_app():
    global content_frame

    for widget in app.winfo_children():
        widget.destroy()

    sidebar = ctk.CTkFrame(app, width=400, corner_radius=0, fg_color="#1f2937")
    sidebar.pack(side="left", fill="y")

    logo_label = ctk.CTkLabel(
        sidebar,
        text="Study Scheduler",
        font=ctk.CTkFont(size=24, weight="bold")
    )
    logo_label.pack(pady=(30, 30))

    dashboard_button = ctk.CTkButton(sidebar, text="Dashboard", width=180, command=show_dashboard_page)
    dashboard_button.pack(pady=10)

    tasks_button = ctk.CTkButton(sidebar, text="Task Management", width=180, command=show_tasks_page)
    tasks_button.pack(pady=10)

    schedule_button = ctk.CTkButton(sidebar, text="Weekly Schedule", width=180, command=show_schedule_page)
    schedule_button.pack(pady=10)

    progress_button = ctk.CTkButton(sidebar, text="Progress", width=180, command=show_progress_page)
    progress_button.pack(pady=10)

    logout_button = ctk.CTkButton(
        sidebar,
        text="Logout",
        width=180,
        fg_color="red",
        hover_color="darkred",
        command=show_login
    )
    logout_button.pack(side="bottom", pady=30)

    content_frame = ctk.CTkFrame(app, corner_radius=0)
    content_frame.pack(side="right", fill="both", expand=True)

    show_dashboard_page()


# Start app
show_login()
app.mainloop()