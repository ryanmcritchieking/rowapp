import customtkinter as ctk
import sqlite3
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


# Dark mode for now
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

app = ctk.CTk()
app.title("Rowing Performance")
app.geometry("1200x750")
app.minsize(1000, 650)


# ---------------- DATABASE ----------------

db = sqlite3.connect("rowing.db")
cursor = db.cursor()

# I added current and adjusted split to the training table
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
    notes TEXT,
    current REAL,
    current_direction TEXT,
    adjusted_split TEXT
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

# Make a profile if there isn't one
cursor.execute("SELECT * FROM profile WHERE id = 1")

if cursor.fetchone() is None:
    cursor.execute("""
    INSERT INTO profile
    (id, name, age, club, boat_class, weight,
     pb_500, pb_1000, pb_2000, pb_5000, pb_6000)
    VALUES (1, '', '', '', '', '', '', '', '', '', '')
    """)

db.commit()



# I added these later, so I need to add them to old databases too
try:
    cursor.execute("ALTER TABLE training ADD COLUMN current REAL")
except sqlite3.OperationalError:
    pass

try:
    cursor.execute("ALTER TABLE training ADD COLUMN current_direction TEXT")
except sqlite3.OperationalError:
    pass

try:
    cursor.execute("ALTER TABLE training ADD COLUMN adjusted_split TEXT")
except sqlite3.OperationalError:
    pass

db.commit()

# ---------------- MAIN WINDOW ----------------

sidebar = ctk.CTkFrame(app, width=220, corner_radius=0)
sidebar.pack(side="left", fill="y")
sidebar.pack_propagate(False)

content = ctk.CTkFrame(app, corner_radius=0)
content.pack(side="right", fill="both", expand=True)


# Clears the page before opening another one
def clear_page():
    for thing in content.winfo_children():
        thing.destroy()


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


# Simple popup message
def message(text):
    popup = ctk.CTkToplevel(app)
    popup.title("Rowing Performance")
    popup.geometry("400x200")
    popup.grab_set()

    ctk.CTkLabel(
        popup,
        text=text,
        font=ctk.CTkFont(size=17, weight="bold")
    ).pack(pady=45)

    ctk.CTkButton(
        popup,
        text="OK",
        command=popup.destroy
    ).pack()


# ---------------- TIDE CALCULATION ----------------

def calculate_adjusted_split(split_text, current, direction):
    """
    This is only an estimate for now.

    A positive current means the river is helping.
    A negative current means the river is slowing the boat.

    Later I can test this against real Waihopai River data.
    """

    try:
        # Turn 2:10 into seconds
        parts = split_text.split(":")

        if len(parts) != 2:
            return "--"

        minutes = float(parts[0])
        seconds = float(parts[1])

        split_seconds = minutes * 60 + seconds

        # This is a simple estimate.
        # I chose 5% per 1 m/s as a starting point.
        adjustment = current * 0.05

        if direction == "Helping":
            adjusted_seconds = split_seconds * (1 + adjustment)

        else:
            adjusted_seconds = split_seconds * (1 - adjustment)

        adjusted_minutes = int(adjusted_seconds // 60)
        adjusted_remaining = adjusted_seconds % 60

        return f"{adjusted_minutes}:{adjusted_remaining:04.1f}"

    except:
        return "--"


# ---------------- HOME ----------------

def home():
    clear_page()

    page_title(
        "Rowing Performance",
        "Your training overview"
    )

    cursor.execute(
        "SELECT COUNT(*), COALESCE(SUM(distance), 0) FROM training"
    )

    result = cursor.fetchone()

    sessions = result[0]
    total_distance = result[1]

    cards = ctk.CTkFrame(content, fg_color="transparent")
    cards.pack(fill="x", padx=30)

    card1 = ctk.CTkFrame(cards)
    card1.pack(side="left", fill="both", expand=True, padx=8)

    ctk.CTkLabel(
        card1,
        text="TOTAL DISTANCE"
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
        text="SESSIONS"
    ).pack(pady=(25, 5))

    ctk.CTkLabel(
        card2,
        text=str(sessions),
        font=ctk.CTkFont(size=28, weight="bold")
    ).pack(pady=(0, 25))

    card3 = ctk.CTkFrame(cards)
    card3.pack(side="left", fill="both", expand=True, padx=8)

    ctk.CTkLabel(
        card3,
        text="2K ERG PB"
    ).pack(pady=(25, 5))

    ctk.CTkLabel(
        card3,
        text=get_pb(),
        font=ctk.CTkFont(size=28, weight="bold")
    ).pack(pady=(0, 25))

    recent = ctk.CTkFrame(content)
    recent.pack(fill="both", expand=True, padx=40, pady=30)

    ctk.CTkLabel(
        recent,
        text="Recent Training",
        font=ctk.CTkFont(size=21, weight="bold")
    ).pack(anchor="w", padx=25, pady=(20, 10))

    cursor.execute("""
    SELECT date, session_type, distance, split, adjusted_split
    FROM training
    ORDER BY id DESC
    LIMIT 8
    """)

    rows = cursor.fetchall()

    if not rows:
        ctk.CTkLabel(
            recent,
            text="No training sessions recorded yet."
        ).pack(anchor="w", padx=25)

    for row in rows:

        text = (
            f"{row[0]}   |   {row[1]}   |   "
            f"{row[2]} km   |   {row[3]}"
        )

        if row[4] and row[4] != "--":
            text += f"   |   Adjusted: {row[4]}"

        ctk.CTkLabel(
            recent,
            text=text
        ).pack(anchor="w", padx=25, pady=4)


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
        values=[
            "Water",
            "Erg",
            "Gym",
            "Running",
            "Cross Training"
        ],
        width=350
    )
    session_type.pack(anchor="w")
    session_type.set("Water")

    ctk.CTkLabel(
        frame,
        text="Distance (km)"
    ).pack(anchor="w", pady=(15, 3))

    distance = ctk.CTkEntry(
        frame,
        width=350,
        placeholder_text="Example: 10"
    )
    distance.pack(anchor="w")

    ctk.CTkLabel(
        frame,
        text="Time"
    ).pack(anchor="w", pady=(15, 3))

    time_entry = ctk.CTkEntry(
        frame,
        width=350,
        placeholder_text="Example: 40:30"
    )
    time_entry.pack(anchor="w")

    ctk.CTkLabel(
        frame,
        text="Average split"
    ).pack(anchor="w", pady=(15, 3))

    split = ctk.CTkEntry(
        frame,
        width=350,
        placeholder_text="Example: 2:05"
    )
    split.pack(anchor="w")

    # ---------------- TIDE ----------------

    ctk.CTkLabel(
        frame,
        text="River Current",
        font=ctk.CTkFont(size=21, weight="bold")
    ).pack(anchor="w", pady=(30, 10))

    ctk.CTkLabel(
        frame,
        text="Current speed (m/s)"
    ).pack(anchor="w", pady=(5, 3))

    current = ctk.CTkEntry(
        frame,
        width=350,
        placeholder_text="Example: 0.4"
    )
    current.pack(anchor="w")

    ctk.CTkLabel(
        frame,
        text="Was the current helping or against you?"
    ).pack(anchor="w", pady=(15, 3))

    direction = ctk.CTkComboBox(
        frame,
        values=[
            "Helping",
            "Against",
            "No current"
        ],
        width=350
    )
    direction.pack(anchor="w")
    direction.set("No current")

    adjusted_label = ctk.CTkLabel(
        frame,
        text="Adjusted split: --",
        font=ctk.CTkFont(size=17, weight="bold")
    )
    adjusted_label.pack(anchor="w", pady=20)

    # Calculate it before saving
    def show_adjusted():

        try:
            current_value = float(current.get())
        except ValueError:
            current_value = 0

        adjusted = calculate_adjusted_split(
            split.get(),
            current_value,
            direction.get()
        )

        adjusted_label.configure(
            text=f"Adjusted split: {adjusted}"
        )

    ctk.CTkButton(
        frame,
        text="Calculate Adjusted Split",
        command=show_adjusted
    ).pack(anchor="w", pady=5)

    # ---------------- OTHER DATA ----------------

    ctk.CTkLabel(
        frame,
        text="Stroke rate"
    ).pack(anchor="w", pady=(20, 3))

    stroke_rate = ctk.CTkEntry(
        frame,
        width=350,
        placeholder_text="Example: 24"
    )
    stroke_rate.pack(anchor="w")

    ctk.CTkLabel(
        frame,
        text="Heart rate"
    ).pack(anchor="w", pady=(15, 3))

    heart_rate = ctk.CTkEntry(
        frame,
        width=350,
        placeholder_text="Example: 150"
    )
    heart_rate.pack(anchor="w")

    ctk.CTkLabel(
        frame,
        text="Boat class"
    ).pack(anchor="w", pady=(15, 3))

    boat_class = ctk.CTkEntry(
        frame,
        width=350,
        placeholder_text="Example: U17 1x"
    )
    boat_class.pack(anchor="w")

    ctk.CTkLabel(
        frame,
        text="Notes"
    ).pack(anchor="w", pady=(15, 3))

    notes = ctk.CTkTextbox(
        frame,
        width=500,
        height=120
    )
    notes.pack(anchor="w")

    def save_training():

        try:
            km = float(distance.get())
        except ValueError:
            message("Enter a number for distance.")
            return

        try:
            current_value = float(current.get()) if current.get() else 0
        except ValueError:
            message("Current needs to be a number.")
            return

        adjusted = calculate_adjusted_split(
            split.get(),
            current_value,
            direction.get()
        )

        cursor.execute("""
        INSERT INTO training
        (date, session_type, distance, time, split,
         stroke_rate, heart_rate, boat_class, notes,
         current, current_direction, adjusted_split)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.now().strftime("%Y-%m-%d"),
            session_type.get(),
            km,
            time_entry.get(),
            split.get(),
            stroke_rate.get() or 0,
            heart_rate.get() or 0,
            boat_class.get(),
            notes.get("1.0", "end").strip(),
            current_value,
            direction.get(),
            adjusted
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
    ).pack(anchor="w", pady=30)


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
        values=[
            "Very good",
            "Good",
            "Average",
            "Tired",
            "Very tired"
        ],
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
        values=[
            "Very good",
            "Good",
            "Average",
            "Tired",
            "Very tired"
        ],
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
        values=[
            "No",
            "Minor",
            "Moderate",
            "Severe"
        ],
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
        "See how your training is changing over time"
    )

    # Get the basic numbers first
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

    # The top boxes show the main stats
    stats = ctk.CTkFrame(content, fg_color="transparent")
    stats.pack(fill="x", padx=30, pady=(0, 10))

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
        ).pack(pady=(15, 5))

        ctk.CTkLabel(
            box,
            text=str(value),
            font=ctk.CTkFont(size=25, weight="bold")
        ).pack(pady=(0, 15))

    # Get the training data for the graphs
    cursor.execute("""
    SELECT date, distance, split, adjusted_split
    FROM training
    WHERE distance > 0
    ORDER BY id ASC
    """)

    rows = cursor.fetchall()

    graph_frame = ctk.CTkScrollableFrame(content)
    graph_frame.pack(fill="both", expand=True, padx=40, pady=10)

    if not rows:

        ctk.CTkLabel(
            graph_frame,
            text="Log some training first and your graphs will appear here.",
            font=ctk.CTkFont(size=18)
        ).pack(pady=50)

        return

    dates = []
    distances = []
    splits = []
    adjusted_splits = []

    for row in rows:

        dates.append(row[0])
        distances.append(row[1])

        # Turn split like 2:05 into seconds
        try:
            parts = row[2].split(":")
            split_seconds = (
                float(parts[0]) * 60 +
                float(parts[1])
            )
            splits.append(split_seconds)
        except:
            splits.append(None)

        # Do the same for adjusted split
        try:
            if row[3] and row[3] != "--":
                parts = row[3].split(":")
                adjusted_seconds = (
                    float(parts[0]) * 60 +
                    float(parts[1])
                )
                adjusted_splits.append(adjusted_seconds)
            else:
                adjusted_splits.append(None)
        except:
            adjusted_splits.append(None)

















    # ---------------- SPLIT GRAPH ----------------

    split_title = ctk.CTkLabel(
        graph_frame,
        text="Average Split",
        font=ctk.CTkFont(size=20, weight="bold")
    )

    split_title.pack(anchor="w", pady=(10, 5))

    figure2 = plt.Figure(figsize=(9, 4), dpi=100)

    graph2 = figure2.add_subplot(111)

    valid_dates = []
    valid_splits = []

    for i in range(len(dates)):

        if splits[i] is not None:

            valid_dates.append(dates[i])
            valid_splits.append(splits[i])

    if valid_splits:

        graph2.plot(
            valid_dates,
            valid_splits,
            marker="o"
        )

        graph2.set_xlabel("Date")
        graph2.set_ylabel("Seconds / 500m")
        graph2.set_title("Average Split")

        graph2.tick_params(axis="x", rotation=45)

        figure2.tight_layout()

        canvas2 = FigureCanvasTkAgg(
            figure2,
            master=graph_frame
        )

        canvas2.draw()

        canvas2.get_tk_widget().pack(
            fill="both",
            expand=True,
            pady=(0, 30)
        )




























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


# ---------------- PROFILE ----------------

def profile():
    clear_page()

    page_title(
        "Profile",
        "Your athlete information and erg PBs"
    )

    frame = ctk.CTkScrollableFrame(content)
    frame.pack(fill="both", expand=True, padx=40, pady=10)

    cursor.execute("""
    SELECT name, age, club, boat_class, weight,
           pb_500, pb_1000, pb_2000, pb_5000, pb_6000
    FROM profile
    WHERE id = 1
    """)

    data = cursor.fetchone()

    labels = [
        "Name",
        "Age",
        "Club",
        "Boat Class",
        "Weight"
    ]

    entries = []

    for i in range(5):

        ctk.CTkLabel(
            frame,
            text=labels[i]
        ).pack(anchor="w", pady=(8, 3))

        entry = ctk.CTkEntry(
            frame,
            width=350
        )
        entry.pack(anchor="w")

        if data[i]:
            entry.insert(0, data[i])

        entries.append(entry)

    ctk.CTkLabel(
        frame,
        text="Erg Personal Bests",
        font=ctk.CTkFont(size=21, weight="bold")
    ).pack(anchor="w", pady=(30, 15))

    pb_labels = [
        "500m PB",
        "1k PB",
        "2k PB",
        "5k PB",
        "6k PB"
    ]

    pb_entries = []

    for i in range(5):

        ctk.CTkLabel(
            frame,
            text=pb_labels[i]
        ).pack(anchor="w", pady=(5, 3))

        entry = ctk.CTkEntry(
            frame,
            width=350
        )
        entry.pack(anchor="w")

        if data[i + 5]:
            entry.insert(0, data[i + 5])

        pb_entries.append(entry)

    def save_profile():

        cursor.execute("""
        UPDATE profile
        SET name = ?,
            age = ?,
            club = ?,
            boat_class = ?,
            weight = ?,
            pb_500 = ?,
            pb_1000 = ?,
            pb_2000 = ?,
            pb_5000 = ?,
            pb_6000 = ?
        WHERE id = 1
        """, (
            entries[0].get(),
            entries[1].get(),
            entries[2].get(),
            entries[3].get(),
            entries[4].get(),
            pb_entries[0].get(),
            pb_entries[1].get(),
            pb_entries[2].get(),
            pb_entries[3].get(),
            pb_entries[4].get()
        ))

        db.commit()
        message("Profile saved!")

    ctk.CTkButton(
        frame,
        text="Save Profile",
        width=250,
        height=45,
        command=save_profile
    ).pack(anchor="w", pady=30)


def get_pb():

    cursor.execute(
        "SELECT pb_2000 FROM profile WHERE id = 1"
    )

    result = cursor.fetchone()

    if result and result[0]:
        return result[0]

    return "--"


# ---------------- SETTINGS ----------------

def settings():
    clear_page()

    page_title(
        "Settings",
        "Change how the app works"
    )

    frame = ctk.CTkFrame(content)
    frame.pack(fill="both", expand=True, padx=40, pady=10)

    ctk.CTkLabel(
        frame,
        text="Appearance",
        font=ctk.CTkFont(size=20, weight="bold")
    ).pack(pady=(30, 10))

    appearance = ctk.CTkOptionMenu(
        frame,
        values=["Dark", "Light", "System"],
        command=change_appearance
    )
    appearance.pack()
    appearance.set("Dark")

    ctk.CTkLabel(
        frame,
        text="Notifications",
        font=ctk.CTkFont(size=20, weight="bold")
    ).pack(pady=(40, 10))

    ctk.CTkSwitch(
        frame,
        text="Training reminders"
    ).pack(pady=10)

    ctk.CTkSwitch(
        frame,
        text="Daily questionnaire reminders"
    ).pack(pady=10)


def change_appearance(choice):
    ctk.set_appearance_mode(choice.lower())


# ---------------- SIDEBAR ----------------

ctk.CTkLabel(
    sidebar,
    text="ROWING\nPERFORMANCE",
    font=ctk.CTkFont(size=22, weight="bold")
).pack(pady=30)


buttons = [
    ("🏠  Home", home),
    ("🚣  Training", training),
    ("📝  Questionnaire", questionnaire),
    ("📈  Progress", progress),
    ("🎯  Goals", goals),
    ("👤  Profile", profile),
    ("⚙  Settings", settings)
]

for text, command in buttons:

    ctk.CTkButton(
        sidebar,
        text=text,
        command=command,
        height=45,
        fg_color="transparent",
        anchor="w"
    ).pack(fill="x", padx=15, pady=4)


# Start on the home screen
home()

app.mainloop()