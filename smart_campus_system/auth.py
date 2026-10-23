"""
auth.py
-------
Registration, login and the session (who is logged in right now).
"""

import hashlib
import database
from models import create_user_object
from utils import (ALL_ROLES, ROLE_OPERATOR, MIN_USERNAME_LENGTH,
                   MIN_PASSWORD_LENGTH)

# The session dictionary remembers the logged-in user while the program runs.
session = {"user": None}


def hash_password(password):
    """Turn a password into a SHA-256 hash so the real password is never stored.
    The same password always gives the same hash, so we can compare them."""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def register_user(username, password, confirm_password, role, campus_name):
    """Check the registration details and save the new user.
    Returns a tuple: (True/False, message)."""
    username = username.strip()

    # ---- Input validation ----
    if len(username) < MIN_USERNAME_LENGTH:
        return (False, f"Username must be at least {MIN_USERNAME_LENGTH} characters.")
    if " " in username:
        return (False, "Username cannot contain spaces.")
    if len(password) < MIN_PASSWORD_LENGTH:
        return (False, f"Password must be at least {MIN_PASSWORD_LENGTH} characters.")
    if password != confirm_password:
        return (False, "The two passwords do not match.")
    if role not in ALL_ROLES:
        return (False, "Please choose a role.")
    if database.get_user(username) is not None:
        return (False, "That username is already taken.")

    # A system operator works across all campuses, so no campus is stored.
    campus_id = None
    if role != ROLE_OPERATOR:
        campus_row = database.get_campus_by_name(campus_name)
        if campus_row is None:
            return (False, "Please choose your campus.")
        campus_id = campus_row[0]

    new_id = database.insert_user(username, hash_password(password), role, campus_id)
    if new_id is None:
        return (False, "Registration failed. Please try again.")
    return (True, "Registration successful. You can now log in.")


def login_user(username, password):
    """Check the username and password.
    Returns a tuple: (user object or None, message)."""
    username = username.strip()
    if username == "" or password == "":
        return (None, "Please enter your username and password.")

    user_row = database.get_user(username)
    if user_row is None:
        # Same message as a wrong password, so nobody can guess usernames
        return (None, "Incorrect username or password.")

    user = create_user_object(user_row)
    if user is None or not user.check_password(hash_password(password)):
        return (None, "Incorrect username or password.")

    session["user"] = user
    return (user, user.get_welcome_message())


def logout_user():
    """Forget the logged-in user."""
    session["user"] = None


def get_current_user():
    return session["user"]
