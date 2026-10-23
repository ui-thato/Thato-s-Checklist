"""
gui/lecturer_dashboard.py
-------------------------
The lecturer's screen:
  1. choose a campus (the active campus and its policy are shown at the top)
  2. see the resources and their real-time availability
  3. fill in the booking form
  4. see and cancel bookings
"""

import tkinter as tk
from tkinter import messagebox
from datetime import timedelta
from models import load_campuses, load_resources
import database
from utils import (APP_TITLE, TITLE_FONT, HEADING_FONT, NORMAL_FONT, BG_COLOUR,
                   make_button, make_listbox, get_selected_index, today,
                   text_to_hour, hour_to_text)

REFRESH_MILLISECONDS = 60000   # refresh the availability list every minute


class LecturerDashboard:

    def __init__(self, root, user, on_logout):
        self.root = root
        self.user = user              # a Lecturer object
        self.on_logout = on_logout    # function from main.py
        self.root.title(APP_TITLE + " - Lecturer")

        # Data that the widgets display. The lists line up with the
        # Listbox lines, so line 0 in the Listbox is item 0 in the list.
        self.campuses = load_campuses()     # dictionary {name: Campus}
        self.campus_names = list(self.campuses.keys())
        self.active_campus = None
        self.resources = []
        self.shown_bookings = []

        self.frame = tk.Frame(root, bg=BG_COLOUR, padx=10, pady=10)
        self.frame.pack(fill="both", expand=True)

        self.build_top_bar()
        self.build_campus_section()
        self.build_resource_section()
        self.build_booking_form()
        self.build_history_section()

        # Start on the lecturer's home campus
        home_campus = user.get_home_campus_name()
        if home_campus in self.campus_names:
            self.campus_listbox.selection_set(self.campus_names.index(home_campus))
        else:
            self.campus_listbox.selection_set(0)
        self.select_campus()
        self.show_active_bookings()
        self.auto_refresh()

    # ---------------- Building the screen ----------------

    def build_top_bar(self):
        top = tk.Frame(self.frame, bg=BG_COLOUR)
        top.grid(row=0, column=0, columnspan=3, sticky="ew")
        tk.Label(top, text=self.user.get_welcome_message(), font=TITLE_FONT,
                 bg=BG_COLOUR).pack(side="left")
        make_button(top, "Logout", self.logout, width=10).pack(side="right")

        # The active campus and its policy are always visible here
        self.active_campus_label = tk.Label(self.frame, text="", font=HEADING_FONT,
                                            fg="#1d4566", bg=BG_COLOUR)
        self.active_campus_label.grid(row=1, column=0, columnspan=3, sticky="w",
                                      pady=(8, 0))
        self.policy_label = tk.Label(self.frame, text="", font=NORMAL_FONT,
                                     fg="#8a2c2c", bg=BG_COLOUR)
        self.policy_label.grid(row=2, column=0, columnspan=3, sticky="w", pady=(0, 8))

    def build_campus_section(self):
        section = tk.LabelFrame(self.frame, text="1. Select Campus", font=HEADING_FONT,
                                bg=BG_COLOUR, padx=5, pady=5)
        section.grid(row=3, column=0, sticky="nsew", padx=5)
        list_frame, self.campus_listbox = make_listbox(section, 18, 6)
        list_frame.pack()
        for campus_name in self.campus_names:
            self.campus_listbox.insert(tk.END, campus_name)
        make_button(section, "Use this campus", self.select_campus).pack(pady=5)

    def build_resource_section(self):
        section = tk.LabelFrame(self.frame, text="2. Resources (live availability)",
                                font=HEADING_FONT, bg=BG_COLOUR, padx=5, pady=5)
        section.grid(row=3, column=1, sticky="nsew", padx=5)
        list_frame, self.resource_listbox = make_listbox(section, 70, 8)
        list_frame.pack()
        buttons = tk.Frame(section, bg=BG_COLOUR)
        buttons.pack(pady=5)
        make_button(buttons, "Refresh", self.refresh_resources).pack(side="left", padx=3)
        make_button(buttons, "Show booked times", self.show_booked_times).pack(
            side="left", padx=3)

    def build_booking_form(self):
        section = tk.LabelFrame(self.frame, text="3. Book Selected Resource",
                                font=HEADING_FONT, bg=BG_COLOUR, padx=5, pady=5)
        section.grid(row=3, column=2, sticky="nsew", padx=5)

        tk.Label(section, text="Date (YYYY-MM-DD):", bg=BG_COLOUR,
                 font=NORMAL_FONT).grid(row=0, column=0, sticky="e", pady=3)
        self.date_entry = tk.Entry(section, width=14, font=NORMAL_FONT)
        self.date_entry.grid(row=0, column=1, pady=3)
        # Fill in tomorrow's date to help the user
        self.date_entry.insert(0, str(today() + timedelta(days=1)))

        tk.Label(section, text="Start time (HH:00):", bg=BG_COLOUR,
                 font=NORMAL_FONT).grid(row=1, column=0, sticky="e", pady=3)
        self.time_entry = tk.Entry(section, width=14, font=NORMAL_FONT)
        self.time_entry.grid(row=1, column=1, pady=3)
        self.time_entry.insert(0, "09:00")

        tk.Label(section, text="Duration (hours):", bg=BG_COLOUR,
                 font=NORMAL_FONT).grid(row=2, column=0, sticky="e", pady=3)
        self.duration_entry = tk.Entry(section, width=14, font=NORMAL_FONT)
        self.duration_entry.grid(row=2, column=1, pady=3)
        self.duration_entry.insert(0, "1")

        make_button(section, "Book Now", self.make_booking).grid(
            row=3, column=0, columnspan=2, pady=8)

        # Shows which times are already taken for the chosen resource and date
        self.booked_times_label = tk.Label(section, text="Select a resource and click\n"
                                           "'Show booked times'.", bg=BG_COLOUR,
                                           font=NORMAL_FONT, justify="left",
                                           wraplength=250)
        self.booked_times_label.grid(row=4, column=0, columnspan=2, sticky="w")

    def build_history_section(self):
        section = tk.LabelFrame(self.frame, text="4. My Bookings", font=HEADING_FONT,
                                bg=BG_COLOUR, padx=5, pady=5)
        section.grid(row=4, column=0, columnspan=3, sticky="nsew", padx=5, pady=10)
        self.history_title = tk.Label(section, text="", font=NORMAL_FONT, bg=BG_COLOUR)
        self.history_title.pack(anchor="w")
        list_frame, self.booking_listbox = make_listbox(section, 110, 9)
        list_frame.pack(fill="both", expand=True)
        buttons = tk.Frame(section, bg=BG_COLOUR)
        buttons.pack(pady=5)
        make_button(buttons, "Active bookings", self.show_active_bookings).pack(
            side="left", padx=3)
        make_button(buttons, "Past history", self.show_past_bookings).pack(
            side="left", padx=3)
        make_button(buttons, "All bookings", self.show_all_bookings).pack(
            side="left", padx=3)
        make_button(buttons, "Cancel selected", self.cancel_selected).pack(
            side="left", padx=3)

    # ---------------- Campus and resources ----------------

    def select_campus(self):
        index = get_selected_index(self.campus_listbox)
        if index is None:
            messagebox.showwarning("No campus", "Please select a campus first.")
            return
        self.active_campus = self.campuses[self.campus_names[index]]
        self.active_campus_label.config(
            text=f"Active campus: {self.active_campus}")
        self.policy_label.config(text="Booking policy in effect -> " +
                                 self.active_campus.get_policy_text())
        # A new campus has different resources, so clear the old selection
        self.resource_listbox.selection_clear(0, tk.END)
        self.refresh_resources()

    def refresh_resources(self):
        """Reload resources from the database so the status is up to date."""
        if self.active_campus is None:
            return
        # Remember which line was selected so the selection is not lost
        selected_index = get_selected_index(self.resource_listbox)
        self.resources = load_resources(self.active_campus.get_id())
        self.resource_listbox.delete(0, tk.END)
        for resource in self.resources:
            self.resource_listbox.insert(tk.END, resource.get_display_text())
            # Colour unavailable resources grey so they stand out
            if not resource.is_available():
                self.resource_listbox.itemconfig(tk.END, fg="grey")
        if len(self.resources) == 0:
            self.resource_listbox.insert(tk.END, "No resources at this campus yet.")
        elif selected_index is not None and selected_index < len(self.resources):
            self.resource_listbox.selection_set(selected_index)

    def auto_refresh(self):
        """Refresh the availability list every minute while the screen is open."""
        if self.frame.winfo_exists():
            self.refresh_resources()
            self.root.after(REFRESH_MILLISECONDS, self.auto_refresh)

    def get_selected_resource(self):
        index = get_selected_index(self.resource_listbox)
        if index is None or index >= len(self.resources):
            messagebox.showwarning("No resource", "Please select a resource first.")
            return None
        return self.resources[index]

    def show_booked_times(self):
        """List the times that are already taken for a resource on the chosen date."""
        resource = self.get_selected_resource()
        if resource is None:
            return
        date_text = self.date_entry.get().strip()
        rows = database.get_active_bookings_for_resource(resource.get_id(), date_text)
        if len(rows) == 0:
            text = f"{resource.get_name()} is free all day on {date_text}."
        else:
            text = f"{resource.get_name()} is booked on {date_text}:"
            for row in rows:
                end_time = hour_to_text(text_to_hour(row[5]) + row[6])
                text = text + f"\n  {row[5]} - {end_time}"
        self.booked_times_label.config(text=text)

    # ---------------- Booking ----------------

    def make_booking(self):
        resource = self.get_selected_resource()
        if resource is None:
            return
        success, message = self.user.book_resource(self.active_campus, resource,
                                                   self.date_entry.get(),
                                                   self.time_entry.get(),
                                                   self.duration_entry.get())
        if success:
            messagebox.showinfo("Booking confirmed", message)
            self.refresh_resources()
            self.show_active_bookings()
            self.show_booked_times()
        else:
            messagebox.showerror("Booking not allowed", message)

    # ---------------- Booking history ----------------

    def fill_booking_list(self, bookings, title):
        """Put a list of Booking objects into the bookings Listbox."""
        self.shown_bookings = bookings
        self.history_title.config(text=f"{title} ({len(bookings)})")
        self.booking_listbox.delete(0, tk.END)
        for booking in bookings:
            self.booking_listbox.insert(tk.END, booking.get_display_text())

    def show_active_bookings(self):
        active = []
        for booking in self.user.get_my_bookings():
            if booking.get_status_text() in ("Upcoming", "In progress"):
                active.append(booking)
        self.fill_booking_list(active, "Active and upcoming bookings")

    def show_past_bookings(self):
        past = []
        for booking in self.user.get_my_bookings():
            if booking.get_status_text() in ("Completed", "Cancelled"):
                past.append(booking)
        self.fill_booking_list(past, "Past and cancelled bookings")

    def show_all_bookings(self):
        self.fill_booking_list(self.user.get_my_bookings(), "All my bookings")

    def cancel_selected(self):
        index = get_selected_index(self.booking_listbox)
        if index is None:
            messagebox.showwarning("No booking", "Please select a booking to cancel.")
            return
        booking = self.shown_bookings[index]
        if not messagebox.askyesno("Cancel booking",
                                   "Are you sure you want to cancel this booking?"):
            return
        success, message = self.user.cancel_booking(booking)
        if success:
            messagebox.showinfo("Cancelled", message)
            self.show_active_bookings()
            self.refresh_resources()
        else:
            messagebox.showerror("Cannot cancel", message)

    def logout(self):
        self.on_logout()
