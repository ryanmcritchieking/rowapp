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


sidebar = ctk.CTkFrame(app, width=220, corner_radius=0)
sidebar.pack(side="left", fill="y")
sidebar.pack_propagate(False)

title = ctk.CTkLabel(
    sidebar,
    text="ROWING\nPERFORMANCE",
    font=ctk.CTkFont(size=24, weight="bold")
)








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




main = ctk.CTkFrame(app, corner_radius=0)
main.pack(side="right", fill="both", expand=True)

welcome = ctk.CTkLabel(
    main,
    text="Welcome to Rowing Performance",
    font=ctk.CTkFont(size=30, weight="bold")
)
welcome.pack(anchor="w", padx=40, pady=(40, 5))

subtitle = ctk.CTkLabel(
    main,
    text="Track your training, performance and progress.",
    font=ctk.CTkFont(size=16)
)
subtitle.pack(anchor="w", padx=40, pady=(0, 30))





#this is were the kms rowed for week card
cards = ctk.CTkFrame(main, fg_color="transparent")
cards.pack(fill="x", padx=30)

# Weekly distance
distance_card = ctk.CTkFrame(cards, height=140)
distance_card.pack(side="left", fill="both", expand=True, padx=10)

ctk.CTkLabel(
    distance_card,
    text="WEEKLY DISTANCE",
    font=ctk.CTkFont(size=13)
).pack(pady=(25, 5))

ctk.CTkLabel(
    distance_card,
    text="0 km",
    font=ctk.CTkFont(size=30, weight="bold")
).pack()


#this is pretty much the same but for how many sessions 

sessions_card = ctk.CTkFrame(cards, height=140)
sessions_card.pack(side="left", fill="both", expand=True, padx=10)

ctk.CTkLabel(
    sessions_card,
    text="SESSIONS",
    font=ctk.CTkFont(size=13)
).pack(pady=(25, 5))

ctk.CTkLabel(
    sessions_card,
    text="0",
    font=ctk.CTkFont(size=30, weight="bold")
).pack()


#this is ames but for you goal you have set

goal_card = ctk.CTkFrame(cards, height=140)
goal_card.pack(side="left", fill="both", expand=True, padx=10)

ctk.CTkLabel(
    goal_card,
    text="CURRENT GOAL",
    font=ctk.CTkFont(size=13)
).pack(pady=(25, 5))

ctk.CTkLabel(
    goal_card,
    text="Not set",
    font=ctk.CTkFont(size=24, weight="bold")
).pack()