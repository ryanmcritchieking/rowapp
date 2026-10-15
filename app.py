import customtkinter as ctk
import sqlite3
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


# Default appearance; users can switch this in Settings.
appearance_choice = "Dark"
ctk.set_appearance_mode("dark")
CURRENT_MAX_MS = 3.0
MAX_DISTANCE_KM = 200.0
MIN_SPLIT_SECONDS = 60.0
MAX_SPLIT_SECONDS = 600.0
ctk.set_default_color_theme("blue")


# Colours
BG_COLOR = ("#F4F6F8", "#15171A")
CARD_COLOR = ("#FFFFFF", "#1E2126")
SIDEBAR_COLOR = ("#E9EDF2", "#111315")
TEXT_COLOR = ("#1A1A1A", "#FFFFFF")
SECONDARY_TEXT = ("#555555", "#B8BEC7")


app = ctk.CTk()
app.title("Rowing Performance")
app.geometry("1200x750")
app.minsize(760, 520)


# ---------------- DATABASE ----------------

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


# Add new columns to old databases
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

sidebar = ctk.CTkFrame(
    app,
    width=220,
    corner_radius=0,
    fg_color=SIDEBAR_COLOR
)
sidebar.pack(side="left", fill="y")
sidebar.pack_propagate(False)

content = ctk.CTkFrame(
    app,
    corner_radius=0,
    fg_color=BG_COLOR
)
content.pack(side="right", fill="both", expand=True)


# Clears the page
def clear_page():
    for thing in content.winfo_children():
        thing.destroy()


def page_title(title, subtitle=""):

    ctk.CTkLabel(
        content,
        text=title,
        text_color=TEXT_COLOR,
        font=ctk.CTkFont(size=30, weight="bold")
    ).pack(anchor="w", padx=40, pady=(30, 5))

    if subtitle:
        ctk.CTkLabel(
            content,
            text=subtitle,
            text_color=SECONDARY_TEXT,
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
        text_color=TEXT_COLOR,
        font=ctk.CTkFont(size=17, weight="bold")
    ).pack(pady=45)

    ctk.CTkButton(
        popup,
        text="OK",
        command=popup.destroy
    ).pack()


# ---------------- TIDE CALCULATION ----------------

def parse_split(split_text):
    """Parse an mm:ss split and return seconds; reject malformed/unrealistic values."""
    text = (split_text or "").strip()
    parts = text.split(":")
    if len(parts) != 2 or not all(part.strip() for part in parts):
        raise ValueError("Enter split as minutes:seconds, for example 2:10.")
    try:
        minutes = int(parts[0])
        seconds = float(parts[1])
    except ValueError:
        raise ValueError("Split must contain numbers in mm:ss format.")
    if minutes < 0 or not 0 <= seconds < 60:
        raise ValueError("Split seconds must be from 0 to under 60.")
    total = minutes * 60 + seconds
    if not MIN_SPLIT_SECONDS <= total <= MAX_SPLIT_SECONDS:
        raise ValueError("Split must be between 1:00 and 10:00 per 500 m.")
    return total


def calculate_adjusted_split(split_text, current, direction):
    """Return an explicitly approximate current-adjusted split, or -- if invalid."""
    try:
        split_seconds = parse_split(split_text)
        current = float(current)
        if not 0 <= current <= CURRENT_MAX_MS:
            return "--"
        if direction == "No current" or current == 0:
            adjusted_seconds = split_seconds
        else:
            # Simplified estimate only; this is not a validated hydrodynamic model.
            adjustment = min(current * 0.05, 0.15)
            if direction == "Helping":
                adjusted_seconds = split_seconds * (1 - adjustment)
            elif direction == "Against":
                adjusted_seconds = split_seconds * (1 + adjustment)
            else:
                return "--"
        adjusted_minutes = int(adjusted_seconds // 60)
        adjusted_remaining = adjusted_seconds % 60
        return f"{adjusted_minutes}:{adjusted_remaining:04.1f}"
    except (ValueError, TypeError, OverflowError):
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

    cards = ctk.CTkFrame(
        content,
        fg_color="transparent"
    )
    cards.pack(fill="x", padx=30)

    card1 = ctk.CTkFrame(
        cards,
        fg_color=CARD_COLOR
    )
    card1.pack(
        side="left",
        fill="both",
        expand=True,
        padx=8
    )

    ctk.CTkLabel(
        card1,
        text="TOTAL DISTANCE",
        text_color=SECONDARY_TEXT
    ).pack(pady=(25, 5))

    ctk.CTkLabel(
        card1,
        text=f"{total_distance:.1f} km",
        text_color=TEXT_COLOR,
        font=ctk.CTkFont(size=28, weight="bold")
    ).pack(pady=(0, 25))

    card2 = ctk.CTkFrame(
        cards,
        fg_color=CARD_COLOR
    )
    card2.pack(
        side="left",
        fill="both",
        expand=True,
        padx=8
    )

    ctk.CTkLabel(
        card2,
        text="SESSIONS",
        text_color=SECONDARY_TEXT
    ).pack(pady=(25, 5))

    ctk.CTkLabel(
        card2,
        text=str(sessions),
        text_color=TEXT_COLOR,
        font=ctk.CTkFont(size=28, weight="bold")
    ).pack(pady=(0, 25))

    card3 = ctk.CTkFrame(
        cards,
        fg_color=CARD_COLOR
    )
    card3.pack(
        side="left",
        fill="both",
        expand=True,
        padx=8
    )

    ctk.CTkLabel(
        card3,
        text="2K ERG PB",
        text_color=SECONDARY_TEXT
    ).pack(pady=(25, 5))

    ctk.CTkLabel(
        card3,
        text=get_pb(),
        text_color=TEXT_COLOR,
        font=ctk.CTkFont(size=28, weight="bold")
    ).pack(pady=(0, 25))

    recent = ctk.CTkFrame(
        content,
        fg_color=CARD_COLOR
    )
    recent.pack(
        fill="both",
        expand=True,
        padx=40,
        pady=30
    )

    ctk.CTkLabel(
        recent,
        text="Recent Training",
        text_color=TEXT_COLOR,
        font=ctk.CTkFont(size=21, weight="bold")
    ).pack(
        anchor="w",
        padx=25,
        pady=(20, 10)
    )

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
            text="No training sessions recorded yet.",
            text_color=SECONDARY_TEXT
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
            text=text,
            text_color=TEXT_COLOR
        ).pack(anchor="w", padx=25, pady=4)


# ---------------- TRAINING ----------------

def training():

    clear_page()

    page_title(
        "Training Log",
        "Record a training session"
    )

    frame = ctk.CTkScrollableFrame(
        content,
        fg_color=BG_COLOR
    )
    frame.pack(
        fill="both",
        expand=True,
        padx=40,
        pady=10
    )

    ctk.CTkLabel(
        frame,
        text="Session type",
        text_color=TEXT_COLOR
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
        text="Distance (km)",
        text_color=TEXT_COLOR
    ).pack(anchor="w", pady=(15, 3))

    distance = ctk.CTkEntry(
        frame,
        width=350,
        placeholder_text="Example: 10"
    )
    distance.pack(anchor="w")

    ctk.CTkLabel(
        frame,
        text="Time",
        text_color=TEXT_COLOR
    ).pack(anchor="w", pady=(15, 3))

    time_entry = ctk.CTkEntry(
        frame,
        width=350,
        placeholder_text="Example: 40:30"
    )
    time_entry.pack(anchor="w")

    ctk.CTkLabel(
        frame,
        text="Average split",
        text_color=TEXT_COLOR
    ).pack(anchor="w", pady=(15, 3))

    split = ctk.CTkEntry(
        frame,
        width=350,
        placeholder_text="Example: 2:05"
    )
    split.pack(anchor="w")

    # Tide

    ctk.CTkLabel(
        frame,
        text="River Current (optional)",
        text_color=TEXT_COLOR,
        font=ctk.CTkFont(size=21, weight="bold")
    ).pack(anchor="w", pady=(30, 10))

    ctk.CTkLabel(
        frame,
        text="Current speed (m/s)",
        text_color=TEXT_COLOR
    ).pack(anchor="w", pady=(5, 3))

    current = ctk.CTkEntry(
        frame,
        width=350,
        placeholder_text="Example: 0.4"
    )
    current.pack(anchor="w")

    ctk.CTkLabel(
        frame,
        text="Was the current helping or against you?",
        text_color=TEXT_COLOR
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
        text_color=TEXT_COLOR,
        font=ctk.CTkFont(size=17, weight="bold")
    )
    adjusted_label.pack(anchor="w", pady=20)

    def show_adjusted():

        try:
            current_value = float(current.get()) if current.get().strip() else 0.0
            if not 0 <= current_value <= CURRENT_MAX_MS:
                raise ValueError
        except ValueError:
            message(f"Current must be between 0 and {CURRENT_MAX_MS:g} m/s.")
            return
        if not split.get().strip():
            adjusted_label.configure(text="Adjusted split: enter a split first")
            return

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

    # Other data

    ctk.CTkLabel(
        frame,
        text="Stroke rate",
        text_color=TEXT_COLOR
    ).pack(anchor="w", pady=(20, 3))

    stroke_rate = ctk.CTkEntry(
        frame,
        width=350,
        placeholder_text="Example: 24"
    )
    stroke_rate.pack(anchor="w")

    ctk.CTkLabel(
        frame,
        text="Heart rate",
        text_color=TEXT_COLOR
    ).pack(anchor="w", pady=(15, 3))

    heart_rate = ctk.CTkEntry(
        frame,
        width=350,
        placeholder_text="Example: 150"
    )
    heart_rate.pack(anchor="w")

    ctk.CTkLabel(
        frame,
        text="Boat class",
        text_color=TEXT_COLOR
    ).pack(anchor="w", pady=(15, 3))

    boat_class = ctk.CTkEntry(
        frame,
        width=350,
        placeholder_text="Example: U17 1x"
    )
    boat_class.pack(anchor="w")

    ctk.CTkLabel(
        frame,
        text="Notes",
        text_color=TEXT_COLOR
    ).pack(anchor="w", pady=(15, 3))

    notes = ctk.CTkTextbox(
        frame,
        width=500,
        height=120
    )
    notes.pack(anchor="w")

    def save_training():

        if not session_type.get().strip() or session_type.get() not in ["Water", "Erg", "Gym", "Running", "Cross Training"]:
            message("Choose a session type.")
            return
        try:
            km = float(distance.get().strip())
            if not 0 < km <= MAX_DISTANCE_KM:
                raise ValueError
        except ValueError:
            message(f"Distance must be a number greater than 0 and no more than {MAX_DISTANCE_KM:g} km.")
            return
        try:
            current_value = float(current.get().strip()) if current.get().strip() else 0.0
            if not 0 <= current_value <= CURRENT_MAX_MS:
                raise ValueError
        except ValueError:
            message(f"Current must be blank or between 0 and {CURRENT_MAX_MS:g} m/s.")
            return
        if not split.get().strip():
            message("Enter an average split in mm:ss format, for example 2:10.")
            return
        try:
            parse_split(split.get())
        except ValueError as exc:
            message(str(exc))
            return
        def optional_int(entry, label, minimum, maximum):
            raw = entry.get().strip()
            if not raw:
                return 0
            try:
                value = int(raw)
            except ValueError:
                raise ValueError(f"{label} must be a whole number.")
            if not minimum <= value <= maximum:
                raise ValueError(f"{label} must be between {minimum} and {maximum}.")
            return value
        try:
            rate_value = optional_int(stroke_rate, "Stroke rate", 1, 60)
            hr_value = optional_int(heart_rate, "Heart rate", 30, 250)
        except ValueError as exc:
            message(str(exc))
            return
        adjusted = calculate_adjusted_split(split.get(), current_value, direction.get())

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
            rate_value,
            hr_value,
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

    frame = ctk.CTkScrollableFrame(
        content,
        fg_color=BG_COLOR
    )
    frame.pack(
        fill="both",
        expand=True,
        padx=40,
        pady=10
    )

    ctk.CTkLabel(
        frame,
        text="How hard was today's session? (RPE)",
        text_color=TEXT_COLOR
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
        text="5",
        text_color=TEXT_COLOR
    )
    rpe_number.pack()

    def update_rpe(value):
        rpe_number.configure(text=str(round(value)))

    rpe.configure(command=update_rpe)

    ctk.CTkLabel(
        frame,
        text="How did you feel before training?",
        text_color=TEXT_COLOR
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
    before.set("Select an answer")

    ctk.CTkLabel(
        frame,
        text="How do you feel after training?",
        text_color=TEXT_COLOR
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
    after.set("Select an answer")

    ctk.CTkLabel(
        frame,
        text="Any pain or injuries?",
        text_color=TEXT_COLOR
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
    pain.set("Select an answer")

    ctk.CTkLabel(
        frame,
        text="Comments",
        text_color=TEXT_COLOR
    ).pack(pady=(25, 5))

    comments = ctk.CTkTextbox(
        frame,
        width=500,
        height=120
    )
    comments.pack()

    def save_questionnaire():

        if before.get() not in ["Very good", "Good", "Average", "Tired", "Very tired"] or after.get() not in ["Very good", "Good", "Average", "Tired", "Very tired"] or pain.get() not in ["No", "Minor", "Moderate", "Severe"]:
            message("Please answer the before, after, and pain questions before saving.")
            return

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

    stats = ctk.CTkFrame(
        content,
        fg_color="transparent"
    )
    stats.pack(
        fill="x",
        padx=30,
        pady=(0, 10)
    )

    values = [
        ("Sessions", sessions),
        ("Total km", f"{kilometres:.1f}"),
        ("Average SR", average_rate),
        ("2k PB", get_pb())
    ]

    for title, value in values:

        box = ctk.CTkFrame(
            stats,
            fg_color=CARD_COLOR
        )
        box.pack(
            side="left",
            fill="both",
            expand=True,
            padx=8
        )

        ctk.CTkLabel(
            box,
            text=title,
            text_color=SECONDARY_TEXT
        ).pack(pady=(15, 5))

        ctk.CTkLabel(
            box,
            text=str(value),
            text_color=TEXT_COLOR,
            font=ctk.CTkFont(size=25, weight="bold")
        ).pack(pady=(0, 15))

    cursor.execute("""
    SELECT date, distance, split, adjusted_split
    FROM training
    WHERE distance > 0
    ORDER BY id ASC
    """)

    rows = cursor.fetchall()

    graph_frame = ctk.CTkScrollableFrame(
        content,
        fg_color=BG_COLOR
    )
    graph_frame.pack(
        fill="both",
        expand=True,
        padx=40,
        pady=10
    )

    if not rows:

        ctk.CTkLabel(
            graph_frame,
            text="Log some training first and your graphs will appear here.",
            text_color=SECONDARY_TEXT,
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

        try:

            parts = row[2].split(":")

            split_seconds = (
                float(parts[0]) * 60 +
                float(parts[1])
            )

            splits.append(split_seconds)

        except:

            splits.append(None)

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

    # Split graph

    split_title = ctk.CTkLabel(
        graph_frame,
        text="Average Split",
        text_color=TEXT_COLOR,
        font=ctk.CTkFont(size=20, weight="bold")
    )

    split_title.pack(
        anchor="w",
        pady=(10, 5)
    )

    figure2 = plt.Figure(
        figsize=(9, 4),
        dpi=100
    )

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

        graph2.tick_params(
            axis="x",
            rotation=45
        )

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

    # Adjusted split graph

    adjusted_title = ctk.CTkLabel(
        graph_frame,
        text="Tide Adjusted Split",
        text_color=TEXT_COLOR,
        font=ctk.CTkFont(size=20, weight="bold")
    )

    adjusted_title.pack(
        anchor="w",
        pady=(10, 5)
    )

    figure3 = plt.Figure(
        figsize=(9, 4),
        dpi=100
    )

    graph3 = figure3.add_subplot(111)

    adjusted_dates = []
    adjusted_values = []

    for i in range(len(dates)):

        if adjusted_splits[i] is not None:

            adjusted_dates.append(dates[i])
            adjusted_values.append(adjusted_splits[i])

    if adjusted_values:

        graph3.plot(
            adjusted_dates,
            adjusted_values,
            marker="o"
        )

        graph3.set_xlabel("Date")
        graph3.set_ylabel("Seconds / 500m")
        graph3.set_title("Estimated Tide Adjusted Split")

        graph3.tick_params(
            axis="x",
            rotation=45
        )

        figure3.tight_layout()

        canvas3 = FigureCanvasTkAgg(
            figure3,
            master=graph_frame
        )

        canvas3.draw()

        canvas3.get_tk_widget().pack(
            fill="both",
            expand=True,
            pady=(0, 30)
        )

    # History

    ctk.CTkLabel(
        graph_frame,
        text="Training History",
        text_color=TEXT_COLOR,
        font=ctk.CTkFont(size=20, weight="bold")
    ).pack(
        anchor="w",
        pady=15
    )

    cursor.execute("""
    SELECT date, distance, split, current,
           current_direction, adjusted_split
    FROM training
    ORDER BY id DESC
    LIMIT 20
    """)

    history = cursor.fetchall()

    for row in history:

        text = (
            f"{row[0]}   |   "
            f"{row[1]} km   |   "
            f"Split: {row[2]}"
        )

        if row[3] != 0:

            text += (
                f"   |   Current: "
                f"{row[3]} m/s ({row[4]})"
            )

        if row[5] and row[5] != "--":

            text += (
                f"   |   Adjusted: {row[5]}"
            )

        ctk.CTkLabel(
            graph_frame,
            text=text,
            text_color=TEXT_COLOR
        ).pack(
            anchor="w",
            pady=4
        )


# ---------------- GOALS ----------------

def goals():

    clear_page()

    page_title(
        "Goals",
        "Set goals and track your progress"
    )

    frame = ctk.CTkScrollableFrame(
        content,
        fg_color=BG_COLOR
    )
    frame.pack(
        fill="both",
        expand=True,
        padx=40,
        pady=10
    )

    ctk.CTkLabel(
        frame,
        text="Goal type",
        text_color=TEXT_COLOR
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
        text="Target",
        text_color=TEXT_COLOR
    ).pack(pady=(20, 5))

    target = ctk.CTkEntry(
        frame,
        width=350,
        placeholder_text="Example: 6:30"
    )
    target.pack()

    ctk.CTkLabel(
        frame,
        text="Progress",
        text_color=TEXT_COLOR
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
        text="0",
        text_color=TEXT_COLOR
    )
    progress_label.pack()

    def change_progress(value):

        progress_label.configure(
            text=f"{round(value)}%"
        )

    goal_progress.configure(
        command=change_progress
    )

    def save_goal():

        target_text = target.get().strip()
        if not target_text:
            message("Enter a target first.")
            return
        if goal_type.get() in ["2k Erg", "5k Erg", "On-Water Split"]:
            try:
                parse_split(target_text)
            except ValueError:
                message("Enter a realistic target time in mm:ss format, for example 6:30 or 2:10.")
                return
        else:
            try:
                target_number = float(target_text)
                if not 0 < target_number <= 100000:
                    raise ValueError
            except ValueError:
                message("Target must be a positive number no greater than 100000.")
                return

        cursor.execute("""
        INSERT INTO goals
        (goal_type, target, progress)
        VALUES (?, ?, ?)
        """, (
            goal_type.get(),
            target_text,
            max(0, min(100, goal_progress.get()))
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
        text_color=TEXT_COLOR,
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
            text="No goals yet.",
            text_color=SECONDARY_TEXT
        ).pack()

    for row in goal_rows:

        box = ctk.CTkFrame(
            frame,
            fg_color=CARD_COLOR
        )
        box.pack(
            fill="x",
            pady=8
        )

        ctk.CTkLabel(
            box,
            text=f"{row[0]}   |   Target: {row[1]}",
            text_color=TEXT_COLOR
        ).pack(
            anchor="w",
            padx=15,
            pady=(10, 3)
        )

        bar = ctk.CTkProgressBar(box)

        bar.pack(
            fill="x",
            padx=15,
            pady=5
        )

        safe_progress = max(0.0, min(100.0, float(row[2] or 0)))
        bar.set(safe_progress / 100)

        ctk.CTkLabel(
            box,
            text=f"{round(safe_progress)}%",
            text_color=TEXT_COLOR
        ).pack(
            anchor="w",
            padx=15,
            pady=(0, 10)
        )


# ---------------- PROFILE ----------------

def profile():

    clear_page()

    page_title(
        "Profile",
        "Your athlete information and erg PBs"
    )

    frame = ctk.CTkScrollableFrame(
        content,
        fg_color=BG_COLOR
    )
    frame.pack(
        fill="both",
        expand=True,
        padx=40,
        pady=10
    )

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
            text=labels[i],
            text_color=TEXT_COLOR
        ).pack(
            anchor="w",
            pady=(8, 3)
        )

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
        text_color=TEXT_COLOR,
        font=ctk.CTkFont(size=21, weight="bold")
    ).pack(
        anchor="w",
        pady=(30, 15)
    )

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
            text=pb_labels[i],
            text_color=TEXT_COLOR
        ).pack(
            anchor="w",
            pady=(5, 3)
        )

        entry = ctk.CTkEntry(
            frame,
            width=350
        )

        entry.pack(anchor="w")

        if data[i + 5]:
            entry.insert(0, data[i + 5])

        pb_entries.append(entry)

    def save_profile():
        name_value = entries[0].get().strip()
        if not name_value:
            message("Enter a name before saving your profile.")
            return
        weight_text = entries[4].get().strip()
        if weight_text:
            try:
                weight_value = float(weight_text)
                if not 20 <= weight_value <= 250:
                    raise ValueError
            except ValueError:
                message("Weight must be a number between 20 and 250 kg.")
                return
        else:
            weight_value = ""
        for label, entry in zip(pb_labels, pb_entries):
            value = entry.get().strip()
            if value:
                try:
                    parse_split(value)
                except ValueError:
                    message(f"{label} must be entered as mm:ss, for example 6:30.")
                    return

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
            name_value,
            entries[1].get().strip(),
            entries[2].get().strip(),
            entries[3].get().strip(),
            str(weight_value) if weight_text else "",
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
    ).pack(
        anchor="w",
        pady=30
    )


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

    frame = ctk.CTkFrame(
        content,
        fg_color=CARD_COLOR
    )
    frame.pack(
        fill="both",
        expand=True,
        padx=40,
        pady=10
    )

    ctk.CTkLabel(
        frame,
        text="Appearance",
        text_color=TEXT_COLOR,
        font=ctk.CTkFont(size=20, weight="bold")
    ).pack(pady=(30, 10))

    appearance = ctk.CTkOptionMenu(
        frame,
        values=[
            "Dark",
            "Light",
            "System"
        ],
        command=change_appearance
    )

    appearance.pack()
    appearance.set(appearance_choice)

    ctk.CTkLabel(
        frame,
        text="Notifications",
        text_color=TEXT_COLOR,
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
    global appearance_choice
    appearance_choice = choice
    ctk.set_appearance_mode(choice.lower())


# ---------------- SIDEBAR ----------------

ctk.CTkLabel(
    sidebar,
    text="ROWING\nPERFORMANCE",
    text_color=TEXT_COLOR,
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
        text_color=TEXT_COLOR,
        hover_color=("#D5DAE0", "#252A30"),
        anchor="w"
    ).pack(
        fill="x",
        padx=15,
        pady=4
    )


# Warn before closing so unsaved form entries are not lost accidentally.
def confirm_close():
    from tkinter import messagebox
    if messagebox.askyesno("Close Rowing Performance", "Close the app? Any information not yet saved will be lost."):
        try:
            db.commit()
            db.close()
        finally:
            app.destroy()

app.protocol("WM_DELETE_WINDOW", confirm_close)

# Start on the home screen
home()

app.mainloop()
