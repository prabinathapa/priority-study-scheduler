import sqlite3

# Connect to the database
connection = sqlite3.connect("database/study_scheduler.db")
cursor = connection.cursor()

# Create tasks table
cursor.execute("""
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_name TEXT NOT NULL,
    deadline TEXT NOT NULL,
    difficulty INTEGER NOT NULL,
    study_hours INTEGER NOT NULL,
    status TEXT NOT NULL
)
""")

print("Database and table created successfully.")

connection.commit()
connection.close()