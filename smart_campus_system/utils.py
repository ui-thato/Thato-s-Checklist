"""
utils.py
--------
Small helper functions and constants that are used in more than one file.
"""

import tkinter as tk
from datetime import datetime, date

# ---------- Named constants (no "magic numbers") ----------
APP_TITLE = "Smart Campus Resource Booking System"
DATE_FORMAT = "%Y-%m-%d"          # e.g. 2026-10-23
MIN_USERNAME_LENGTH = 3
MIN_PASSWORD_LENGTH = 6
MAX_RESOURCE_NAME_LENGTH = 50

# The three roles in the system
ROLE_LECTURER = "Lecturer"
ROLE_ADMIN = "Campus Administrator"
ROLE_OPERATOR = "System Operator"
ALL_ROLES = [ROLE_LECTURER, ROLE_ADMIN, ROLE_OPERATOR]

# Booking status values stored in the database
STATUS_ACTIVE = "Active"
STATUS_CANCELLED = "Cancelled"

# The kinds of resources a campus can have
RESOURCE_TYPES = ["Computer Lab", "Projector", "Seminar Room",
                  "Lecture Hall", "Presentation Equipment"]

# Fonts and colours used by every window, so the GUI looks the same everywhere
TITLE_FONT = ("Arial", 16, "bold")
HEADING_FONT = ("Arial", 12, "bold")
NORMAL_FONT = ("Arial", 10)
LIST_FONT = ("Courier New", 9)   # fixed-width font so list columns line up
BG_COLOUR = "#eef3f8"
BUTTON_COLOUR = "#2c5f8a"
BUTTON_TEXT = "white"


def make_button(parent, text, command, width=18):
    """Create a button with the same look everywhere in the app."""
    return tk.Button(parent, text=text, command=command, width=width,
                     bg=BUTTON_COLOUR, fg=BUTTON_TEXT, font=NORMAL_FONT,
                     activebackground="#1d4566", activeforeground="white")


def make_listbox(parent, width, height):
    """Create a Listbox with a scrollbar inside its own frame.
    Returns (frame, listbox). exportselection=False stops one list from
    losing its selection when you click in another list."""
    frame = tk.Frame(parent)
    scrollbar = tk.Scrollbar(frame)
    listbox = tk.Listbox(frame, width=width, height=height, font=LIST_FONT,
                         exportselection=False, yscrollcommand=scrollbar.set)
    scrollbar.config(command=listbox.yview)
    listbox.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")
    return frame, listbox


def get_selected_index(listbox):
    """Return the index of the selected Listbox line, or None."""
    selection = listbox.curselection()
    if len(selection) == 0:
        return None
    return selection[0]


def parse_date(date_text):
    """Turn text like '2026-10-23' into a date object.
    Returns None if the text is not a valid date."""
    try:
        return datetime.strptime(date_text.strip(), DATE_FORMAT).date()
    except ValueError:
        return None


def parse_start_hour(time_text):
    """Turn text like '09:00' or '9' into the whole hour 9.
    Bookings start on the hour, so minutes must be 00.
    Returns None if the text is not valid."""
    time_text = time_text.strip()
    if ":" in time_text:
        parts = time_text.split(":")
        if len(parts) != 2 or parts[1] != "00":
            return None
        hour_text = parts[0]
    else:
        hour_text = time_text

    if not hour_text.isdigit():
        return None
    hour = int(hour_text)
    if hour < 0 or hour > 23:
        return None
    return hour


def parse_duration(duration_text):
    """Turn text like '2' into the whole number 2.
    Returns None if it is not a positive whole number."""
    duration_text = duration_text.strip()
    if not duration_text.isdigit():
        return None
    duration = int(duration_text)
    if duration <= 0:
        return None
    return duration


def hour_to_text(hour):
    """Turn the number 9 into the text '09:00'."""
    return f"{hour:02d}:00"


def text_to_hour(time_text):
    """Turn the stored text '09:00' back into the number 9."""
    return int(time_text.split(":")[0])


def today():
    """Return today's date. Kept in one place so it is easy to change."""
    return date.today()


def current_hour():
    """Return the current hour of the day (0 to 23)."""
    return datetime.now().hour


def is_future_booking(booking_date_text, start_time_text):
    """Return True if the booking has not started yet."""
    booking_date = parse_date(booking_date_text)
    start_hour = text_to_hour(start_time_text)
    if booking_date > today():
        return True
    if booking_date == today() and start_hour > current_hour():
        return True
    return False


def is_happening_now(booking_date_text, start_time_text, duration_hours):
    """Return True if the booking is in progress right now."""
    if parse_date(booking_date_text) != today():
        return False
    start_hour = text_to_hour(start_time_text)
    return start_hour <= current_hour() < start_hour + duration_hours


def times_overlap(start_a, duration_a, start_b, duration_b):
    """Check if two time slots on the same day overlap.
    Two slots overlap when each one starts before the other one ends.
    Example: 09:00-11:00 and 10:00-12:00 overlap, but
             09:00-11:00 and 11:00-12:00 do not."""
    end_a = start_a + duration_a
    end_b = start_b + duration_b
    return start_a < end_b and start_b < end_a
