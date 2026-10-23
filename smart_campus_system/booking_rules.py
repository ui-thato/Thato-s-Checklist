"""
booking_rules.py
----------------
All campus booking policies live in this one file.

I kept the rules separate from the rest of the program so that the
booking code does not need to change when a campus changes its rules.
To add a new campus, add one new entry to the CAMPUS_POLICIES dictionary
below. The database will pick it up the next time the program starts.
"""

# Each campus is a key in this dictionary. The value is another dictionary
# that holds that campus's booking policy.
#   max_hours      - the longest a single booking may last
#   start_hour     - the earliest hour a booking may start (24-hour clock)
#   end_hour       - the latest hour a booking may END (24-hour clock)
#   max_days_ahead - how far into the future a lecturer may book
CAMPUS_POLICIES = {
    "Main Campus": {
        "code": "A",
        "max_hours": 4,
        "start_hour": 8,
        "end_hour": 18,
        "max_days_ahead": 14,
    },
    "North Campus": {
        "code": "B",
        "max_hours": 2,
        "start_hour": 9,
        "end_hour": 17,
        "max_days_ahead": 7,
    },
    "South Campus": {
        "code": "C",
        "max_hours": 6,
        "start_hour": 7,
        "end_hour": 20,
        "max_days_ahead": 30,
    },
}


def check_duration_rule(campus, duration_hours):
    """Check the booking length against the campus maximum.
    Returns a tuple: (True/False, message)."""
    if duration_hours <= 0:
        return (False, "Duration must be at least 1 hour.")
    if duration_hours > campus.get_max_hours():
        return (False, f"{campus.get_name()} allows a maximum of "
                       f"{campus.get_max_hours()} hour(s) per booking.")
    return (True, "Duration is valid.")


def check_hours_rule(campus, start_hour, duration_hours):
    """Check that the booking starts and ends inside the campus opening hours."""
    end_hour = start_hour + duration_hours
    if start_hour < campus.get_start_hour():
        return (False, f"{campus.get_name()} bookings cannot start before "
                       f"{campus.get_start_hour():02d}:00.")
    if end_hour > campus.get_end_hour():
        return (False, f"{campus.get_name()} bookings must end by "
                       f"{campus.get_end_hour():02d}:00.")
    return (True, "Booking hours are valid.")


def check_days_ahead_rule(campus, days_ahead):
    """Check that the booking is not too far into the future."""
    if days_ahead > campus.get_max_days_ahead():
        return (False, f"{campus.get_name()} only allows bookings up to "
                       f"{campus.get_max_days_ahead()} days ahead.")
    return (True, "Booking date is within the allowed range.")


def apply_campus_rules(campus, start_hour, duration_hours, days_ahead):
    """Run every rule for the campus, one after the other.
    The first rule that fails stops the booking.

    Adding a new rule is easy: write a new check_..._rule function above
    and call it here."""
    rule_results = [
        check_duration_rule(campus, duration_hours),
        check_hours_rule(campus, start_hour, duration_hours),
        check_days_ahead_rule(campus, days_ahead),
    ]
    for passed, message in rule_results:
        if not passed:
            return (False, message)
    return (True, "All campus rules passed.")
