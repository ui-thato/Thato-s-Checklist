"""
gui/admin_dashboard.py
----------------------
The campus administrator's screen:
  - add, update and remove resources at their campus
  - view every booking at their campus
  - generate the campus report (totals, most used resource, average duration)
"""

import tkinter as tk
from tkinter import messagebox
from models import load_resources, campus_from_row
import database
from utils import (APP_TITLE, TITLE_FONT, HEADING_FONT, NORMAL_FONT, LIST_FONT,
                   BG_COLOUR, RESOURCE_TYPES, make_button, make_listbox,
                   get_selected_index)


class AdminDashboard:

    def __init__(self, root, user, on_logout):
        self.root = root
        self.user = user              # a CampusAdmin object
        self.on_logout = on_logout
        self.root.title(APP_TITLE + " - Campus Administrator")

        # An administrator always works with the campus they registered for
        self.campus = campus_from_row(database.get_campus_by_id(user.get_campus_id()))
        self.resources = []

        self.frame = tk.Frame(root, bg=BG_COLOUR, padx=10, pady=10)
        self.frame.pack(fill="both", expand=True)

        self.build_top_bar()
        self.build_resource_section()
        self.build_bookings_section()
        self.build_report_section()

        self.refresh_resources()
        self.refresh_bookings()
        self.show_report()

    # ---------------- Building the screen ----------------

    def build_top_bar(self):
        top = tk.Frame(self.frame, bg=BG_COLOUR)
        top.grid(row=0, column=0, columnspan=2, sticky="ew")
        tk.Label(top, text=self.user.get_welcome_message(), font=TITLE_FONT,
                 bg=BG_COLOUR).pack(side="left")
        make_button(top, "Logout", self.on_logout, width=10).pack(side="right")

        tk.Label(self.frame, text=f"Active campus: {self.campus} (the campus you manage)",
                 font=HEADING_FONT, fg="#1d4566", bg=BG_COLOUR).grid(
            row=1, column=0, columnspan=2, sticky="w", pady=(8, 0))
        tk.Label(self.frame, text="Booking policy in effect -> " +
                 self.campus.get_policy_text(), font=NORMAL_FONT, fg="#8a2c2c",
                 bg=BG_COLOUR).grid(row=2, column=0, columnspan=2, sticky="w",
                                    pady=(0, 8))

    def build_resource_section(self):
        section = tk.LabelFrame(self.frame, text="Manage Resources", font=HEADING_FONT,
                                bg=BG_COLOUR, padx=5, pady=5)
        section.grid(row=3, column=0, rowspan=2, sticky="nsew", padx=5)

        list_frame, self.resource_listbox = make_listbox(section, 70, 10)
        list_frame.grid(row=0, column=0, columnspan=2)

        tk.Label(section, text="Resource name:", bg=BG_COLOUR,
                 font=NORMAL_FONT).grid(row=1, column=0, sticky="e", pady=(8, 2))
        self.name_entry = tk.Entry(section, width=30, font=NORMAL_FONT)
        self.name_entry.grid(row=1, column=1, sticky="w", pady=(8, 2))

        tk.Label(section, text="Resource type:", bg=BG_COLOUR,
                 font=NORMAL_FONT).grid(row=2, column=0, sticky="ne", pady=2)
        type_frame, self.type_listbox = make_listbox(section, 28, 5)
        type_frame.grid(row=2, column=1, sticky="w", pady=2)
        for resource_type in RESOURCE_TYPES:
            self.type_listbox.insert(tk.END, resource_type)

        # A Checkbutton is linked to an IntVar: 1 = ticked, 0 = not ticked
        self.available_value = tk.IntVar(value=1)
        tk.Checkbutton(section, text="Available for booking",
                       variable=self.available_value, bg=BG_COLOUR,
                       font=NORMAL_FONT).grid(row=3, column=1, sticky="w")

        buttons = tk.Frame(section, bg=BG_COLOUR)
        buttons.grid(row=4, column=0, columnspan=2, pady=5)
        make_button(buttons, "Add new", self.add_resource, width=13).grid(
            row=0, column=0, padx=2, pady=2)
        make_button(buttons, "Edit selected", self.load_selected, width=13).grid(
            row=0, column=1, padx=2, pady=2)
        make_button(buttons, "Save changes", self.update_resource, width=13).grid(
            row=0, column=2, padx=2, pady=2)
        make_button(buttons, "Remove selected", self.remove_resource, width=13).grid(
            row=1, column=0, padx=2, pady=2)
        make_button(buttons, "Clear form", self.clear_form, width=13).grid(
            row=1, column=1, padx=2, pady=2)
        make_button(buttons, "Refresh", self.refresh_all, width=13).grid(
            row=1, column=2, padx=2, pady=2)

    def build_bookings_section(self):
        section = tk.LabelFrame(self.frame, text="All Bookings at this Campus",
                                font=HEADING_FONT, bg=BG_COLOUR, padx=5, pady=5)
        section.grid(row=3, column=1, sticky="nsew", padx=5)
        list_frame, self.booking_listbox = make_listbox(section, 95, 9)
        list_frame.pack(fill="both", expand=True)

    def build_report_section(self):
        section = tk.LabelFrame(self.frame, text="Campus Report and Usage Trends",
                                font=HEADING_FONT, bg=BG_COLOUR, padx=5, pady=5)
        section.grid(row=4, column=1, sticky="nsew", padx=5, pady=(5, 0))
        make_button(section, "Generate report", self.show_report).pack(side="bottom",
                                                                        pady=5)
        scrollbar = tk.Scrollbar(section)
        self.report_text = tk.Text(section, width=95, height=16, font=LIST_FONT,
                                   yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.report_text.yview)
        self.report_text.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    # ---------------- Showing data ----------------

    def refresh_resources(self):
        # Remember which line was selected so the selection is not lost
        selected_index = get_selected_index(self.resource_listbox)
        self.resources = load_resources(self.campus.get_id())
        self.resource_listbox.delete(0, tk.END)
        for resource in self.resources:
            self.resource_listbox.insert(tk.END, resource.get_display_text())
            if not resource.is_available():
                self.resource_listbox.itemconfig(tk.END, fg="grey")
        if selected_index is not None and selected_index < len(self.resources):
            self.resource_listbox.selection_set(selected_index)

    def refresh_bookings(self):
        self.booking_listbox.delete(0, tk.END)
        bookings = self.user.get_campus_bookings()
        for booking in bookings:
            self.booking_listbox.insert(tk.END, booking.get_display_text(show_user=True))
        if len(bookings) == 0:
            self.booking_listbox.insert(tk.END, "No bookings at this campus yet.")

    def show_report(self):
        # A Text widget is cleared from line 1, character 0 up to the end
        self.report_text.delete("1.0", tk.END)
        self.report_text.insert(tk.END, self.user.get_campus_report())

    def refresh_all(self):
        self.refresh_resources()
        self.refresh_bookings()
        self.show_report()

    # ---------------- Resource management ----------------

    def get_form_type(self):
        index = get_selected_index(self.type_listbox)
        if index is None:
            return ""
        return RESOURCE_TYPES[index]

    def get_selected_resource(self):
        index = get_selected_index(self.resource_listbox)
        if index is None or index >= len(self.resources):
            messagebox.showwarning("No resource", "Please select a resource first.")
            return None
        return self.resources[index]

    def clear_form(self):
        self.name_entry.delete(0, tk.END)
        self.type_listbox.selection_clear(0, tk.END)
        self.available_value.set(1)

    def add_resource(self):
        success, message = self.user.add_resource(self.name_entry.get(),
                                                  self.get_form_type())
        if success:
            messagebox.showinfo("Resource added", message)
            self.clear_form()
            self.refresh_all()
        else:
            messagebox.showerror("Cannot add resource", message)

    def load_selected(self):
        """Copy the selected resource into the form so it can be edited."""
        resource = self.get_selected_resource()
        if resource is None:
            return
        self.clear_form()
        self.name_entry.insert(0, resource.get_name())
        if resource.get_type() in RESOURCE_TYPES:
            self.type_listbox.selection_set(RESOURCE_TYPES.index(resource.get_type()))
        self.available_value.set(int(resource.is_available()))

    def update_resource(self):
        resource = self.get_selected_resource()
        if resource is None:
            return
        success, message = self.user.update_resource(resource, self.name_entry.get(),
                                                     self.get_form_type(),
                                                     self.available_value.get() == 1)
        if success:
            messagebox.showinfo("Resource updated", message)
            self.clear_form()
            self.refresh_all()
        else:
            messagebox.showerror("Cannot update resource", message)

    def remove_resource(self):
        resource = self.get_selected_resource()
        if resource is None:
            return
        if not messagebox.askyesno("Remove resource",
                                   f"Remove '{resource.get_name()}'? Its past "
                                   "bookings will also be removed."):
            return
        success, message = self.user.remove_resource(resource)
        if success:
            messagebox.showinfo("Resource removed", message)
            self.refresh_all()
        else:
            messagebox.showerror("Cannot remove resource", message)
