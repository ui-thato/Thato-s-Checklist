"""
database.py
-----------
Everything that talks to the SQLite database is in this file.
The rest of the program calls these functions and never writes SQL itself.

All queries use ? placeholders (parameterised queries) so that user input
can never break the SQL statement.
"""

import sqlite3
import os
from booking_rules import CAMPUS_POLICIES
from utils import (ROLE_LECTURER, ROLE_ADMIN, ROLE_OPERATOR, STATUS_ACTIVE,
                   STATUS_CANCELLED, times_overlap, text_to_hour)

# The database file is saved in the same folder as this file,
# so the data is kept no matter where the program is started from.
DATABASE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             "smart_campus.db")


# ====================================================================
# Connection and general helpers
# ====================================================================

def create_connection():
    """Open a connection to the database file and return it.
    Returns None if the connection fails."""
    try:
        connection = sqlite3.connect(DATABASE_FILE)
        # Make SQLite check that linked IDs (foreign keys) really exist
        connection.execute("PRAGMA foreign_keys = ON")
        return connection
    except sqlite3.Error as error:
        print("Could not connect to the database:", error)
        return None


def run_change(sql, values=()):
    """Run an INSERT, UPDATE or DELETE statement.
    Returns the id of the new row for INSERTs, True for other changes,
    or None if something went wrong."""
    connection = create_connection()
    if connection is None:
        return None
    try:
        cursor = connection.cursor()
        cursor.execute(sql, values)
        connection.commit()
        if cursor.lastrowid:
            return cursor.lastrowid
        return True
    except sqlite3.Error as error:
        print("Database error:", error)
        return None
    finally:
        connection.close()


def run_select(sql, values=()):
    """Run a SELECT statement and return a list of row tuples.
    Returns an empty list if something went wrong."""
    connection = create_connection()
    if connection is None:
        return []
    try:
        cursor = connection.cursor()
        cursor.execute(sql, values)
        return cursor.fetchall()
    except sqlite3.Error as error:
        print("Database error:", error)
        return []
    finally:
        connection.close()


# ====================================================================
# Creating the tables and starting data
# ====================================================================

def create_tables():
    """Create the four tables if they do not exist yet."""
    connection = create_connection()
    if connection is None:
        return False
    try:
        cursor = connection.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS campuses (
                campus_id          INTEGER PRIMARY KEY AUTOINCREMENT,
                campus_name        TEXT NOT NULL UNIQUE,
                campus_code        TEXT NOT NULL,
                max_booking_hours  INTEGER NOT NULL,
                allowed_start_hour INTEGER NOT NULL,
                allowed_end_hour   INTEGER NOT NULL,
                max_days_ahead     INTEGER NOT NULL
            )""")

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id   INTEGER PRIMARY KEY AUTOINCREMENT,
                username  TEXT NOT NULL UNIQUE,
                password  TEXT NOT NULL,
                role      TEXT NOT NULL,
                campus_id INTEGER,
                FOREIGN KEY (campus_id) REFERENCES campuses (campus_id)
            )""")

        # UNIQUE(resource_name, campus_id) means the same campus can
        # never have two resources with the same name.
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS resources (
                resource_id   INTEGER PRIMARY KEY AUTOINCREMENT,
                resource_name TEXT NOT NULL,
                campus_id     INTEGER NOT NULL,
                resource_type TEXT NOT NULL,
                is_available  INTEGER NOT NULL DEFAULT 1,
                UNIQUE (resource_name, campus_id),
                FOREIGN KEY (campus_id) REFERENCES campuses (campus_id)
            )""")

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bookings (
                booking_id     INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id        INTEGER NOT NULL,
                resource_id    INTEGER NOT NULL,
                campus_id      INTEGER NOT NULL,
                booking_date   TEXT NOT NULL,
                start_time     TEXT NOT NULL,
                duration_hours INTEGER NOT NULL,
                status         TEXT NOT NULL DEFAULT 'Active',
                FOREIGN KEY (user_id) REFERENCES users (user_id),
                FOREIGN KEY (resource_id) REFERENCES resources (resource_id),
                FOREIGN KEY (campus_id) REFERENCES campuses (campus_id)
            )""")

        connection.commit()
        return True
    except sqlite3.Error as error:
        print("Could not create tables:", error)
        return False
    finally:
        connection.close()


def load_campus_policies():
    """Copy the campus policies from booking_rules.py into the campuses table.
    New campuses are added and existing campuses get their rules updated,
    so booking_rules.py is the one place where rules are changed."""
    for campus_name, policy in CAMPUS_POLICIES.items():
        existing = run_select("SELECT campus_id FROM campuses WHERE campus_name = ?",
                              (campus_name,))
        values = (policy["code"], policy["max_hours"], policy["start_hour"],
                  policy["end_hour"], policy["max_days_ahead"], campus_name)
        if existing:
            run_change("""UPDATE campuses
                          SET campus_code = ?, max_booking_hours = ?,
                              allowed_start_hour = ?, allowed_end_hour = ?,
                              max_days_ahead = ?
                          WHERE campus_name = ?""", values)
        else:
            run_change("""INSERT INTO campuses (campus_code, max_booking_hours,
                              allowed_start_hour, allowed_end_hour,
                              max_days_ahead, campus_name)
                          VALUES (?, ?, ?, ?, ?, ?)""", values)


def add_sample_data(hash_function):
    """Add demo accounts and resources the first time the program runs,
    so the marker can test the system straight away.
    hash_function is passed in from auth.py so passwords are stored hashed."""
    user_count = run_select("SELECT COUNT(*) FROM users")[0][0]
    if user_count > 0:
        return  # sample data was already added on an earlier run

    main_id = get_campus_by_name("Main Campus")[0]
    north_id = get_campus_by_name("North Campus")[0]
    south_id = get_campus_by_name("South Campus")[0]

    # A list of tuples: (username, password, role, campus_id)
    sample_users = [
        ("lecturer1", "lecturer123", ROLE_LECTURER, main_id),
        ("admin_main", "admin123", ROLE_ADMIN, main_id),
        ("admin_north", "admin123", ROLE_ADMIN, north_id),
        ("admin_south", "admin123", ROLE_ADMIN, south_id),
        ("operator", "operator123", ROLE_OPERATOR, None),
    ]
    for username, password, role, campus_id in sample_users:
        insert_user(username, hash_function(password), role, campus_id)

    # A list of tuples: (resource_name, campus_id, resource_type)
    sample_resources = [
        ("Computer Lab 1", main_id, "Computer Lab"),
        ("Computer Lab 2", main_id, "Computer Lab"),
        ("Seminar Room A", main_id, "Seminar Room"),
        ("Projector P1", main_id, "Projector"),
        ("Computer Lab North", north_id, "Computer Lab"),
        ("Lecture Hall N1", north_id, "Lecture Hall"),
        ("Projector N1", north_id, "Projector"),
        ("Computer Lab South", south_id, "Computer Lab"),
        ("Seminar Room S1", south_id, "Seminar Room"),
        ("Smart Board S1", south_id, "Presentation Equipment"),
    ]
    for resource_name, campus_id, resource_type in sample_resources:
        insert_resource(resource_name, campus_id, resource_type)


def setup_database(hash_function):
    """Do every setup step. Called once from main.py."""
    if not create_tables():
        return False
    load_campus_policies()
    add_sample_data(hash_function)
    return True


# ====================================================================
# Users
# ====================================================================

def insert_user(username, password_hash, role, campus_id):
    """Save a new user. Returns the new user_id or None."""
    return run_change("""INSERT INTO users (username, password, role, campus_id)
                         VALUES (?, ?, ?, ?)""",
                      (username, password_hash, role, campus_id))


def get_user(username):
    """Find a user by username. Returns a tuple or None.
    Tuple order: (user_id, username, password, role, campus_id)"""
    rows = run_select("""SELECT user_id, username, password, role, campus_id
                         FROM users WHERE username = ?""", (username,))
    if rows:
        return rows[0]
    return None


# ====================================================================
# Campuses
# ====================================================================

CAMPUS_COLUMNS = """campus_id, campus_name, campus_code, max_booking_hours,
                    allowed_start_hour, allowed_end_hour, max_days_ahead"""


def get_all_campuses():
    """Return every campus as a list of tuples."""
    return run_select(f"SELECT {CAMPUS_COLUMNS} FROM campuses ORDER BY campus_id")


def get_campus_by_id(campus_id):
    rows = run_select(f"SELECT {CAMPUS_COLUMNS} FROM campuses WHERE campus_id = ?",
                      (campus_id,))
    if rows:
        return rows[0]
    return None


def get_campus_by_name(campus_name):
    rows = run_select(f"SELECT {CAMPUS_COLUMNS} FROM campuses WHERE campus_name = ?",
                      (campus_name,))
    if rows:
        return rows[0]
    return None


# ====================================================================
# Resources
# ====================================================================

RESOURCE_COLUMNS = "resource_id, resource_name, campus_id, resource_type, is_available"


def insert_resource(resource_name, campus_id, resource_type):
    """Save a new resource. Returns the new resource_id or None
    (None also happens if the name already exists at this campus)."""
    return run_change("""INSERT INTO resources (resource_name, campus_id, resource_type)
                         VALUES (?, ?, ?)""",
                      (resource_name, campus_id, resource_type))


def get_resources_by_campus(campus_id):
    """Return all resources for one campus as a list of tuples."""
    return run_select(f"""SELECT {RESOURCE_COLUMNS} FROM resources
                          WHERE campus_id = ? ORDER BY resource_name""",
                      (campus_id,))


def get_resource_by_id(resource_id):
    rows = run_select(f"SELECT {RESOURCE_COLUMNS} FROM resources WHERE resource_id = ?",
                      (resource_id,))
    if rows:
        return rows[0]
    return None


def update_resource(resource_id, resource_name, resource_type, is_available):
    """Change a resource's details. Returns True or None."""
    return run_change("""UPDATE resources
                         SET resource_name = ?, resource_type = ?, is_available = ?
                         WHERE resource_id = ?""",
                      (resource_name, resource_type, is_available, resource_id))


def delete_resource(resource_id):
    """Remove a resource and its old bookings. Returns True or None."""
    connection = create_connection()
    if connection is None:
        return None
    try:
        cursor = connection.cursor()
        # Bookings point at the resource, so they must be removed first
        cursor.execute("DELETE FROM bookings WHERE resource_id = ?", (resource_id,))
        cursor.execute("DELETE FROM resources WHERE resource_id = ?", (resource_id,))
        connection.commit()
        return True
    except sqlite3.Error as error:
        print("Could not delete resource:", error)
        return None
    finally:
        connection.close()


# ====================================================================
# Bookings
# ====================================================================

# Every booking query returns the same columns in this order, joined with
# the user, resource and campus names so the GUI can show readable text.
BOOKING_SELECT = """
    SELECT b.booking_id, u.username, r.resource_name, c.campus_name,
           b.booking_date, b.start_time, b.duration_hours, b.status,
           b.user_id, b.resource_id, b.campus_id, r.resource_type
    FROM bookings b
    JOIN users u ON b.user_id = u.user_id
    JOIN resources r ON b.resource_id = r.resource_id
    JOIN campuses c ON b.campus_id = c.campus_id
"""
BOOKING_ORDER = " ORDER BY b.booking_date DESC, b.start_time DESC"


def insert_booking(user_id, resource_id, campus_id, booking_date, start_time,
                   duration_hours):
    """Save a new booking. Returns the new booking_id or None."""
    return run_change("""INSERT INTO bookings (user_id, resource_id, campus_id,
                             booking_date, start_time, duration_hours, status)
                         VALUES (?, ?, ?, ?, ?, ?, ?)""",
                      (user_id, resource_id, campus_id, booking_date,
                       start_time, duration_hours, STATUS_ACTIVE))


def get_bookings_by_user(user_id):
    return run_select(BOOKING_SELECT + " WHERE b.user_id = ?" + BOOKING_ORDER,
                      (user_id,))


def get_bookings_by_campus(campus_id):
    return run_select(BOOKING_SELECT + " WHERE b.campus_id = ?" + BOOKING_ORDER,
                      (campus_id,))


def get_all_bookings():
    return run_select(BOOKING_SELECT + BOOKING_ORDER)


def get_active_bookings_for_resource(resource_id, booking_date):
    """Return the active bookings for one resource on one date."""
    return run_select(BOOKING_SELECT +
                      """ WHERE b.resource_id = ? AND b.booking_date = ?
                          AND b.status = ? ORDER BY b.start_time""",
                      (resource_id, booking_date, STATUS_ACTIVE))


def get_booking_by_id(booking_id):
    rows = run_select(BOOKING_SELECT + " WHERE b.booking_id = ?", (booking_id,))
    if rows:
        return rows[0]
    return None


def check_booking_conflict(resource_id, booking_date, start_hour, duration_hours):
    """Return True if the new time slot overlaps an existing active booking
    for the same resource on the same day."""
    existing_bookings = get_active_bookings_for_resource(resource_id, booking_date)
    for booking in existing_bookings:
        existing_start = text_to_hour(booking[5])
        existing_duration = booking[6]
        if times_overlap(start_hour, duration_hours, existing_start, existing_duration):
            return True
    return False


def cancel_booking(booking_id):
    """Mark a booking as cancelled (we keep it for the history)."""
    return run_change("UPDATE bookings SET status = ? WHERE booking_id = ?",
                      (STATUS_CANCELLED, booking_id))


# ====================================================================
# Reports
# ====================================================================

def get_campus_statistics(campus_id):
    """Work out the report numbers for one campus.
    Returns a dictionary so the GUI can look values up by name."""
    statistics = {}

    # Total, active and cancelled bookings
    statistics["total_bookings"] = run_select(
        "SELECT COUNT(*) FROM bookings WHERE campus_id = ?", (campus_id,))[0][0]
    statistics["cancelled_bookings"] = run_select(
        "SELECT COUNT(*) FROM bookings WHERE campus_id = ? AND status = ?",
        (campus_id, STATUS_CANCELLED))[0][0]
    statistics["active_bookings"] = (statistics["total_bookings"]
                                     - statistics["cancelled_bookings"])

    # Average and total duration (cancelled bookings are not counted as usage)
    duration_row = run_select(
        """SELECT AVG(duration_hours), SUM(duration_hours) FROM bookings
           WHERE campus_id = ? AND status = ?""",
        (campus_id, STATUS_ACTIVE))[0]
    statistics["average_duration"] = duration_row[0] or 0
    statistics["total_hours"] = duration_row[1] or 0

    # How many times each resource was booked, most used first.
    # LEFT JOIN keeps resources that were never booked (count 0).
    statistics["resource_usage"] = run_select(
        """SELECT r.resource_name, COUNT(b.booking_id), COALESCE(SUM(b.duration_hours), 0)
           FROM resources r
           LEFT JOIN bookings b ON r.resource_id = b.resource_id AND b.status = ?
           WHERE r.campus_id = ?
           GROUP BY r.resource_id
           ORDER BY COUNT(b.booking_id) DESC, r.resource_name""",
        (STATUS_ACTIVE, campus_id))

    # Bookings that used the full maximum time allowed by the campus rule
    statistics["max_length_bookings"] = run_select(
        """SELECT COUNT(*) FROM bookings b
           JOIN campuses c ON b.campus_id = c.campus_id
           WHERE b.campus_id = ? AND b.status = ?
           AND b.duration_hours = c.max_booking_hours""",
        (campus_id, STATUS_ACTIVE))[0][0]

    # Usage per resource type, e.g. Computer Lab: 5 bookings
    statistics["type_usage"] = run_select(
        """SELECT r.resource_type, COUNT(*) FROM bookings b
           JOIN resources r ON b.resource_id = r.resource_id
           WHERE b.campus_id = ? AND b.status = ?
           GROUP BY r.resource_type ORDER BY COUNT(*) DESC""",
        (campus_id, STATUS_ACTIVE))

    # The start time that is booked the most
    busiest = run_select(
        """SELECT start_time, COUNT(*) FROM bookings
           WHERE campus_id = ? AND status = ?
           GROUP BY start_time ORDER BY COUNT(*) DESC LIMIT 1""",
        (campus_id, STATUS_ACTIVE))
    if busiest:
        statistics["busiest_start_time"] = busiest[0][0]
    else:
        statistics["busiest_start_time"] = "None yet"

    # Resource availability counts
    statistics["resource_count"] = run_select(
        "SELECT COUNT(*) FROM resources WHERE campus_id = ?", (campus_id,))[0][0]
    statistics["available_count"] = run_select(
        "SELECT COUNT(*) FROM resources WHERE campus_id = ? AND is_available = 1",
        (campus_id,))[0][0]

    return statistics
