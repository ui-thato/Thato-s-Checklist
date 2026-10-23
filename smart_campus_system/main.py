"""
main.py
-------
Smart Campus Resource Booking System - start the program from this file.

    python main.py

It sets up the database, opens the login screen and moves between
the screens when users log in and out.
"""

import tkinter as tk
from tkinter import messagebox
import database
import auth
from gui.login_window import LoginWindow
from gui.lecturer_dashboard import LecturerDashboard
from gui.admin_dashboard import AdminDashboard
from gui.operator_dashboard import OperatorDashboard
from utils import ROLE_LECTURER, ROLE_ADMIN, ROLE_OPERATOR, BG_COLOUR

# Which dashboard each role should see. To add a new role, add one line here.
DASHBOARDS = {
    ROLE_LECTURER: LecturerDashboard,
    ROLE_ADMIN: AdminDashboard,
    ROLE_OPERATOR: OperatorDashboard,
}


class SmartCampusApp:
    """Controls the main window and which screen is showing."""

    def __init__(self, root):
        self.root = root
        self.root.configure(bg=BG_COLOUR)
        self.root.minsize(700, 450)
        self.show_login()

    def clear_window(self):
        """Remove every widget so the next screen starts on a clean window."""
        for widget in self.root.winfo_children():
            widget.destroy()

    def show_login(self):
        self.clear_window()
        self.root.geometry("520x420")
        LoginWindow(self.root, self.open_dashboard)

    def open_dashboard(self, user):
        """Open the right dashboard for the user's role (role-based access)."""
        dashboard_class = DASHBOARDS.get(user.get_role())
        if dashboard_class is None:
            messagebox.showerror("Error", "Your role does not have a dashboard.")
            return
        self.clear_window()
        self.root.geometry("")   # let the window grow to fit the dashboard
        dashboard_class(self.root, user, self.logout)

    def logout(self):
        if messagebox.askyesno("Logout", "Do you want to log out?"):
            auth.logout_user()
            self.show_login()


def main():
    # Create the tables, campus policies and demo data if needed
    if not database.setup_database(auth.hash_password):
        print("The database could not be set up. The program will close.")
        return
    root = tk.Tk()
    SmartCampusApp(root)
    root.mainloop()


# Only run main() when this file is started directly
if __name__ == "__main__":
    main()
