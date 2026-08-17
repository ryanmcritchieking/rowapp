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












# ---------------- MAIN WINDOW ----------------

sidebar = ctk.CTkFrame(app, width=220, corner_radius=0)
sidebar.pack(side="left", fill="y")
sidebar.pack_propagate(False)

content = ctk.CTkFrame(app, corner_radius=0)
content.pack(side="right", fill="both", expand=True)


# Clears the old screen before opening another one
def clear_page():
    for thing in content.winfo_children():
        thing.destroy()


# Makes the title on each page
def page_title(title, subtitle=""):
    ctk.CTkLabel(
        content,
        text=title,
        font=ctk.CTkFont(size=30, weight="bold")
    ).pack(anchor="w", padx=40, pady=(30, 5))

    if subtitle:
        ctk.CTkLabel(
            content,
            text=subtitle,
            font=ctk.CTkFont(size=15)
        ).pack(anchor="w", padx=40, pady=(0, 20))


# Small popup for messages
def message(text):
    popup = ctk.CTkToplevel(app)
    popup.title("Rowing Performance")
    popup.geometry("350x180")
    popup.grab_set()

    ctk.CTkLabel(
        popup,
        text=text,
        font=ctk.CTkFont(size=18, weight="bold")
    ).pack(pady=40)

    ctk.CTkButton(
        popup,
        text="OK",
        command=popup.destroy
    ).pack()




















# ---------------- HOME ----------------

def home():
    clear_page()

    page_title(
        "Rowing Performance",
        "Your training overview"
    )

    # Get some numbers from the database
    cursor.execute("SELECT COUNT(*), COALESCE(SUM(distance), 0) FROM training")
    result = cursor.fetchone()

    sessions = result[0]
    total_distance = result[1]

    # These are the three main dashboard boxes
    cards = ctk.CTkFrame(content, fg_color="transparent")
    cards.pack(fill="x", padx=30)

    card1 = ctk.CTkFrame(cards)
    card1.pack(side="left", fill="both", expand=True, padx=8)

    ctk.CTkLabel(
        card1,
        text="TOTAL DISTANCE",
        font=ctk.CTkFont(size=13)
    ).pack(pady=(25, 5))

    ctk.CTkLabel(
        card1,
        text=f"{total_distance:.1f} km",
        font=ctk.CTkFont(size=28, weight="bold")
    ).pack(pady=(0, 25))

    card2 = ctk.CTkFrame(cards)
    card2.pack(side="left", fill="both", expand=True, padx=8)

    ctk.CTkLabel(
        card2,
        text="SESSIONS",
        font=ctk.CTkFont(size=13)
    ).pack(pady=(25, 5))

    ctk.CTkLabel(
        card2,
        text=str(sessions),
        font=ctk.CTkFont(size=28, weight="bold")
    ).pack(pady=(0, 25))

    cursor.execute("SELECT pb_2000 FROM profile WHERE id = 1")
    pb = cursor.fetchone()[0]

    if not pb:
        pb = "--"

    card3 = ctk.CTkFrame(cards)
    card3.pack(side="left", fill="both", expand=True, padx=8)

    ctk.CTkLabel(
        card3,
        text="2K ERG PB",
        font=ctk.CTkFont(size=13)
    ).pack(pady=(25, 5))

    ctk.CTkLabel(
        card3,
        text=pb,
        font=ctk.CTkFont(size=28, weight="bold")
    ).pack(pady=(0, 25))

    # Recent sessions
    recent = ctk.CTkFrame(content)
    recent.pack(fill="both", expand=True, padx=40, pady=30)

    ctk.CTkLabel(
        recent,
        text="Recent Training",
        font=ctk.CTkFont(size=21, weight="bold")
    ).pack(anchor="w", padx=25, pady=(20, 10))

    cursor.execute("""
    SELECT date, session_type, distance, split
    FROM training
    ORDER BY id DESC
    LIMIT 6
    """)

    sessions_data = cursor.fetchall()

    if not sessions_data:
        ctk.CTkLabel(
            recent,
            text="No training sessions recorded yet."
        ).pack(anchor="w", padx=25, pady=10)

    else:
        for row in sessions_data:
            text = f"{row[0]}   |   {row[1]}   |   {row[2]} km   |   {row[3]}"
            ctk.CTkLabel(
                recent,
                text=text,
                font=ctk.CTkFont(size=14)
            ).pack(anchor="w", padx=25, pady=5)
