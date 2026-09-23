from flask import Flask, request, redirect, url_for, render_template_string, flash
import sqlite3
import os
import webbrowser
import threading
from datetime import date
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import io
import base64

app = Flask(__name__)
app.secret_key = "campusfix-secret-key"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(DATA_DIR, "campus.db")

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(os.path.join(BASE_DIR, "reports"), exist_ok=True)


# ---------------- DATABASE ----------------

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS complaints (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            complaint_id TEXT UNIQUE NOT NULL,
            student_name TEXT NOT NULL,
            department TEXT NOT NULL,
            building TEXT NOT NULL,
            room_no TEXT NOT NULL,
            category TEXT NOT NULL,
            problem TEXT NOT NULL,
            priority TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Pending',
            date TEXT NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS maintenance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            complaint_id TEXT NOT NULL,
            staff_name TEXT NOT NULL,
            repair_date TEXT NOT NULL,
            cost REAL NOT NULL,
            remarks TEXT
        )
    """)

    conn.commit()
    conn.close()


def next_complaint_id():
    conn = get_db()
    row = conn.execute(
        "SELECT complaint_id FROM complaints ORDER BY id DESC LIMIT 1"
    ).fetchone()
    conn.close()

    if row is None:
        return "CMP001"

    number = int(row["complaint_id"].replace("CMP", ""))
    return f"CMP{number + 1:03d}"


# ---------------- DATA ----------------

CATEGORIES = [
    "Electrical",
    "Furniture",
    "Plumbing",
    "IT",
    "Internet",
    "Cleaning",
    "AC/Cooling",
    "Other"
]

STATUSES = ["Pending", "In Progress", "Resolved"]

PRIORITIES = ["Low", "Medium", "High"]

BUILDINGS = [
    "Block A",
    "Block B",
    "Block C",
    "Computer Lab",
    "Library",
    "Hostel Block"
]

DEPARTMENTS = [
    "BCA",
    "B.Tech",
    "MCA",
    "MBA",
    "BBA",
    "Other"
]


# ---------------- CHART ----------------

def chart_image(kind):
    conn = get_db()

    complaints = pd.read_sql_query(
        "SELECT * FROM complaints",
        conn
    )

    maintenance = pd.read_sql_query(
        "SELECT * FROM maintenance",
        conn
    )

    conn.close()

    if complaints.empty:
        return None

    plt.figure(figsize=(8, 4.5))

    if kind == "category":
        data = complaints["category"].value_counts()
        data = data.reindex(CATEGORIES, fill_value=0)
        plt.bar(data.index, data.values)
        plt.title("COMPLAINTS BY CATEGORY")
        plt.xticks(rotation=30, ha="right")
        plt.ylabel("Complaints")

    elif kind == "status":
        data = complaints["status"].value_counts()
        data = data.reindex(STATUSES, fill_value=0)
        plt.pie(
            data.values,
            labels=data.index,
            autopct="%1.0f%%",
            startangle=90
        )
        plt.title("STATUS DISTRIBUTION")

    elif kind == "building":
        data = complaints["building"].value_counts()
        plt.bar(data.index, data.values)
        plt.title("COMPLAINTS BY BUILDING")
        plt.xticks(rotation=30, ha="right")
        plt.ylabel("Complaints")

    elif kind == "month":
        complaints["date"] = pd.to_datetime(
            complaints["date"],
            errors="coerce"
        )
        data = (
            complaints
            .dropna(subset=["date"])
            .groupby(complaints["date"].dt.to_period("M"))
            .size()
        )

        if data.empty:
            return None

        x = data.index.astype(str)
        plt.plot(x, data.values, marker="o")
        plt.title("COMPLAINTS REPORTED PER MONTH")
        plt.xticks(rotation=30)
        plt.ylabel("Complaints")

    elif kind == "cost":
        if maintenance.empty:
            return None

        merged = maintenance.merge(
            complaints[["complaint_id", "category"]],
            on="complaint_id",
            how="left"
        )

        data = merged.groupby("category")["cost"].sum()
        data = data.reindex(CATEGORIES, fill_value=0)

        plt.bar(data.index, data.values)
        plt.title("REPAIR COST BY CATEGORY")
        plt.xticks(rotation=30, ha="right")
        plt.ylabel("Cost (₹)")

    plt.tight_layout()

    output = io.BytesIO()
    plt.savefig(output, format="png", dpi=120)
    plt.close()

    output.seek(0)
    return base64.b64encode(output.read()).decode("utf-8")


# ---------------- STYLE ----------------

STYLE = """
<style>
* {
    box-sizing: border-box;
}

body {
    margin: 0;
    background: #09182b;
    color: #e9f1f7;
    font-family: Arial, Helvetica, sans-serif;
}

.navbar {
    height: 86px;
    border-bottom: 1px solid #29435e;
    display: flex;
    align-items: center;
    padding: 0 7%;
    gap: 35px;
}

.logo {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-right: auto;
}

.logo-box {
    width: 43px;
    height: 43px;
    border-radius: 7px;
    background: #66cce8;
    color: #092039;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: bold;
    font-size: 18px;
}

.logo-name {
    font-size: 22px;
    font-weight: bold;
}

.logo-sub {
    font-size: 8px;
    letter-spacing: 2px;
    color: #91a7b9;
}

.nav {
    display: flex;
    gap: 34px;
}

.nav a {
    color: #a8bbcc;
    text-decoration: none;
    font-weight: bold;
    padding: 13px 17px;
    border-radius: 25px;
}

.nav a:hover,
.nav a.active {
    background: #64c9e5;
    color: #10233a;
}

.report-btn {
    background: #f4ad42;
    color: #18263a;
    padding: 15px 23px;
    border-radius: 8px;
    text-decoration: none;
    font-weight: bold;
}

.container {
    width: 88%;
    max-width: 1400px;
    margin: 45px auto;
}

h1 {
    font-size: 38px;
    margin: 0 0 8px;
    letter-spacing: 1px;
}

.subtitle {
    color: #91aec2;
    margin-bottom: 35px;
    font-size: 17px;
}

.card {
    background: #f2efe3;
    color: #182536;
    border-radius: 18px;
    padding: 38px;
}

.form-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 24px;
}

.field label {
    display: block;
    font-size: 12px;
    font-weight: bold;
    margin-bottom: 8px;
    color: #48525c;
}

input, select, textarea {
    width: 100%;
    padding: 14px;
    border: 1px solid #c7c6bd;
    border-radius: 8px;
    background: #faf9f4;
    font-size: 15px;
}

textarea {
    min-height: 110px;
    resize: vertical;
}

.full {
    grid-column: 1 / -1;
}

.submit-row {
    margin-top: 28px;
    display: flex;
    align-items: center;
    gap: 18px;
}

.primary {
    border: 0;
    background: #10243b;
    color: white;
    padding: 15px 28px;
    border-radius: 9px;
    font-size: 15px;
    font-weight: bold;
    cursor: pointer;
}

.primary:hover {
    background: #1b3857;
}

.badge {
    display: inline-block;
    padding: 7px 13px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: bold;
}

.pending {
    background: #fff0c8;
    color: #9a6a00;
}

.progress {
    background: #d9efff;
    color: #17688c;
}

.resolved {
    background: #d9f2df;
    color: #26703b;
}

.table-wrap {
    overflow-x: auto;
    background: #122942;
    border-radius: 15px;
    padding: 10px;
}

table {
    width: 100%;
    border-collapse: collapse;
}

th, td {
    padding: 15px;
    text-align: left;
    border-bottom: 1px solid #29435e;
}

th {
    color: #70cde6;
    font-size: 13px;
}

.search {
    display: flex;
    gap: 12px;
    margin-bottom: 25px;
}

.search input {
    max-width: 450px;
}

.message {
    padding: 13px 18px;
    background: #173d35;
    border: 1px solid #3f9e82;
    border-radius: 8px;
    margin-bottom: 20px;
}

.error {
    padding: 13px 18px;
    background: #482727;
    border: 1px solid #b65b5b;
    border-radius: 8px;
    margin-bottom: 20px;
}

.metrics {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 16px;
}

.metric {
    background: #17304b;
    border: 1px solid #31506d;
    border-radius: 15px;
    padding: 25px;
}

.metric-value {
    color: #65cce8;
    font-size: 31px;
    font-weight: bold;
    margin-bottom: 8px;
}

.metric-label {
    color: #a8b8c7;
    font-size: 11px;
    letter-spacing: 1px;
}

.charts {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 20px;
    margin-top: 25px;
}

.chart {
    background: #122942;
    border: 1px solid #31506d;
    border-radius: 15px;
    padding: 20px;
}

.chart.wide {
    grid-column: 1 / -1;
}

.chart h3 {
    color: #a9c0d0;
    font-size: 14px;
    letter-spacing: 1px;
}

.chart img {
    width: 100%;
    display: block;
    background: white;
    border-radius: 8px;
}

.export {
    display: inline-block;
    border: 1px solid #69cde8;
    color: #69cde8;
    padding: 12px 18px;
    border-radius: 8px;
    text-decoration: none;
    margin-bottom: 20px;
}

.center {
    text-align: center;
}

@media (max-width: 900px) {
    .navbar {
        height: auto;
        padding: 20px;
        flex-wrap: wrap;
    }

    .logo {
        width: 100%;
    }

    .nav {
        gap: 5px;
        flex-wrap: wrap;
    }

    .metrics {
        grid-template-columns: 1fr 1fr;
    }

    .charts {
        grid-template-columns: 1fr;
    }

    .chart.wide {
        grid-column: auto;
    }

    .form-grid {
        grid-template-columns: 1fr;
    }

    .full {
        grid-column: auto;
    }
}
</style>
"""


# ---------------- TEMPLATE ----------------

BASE = """
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>CampusFix — Maintenance Control System</title>
""" + STYLE + """
</head>
<body>

<div class="navbar">

    <div class="logo">
        <div class="logo-box">CF</div>
        <div>
            <div class="logo-name">CampusFix</div>
            <div class="logo-sub">MAINTENANCE CONTROL SYSTEM</div>
        </div>
    </div>

    <div class="nav">
        <a href="/" class="{{ 'active' if page == 'dashboard' else '' }}">Dashboard</a>
        <a href="/register" class="{{ 'active' if page == 'register' else '' }}">Register</a>
        <a href="/tickets" class="{{ 'active' if page == 'tickets' else '' }}">All Tickets</a>
        <a href="/reports" class="{{ 'active' if page == 'reports' else '' }}">Reports</a>
    </div>

    <a class="report-btn" href="/register">+ Report an Issue</a>

</div>

<div class="container">

{% with messages = get_flashed_messages() %}
    {% if messages %}
        {% for message in messages %}
            <div class="message">{{ message }}</div>
        {% endfor %}
    {% endif %}
{% endwith %}

{{ content|safe }}

</div>

</body>
</html>
"""


# ---------------- DASHBOARD ----------------

@app.route("/")
def dashboard():

    content = """
    <div style="padding:55px 3%;">
        <div style="color:#76cfe8;letter-spacing:3px;margin-bottom:25px;">
            ● LIVE ACROSS CAMPUS BUILDINGS
        </div>

        <h1 style="font-size:55px;max-width:700px;">
            EVERY SQUEAK, LEAK,<br>
            AND <span style="color:#f4ad42;">FLICKER</span> —<br>
            LOGGED, TRACKED,<br>
            FIXED.
        </h1>

        <p class="subtitle" style="max-width:650px;line-height:1.8;">
            CampusFix turns scattered maintenance complaints into a single
            work-order board — from the moment a student reports a broken
            fan to the day a technician closes the ticket.
        </p>

        <a class="report-btn" href="/register">
            Report an Issue →
        </a>
    </div>
    """

    return render_template_string(
        BASE,
        page="dashboard",
        content=content
    )


# ---------------- REGISTER ----------------

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        student_name = request.form.get("student_name", "").strip()
        department = request.form.get("department", "").strip()
        building = request.form.get("building", "").strip()
        room_no = request.form.get("room_no", "").strip()
        category = request.form.get("category", "").strip()
        priority = request.form.get("priority", "").strip()
        problem = request.form.get("problem", "").strip()

        if not student_name:
            flash("Please enter Student Name.")
            return redirect(url_for("register"))

        if not problem:
            flash("Please enter Problem Description.")
            return redirect(url_for("register"))

        if not department or not building or not room_no:
            flash("Please complete all required fields.")
            return redirect(url_for("register"))

        if category not in CATEGORIES:
            flash("Please select a valid category.")
            return redirect(url_for("register"))

        if priority not in PRIORITIES:
            flash("Please select a valid priority.")
            return redirect(url_for("register"))

        complaint_id = next_complaint_id()

        conn = get_db()

        conn.execute("""
            INSERT INTO complaints
            (complaint_id, student_name, department, building,
             room_no, category, problem, priority, status, date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            complaint_id,
            student_name,
            department,
            building,
            room_no,
            category,
            problem,
            priority,
            "Pending",
            str(date.today())
        ))

        conn.commit()
        conn.close()

        flash(
            f"Complaint Registered Successfully — Complaint ID: {complaint_id}"
        )

        return redirect(url_for("tickets"))

    content = """
    <h1>REGISTER A COMPLAINT</h1>

    <div class="subtitle">
        Fill in the details below — a ticket ID is generated automatically.
    </div>

    <div class="card">

        <div style="text-align:right;color:#a75d4a;font-size:12px;font-weight:bold;">
            NEW TICKET
        </div>

        <form method="POST">

            <div class="form-grid">

                <div class="field">
                    <label>STUDENT NAME</label>
                    <input
                        name="student_name"
                        placeholder="e.g. Rahul Sharma"
                        required>
                </div>

                <div class="field">
                    <label>DEPARTMENT</label>
                    <select name="department" required>
                        <option value="">Select department</option>
                        {% for item in departments %}
                        <option>{{ item }}</option>
                        {% endfor %}
                    </select>
                </div>

                <div class="field">
                    <label>BUILDING</label>
                    <select name="building" required>
                        <option value="">Select building</option>
                        {% for item in buildings %}
                        <option>{{ item }}</option>
                        {% endfor %}
                    </select>
                </div>

                <div class="field">
                    <label>ROOM NO.</label>
                    <input
                        name="room_no"
                        placeholder="e.g. 204"
                        required>
                </div>

                <div class="field">
                    <label>CATEGORY</label>
                    <select name="category" required>
                        <option value="">Select category</option>
                        {% for item in categories %}
                        <option>{{ item }}</option>
                        {% endfor %}
                    </select>
                </div>

                <div class="field">
                    <label>PRIORITY</label>
                    <select name="priority" required>
                        <option value="">Select priority</option>
                        {% for item in priorities %}
                        <option>{{ item }}</option>
                        {% endfor %}
                    </select>
                </div>

                <div class="field full">
                    <label>PROBLEM DESCRIPTION</label>
                    <textarea
                        name="problem"
                        placeholder="Describe what's wrong, e.g. 'Ceiling fan is not working.'"
                        required></textarea>
                </div>

            </div>

            <div class="submit-row">
                <button class="primary" type="submit">
                    Register complaint
                </button>

                <span style="color:#6b6b65;font-size:14px;">
                    Date & ticket ID are assigned automatically on submit.
                </span>
            </div>

        </form>

    </div>
    """

    return render_template_string(
        BASE,
        page="register",
        content=render_template_string(
            content,
            departments=DEPARTMENTS,
            buildings=BUILDINGS,
            categories=CATEGORIES,
            priorities=PRIORITIES
        )
    )


# ---------------- TICKETS ----------------

@app.route("/tickets")
def tickets():

    search_id = request.args.get("search", "").strip()

    conn = get_db()

    if search_id:
        rows = conn.execute("""
            SELECT * FROM complaints
            WHERE complaint_id LIKE ?
            ORDER BY id DESC
        """, (f"%{search_id}%",)).fetchall()
    else:
        rows = conn.execute("""
            SELECT * FROM complaints
            ORDER BY id DESC
        """).fetchall()

    conn.close()

    rows_html = ""

    for row in rows:

        status_class = {
            "Pending": "pending",
            "In Progress": "progress",
            "Resolved": "resolved"
        }.get(row["status"], "pending")

        rows_html += f"""
        <tr>
            <td><strong>{row["complaint_id"]}</strong></td>
            <td>{row["student_name"]}</td>
            <td>{row["category"]}</td>
            <td>{row["building"]}</td>
            <td>{row["priority"]}</td>
            <td>
                <span class="badge {status_class}">
                    {row["status"]}
                </span>
            </td>
            <td>{row["date"]}</td>
        </tr>
        """

    if not rows_html:
        rows_html = """
        <tr>
            <td colspan="7" class="center">
                No complaints found.
            </td>
        </tr>
        """

    content = f"""
    <h1>ALL TICKETS</h1>

    <div class="subtitle">
        View and search all registered maintenance complaints.
    </div>

    <form class="search" method="GET">
        <input
            name="search"
            value="{search_id}"
            placeholder="Search by Complaint ID e.g. CMP001">

        <button class="primary" type="submit">
            Search
        </button>

        <a href="/tickets"
           style="padding:15px;color:#70cde6;text-decoration:none;">
           Clear
        </a>
    </form>

    <div class="table-wrap">
        <table>
            <thead>
                <tr>
                    <th>COMPLAINT ID</th>
                    <th>STUDENT</th>
                    <th>CATEGORY</th>
                    <th>BUILDING</th>
                    <th>PRIORITY</th>
                    <th>STATUS</th>
                    <th>DATE</th>
                </tr>
            </thead>
            <tbody>
                {rows_html}
            </tbody>
        </table>
    </div>

    <br>

    <div style="display:flex;gap:15px;flex-wrap:wrap;">
        <a class="report-btn" href="/status">
            Update Status
        </a>

        <a class="report-btn" href="/maintenance">
            Add Maintenance
        </a>
    </div>
    """

    return render_template_string(
        BASE,
        page="tickets",
        content=content
    )


# ---------------- STATUS ----------------

@app.route("/status", methods=["GET", "POST"])
def status():

    complaint = None
    complaint_id = request.values.get("complaint_id", "").strip()

    if complaint_id:
        conn = get_db()
        complaint = conn.execute(
            "SELECT * FROM complaints WHERE complaint_id = ?",
            (complaint_id,)
        ).fetchone()

        if request.method == "POST":

            if complaint is None:
                flash("Complaint ID does not exist.")
            else:
                new_status = request.form.get("status")

                if new_status not in STATUSES:
                    flash("Invalid status.")
                else:
                    conn.execute(
                        "UPDATE complaints SET status=? WHERE complaint_id=?",
                        (new_status, complaint_id)
                    )
                    conn.commit()
                    flash(
                        f"Status updated successfully for {complaint_id}."
                    )

                    complaint = conn.execute(
                        "SELECT * FROM complaints WHERE complaint_id=?",
                        (complaint_id,)
                    ).fetchone()

        conn.close()

    content = f"""
    <h1>UPDATE STATUS</h1>

    <div class="subtitle">
        Change a complaint from Pending to In Progress or Resolved.
    </div>

    <div class="card">

        <form method="GET">
            <div class="field">
                <label>COMPLAINT ID</label>
                <input
                    name="complaint_id"
                    placeholder="e.g. CMP001"
                    value="{complaint_id}"
                    required>
            </div>

            <br>

            <button class="primary" type="submit">
                Find Complaint
            </button>
        </form>

        {"<hr style='margin:30px 0;border:0;border-top:1px solid #ccc;'>" if complaint else ""}

        {
        f'''
        <form method="POST">

            <input type="hidden"
                   name="complaint_id"
                   value="{complaint["complaint_id"]}">

            <p>
                <strong>Current Status:</strong>
                {complaint["status"]}
            </p>

            <div class="field">
                <label>NEW STATUS</label>
                <select name="status">
                    <option>Pending</option>
                    <option>In Progress</option>
                    <option>Resolved</option>
                </select>
            </div>

            <br>

            <button class="primary" type="submit">
                Update Status
            </button>

        </form>
        '''
        if complaint else ""
        }

    </div>
    """

    return render_template_string(
        BASE,
        page="tickets",
        content=content
    )


# ---------------- MAINTENANCE ----------------

@app.route("/maintenance", methods=["GET", "POST"])
def maintenance():

    if request.method == "POST":

        complaint_id = request.form.get(
            "complaint_id", ""
        ).strip()

        staff_name = request.form.get(
            "staff_name", ""
        ).strip()

        repair_date = request.form.get(
            "repair_date", ""
        ).strip()

        remarks = request.form.get(
            "remarks", ""
        ).strip()

        try:
            cost = float(request.form.get("cost", ""))
        except ValueError:
            flash("Please enter a valid repair cost.")
            return redirect(url_for("maintenance"))

        if cost < 0:
            flash("Repair cost cannot be negative.")
            return redirect(url_for("maintenance"))

        if not complaint_id or not staff_name or not repair_date:
            flash("Please complete all required maintenance fields.")
            return redirect(url_for("maintenance"))

        conn = get_db()

        complaint = conn.execute(
            "SELECT * FROM complaints WHERE complaint_id=?",
            (complaint_id,)
        ).fetchone()

        if complaint is None:
            conn.close()
            flash("Complaint ID does not exist.")
            return redirect(url_for("maintenance"))

        conn.execute("""
            INSERT INTO maintenance
            (complaint_id, staff_name, repair_date, cost, remarks)
            VALUES (?, ?, ?, ?, ?)
        """, (
            complaint_id,
            staff_name,
            repair_date,
            cost,
            remarks
        ))

        conn.commit()
        conn.close()

        flash("Maintenance details saved successfully.")
        return redirect(url_for("maintenance"))

    content = """
    <h1>ADD MAINTENANCE DETAILS</h1>

    <div class="subtitle">
        Record the repair work completed for a complaint.
    </div>

    <div class="card">

        <form method="POST">

            <div class="form-grid">

                <div class="field">
                    <label>COMPLAINT ID</label>
                    <input
                        name="complaint_id"
                        placeholder="e.g. CMP001"
                        required>
                </div>

                <div class="field">
                    <label>MAINTENANCE STAFF</label>
                    <input
                        name="staff_name"
                        placeholder="e.g. Amit"
                        required>
                </div>

                <div class="field">
                    <label>REPAIR DATE</label>
                    <input
                        type="date"
                        name="repair_date"
                        value="{{ today }}"
                        required>
                </div>

                <div class="field">
                    <label>REPAIR COST</label>
                    <input
                        type="number"
                        name="cost"
                        min="0"
                        step="0.01"
                        placeholder="e.g. 500"
                        required>
                </div>

                <div class="field full">
                    <label>REPAIR REMARKS</label>
                    <textarea
                        name="remarks"
                        placeholder="e.g. Fan capacitor replaced"></textarea>
                </div>

            </div>

            <div class="submit-row">
                <button class="primary" type="submit">
                    Save Maintenance
                </button>
            </div>

        </form>

    </div>
    """

    return render_template_string(
        BASE,
        page="tickets",
        content=render_template_string(
            content,
            today=str(date.today())
        )
    )


# ---------------- REPORTS ----------------

@app.route("/reports")
def reports():

    conn = get_db()

    complaints = pd.read_sql_query(
        "SELECT * FROM complaints",
        conn
    )

    maintenance = pd.read_sql_query(
        "SELECT * FROM maintenance",
        conn
    )

    conn.close()

    total = len(complaints)

    pending = 0
    progress = 0
    resolved = 0

    if not complaints.empty:
        pending = int(
            (complaints["status"] == "Pending").sum()
        )
        progress = int(
            (complaints["status"] == "In Progress").sum()
        )
        resolved = int(
            (complaints["status"] == "Resolved").sum()
        )

    if maintenance.empty:
        total_cost = 0
        average_cost = 0
    else:
        total_cost = float(maintenance["cost"].sum())
        average_cost = float(maintenance["cost"].mean())

    if complaints.empty:
        common_category = "—"
        common_building = "—"
    else:
        common_category = complaints["category"].mode()[0]
        common_building = complaints["building"].mode()[0]

    charts = {
        "category": chart_image("category"),
        "status": chart_image("status"),
        "building": chart_image("building"),
        "month": chart_image("month"),
        "cost": chart_image("cost")
    }

    chart_html = ""

    titles = {
        "category": "COMPLAINTS BY CATEGORY",
        "status": "STATUS DISTRIBUTION",
        "building": "COMPLAINTS BY BUILDING",
        "month": "COMPLAINTS REPORTED PER MONTH",
        "cost": "REPAIR COST BY CATEGORY"
    }

    for key in [
        "category",
        "status",
        "building",
        "month",
        "cost"
    ]:

        if charts[key]:

            wide = "wide" if key == "cost" else ""

            chart_html += f"""
            <div class="chart {wide}">
                <h3>{titles[key]}</h3>
                <img src="data:image/png;base64,{charts[key]}">
            </div>
            """

    content = f"""
    <h1>REPORTS & ANALYSIS</h1>

    <div class="subtitle">
        Everything Pandas would have crunched — rendered live.
    </div>

    <a class="export" href="/export">
        ⇩ Export tickets to CSV
    </a>

    <div class="metrics">

        <div class="metric">
            <div class="metric-value">{total}</div>
            <div class="metric-label">TOTAL COMPLAINTS</div>
        </div>

        <div class="metric">
            <div class="metric-value">{pending}</div>
            <div class="metric-label">PENDING</div>
        </div>

        <div class="metric">
            <div class="metric-value">{progress}</div>
            <div class="metric-label">IN PROGRESS</div>
        </div>

        <div class="metric">
            <div class="metric-value">{resolved}</div>
            <div class="metric-label">RESOLVED</div>
        </div>

        <div class="metric">
            <div class="metric-value">₹{total_cost:,.0f}</div>
            <div class="metric-label">TOTAL MAINTENANCE COST</div>
        </div>

        <div class="metric">
            <div class="metric-value">₹{average_cost:,.0f}</div>
            <div class="metric-label">AVERAGE REPAIR COST</div>
        </div>

        <div class="metric">
            <div class="metric-value">{common_category}</div>
            <div class="metric-label">MOST COMMON CATEGORY</div>
        </div>

        <div class="metric">
            <div class="metric-value">{common_building}</div>
            <div class="metric-label">MOST REPORTED BUILDING</div>
        </div>

    </div>

    <div class="charts">
        {chart_html}
    </div>
    """

    return render_template_string(
        BASE,
        page="reports",
        content=content
    )


# ---------------- CSV ----------------

@app.route("/export")
def export_csv():

    conn = get_db()

    df = pd.read_sql_query(
        "SELECT * FROM complaints",
        conn
    )

    conn.close()

    path = os.path.join(
        BASE_DIR,
        "reports",
        "complaints_report.csv"
    )

    df.to_csv(path, index=False)

    flash("CSV report exported successfully to reports/complaints_report.csv")

    return redirect(url_for("reports"))


# ---------------- START ----------------

init_db()


def open_browser():
    webbrowser.open("http://127.0.0.1:5000")


if __name__ == "__main__":

    threading.Timer(
        1.5,
        open_browser
    ).start()

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=False
    )