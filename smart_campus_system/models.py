"""
models.py
---------
The classes for the system.

    User  (parent class)
      |-- Lecturer        books resources
      |-- CampusAdmin     manages resources at one campus
      |-- SystemOperator  sees every campus and compares them

    Campus    holds one campus and its booking policy
    Resource  holds one bookable resource
    Booking   holds one booking and knows how to check itself

Attributes that start with two underscores (for example __password_hash)
are private. Other code has to use the get_ methods to read them. This is
encapsulation.
"""

import database
from booking_rules import apply_campus_rules
from utils import (ROLE_LECTURER, ROLE_ADMIN, ROLE_OPERATOR, STATUS_ACTIVE,
                   STATUS_CANCELLED, MAX_RESOURCE_NAME_LENGTH, RESOURCE_TYPES,
                   parse_date, parse_start_hour, parse_duration, hour_to_text,
                   text_to_hour, today, current_hour, is_future_booking,
                   is_happening_now, times_overlap)


# ====================================================================
# Campus
# ====================================================================

class Campus:
    """One campus and the booking policy that applies there."""

    def __init__(self, campus_id, name, code, max_hours, start_hour, end_hour,
                 max_days_ahead):
        self.__campus_id = campus_id
        self.__name = name
        self.__code = code
        self.__max_hours = max_hours
        self.__start_hour = start_hour
        self.__end_hour = end_hour
        self.__max_days_ahead = max_days_ahead

    def get_id(self):
        return self.__campus_id

    def get_name(self):
        return self.__name

    def get_code(self):
        return self.__code

    def get_max_hours(self):
        return self.__max_hours

    def get_start_hour(self):
        return self.__start_hour

    def get_end_hour(self):
        return self.__end_hour

    def get_max_days_ahead(self):
        return self.__max_days_ahead

    def get_policy_text(self):
        """Return the booking policy as a sentence for the GUI."""
        return (f"{self.__name} policy: max {self.__max_hours} hour(s) per booking, "
                f"between {hour_to_text(self.__start_hour)} and "
                f"{hour_to_text(self.__end_hour)}, up to "
                f"{self.__max_days_ahead} days ahead.")

    def __str__(self):
        return f"{self.__name} (Campus {self.__code})"


def campus_from_row(row):
    """Build a Campus object from a database row tuple."""
    if row is None:
        return None
    return Campus(row[0], row[1], row[2], row[3], row[4], row[5], row[6])


def load_campuses():
    """Return a dictionary of every campus: {campus_name: Campus object}."""
    campuses = {}
    for row in database.get_all_campuses():
        campus = campus_from_row(row)
        campuses[campus.get_name()] = campus
    return campuses


# ====================================================================
# Resource
# ====================================================================

class Resource:
    """One bookable resource, such as a lab or a projector."""

    def __init__(self, resource_id, name, campus_id, resource_type, is_available):
        self.__resource_id = resource_id
        self.__name = name
        self.__campus_id = campus_id
        self.__resource_type = resource_type
        # Stored as 1 or 0 in SQLite, so turn it into True or False
        self.__is_available = bool(is_available)

    def get_id(self):
        return self.__resource_id

    def get_name(self):
        return self.__name

    def get_campus_id(self):
        return self.__campus_id

    def get_type(self):
        return self.__resource_type

    def is_available(self):
        return self.__is_available

    def is_booked_now(self):
        """Return True if somebody is using the resource at this moment."""
        bookings_today = database.get_active_bookings_for_resource(
            self.__resource_id, today().strftime("%Y-%m-%d"))
        for booking in bookings_today:
            if is_happening_now(booking[4], booking[5], booking[6]):
                return True
        return False

    def get_status_text(self):
        """Real-time status shown in the resource lists."""
        if not self.__is_available:
            return "Unavailable"
        if self.is_booked_now():
            return "In use now"
        return "Available"

    def get_display_text(self):
        """One line of text for a Listbox. The widths keep columns lined up."""
        return (f"ID {self.__resource_id:<4} {self.__name:<22} "
                f"{self.__resource_type:<22} {self.get_status_text()}")


def resource_from_row(row):
    if row is None:
        return None
    return Resource(row[0], row[1], row[2], row[3], row[4])


def load_resources(campus_id):
    """Return a list of Resource objects for one campus."""
    resources = []
    for row in database.get_resources_by_campus(campus_id):
        resources.append(resource_from_row(row))
    return resources


# ====================================================================
# Booking
# ====================================================================

class Booking:
    """One booking of a resource by a lecturer."""

    def __init__(self, booking_id, user_id, resource_id, campus_id, booking_date,
                 start_time, duration_hours, status=STATUS_ACTIVE,
                 username="", resource_name="", campus_name=""):
        self.__booking_id = booking_id
        self.__user_id = user_id
        self.__resource_id = resource_id
        self.__campus_id = campus_id
        self.__booking_date = booking_date      # text, e.g. "2026-10-23"
        self.__start_time = start_time          # text, e.g. "09:00"
        self.__duration_hours = duration_hours  # whole number of hours
        self.__status = status
        # These three are only for display
        self.__username = username
        self.__resource_name = resource_name
        self.__campus_name = campus_name

    def get_id(self):
        return self.__booking_id

    def get_status(self):
        return self.__status

    def get_duration(self):
        return self.__duration_hours

    def get_end_time(self):
        return hour_to_text(text_to_hour(self.__start_time) + self.__duration_hours)

    def is_future(self):
        """True if the booking is active and has not started yet."""
        return (self.__status == STATUS_ACTIVE and
                is_future_booking(self.__booking_date, self.__start_time))

    def get_status_text(self):
        """A friendlier status than the one stored in the database."""
        if self.__status == STATUS_CANCELLED:
            return "Cancelled"
        if self.is_future():
            return "Upcoming"
        if is_happening_now(self.__booking_date, self.__start_time,
                            self.__duration_hours):
            return "In progress"
        return "Completed"

    def get_display_text(self, show_user=False):
        """One line of text for a Listbox."""
        text = (f"#{self.__booking_id:<4} {self.__booking_date} "
                f"{self.__start_time}-{self.get_end_time()} "
                f"{self.__resource_name:<22} {self.__campus_name:<13}")
        if show_user:
            text = text + f" {self.__username:<12}"
        return text + f" {self.get_status_text()}"

    def validate(self, campus, resource):
        """Check the booking before it is saved.
        Returns a tuple: (True/False, message)."""
        booking_date = parse_date(self.__booking_date)
        start_hour = text_to_hour(self.__start_time)

        # 1. The resource must be switched on by the administrator
        if not resource.is_available():
            return (False, f"{resource.get_name()} is currently unavailable.")

        # 2. No bookings in the past
        if booking_date < today():
            return (False, "You cannot book a date in the past.")
        if booking_date == today() and start_hour <= current_hour():
            return (False, "That time has already started or passed today.")

        # 3. The campus rules (these live in booking_rules.py)
        days_ahead = (booking_date - today()).days
        passed, message = apply_campus_rules(campus, start_hour,
                                             self.__duration_hours, days_ahead)
        if not passed:
            return (False, message)

        # 4. No overlap with another booking for the same resource
        if database.check_booking_conflict(self.__resource_id, self.__booking_date,
                                           start_hour, self.__duration_hours):
            return (False, f"{resource.get_name()} is already booked during that "
                           "time. Please choose another time.")

        # 5. The lecturer cannot be in two places at once
        for row in database.get_bookings_by_user(self.__user_id):
            if row[4] == self.__booking_date and row[7] == STATUS_ACTIVE:
                if times_overlap(start_hour, self.__duration_hours,
                                 text_to_hour(row[5]), row[6]):
                    return (False, f"You already have {row[2]} booked at that time.")

        return (True, "Booking is valid.")

    def save(self):
        """Store the booking in the database. Returns True or False."""
        new_id = database.insert_booking(self.__user_id, self.__resource_id,
                                         self.__campus_id, self.__booking_date,
                                         self.__start_time, self.__duration_hours)
        if new_id is None:
            return False
        self.__booking_id = new_id
        return True


def booking_from_row(row):
    """Build a Booking from a row returned by database.BOOKING_SELECT."""
    return Booking(booking_id=row[0], user_id=row[8], resource_id=row[9],
                   campus_id=row[10], booking_date=row[4], start_time=row[5],
                   duration_hours=row[6], status=row[7], username=row[1],
                   resource_name=row[2], campus_name=row[3])


def bookings_from_rows(rows):
    bookings = []
    for row in rows:
        bookings.append(booking_from_row(row))
    return bookings


# ====================================================================
# Users
# ====================================================================

class User:
    """The parent class for every kind of user."""

    def __init__(self, user_id, username, password_hash, role, campus_id):
        self.__user_id = user_id
        self.__username = username
        self.__password_hash = password_hash   # private: never shown anywhere
        self.__role = role
        self.__campus_id = campus_id

    def get_id(self):
        return self.__user_id

    def get_username(self):
        return self.__username

    def get_role(self):
        return self.__role

    def get_campus_id(self):
        return self.__campus_id

    def check_password(self, password_hash):
        """Compare a hashed password with the stored one."""
        return self.__password_hash == password_hash

    def get_home_campus_name(self):
        campus = campus_from_row(database.get_campus_by_id(self.__campus_id))
        if campus is None:
            return "All campuses"
        return campus.get_name()

    def get_permissions(self):
        """What this user may do. Each child class overrides this."""
        return ["Log in", "Log out"]

    def get_welcome_message(self):
        return f"Welcome, {self.__username} ({self.__role})"


class Lecturer(User):
    """A lecturer books resources for classes and presentations."""

    def __init__(self, user_id, username, password_hash, campus_id):
        # Call the parent class __init__ to set the shared attributes
        super().__init__(user_id, username, password_hash, ROLE_LECTURER, campus_id)

    def get_permissions(self):
        # Method overriding (polymorphism): a lecturer gets extra permissions
        return super().get_permissions() + ["Select a campus", "View resources",
                                            "Book resources", "Cancel own bookings",
                                            "View own booking history"]

    def book_resource(self, campus, resource, date_text, time_text, duration_text):
        """Try to book a resource. Returns a tuple: (True/False, message)."""
        # Check the typed input first
        if parse_date(date_text) is None:
            return (False, "Please enter the date as YYYY-MM-DD, e.g. 2026-11-05.")
        start_hour = parse_start_hour(time_text)
        if start_hour is None:
            return (False, "Please enter the start time on the hour, e.g. 09:00.")
        duration = parse_duration(duration_text)
        if duration is None:
            return (False, "Duration must be a whole number of hours, e.g. 2.")

        booking = Booking(None, self.get_id(), resource.get_id(), campus.get_id(),
                          date_text.strip(), hour_to_text(start_hour), duration)
        is_valid, message = booking.validate(campus, resource)
        if not is_valid:
            return (False, message)

        if booking.save():
            return (True, f"{resource.get_name()} booked on {date_text.strip()} from "
                          f"{hour_to_text(start_hour)} to {booking.get_end_time()}.")
        return (False, "The booking could not be saved. Please try again.")

    def get_my_bookings(self):
        """Return this lecturer's bookings as a list of Booking objects."""
        return bookings_from_rows(database.get_bookings_by_user(self.get_id()))

    def cancel_booking(self, booking):
        """Cancel one of this lecturer's future bookings."""
        if not booking.is_future():
            return (False, "Only upcoming bookings can be cancelled.")
        if database.cancel_booking(booking.get_id()):
            return (True, "The booking was cancelled.")
        return (False, "The booking could not be cancelled.")


class CampusAdmin(User):
    """A campus administrator manages the resources at their own campus."""

    def __init__(self, user_id, username, password_hash, campus_id):
        super().__init__(user_id, username, password_hash, ROLE_ADMIN, campus_id)

    def get_permissions(self):
        return super().get_permissions() + ["Add resources", "Update resources",
                                            "Remove resources",
                                            "View campus bookings",
                                            "View campus reports"]

    def __check_resource_details(self, name, resource_type, ignore_resource_id=None):
        """Private helper used by add and update. Returns (True/False, message)."""
        if name == "":
            return (False, "Please enter a resource name.")
        if len(name) > MAX_RESOURCE_NAME_LENGTH:
            return (False, f"The name must be {MAX_RESOURCE_NAME_LENGTH} "
                           "characters or less.")
        if resource_type not in RESOURCE_TYPES:
            return (False, "Please choose a resource type from the list.")

        # Build a SET of existing names (lower case) so "lab 1" and "Lab 1"
        # are treated as the same name. Sets make this check quick.
        existing_names = set()
        for resource in load_resources(self.get_campus_id()):
            if resource.get_id() != ignore_resource_id:
                existing_names.add(resource.get_name().lower())
        if name.lower() in existing_names:
            return (False, f"A resource called '{name}' already exists at this campus.")
        return (True, "Details are valid.")

    def add_resource(self, name, resource_type):
        name = name.strip()
        is_valid, message = self.__check_resource_details(name, resource_type)
        if not is_valid:
            return (False, message)
        new_id = database.insert_resource(name, self.get_campus_id(), resource_type)
        if new_id is None:
            return (False, "The resource could not be saved.")
        return (True, f"'{name}' was added with resource ID {new_id}.")

    def update_resource(self, resource, name, resource_type, is_available):
        name = name.strip()
        is_valid, message = self.__check_resource_details(name, resource_type,
                                                          resource.get_id())
        if not is_valid:
            return (False, message)
        if database.update_resource(resource.get_id(), name, resource_type,
                                    int(is_available)):
            return (True, f"Resource ID {resource.get_id()} was updated.")
        return (False, "The resource could not be updated.")

    def remove_resource(self, resource):
        # Do not remove a resource that lecturers are still counting on
        for row in database.get_bookings_by_campus(self.get_campus_id()):
            booking = booking_from_row(row)
            if row[9] == resource.get_id() and booking.is_future():
                return (False, f"{resource.get_name()} has upcoming bookings. "
                               "Mark it as unavailable instead, or wait until "
                               "the bookings are finished.")
        if database.delete_resource(resource.get_id()):
            return (True, f"'{resource.get_name()}' was removed.")
        return (False, "The resource could not be removed.")

    def get_campus_bookings(self):
        return bookings_from_rows(database.get_bookings_by_campus(self.get_campus_id()))

    def get_campus_report(self):
        campus = campus_from_row(database.get_campus_by_id(self.get_campus_id()))
        statistics = database.get_campus_statistics(campus.get_id())
        return build_campus_report(campus, statistics)


class SystemOperator(User):
    """A system operator can see every campus and compare them."""

    def __init__(self, user_id, username, password_hash, campus_id=None):
        super().__init__(user_id, username, password_hash, ROLE_OPERATOR, campus_id)

    def get_permissions(self):
        return super().get_permissions() + ["View all campuses", "View all bookings",
                                            "Generate comparison reports",
                                            "Save reports to a file"]

    def get_bookings(self, campus=None):
        """All bookings, or only one campus if a campus is given."""
        if campus is None:
            return bookings_from_rows(database.get_all_bookings())
        return bookings_from_rows(database.get_bookings_by_campus(campus.get_id()))

    def get_campus_report(self, campus):
        return build_campus_report(campus, database.get_campus_statistics(campus.get_id()))

    def get_comparison_report(self):
        """Compare every campus side by side and explain the differences."""
        campuses = load_campuses()
        all_statistics = {}
        for campus_name, campus in campuses.items():
            all_statistics[campus_name] = database.get_campus_statistics(campus.get_id())

        lines = ["CROSS-CAMPUS COMPARISON REPORT",
                 f"Generated on {today()}", "=" * 60, ""]

        lines.append("1. Booking totals and rules per campus")
        for campus_name, campus in campuses.items():
            stats = all_statistics[campus_name]
            lines.append(f"   {campus_name}: {stats['active_bookings']} active bookings, "
                         f"{stats['cancelled_bookings']} cancelled, "
                         f"{stats['total_hours']} hours booked")
            lines.append(f"      Rule: max {campus.get_max_hours()} h, "
                         f"{hour_to_text(campus.get_start_hour())}-"
                         f"{hour_to_text(campus.get_end_hour())}")
            lines.append(f"      Average booking: {stats['average_duration']:.1f} h, "
                         f"bookings at the maximum length: "
                         f"{stats['max_length_bookings']}")
            lines.append(f"      Busiest start time: {stats['busiest_start_time']}")
        lines.append("")

        # Find the busiest campus with a simple loop
        busiest_campus = ""
        highest_count = -1
        for campus_name in all_statistics:
            count = all_statistics[campus_name]["active_bookings"]
            if count > highest_count:
                highest_count = count
                busiest_campus = campus_name
        lines.append(f"2. Busiest campus: {busiest_campus} ({highest_count} bookings)")
        lines.append("")

        lines.append("3. Resource usage")
        for campus_name in all_statistics:
            stats = all_statistics[campus_name]
            lines.append(f"   {campus_name}: {stats['available_count']} of "
                         f"{stats['resource_count']} resources available")
            for resource_name, count, hours in stats["resource_usage"]:
                lines.append(f"      {resource_name:<24} {count} booking(s), {hours} h")
        lines.append("")

        # Use SETS to compare which resource types each campus has
        lines.append("4. Resource types across campuses")
        type_sets = {}
        for campus_name, campus in campuses.items():
            campus_types = set()
            for resource in load_resources(campus.get_id()):
                campus_types.add(resource.get_type())
            type_sets[campus_name] = campus_types

        every_type = set()
        common_types = None
        for campus_types in type_sets.values():
            every_type = every_type.union(campus_types)
            if common_types is None:
                common_types = campus_types
            else:
                common_types = common_types.intersection(campus_types)
        if common_types is None:
            common_types = set()
        lines.append("   Types offered somewhere: " + ", ".join(sorted(every_type)))
        lines.append("   Types offered at every campus: " +
                     (", ".join(sorted(common_types)) or "none"))
        for campus_name in type_sets:
            missing = every_type.difference(type_sets[campus_name])
            if missing:
                lines.append(f"   {campus_name} does not have: " +
                             ", ".join(sorted(missing)))
        lines.append("")

        lines.append("5. What the campus rules seem to cause")
        for campus_name, campus in campuses.items():
            stats = all_statistics[campus_name]
            if stats["active_bookings"] == 0:
                lines.append(f"   {campus_name}: no bookings yet, so no pattern.")
            elif stats["max_length_bookings"] * 2 >= stats["active_bookings"]:
                lines.append(f"   {campus_name}: at least half the bookings use the full "
                             f"{campus.get_max_hours()} h limit, so the limit may be "
                             "too short for lecturers.")
            else:
                lines.append(f"   {campus_name}: most bookings are shorter than the "
                             f"{campus.get_max_hours()} h limit, so the rule suits users.")
        return "\n".join(lines)

    def save_report_to_file(self, report_text, file_name):
        """Write a report to a text file. Returns (True/False, message)."""
        try:
            report_file = open(file_name, "w")
            report_file.write(report_text)
            report_file.close()
            return (True, f"Report saved to {file_name}")
        except OSError as error:
            return (False, f"Could not save the report: {error}")


def build_campus_report(campus, statistics):
    """Turn the statistics dictionary into readable report text."""
    lines = [f"CAMPUS REPORT: {campus.get_name()}",
             f"Generated on {today()}", "=" * 60,
             campus.get_policy_text(), "",
             f"Total bookings made:      {statistics['total_bookings']}",
             f"Active bookings:          {statistics['active_bookings']}",
             f"Cancelled bookings:       {statistics['cancelled_bookings']}",
             f"Total hours booked:       {statistics['total_hours']}",
             f"Average booking duration: {statistics['average_duration']:.1f} hours",
             f"Busiest start time:       {statistics['busiest_start_time']}",
             f"Resources available now:  {statistics['available_count']} of "
             f"{statistics['resource_count']}", ""]

    usage = statistics["resource_usage"]
    if usage and usage[0][1] > 0:
        lines.append(f"Most frequently used resource: {usage[0][0]} "
                     f"({usage[0][1]} bookings)")
    else:
        lines.append("Most frequently used resource: no bookings yet")
    lines.append("")
    lines.append("Usage per resource (most used first):")
    for resource_name, count, hours in usage:
        lines.append(f"   {resource_name:<24} {count} booking(s), {hours} hour(s)")
    lines.append("")
    lines.append("Usage per resource type:")
    if not statistics["type_usage"]:
        lines.append("   No bookings yet")
    for resource_type, count in statistics["type_usage"]:
        lines.append(f"   {resource_type:<24} {count} booking(s)")
    return "\n".join(lines)


def create_user_object(user_row):
    """Turn a database row into the right kind of user object.
    The GUI then treats every user the same way (polymorphism)."""
    user_id, username, password_hash, role, campus_id = user_row
    if role == ROLE_LECTURER:
        return Lecturer(user_id, username, password_hash, campus_id)
    elif role == ROLE_ADMIN:
        return CampusAdmin(user_id, username, password_hash, campus_id)
    elif role == ROLE_OPERATOR:
        return SystemOperator(user_id, username, password_hash, campus_id)
    return None
