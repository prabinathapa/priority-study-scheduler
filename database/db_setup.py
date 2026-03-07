import sqlite3

# Connect to the database
connection = sqlite3.connect("database/study_scheduler.db")
cursor = connection.cursor()

# Create users table
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL
)
""")

# Create tasks table
cursor.execute("""
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    task_name TEXT NOT NULL,
    deadline TEXT NOT NULL,
    difficulty INTEGER NOT NULL,
    study_hours INTEGER NOT NULL,
    status TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id)
)
""")

print("Database and tables created successfully.")

connection.commit()
connection.close()