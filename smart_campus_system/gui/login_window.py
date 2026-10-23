"""
gui/login_window.py
-------------------
The login screen and the registration screen.
Both screens are drawn inside the main window (root) inside a Frame.
"""

import tkinter as tk
from tkinter import messagebox
import auth
import database
from utils import (APP_TITLE, TITLE_FONT, HEADING_FONT, NORMAL_FONT, BG_COLOUR,
                   ALL_ROLES, ROLE_LECTURER, make_button)


class LoginWindow:
    """Username and password boxes, a Login button and a Register button."""

    def __init__(self, root, on_login_success):
        self.root = root
        # on_login_success is a function from main.py that opens the dashboard
        self.on_login_success = on_login_success
        self.root.title(APP_TITLE + " - Login")

        self.frame = tk.Frame(root, bg=BG_COLOUR, padx=40, pady=30)
        self.frame.pack(expand=True)

        tk.Label(self.frame, text=APP_TITLE, font=TITLE_FONT,
                 bg=BG_COLOUR).grid(row=0, column=0, columnspan=2, pady=(0, 5))
        tk.Label(self.frame, text="Richfield Graduate Institute of Technology",
                 font=NORMAL_FONT, bg=BG_COLOUR).grid(row=1, column=0, columnspan=2,
                                                      pady=(0, 20))

        tk.Label(self.frame, text="Username:", font=NORMAL_FONT,
                 bg=BG_COLOUR).grid(row=2, column=0, sticky="e", pady=5)
        self.username_entry = tk.Entry(self.frame, width=30, font=NORMAL_FONT)
        self.username_entry.grid(row=2, column=1, pady=5)

        tk.Label(self.frame, text="Password:", font=NORMAL_FONT,
                 bg=BG_COLOUR).grid(row=3, column=0, sticky="e", pady=5)
        # show="*" hides the password while typing
        self.password_entry = tk.Entry(self.frame, width=30, show="*", font=NORMAL_FONT)
        self.password_entry.grid(row=3, column=1, pady=5)

        make_button(self.frame, "Login", self.login).grid(row=4, column=0,
                                                          columnspan=2, pady=(15, 5))
        tk.Label(self.frame, text="Don't have an account?", font=NORMAL_FONT,
                 bg=BG_COLOUR).grid(row=5, column=0, columnspan=2, pady=(10, 0))
        make_button(self.frame, "Register", self.open_register).grid(
            row=6, column=0, columnspan=2, pady=5)

        # Pressing Enter in the password box also logs in
        self.password_entry.bind("<Return>", self.login_with_enter_key)
        self.username_entry.focus()

    def login(self):
        """Called when the Login button is clicked."""
        user, message = auth.login_user(self.username_entry.get(),
                                        self.password_entry.get())
        if user is None:
            messagebox.showerror("Login failed", message)
            self.password_entry.delete(0, tk.END)
            return
        self.on_login_success(user)

    def login_with_enter_key(self, event):
        """bind() passes an event object, so this small method accepts it."""
        self.login()

    def open_register(self):
        """Swap the login screen for the registration screen."""
        self.frame.destroy()
        RegisterWindow(self.root, self.on_login_success)


class RegisterWindow:
    """Form for creating a new account with a role and a campus."""

    def __init__(self, root, on_login_success):
        self.root = root
        self.on_login_success = on_login_success   # needed to go back to login
        self.root.title(APP_TITLE + " - Register")

        self.frame = tk.Frame(root, bg=BG_COLOUR, padx=40, pady=20)
        self.frame.pack(expand=True)

        tk.Label(self.frame, text="Create an Account", font=TITLE_FONT,
                 bg=BG_COLOUR).grid(row=0, column=0, columnspan=2, pady=(0, 15))

        # Labels and entry boxes for the text fields
        tk.Label(self.frame, text="Username:", font=NORMAL_FONT,
                 bg=BG_COLOUR).grid(row=1, column=0, sticky="e", pady=4)
        self.username_entry = tk.Entry(self.frame, width=30, font=NORMAL_FONT)
        self.username_entry.grid(row=1, column=1, pady=4, sticky="w")

        tk.Label(self.frame, text="Password:", font=NORMAL_FONT,
                 bg=BG_COLOUR).grid(row=2, column=0, sticky="e", pady=4)
        self.password_entry = tk.Entry(self.frame, width=30, show="*", font=NORMAL_FONT)
        self.password_entry.grid(row=2, column=1, pady=4, sticky="w")

        tk.Label(self.frame, text="Confirm password:", font=NORMAL_FONT,
                 bg=BG_COLOUR).grid(row=3, column=0, sticky="e", pady=4)
        self.confirm_entry = tk.Entry(self.frame, width=30, show="*", font=NORMAL_FONT)
        self.confirm_entry.grid(row=3, column=1, pady=4, sticky="w")

        # Radio buttons for the role. StringVar holds the chosen value.
        tk.Label(self.frame, text="Role:", font=HEADING_FONT,
                 bg=BG_COLOUR).grid(row=4, column=0, sticky="ne", pady=(10, 0))
        self.role_value = tk.StringVar(value=ROLE_LECTURER)
        role_frame = tk.Frame(self.frame, bg=BG_COLOUR)
        role_frame.grid(row=4, column=1, sticky="w", pady=(10, 0))
        for role in ALL_ROLES:
            tk.Radiobutton(role_frame, text=role, variable=self.role_value, value=role,
                           bg=BG_COLOUR, font=NORMAL_FONT).pack(anchor="w")

        # Radio buttons for the campus, built from the campuses table
        tk.Label(self.frame, text="Campus:", font=HEADING_FONT,
                 bg=BG_COLOUR).grid(row=5, column=0, sticky="ne", pady=(10, 0))
        campus_frame = tk.Frame(self.frame, bg=BG_COLOUR)
        campus_frame.grid(row=5, column=1, sticky="w", pady=(10, 0))
        campus_names = []
        for campus_row in database.get_all_campuses():
            campus_names.append(campus_row[1])
        self.campus_value = tk.StringVar(value=campus_names[0])
        for campus_name in campus_names:
            tk.Radiobutton(campus_frame, text=campus_name, variable=self.campus_value,
                           value=campus_name, bg=BG_COLOUR,
                           font=NORMAL_FONT).pack(anchor="w")
        tk.Label(campus_frame, text="(A System Operator covers all campuses)",
                 font=("Arial", 8), bg=BG_COLOUR).pack(anchor="w")

        button_frame = tk.Frame(self.frame, bg=BG_COLOUR)
        button_frame.grid(row=6, column=0, columnspan=2, pady=15)
        make_button(button_frame, "Register", self.register).pack(side="left", padx=5)
        make_button(button_frame, "Back to Login", self.back_to_login).pack(side="left",
                                                                            padx=5)

    def register(self):
        """Called when the Register button is clicked."""
        success, message = auth.register_user(self.username_entry.get(),
                                              self.password_entry.get(),
                                              self.confirm_entry.get(),
                                              self.role_value.get(),
                                              self.campus_value.get())
        if success:
            messagebox.showinfo("Registered", message)
            self.back_to_login()
        else:
            messagebox.showerror("Registration failed", message)

    def back_to_login(self):
        self.frame.destroy()
        LoginWindow(self.root, self.on_login_success)
