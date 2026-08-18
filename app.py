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



















# ---------------- TRAINING ----------------

def training():
    clear_page()

    page_title(
        "Training Log",
        "Record a training session"
    )

    frame = ctk.CTkScrollableFrame(content)
    frame.pack(fill="both", expand=True, padx=40, pady=10)

    ctk.CTkLabel(
        frame,
        text="Session type"
    ).pack(anchor="w", pady=(10, 3))

    session_type = ctk.CTkComboBox(
        frame,
        values=["Water", "Erg", "Gym", "Running", "Cross Training"],
        width=350
    )
    session_type.pack(anchor="w", pady=(0, 15))
    session_type.set("Water")

    ctk.CTkLabel(
        frame,
        text="Distance (km)"
    ).pack(anchor="w", pady=(5, 3))

    distance = ctk.CTkEntry(
        frame,
        width=350,
        placeholder_text="Example: 10"
    )
    distance.pack(anchor="w", pady=(0, 15))

    ctk.CTkLabel(
        frame,
        text="Time"
    ).pack(anchor="w", pady=(5, 3))

    time_entry = ctk.CTkEntry(
        frame,
        width=350,
        placeholder_text="Example: 40:30"
    )
    time_entry.pack(anchor="w", pady=(0, 15))

    ctk.CTkLabel(
        frame,
        text="Average split"
    ).pack(anchor="w", pady=(5, 3))

    split = ctk.CTkEntry(
        frame,
        width=350,
        placeholder_text="Example: 2:05"
    )
    split.pack(anchor="w", pady=(0, 15))

    ctk.CTkLabel(
        frame,
        text="Stroke rate"
    ).pack(anchor="w", pady=(5, 3))

    stroke_rate = ctk.CTkEntry(
        frame,
        width=350,
        placeholder_text="Example: 24"
    )
    stroke_rate.pack(anchor="w", pady=(0, 15))

    ctk.CTkLabel(
        frame,
        text="Heart rate"
    ).pack(anchor="w", pady=(5, 3))

    heart_rate = ctk.CTkEntry(
        frame,
        width=350,
        placeholder_text="Example: 150"
    )
    heart_rate.pack(anchor="w", pady=(0, 15))

    ctk.CTkLabel(
        frame,
        text="Boat class"
    ).pack(anchor="w", pady=(5, 3))

    boat_class = ctk.CTkEntry(
        frame,
        width=350,
        placeholder_text="Example: U17 1x"
    )
    boat_class.pack(anchor="w", pady=(0, 15))

    ctk.CTkLabel(
        frame,
        text="Notes"
    ).pack(anchor="w", pady=(5, 3))

    notes = ctk.CTkTextbox(
        frame,
        width=500,
        height=120
    )
    notes.pack(anchor="w", pady=(0, 20))

    # Tide information is mainly for water sessions
    ctk.CTkLabel(
        frame,
        text="Tide / current"
    ).pack(anchor="w", pady=(5, 3))

    tide = ctk.CTkEntry(
        frame,
        width=350,
        placeholder_text="Example: +0.4 m/s"
    )
    tide.pack(anchor="w", pady=(0, 20))

    def save_training():
        try:
            km = float(distance.get())
        except ValueError:
            message("Enter a number for distance.")
            return

        notes_text = notes.get("1.0", "end").strip()

        cursor.execute("""
        INSERT INTO training
        (date, session_type, distance, time, split,
         stroke_rate, heart_rate, boat_class, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.now().strftime("%Y-%m-%d"),
            session_type.get(),
            km,
            time_entry.get(),
            split.get(),
            stroke_rate.get() or 0,
            heart_rate.get() or 0,
            boat_class.get(),
            notes_text
        ))

        db.commit()

        message("Training saved!")
        home()

    ctk.CTkButton(
        frame,
        text="Save Training",
        width=250,
        height=45,
        command=save_training
    ).pack(anchor="w", pady=10)
















# ---------------- QUESTIONNAIRE ----------------

def questionnaire():
    clear_page()

    page_title(
        "Daily Questionnaire",
        "A quick check of how you are feeling"
    )

    frame = ctk.CTkScrollableFrame(content)
    frame.pack(fill="both", expand=True, padx=40, pady=10)

    ctk.CTkLabel(
        frame,
        text="How hard was today's session? (RPE)"
    ).pack(pady=(20, 5))

    rpe = ctk.CTkSlider(
        frame,
        from_=1,
        to=10,
        number_of_steps=9,
        width=500
    )
    rpe.pack(pady=10)
    rpe.set(5)

    rpe_number = ctk.CTkLabel(
        frame,
        text="5"
    )
    rpe_number.pack()

    def update_rpe(value):
        rpe_number.configure(text=str(round(value)))

    rpe.configure(command=update_rpe)

    ctk.CTkLabel(
        frame,
        text="How did you feel before training?"
    ).pack(pady=(30, 5))

    before = ctk.CTkComboBox(
        frame,
        values=["Very good", "Good", "Average", "Tired", "Very tired"],
        width=350
    )
    before.pack()
    before.set("Average")

    ctk.CTkLabel(
        frame,
        text="How do you feel after training?"
    ).pack(pady=(25, 5))

    after = ctk.CTkComboBox(
        frame,
        values=["Very good", "Good", "Average", "Tired", "Very tired"],
        width=350
    )
    after.pack()
    after.set("Average")

    ctk.CTkLabel(
        frame,
        text="Any pain or injuries?"
    ).pack(pady=(25, 5))

    pain = ctk.CTkComboBox(
        frame,
        values=["No", "Minor", "Moderate", "Severe"],
        width=350
    )
    pain.pack()
    pain.set("No")

    ctk.CTkLabel(
        frame,
        text="Comments"
    ).pack(pady=(25, 5))

    comments = ctk.CTkTextbox(
        frame,
        width=500,
        height=120
    )
    comments.pack()

    def save_questionnaire():
        cursor.execute("""
        INSERT INTO questionnaire
        (date, rpe, before_feeling, after_feeling, pain, comments)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (
            datetime.now().strftime("%Y-%m-%d"),
            round(rpe.get()),
            before.get(),
            after.get(),
            pain.get(),
            comments.get("1.0", "end").strip()
        ))

        db.commit()
        message("Questionnaire saved!")

    ctk.CTkButton(
        frame,
        text="Save Questionnaire",
        width=250,
        height=45,
        command=save_questionnaire
    ).pack(pady=30)











# ---------------- PROGRESS ----------------

def progress():
    clear_page()

    page_title(
        "Progress",
        "Your training statistics"
    )

    cursor.execute("""
    SELECT COUNT(*), COALESCE(SUM(distance), 0)
    FROM training
    """)

    data = cursor.fetchone()

    sessions = data[0]
    kilometres = data[1]

    cursor.execute("""
    SELECT AVG(stroke_rate)
    FROM training
    WHERE stroke_rate > 0
    """)

    average_rate = cursor.fetchone()[0]

    if average_rate:
        average_rate = round(average_rate)
    else:
        average_rate = "--"

    stats = ctk.CTkFrame(content, fg_color="transparent")
    stats.pack(fill="x", padx=30)

    values = [
        ("Sessions", sessions),
        ("Total km", f"{kilometres:.1f}"),
        ("Average SR", average_rate),
        ("2k PB", get_pb())
    ]

    for title, value in values:
        box = ctk.CTkFrame(stats)
        box.pack(side="left", fill="both", expand=True, padx=8)

        ctk.CTkLabel(
            box,
            text=title
        ).pack(pady=(20, 5))

        ctk.CTkLabel(
            box,
            text=str(value),
            font=ctk.CTkFont(size=25, weight="bold")
        ).pack(pady=(0, 20))

    # Simple training history
    history = ctk.CTkFrame(content)
    history.pack(fill="both", expand=True, padx=40, pady=30)

    ctk.CTkLabel(
        history,
        text="Training History",
        font=ctk.CTkFont(size=21, weight="bold")
    ).pack(anchor="w", padx=20, pady=20)

    cursor.execute("""
    SELECT date, distance, split
    FROM training
    ORDER BY id DESC
    LIMIT 10
    """)

    rows = cursor.fetchall()

    if not rows:
        ctk.CTkLabel(
            history,
            text="Log some training to see your progress."
        ).pack()

    for row in rows:
        ctk.CTkLabel(
            history,
            text=f"{row[0]}     {row[1]} km     {row[2]}"
        ).pack(anchor="w", padx=20, pady=4)
























# ---------------- GOALS ----------------

def goals():
    clear_page()

    page_title(
        "Goals",
        "Set goals and track your progress"
    )

    frame = ctk.CTkScrollableFrame(content)
    frame.pack(fill="both", expand=True, padx=40, pady=10)

    ctk.CTkLabel(
        frame,
        text="Goal type"
    ).pack(pady=(15, 5))

    goal_type = ctk.CTkComboBox(
        frame,
        values=[
            "2k Erg",
            "5k Erg",
            "Weekly Distance",
            "Season Distance",
            "On-Water Split",
            "Other"
        ],
        width=350
    )
    goal_type.pack()
    goal_type.set("2k Erg")

    ctk.CTkLabel(
        frame,
        text="Target"
    ).pack(pady=(20, 5))

    target = ctk.CTkEntry(
        frame,
        width=350,
        placeholder_text="Example: 6:30"
    )
    target.pack()

    ctk.CTkLabel(
        frame,
        text="Progress"
    ).pack(pady=(20, 5))

    goal_progress = ctk.CTkSlider(
        frame,
        from_=0,
        to=100,
        width=500
    )
    goal_progress.pack()
    goal_progress.set(0)

    progress_label = ctk.CTkLabel(
        frame,
        text="0%"
    )
    progress_label.pack()

    def change_progress(value):
        progress_label.configure(
            text=f"{round(value)}%"
        )

    goal_progress.configure(command=change_progress)

    def save_goal():
        if not target.get():
            message("Enter a target first.")
            return

        cursor.execute("""
        INSERT INTO goals
        (goal_type, target, progress)
        VALUES (?, ?, ?)
        """, (
            goal_type.get(),
            target.get(),
            goal_progress.get()
        ))

        db.commit()

        message("Goal saved!")
        goals()

    ctk.CTkButton(
        frame,
        text="Save Goal",
        width=250,
        height=45,
        command=save_goal
    ).pack(pady=25)

    ctk.CTkLabel(
        frame,
        text="My Goals",
        font=ctk.CTkFont(size=21, weight="bold")
    ).pack(pady=20)

    cursor.execute("""
    SELECT goal_type, target, progress
    FROM goals
    ORDER BY id DESC
    """)

    goal_rows = cursor.fetchall()

    if not goal_rows:
        ctk.CTkLabel(
            frame,
            text="No goals yet."
        ).pack()

    for row in goal_rows:
        box = ctk.CTkFrame(frame)
        box.pack(fill="x", pady=8)

        ctk.CTkLabel(
            box,
            text=f"{row[0]}   |   Target: {row[1]}"
        ).pack(anchor="w", padx=15, pady=(10, 3))

        bar = ctk.CTkProgressBar(box)
        bar.pack(fill="x", padx=15, pady=5)
        bar.set(row[2] / 100)

        ctk.CTkLabel(
            box,
            text=f"{round(row[2])}%"
        ).pack(anchor="w", padx=15, pady=(0, 10))
