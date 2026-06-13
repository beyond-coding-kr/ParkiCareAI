import customtkinter as ctk

app = ctk.CTk()
app.geometry("400x400")

scroll = ctk.CTkScrollableFrame(app)
scroll.pack(fill="both", expand=True)

# Make scrollbar wider
scroll._scrollbar.configure(width=40)

for i in range(50):
    ctk.CTkLabel(scroll, text=f"Item {i}").pack(pady=5)

app.mainloop()
