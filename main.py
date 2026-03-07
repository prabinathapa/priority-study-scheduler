import tkinter as tk
from tkinter import messagebox, ttk, simpledialog
import sqlite3
from datetime import datetime


# Function to handle adding a task
def add_task():
    task_name = task_entry.get()
    deadline = deadline_entry.get()
    difficulty = difficulty_entry.get()
    hours = hours_entry.get()

    if task_name == "" or deadline == "" or difficulty == "" or hours == "":
        messagebox.showwarning("Missing Information", "Please fill in all fields.")
        return

    if not is_valid_date(deadline):
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
        INSERT INTO tasks (task_name, deadline, difficulty, study_hours, status)
        VALUES (?, ?, ?, ?, ?)
        """, (task_name, deadline, int(difficulty), int(hours), "Pending"))

        connection.commit()
        connection.close()

        messagebox.showinfo("Success", "Task added successfully!")
        update_progress_label()

        task_entry.delete(0, tk.END)
        deadline_entry.delete(0, tk.END)
        difficulty_entry.delete(0, tk.END)
        hours_entry.delete(0, tk.END)

    except Exception as e:
        messagebox.showerror("Database Error", str(e))
        
def view_tasks():
    try:
        connection = sqlite3.connect("database/study_scheduler.db")
        cursor = connection.cursor()

        cursor.execute("SELECT task_name, deadline, difficulty, study_hours FROM tasks")
        tasks = cursor.fetchall()

        connection.close()

        if not tasks:
            messagebox.showinfo("Saved Tasks", "No tasks found.")
            return

        task_list = ""
        for task in tasks:
            task_list += f"Task: {task[0]}\nDeadline: {task[1]}\nDifficulty: {task[2]}\nStudy Hours: {task[3]}\n\n"

        messagebox.showinfo("Saved Tasks", task_list)

    except Exception as e:
        messagebox.showerror("Database Error", str(e))

def get_priority_level(score):
    if score >= 15:
        return "HIGH"
    elif score >= 8:
        return "MEDIUM"
    else:
        return "LOW"
def calculate_days_left(deadline_text):
    try:
        deadline_date = datetime.strptime(deadline_text, "%Y-%m-%d")
        today = datetime.today()
        days_left = (deadline_date - today).days

        if days_left <= 0:
            return 1
        return days_left

    except:
        return 1
    
def is_valid_date(date_text):
    try:
        datetime.strptime(date_text, "%Y-%m-%d")
        return True
    except ValueError:
        return False    
    
def generate_plan():
    try:
        connection = sqlite3.connect("database/study_scheduler.db")
        cursor = connection.cursor()

        cursor.execute("SELECT task_name, deadline, difficulty, study_hours FROM tasks WHERE status = 'Pending'")
        tasks = cursor.fetchall()

        connection.close()

        if not tasks:
            messagebox.showinfo("Study Plan", "No pending tasks available.")
            return

        priority_list = []

        for task in tasks:
            name = task[0]
            deadline = task[1]
            difficulty = task[2]
            hours = task[3]

            days_left = calculate_days_left(deadline)
            priority_score = (difficulty * hours) / days_left
            priority_level = get_priority_level(priority_score)
            priority_list.append((name, deadline, priority_score, priority_level))

        priority_list.sort(key=lambda x: x[2], reverse=True)

        result = "Recommended Study Order:\n\n"

        for i, task in enumerate(priority_list, start=1):
            result += f"{i}. {task[0]} | Deadline: {task[1]} | {task[3]} (Score: {task[2]:.2f})\n"

        messagebox.showinfo("Study Plan", result)

    except Exception as e:
        messagebox.showerror("Error", str(e))

def show_timetable():
    try:
        connection = sqlite3.connect("database/study_scheduler.db")
        cursor = connection.cursor()

        cursor.execute("SELECT task_name, deadline, difficulty, study_hours FROM tasks WHERE status = 'Pending'")
        tasks = cursor.fetchall()

        connection.close()

        if not tasks:
            messagebox.showinfo("Today's Timetable", "No pending tasks available.")
            return

        timetable_tasks = []

        for task in tasks:
            name = task[0]
            deadline = task[1]
            difficulty = task[2]
            hours = task[3]

            days_left = calculate_days_left(deadline)
            priority_score = (difficulty * hours) / days_left
            timetable_tasks.append((name, hours, priority_score))

        timetable_tasks.sort(key=lambda x: x[2], reverse=True)

        result = "Today's Study Timetable:\n\n"
        start_hour = 9

        for task in timetable_tasks:
            end_hour = start_hour + task[1]
            result += f"{start_hour}:00 - {end_hour}:00  {task[0]}\n"
            start_hour = end_hour

        messagebox.showinfo("Today's Timetable", result)

    except Exception as e:
        messagebox.showerror("Error", str(e))
def open_task_table():
    try:
        connection = sqlite3.connect("database/study_scheduler.db")
        cursor = connection.cursor()

        cursor.execute("SELECT id, task_name, deadline, difficulty, study_hours, status FROM tasks")
        tasks = cursor.fetchall()

        connection.close()

        table_window = tk.Toplevel(root)
        table_window.title("Saved Tasks")
        table_window.geometry("1100x400")

        tree = ttk.Treeview(
            table_window,
            columns=("ID", "Task Name", "Deadline", "Difficulty", "Study Hours", "Score", "Priority", "Status"),
            show="headings"
        )

        tree.heading("ID", text="ID")
        tree.heading("Task Name", text="Task Name")
        tree.heading("Deadline", text="Deadline")
        tree.heading("Difficulty", text="Difficulty")
        tree.heading("Study Hours", text="Study Hours")
        tree.heading("Score", text="Score")
        tree.heading("Priority", text="Priority")
        tree.heading("Status", text="Status")

        tree.column("ID", width=50)
        tree.column("Task Name", width=180)
        tree.column("Deadline", width=150)
        tree.column("Difficulty", width=100)
        tree.column("Study Hours", width=120)
        tree.column("Score", width=100)
        tree.column("Priority", width=120)
        tree.column("Status", width=120)

        for task in tasks:
            days_left = calculate_days_left(task[2])
            score = (task[3] * task[4]) / days_left
            priority_level = get_priority_level(score)
            tree.insert("", tk.END, values=(task[0], task[1], task[2], task[3], task[4], f"{score:.2f}", priority_level, task[5]))
        tree.pack(fill="both", expand=True, padx=10, pady=10)

        button_frame = tk.Frame(table_window)
        button_frame.pack(pady=10)

        def refresh_table():
            for item in tree.get_children():
                tree.delete(item)

            connection = sqlite3.connect("database/study_scheduler.db")
            cursor = connection.cursor()
            cursor.execute("SELECT id, task_name, deadline, difficulty, study_hours, status FROM tasks")
            updated_tasks = cursor.fetchall()
            connection.close()

            for task in updated_tasks:
                days_left = calculate_days_left(task[2])
                score = (task[3] * task[4]) / days_left
                priority_level = get_priority_level(score)
                tree.insert("", tk.END, values=(task[0], task[1], task[2], task[3], task[4], f"{score:.2f}", priority_level, task[5]))

        def delete_selected_task():
            selected_item = tree.selection()
            if not selected_item:
                messagebox.showwarning("No Selection", "Please select a task first.")
                return

            task_values = tree.item(selected_item[0], "values")
            task_id = task_values[0]
            task_name = task_values[1]

            connection = sqlite3.connect("database/study_scheduler.db")
            cursor = connection.cursor()
            cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
            connection.commit()
            connection.close()

            messagebox.showinfo("Delete Task", f"Task '{task_name}' deleted successfully.")
            refresh_table()

        def edit_selected_task():
            selected_item = tree.selection()
            if not selected_item:
                messagebox.showwarning("No Selection", "Please select a task first.")
                return

            task_values = tree.item(selected_item[0], "values")
            task_id = task_values[0]
            old_name = task_values[1]

            new_name = simpledialog.askstring("Edit Task", "Enter new task name:", initialvalue=old_name)
            if not new_name:
                return

            connection = sqlite3.connect("database/study_scheduler.db")
            cursor = connection.cursor()
            cursor.execute("UPDATE tasks SET task_name = ? WHERE id = ?", (new_name, task_id))
            connection.commit()
            connection.close()

            messagebox.showinfo("Edit Task", "Task updated successfully.")
            refresh_table()

        def complete_selected_task():
            selected_item = tree.selection()
            if not selected_item:
                messagebox.showwarning("No Selection", "Please select a task first.")
                return

            task_values = tree.item(selected_item[0], "values")
            task_id = task_values[0]
            task_name = task_values[1]

            connection = sqlite3.connect("database/study_scheduler.db")
            cursor = connection.cursor()
            cursor.execute("UPDATE tasks SET status = 'Completed' WHERE id = ?", (task_id,))
            connection.commit()
            connection.close()

            messagebox.showinfo("Task Status", f"Task '{task_name}' marked as Completed.")
            refresh_table()

        edit_selected_button = tk.Button(button_frame, text="Edit Selected Task", command=edit_selected_task)
        edit_selected_button.grid(row=0, column=0, padx=10)

        delete_selected_button = tk.Button(button_frame, text="Delete Selected Task", command=delete_selected_task)
        delete_selected_button.grid(row=0, column=1, padx=10)

        complete_selected_button = tk.Button(button_frame, text="Mark Selected Task Completed", command=complete_selected_task)
        complete_selected_button.grid(row=0, column=2, padx=10)

    except Exception as e:
        messagebox.showerror("Error", str(e))
        def complete_selected_task():
            selected_item = tree.selection()
            if not selected_item:
                messagebox.showwarning("No Selection", "Please select a task first.")
                return

            task_values = tree.item(selected_item[0], "values")
            task_id = task_values[0]
            task_name = task_values[1]

            connection = sqlite3.connect("database/study_scheduler.db")
            cursor = connection.cursor()
            cursor.execute("UPDATE tasks SET status = 'Completed' WHERE id = ?", (task_id,))
            connection.commit()
            connection.close()

            messagebox.showinfo("Task Status", f"Task '{task_name}' marked as Completed.")
            refresh_table()

def mark_task_completed():
    try:
        connection = sqlite3.connect("database/study_scheduler.db")
        cursor = connection.cursor()

        cursor.execute("""
        SELECT id, task_name FROM tasks
        WHERE status = 'Pending'
        ORDER BY id ASC
        LIMIT 1
        """)
        task = cursor.fetchone()

        if task is None:
            connection.close()
            messagebox.showinfo("Task Status", "No pending tasks found.")
            return

        task_id = task[0]
        task_name = task[1]

        cursor.execute("""
        UPDATE tasks
        SET status = 'Completed'
        WHERE id = ?
        """, (task_id,))

        connection.commit()
        connection.close()

        messagebox.showinfo("Task Status", f"Task '{task_name}' marked as Completed.")
        update_progress_label()

    except Exception as e:
        messagebox.showerror("Error", str(e))

def delete_first_task():
    try:
        connection = sqlite3.connect("database/study_scheduler.db")
        cursor = connection.cursor()

        cursor.execute("""
        SELECT id, task_name FROM tasks
        ORDER BY id ASC
        LIMIT 1
        """)
        task = cursor.fetchone()

        if task is None:
            connection.close()
            messagebox.showinfo("Delete Task", "No tasks found.")
            return

        task_id = task[0]
        task_name = task[1]

        cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        connection.commit()
        connection.close()

        messagebox.showinfo("Delete Task", f"Task '{task_name}' deleted successfully.")
        update_progress_label()

    except Exception as e:
        messagebox.showerror("Error", str(e))
def show_progress():
    try:
        connection = sqlite3.connect("database/study_scheduler.db")
        cursor = connection.cursor()

        cursor.execute("SELECT COUNT(*) FROM tasks")
        total_tasks = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM tasks WHERE status = 'Completed'")
        completed_tasks = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM tasks WHERE status = 'Pending'")
        pending_tasks = cursor.fetchone()[0]

        connection.close()

        if total_tasks == 0:
            completion_rate = 0
        else:
            completion_rate = (completed_tasks / total_tasks) * 100

        result = (
            f"Total Tasks: {total_tasks}\n"
            f"Completed Tasks: {completed_tasks}\n"
            f"Pending Tasks: {pending_tasks}\n"
            f"Completion Rate: {completion_rate:.1f}%"
        )

        messagebox.showinfo("Progress Summary", result)

    except Exception as e:
        messagebox.showerror("Error", str(e))

# Create main window
def update_progress_label():
    try:
        connection = sqlite3.connect("database/study_scheduler.db")
        cursor = connection.cursor()

        cursor.execute("SELECT COUNT(*) FROM tasks")
        total_tasks = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM tasks WHERE status = 'Completed'")
        completed_tasks = cursor.fetchone()[0]

        connection.close()

        if total_tasks == 0:
            completion_rate = 0
        else:
            completion_rate = (completed_tasks / total_tasks) * 100

        progress_text.set(f"Progress: {completion_rate:.1f}% completed")
        progress_bar["value"] = completion_rate

    except Exception as e:
        progress_text.set("Progress: Error")
        progress_bar["value"] = 0

root = tk.Tk()
progress_text = tk.StringVar()
progress_text.set("Progress: 0.0% completed")
root.title("Priority-Based Study Scheduler")
root.geometry("700x700")

title = tk.Label(root, text="Priority-Based Study Scheduler", font=("Arial", 20))
title.pack(pady=20)

progress_label = tk.Label(root, textvariable=progress_text, font=("Arial", 12))
progress_label.pack(pady=10)

progress_bar = ttk.Progressbar(root, orient="horizontal", length=300, mode="determinate")
progress_bar.pack(pady=5)

task_frame = tk.Frame(root)
task_frame.pack(pady=20)

# Task name
task_label = tk.Label(task_frame, text="Task Name:")
task_label.grid(row=0, column=0, padx=10, pady=5)

task_entry = tk.Entry(task_frame)
task_entry.grid(row=0, column=1)

# Deadline
deadline_label = tk.Label(task_frame, text="Deadline:")
deadline_label.grid(row=1, column=0, padx=10, pady=5)

deadline_entry = tk.Entry(task_frame)
deadline_entry.grid(row=1, column=1)

# Difficulty
difficulty_label = tk.Label(task_frame, text="Difficulty (1-5):")
difficulty_label.grid(row=2, column=0, padx=10, pady=5)

difficulty_entry = tk.Entry(task_frame)
difficulty_entry.grid(row=2, column=1)

# Study hours
hours_label = tk.Label(task_frame, text="Study Hours:")
hours_label.grid(row=3, column=0, padx=10, pady=5)

hours_entry = tk.Entry(task_frame)
hours_entry.grid(row=3, column=1)

# Button
add_button = tk.Button(root, text="Add Task", command=add_task)
add_button.pack(pady=20)

view_button = tk.Button(root, text="View Tasks", command=view_tasks)
view_button.pack(pady=10)

plan_button = tk.Button(root, text="Generate Study Plan", command=generate_plan)
plan_button.pack(pady=10)

timetable_button = tk.Button(root, text="Show Timetable", command=show_timetable)
timetable_button.pack(pady=10)

table_button = tk.Button(root, text="Open Task Table", command=open_task_table)
table_button.pack(pady=10)

progress_button = tk.Button(root, text="Show Progress", command=show_progress)
progress_button.pack(pady=10)

update_progress_label()
root.mainloop()