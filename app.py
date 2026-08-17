import customtkinter as ctk
import sqlite3
from datetime import datetime

# Dark mode for now
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

app = ctk.CTk()
app.title("Rowing Performance")
app.geometry("1200x750")
app.minsize(1000, 650)










# ---------------- DATABASE ----------------

# I am using SQLite so the training doesn't disappear
# when I close the app
db = sqlite3.connect("rowing.db")
cursor = db.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS training (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT,
    session_type TEXT,
    distance REAL,
    time TEXT,
    split TEXT,
    stroke_rate INTEGER,
    heart_rate INTEGER,
    boat_class TEXT,
    notes TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS questionnaire (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT,
    rpe INTEGER,
    before_feeling TEXT,
    after_feeling TEXT,
    pain TEXT,
    comments TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS goals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    goal_type TEXT,
    target TEXT,
    progress REAL
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS profile (
    id INTEGER PRIMARY KEY,
    name TEXT,
    age TEXT,
    club TEXT,
    boat_class TEXT,
    weight TEXT,
    pb_500 TEXT,
    pb_1000 TEXT,
    pb_2000 TEXT,
    pb_5000 TEXT,
    pb_6000 TEXT
)
""")

# Make one profile row if there isn't one yet
cursor.execute("SELECT * FROM profile WHERE id = 1")

if cursor.fetchone() is None:
    cursor.execute("""
    INSERT INTO profile
    (id, name, age, club, boat_class, weight,
     pb_500, pb_1000, pb_2000, pb_5000, pb_6000)
    VALUES (1, '', '', '', '', '', '', '', '', '', '')
    """)

db.commit()
