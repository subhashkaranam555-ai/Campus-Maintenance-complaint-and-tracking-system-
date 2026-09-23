import sqlite3
import os
from datetime import date, timedelta

DB_PATH = os.path.join("data", "campus.db")


def get_connection():
    os.makedirs("data", exist_ok=True)
    return sqlite3.connect(DB_PATH)


def create_database():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS complaints (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            complaint_id TEXT UNIQUE,
            student_name TEXT NOT NULL,
            department TEXT,
            building TEXT,
            room_no TEXT,
            category TEXT,
            problem TEXT NOT NULL,
            priority TEXT,
            status TEXT,
            date TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS maintenance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            complaint_id TEXT,
            staff_name TEXT,
            repair_date TEXT,
            cost REAL,
            remarks TEXT
        )
    """)

    conn.commit()
    conn.close()


def generate_complaint_id():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id FROM complaints ORDER BY id DESC LIMIT 1"
    )

    row = cursor.fetchone()
    conn.close()

    number = row[0] + 1 if row else 1
    return f"CMP{number:03d}"


def add_complaint(
    student_name,
    department,
    building,
    room_no,
    category,
    problem,
    priority,
    complaint_date=None
):
    complaint_date = complaint_date or str(date.today())

    conn = get_connection()
    cursor = conn.cursor()

    complaint_id = generate_complaint_id()

    cursor.execute("""
        INSERT INTO complaints
        (
            complaint_id,
            student_name,
            department,
            building,
            room_no,
            category,
            problem,
            priority,
            status,
            date
        )
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
        complaint_date
    ))

    conn.commit()
    conn.close()

    return complaint_id


def get_all_complaints():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            complaint_id,
            student_name,
            department,
            building,
            room_no,
            category,
            problem,
            priority,
            status,
            date
        FROM complaints
        ORDER BY id DESC
    """)

    rows = cursor.fetchall()
    conn.close()

    return rows


def search_complaint(complaint_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            complaint_id,
            student_name,
            department,
            building,
            room_no,
            category,
            problem,
            priority,
            status,
            date
        FROM complaints
        WHERE complaint_id = ?
    """, (complaint_id.strip().upper(),))

    row = cursor.fetchone()
    conn.close()

    return row


def get_status(complaint_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT status
        FROM complaints
        WHERE complaint_id = ?
    """, (complaint_id.strip().upper(),))

    row = cursor.fetchone()
    conn.close()

    return row[0] if row else None


def update_status(complaint_id, status):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE complaints
        SET status = ?
        WHERE complaint_id = ?
    """, (
        status,
        complaint_id.strip().upper()
    ))

    changed = cursor.rowcount

    conn.commit()
    conn.close()

    return changed


def add_maintenance(
    complaint_id,
    staff_name,
    repair_date,
    cost,
    remarks
):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO maintenance
        (
            complaint_id,
            staff_name,
            repair_date,
            cost,
            remarks
        )
        VALUES (?, ?, ?, ?, ?)
    """, (
        complaint_id.strip().upper(),
        staff_name.strip(),
        repair_date.strip(),
        float(cost),
        remarks.strip()
    ))

    conn.commit()
    conn.close()


def get_maintenance():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            complaint_id,
            staff_name,
            repair_date,
            cost,
            remarks
        FROM maintenance
        ORDER BY id DESC
    """)

    rows = cursor.fetchall()
    conn.close()

    return rows


def seed_sample_data():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM complaints")
    count = cursor.fetchone()[0]

    if count > 0:
        conn.close()
        return

    samples = [
        ("Rahul Sharma", "BCA", "Block A", "204",
         "Electrical", "Fan not working", "Medium", "Pending"),

        ("Priya Verma", "B.Tech", "Block B", "112",
         "Furniture", "Broken chair", "Low", "Resolved"),

        ("Aman Patel", "BCA", "Computer Lab", "Lab-1",
         "IT", "Projector fault", "High", "In Progress"),

        ("Neha Singh", "B.Tech", "Block C", "118",
         "Plumbing", "Tap leakage", "High", "Resolved"),

        ("Rohit Jain", "BCA", "Block A", "305",
         "Internet", "Wi-Fi down", "Medium", "Pending"),

        ("Kavya Gupta", "BBA", "Library", "1F",
         "Cleaning", "Reading area needs cleaning", "Low", "Resolved"),

        ("Arjun Mehta", "B.Tech", "AC/Cooling", "210",
         "AC/Cooling", "AC not cooling", "High", "In Progress"),

        ("Simran Kaur", "BCA", "Hostel Block", "H-12",
         "Other", "Door handle damaged", "Medium", "Pending"),

        ("Vivek Rao", "BBA", "Block A", "106",
         "Electrical", "Tube light flickering", "Medium", "Resolved"),

        ("Anjali Shah", "BCA", "Block B", "208",
         "Furniture", "Desk drawer broken", "Low", "Pending"),

        ("Karan Joshi", "B.Tech", "Block C", "302",
         "IT", "Keyboard not working", "Medium", "Resolved"),

        ("Isha Malhotra", "BBA", "Library", "2F",
         "Internet", "Network connection slow", "High", "In Progress"),

        ("Dev Kumar", "BCA", "Block A", "410",
         "Plumbing", "Water leakage", "High", "Resolved"),

        ("Pooja Yadav", "B.Tech", "Computer Lab", "Lab-2",
         "IT", "Computer not starting", "High", "Pending"),

        ("Nitin Soni", "BCA", "Block B", "118",
         "Cleaning", "Classroom cleaning required", "Low", "Resolved"),

        ("Riya Das", "BBA", "Library", "1F",
         "Electrical", "Light not working", "Medium", "Pending"),

        ("Harsh Tiwari", "B.Tech", "Hostel Block", "H-20",
         "Plumbing", "Washroom tap leaking", "High", "In Progress"),

        ("Sakshi Jain", "BCA", "Block C", "214",
         "Furniture", "Broken desk", "Medium", "Resolved"),

        ("Yash Mishra", "BBA", "Block A", "220",
         "Internet", "Wi-Fi unavailable", "High", "Pending"),

        ("Muskan Khan", "BCA", "Block B", "316",
         "AC/Cooling", "Cooler not working", "High", "In Progress"),

        ("Aditya Sen", "B.Tech", "Computer Lab", "Lab-3",
         "IT", "Mouse not working", "Low", "Resolved"),

        ("Megha Roy", "BBA", "Library", "3F",
         "Cleaning", "Dustbin overflowing", "Low", "Pending"),

        ("Sahil Khan", "BCA", "Block C", "120",
         "Electrical", "Switch damaged", "Medium", "Resolved"),

        ("Tanya Jain", "B.Tech", "Hostel Block", "H-05",
         "Furniture", "Bed repair required", "High", "Pending"),

        ("Manish Gupta", "BBA", "Block A", "109",
         "Plumbing", "Pipe leakage", "High", "Resolved"),

        ("Aditi Singh", "BCA", "Block B", "201",
         "Internet", "Network unavailable", "High", "Pending"),

        ("Mohit Verma", "B.Tech", "Library", "2F",
         "AC/Cooling", "AC making noise", "Medium", "In Progress"),

        ("Nisha Patel", "BBA", "Computer Lab", "Lab-1",
         "IT", "Projector cable damaged", "Medium", "Resolved"),

        ("Varun Sharma", "BCA", "Block C", "205",
         "Cleaning", "Floor needs cleaning", "Low", "Pending"),

        ("Diya Mehta", "B.Tech", "Hostel Block", "H-18",
         "Other", "Window latch broken", "Medium", "Resolved")
    ]

    start = date.today() - timedelta(days=120)

    for i, item in enumerate(samples):

        complaint_id = f"CMP{i + 1:03d}"
        complaint_date = str(start + timedelta(days=i * 4))

        cursor.execute("""
            INSERT INTO complaints
            (
                complaint_id,
                student_name,
                department,
                building,
                room_no,
                category,
                problem,
                priority,
                status,
                date
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            complaint_id,
            item[0],
            item[1],
            item[2],
            item[3],
            item[4],
            item[5],
            item[6],
            item[7],
            complaint_date
        ))

    maintenance_samples = [
        ("CMP002", "Amit", str(date.today()), 450,
         "Chair joint repaired"),

        ("CMP004", "Ravi", str(date.today()), 650,
         "Tap seal replaced"),

        ("CMP006", "Suresh", str(date.today()), 300,
         "Cleaning completed"),

        ("CMP009", "Amit", str(date.today()), 550,
         "Tube light replaced"),

        ("CMP011", "Ravi", str(date.today()), 900,
         "Keyboard replaced"),

        ("CMP013", "Suresh", str(date.today()), 700,
         "Pipe repaired"),

        ("CMP018", "Amit", str(date.today()), 800,
         "Desk repaired"),

        ("CMP021", "Ravi", str(date.today()), 500,
         "Mouse replaced"),

        ("CMP025", "Suresh", str(date.today()), 1100,
         "Pipe repaired"),

        ("CMP028", "Amit", str(date.today()), 1200,
         "Projector cable replaced")
    ]

    cursor.executemany("""
        INSERT INTO maintenance
        (
            complaint_id,
            staff_name,
            repair_date,
            cost,
            remarks
        )
        VALUES (?, ?, ?, ?, ?)
    """, maintenance_samples)

    conn.commit()
    conn.close()