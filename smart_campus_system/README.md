# Smart Campus Resource Booking System

Programming 512 assignment for Richfield Graduate Institute of Technology. It's written in Python and uses only the standard library (`tkinter`, `sqlite3`, `hashlib`, `datetime`, `os`).

## How to run

1. Install Python 3.8 or newer from python.org. On Windows, Tkinter is included automatically. On Linux you may need `sudo apt install python3-tk`.
2. Open a terminal in the `smart_campus_system` folder.
3. Run:

   ```
   python main.py
   ```

The first time it runs, the program creates `smart_campus.db` and adds the three campuses, some sample resources and these demo accounts:

| Username      | Password      | Role                 | Campus        |
|---------------|---------------|----------------------|---------------|
| `lecturer1`   | `lecturer123` | Lecturer             | Main Campus   |
| `admin_main`  | `admin123`    | Campus Administrator | Main Campus   |
| `admin_north` | `admin123`    | Campus Administrator | North Campus  |
| `admin_south` | `admin123`    | Campus Administrator | South Campus  |
| `operator`    | `operator123` | System Operator      | All campuses  |

You can also register new accounts from the login screen. To start again with an empty system, delete `smart_campus.db`.

## Project structure

```
smart_campus_system/
├── main.py                 starts the program and switches between screens
├── database.py             every SQLite query (tables, users, resources, bookings, reports)
├── models.py               classes: User -> Lecturer / CampusAdmin / SystemOperator,
│                           Campus, Resource, Booking
├── auth.py                 register, login, password hashing, session
├── booking_rules.py        campus policies (dictionary) and the rule functions
├── utils.py                constants, input parsing, time-overlap check, GUI helpers
└── gui/
    ├── login_window.py     LoginWindow and RegisterWindow
    ├── lecturer_dashboard.py
    ├── admin_dashboard.py
    └── operator_dashboard.py
```

## Campus booking policies

| Campus       | Max per booking | Allowed hours | Book ahead |
|--------------|-----------------|---------------|------------|
| Main Campus  | 4 hours         | 08:00–18:00   | 14 days    |
| North Campus | 2 hours         | 09:00–17:00   | 7 days     |
| South Campus | 6 hours         | 07:00–20:00   | 30 days    |

To add a campus, add one entry to `CAMPUS_POLICIES` in `booking_rules.py` and restart the program. To add a new kind of rule, write a `check_..._rule()` function and add it to the list in `apply_campus_rules()`.

## Key design decisions

- **The rules are kept apart from the logic.** Campus policies live in a single dictionary in `booking_rules.py`. The database copies them into the `campuses` table at startup, so the booking code never hard-codes a campus.
- **Inheritance and polymorphism.** `create_user_object()` builds the correct subclass from the role stored in the database. `main.py` then uses a dictionary of `{role: DashboardClass}` to open the right screen.
- **Encapsulation.** All attributes are private (`__name`) and accessed through `get_...()` methods. The password hash can only be compared, never read.
- **Duplicates are blocked twice.** A Python `set` of lower-case names catches "Lab 1" vs "lab 1", and the database has `UNIQUE(resource_name, campus_id)` as a backup.
- **Overlap rule.** Two slots overlap when each starts before the other ends (`utils.times_overlap`). Back-to-back bookings, such as 09–11 followed by 11–12, are allowed.
- **Cancelled bookings are kept** with status `Cancelled`, so the history and reports stay accurate.
- **All SQL uses `?` placeholders** and every database call is wrapped in `try/except`.

## Testing checklist

| Test | How to check |
|------|--------------|
| Register each user type | Register screen, choose each role |
| Login with correct and incorrect credentials | `lecturer1` / `lecturer123`, then a wrong password |
| Lecturer views resources for a campus | Select a campus, click **Use this campus** |
| Create a valid booking | Select resource, tomorrow, 09:00, 2 hours |
| Overlapping booking blocked | Same resource, 10:00, 1 hour |
| Duration limit enforced | North Campus, 3 hours |
| Admin adds a resource / duplicate rejected | `admin_main`, add "Projector P2", then "computer lab 1" |
| Admin deletes a resource | Select it, then **Remove selected** |
| Admin views campus bookings and report | Right-hand side of the admin dashboard |
| Operator views all campus statistics | Log in as `operator`, **Compare campuses** |
| Data persists | Close the program, run it again, and log in |

Saved reports go to the `reports/` folder.
