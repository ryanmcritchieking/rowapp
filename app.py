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


