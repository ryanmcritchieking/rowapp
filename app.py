import customtkinter as ctk

#made steeings defult and then go ai to fix them so they fit kniter

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

app = ctk.CTk()
app.title("Rowing Performance")
app.geometry("1100x700")
app.minsize(900, 600)


#mint ai emoges 
buttons= [
     "🏠  Home",
    "🚣  Training",
    "📝  Questionnaire",
    "📈  Progress",
    "🎯  Goals",
    "👤  Profile",
    "⚙  Settings"

]


for button in buttons:
    nav_button = ctk.CTkButton(
        sidebar,
        text=button,
        height=45,
        corner_radius=8,
        font=ctk.CTkFont(size=15),
        fg_color="transparent",
        anchor="w"
    )
    nav_button.pack(fill="x", padx=15, pady=4)
    