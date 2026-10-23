"""
gui/operator_dashboard.py
-------------------------
The system operator's screen. The operator can:
  - pick any campus (or all campuses) and see its resources and bookings
  - generate a report for one campus
  - generate a comparison report across all campuses
  - save the report to a text file
"""

import tkinter as tk
from tkinter import messagebox
import os
from models import load_campuses, load_resources
from utils import (APP_TITLE, TITLE_FONT, HEADING_FONT, NORMAL_FONT, LIST_FONT,
                   BG_COLOUR, make_button, make_listbox, get_selected_index, today)

ALL_CAMPUSES = "All campuses"
# Reports are saved in a "reports" folder next to main.py
REPORT_FOLDER = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                             "reports")


class OperatorDashboard:

    def __init__(self, root, user, on_logout):
        self.root = root
        self.user = user              # a SystemOperator object
        self.on_logout = on_logout
        self.root.title(APP_TITLE + " - System Operator")

        self.campuses = load_campuses()
        # The first choice is "All campuses", then each campus name
        self.campus_choices = [ALL_CAMPUSES] + list(self.campuses.keys())
        self.active_campus = None     # None means all campuses

        self.frame = tk.Frame(root, bg=BG_COLOUR, padx=10, pady=10)
        self.frame.pack(fill="both", expand=True)

        self.build_top_bar()
        self.build_campus_section()
        self.build_data_section()
        self.build_report_section()

        self.campus_listbox.selection_set(0)
        self.select_campus()
        self.show_comparison_report()

    # ---------------- Building the screen ----------------

    def build_top_bar(self):
        top = tk.Frame(self.frame, bg=BG_COLOUR)
        top.grid(row=0, column=0, columnspan=2, sticky="ew")
        tk.Label(top, text=self.user.get_welcome_message(), font=TITLE_FONT,
                 bg=BG_COLOUR).pack(side="left")
        make_button(top, "Logout", self.on_logout, width=10).pack(side="right")

        self.active_campus_label = tk.Label(self.frame, text="", font=HEADING_FONT,
                                            fg="#1d4566", bg=BG_COLOUR)
        self.active_campus_label.grid(row=1, column=0, columnspan=2, sticky="w",
                                      pady=(8, 0))
        self.policy_label = tk.Label(self.frame, text="", font=NORMAL_FONT,
                                     fg="#8a2c2c", bg=BG_COLOUR, justify="left")
        self.policy_label.grid(row=2, column=0, columnspan=2, sticky="w", pady=(0, 8))

    def build_campus_section(self):
        section = tk.LabelFrame(self.frame, text="Select Campus", font=HEADING_FONT,
                                bg=BG_COLOUR, padx=5, pady=5)
        section.grid(row=3, column=0, sticky="nsew", padx=5)
        list_frame, self.campus_listbox = make_listbox(section, 18, 6)
        list_frame.pack()
        for choice in self.campus_choices:
            self.campus_listbox.insert(tk.END, choice)
        make_button(section, "View campus", self.select_campus).pack(pady=5)

        tk.Label(section, text="Reports", font=HEADING_FONT,
                 bg=BG_COLOUR).pack(pady=(15, 5))
        make_button(section, "Campus report", self.show_campus_report).pack(pady=3)
        make_button(section, "Compare campuses", self.show_comparison_report).pack(pady=3)
        make_button(section, "Save report to file", self.save_report).pack(pady=3)

    def build_data_section(self):
        section = tk.LabelFrame(self.frame, text="Resources and Bookings",
                                font=HEADING_FONT, bg=BG_COLOUR, padx=5, pady=5)
        section.grid(row=3, column=1, sticky="nsew", padx=5)
        tk.Label(section, text="Resources:", font=NORMAL_FONT,
                 bg=BG_COLOUR).pack(anchor="w")
        list_frame, self.resource_listbox = make_listbox(section, 100, 6)
        list_frame.pack(fill="x")
        tk.Label(section, text="Bookings:", font=NORMAL_FONT,
                 bg=BG_COLOUR).pack(anchor="w", pady=(5, 0))
        list_frame, self.booking_listbox = make_listbox(section, 100, 7)
        list_frame.pack(fill="x")

    def build_report_section(self):
        section = tk.LabelFrame(self.frame, text="Report", font=HEADING_FONT,
                                bg=BG_COLOUR, padx=5, pady=5)
        section.grid(row=4, column=0, columnspan=2, sticky="nsew", padx=5, pady=(8, 0))
        scrollbar = tk.Scrollbar(section)
        self.report_text = tk.Text(section, width=125, height=15, font=LIST_FONT,
                                   yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.report_text.yview)
        self.report_text.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    # ---------------- Actions ----------------

    def select_campus(self):
        index = get_selected_index(self.campus_listbox)
        if index is None:
            messagebox.showwarning("No campus", "Please select a campus first.")
            return
        choice = self.campus_choices[index]
        if choice == ALL_CAMPUSES:
            self.active_campus = None
            self.active_campus_label.config(text="Active view: All campuses")
            policy_lines = []
            for campus in self.campuses.values():
                policy_lines.append(campus.get_policy_text())
            self.policy_label.config(text="\n".join(policy_lines))
        else:
            self.active_campus = self.campuses[choice]
            self.active_campus_label.config(text=f"Active campus: {self.active_campus}")
            self.policy_label.config(text="Booking policy in effect -> " +
                                     self.active_campus.get_policy_text())
        self.refresh_lists()

    def refresh_lists(self):
        # Resources: one campus, or every campus one after the other
        self.resource_listbox.delete(0, tk.END)
        if self.active_campus is None:
            campuses_to_show = list(self.campuses.values())
        else:
            campuses_to_show = [self.active_campus]
        for campus in campuses_to_show:
            for resource in load_resources(campus.get_id()):
                self.resource_listbox.insert(
                    tk.END, f"{campus.get_code()}  {resource.get_display_text()}")

        self.booking_listbox.delete(0, tk.END)
        bookings = self.user.get_bookings(self.active_campus)
        for booking in bookings:
            self.booking_listbox.insert(tk.END, booking.get_display_text(show_user=True))
        if len(bookings) == 0:
            self.booking_listbox.insert(tk.END, "No bookings yet.")

    def show_report_text(self, text):
        self.report_text.delete("1.0", tk.END)
        self.report_text.insert(tk.END, text)

    def show_campus_report(self):
        if self.active_campus is None:
            # With "All campuses" selected, show every campus report in turn
            reports = []
            for campus in self.campuses.values():
                reports.append(self.user.get_campus_report(campus))
            self.show_report_text("\n\n".join(reports))
        else:
            self.show_report_text(self.user.get_campus_report(self.active_campus))

    def show_comparison_report(self):
        self.show_report_text(self.user.get_comparison_report())

    def save_report(self):
        report = self.report_text.get("1.0", tk.END).strip()
        if report == "":
            messagebox.showwarning("Empty report", "Please generate a report first.")
            return
        try:
            os.makedirs(REPORT_FOLDER, exist_ok=True)
        except OSError as error:
            messagebox.showerror("Error", f"Could not create the reports folder: {error}")
            return
        file_name = os.path.join(REPORT_FOLDER, f"report_{today()}.txt")
        success, message = self.user.save_report_to_file(report, file_name)
        if success:
            messagebox.showinfo("Saved", message)
        else:
            messagebox.showerror("Error", message)
