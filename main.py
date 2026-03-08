import tkinter as tk
from tkinter import messagebox

def main():
    root = tk.Tk()
    root.title("Horizon Cinemas Booking System")
    root.geometry("400x300")
    
    label = tk.Label(root, text="Welcome to HCBS", font=("Arial", 16))
    label.pack(pady=50)
    
    btn = tk.Button(root, text="Launch System", command=lambda: messagebox.showinfo("Info", "System Launching..."))
    btn.pack()
    
    root.mainloop()

if __name__ == "__main__":
    main()
