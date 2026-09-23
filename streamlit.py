import os
import sqlite3
from datetime import date

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt


# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="CampusFix - Campus Maintenance System",
    page_icon="🏫",
    layout="wide"
)


# =========================================================
# PATHS & CONSTANTS
# =========================================================

DB_PATH = os.path.join("data", "campus.db")

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

PRIORITIES = [
    "Low",
    "Medium",
    "High"
]

STATUSES = [
    "Pending",
    "In Progress",
    "Resolved"
]

os.makedirs("data", exist_ok=True)


# =========================================================
# DATABASE CONNECTION
# =========================================================

def connect_db():
    return sqlite3.connect(DB_PATH)


# =========================================================
# DATABASE SETUP / COMPATIBILITY
# =========================================================

def create_tables():

    conn = connect_db()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS complaints (
            complaint_id TEXT PRIMARY KEY,
            student_name TEXT NOT NULL,
            department TEXT,
            building TEXT,
            room_no TEXT,
            category TEXT,
            problem TEXT NOT NULL,
            priority TEXT,
            status TEXT DEFAULT 'Pending',
            complaint_date TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS maintenance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            complaint_id TEXT NOT NULL,
            staff_name TEXT,
            repair_date TEXT,
            repair_cost REAL DEFAULT 0,
            remarks TEXT
        )
    """)

    conn.commit()
    conn.close()


def fix_existing_database():

    conn = connect_db()
    cur = conn.cursor()

    # Check complaints columns
    cur.execute("PRAGMA table_info(complaints)")
    complaint_columns = [
        row[1] for row in cur.fetchall()
    ]

    # Existing database may have "date" instead of "complaint_date"
    if complaint_columns:

        if "complaint_date" not in complaint_columns:

            cur.execute("""
                ALTER TABLE complaints
                ADD COLUMN complaint_date TEXT
            """)

            if "date" in complaint_columns:

                cur.execute("""
                    UPDATE complaints
                    SET complaint_date = date
                    WHERE complaint_date IS NULL
                """)

    # Check maintenance table
    cur.execute("PRAGMA table_info(maintenance)")
    maintenance_columns = [
        row[1] for row in cur.fetchall()
    ]

    if maintenance_columns:

        if "repair_date" not in maintenance_columns:

            cur.execute("""
                ALTER TABLE maintenance
                ADD COLUMN repair_date TEXT
            """)

    conn.commit()
    conn.close()


create_tables()
fix_existing_database()


# =========================================================
# COMPLAINT DATA
# =========================================================

def get_complaints():

    conn = connect_db()

    cur = conn.cursor()

    cur.execute("PRAGMA table_info(complaints)")

    columns = [
        row[1] for row in cur.fetchall()
    ]

    # Use existing date column if available
    if "complaint_date" in columns:

        date_column = "complaint_date"

    elif "date" in columns:

        date_column = "date"

    else:

        date_column = "NULL"

    query = f"""
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
            {date_column} AS complaint_date
        FROM complaints
        ORDER BY ROWID DESC
    """

    df = pd.read_sql_query(
        query,
        conn
    )

    conn.close()

    return df


def get_maintenance():

    conn = connect_db()

    cur = conn.cursor()

    cur.execute("PRAGMA table_info(maintenance)")

    columns = [
        row[1] for row in cur.fetchall()
    ]

    repair_date = (
        "repair_date"
        if "repair_date" in columns
        else "NULL"
    )

    staff_name = (
        "staff_name"
        if "staff_name" in columns
        else "''"
    )

    repair_cost = (
        "repair_cost"
        if "repair_cost" in columns
        else "0"
    )

    remarks = (
        "remarks"
        if "remarks" in columns
        else "''"
    )

    query = f"""
        SELECT
            id,
            complaint_id,
            {staff_name} AS staff_name,
            {repair_date} AS repair_date,
            {repair_cost} AS repair_cost,
            {remarks} AS remarks
        FROM maintenance
        ORDER BY id DESC
    """

    df = pd.read_sql_query(
        query,
        conn
    )

    conn.close()

    return df


# =========================================================
# COMPLAINT ID
# =========================================================

def generate_complaint_id():

    conn = connect_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT complaint_id
        FROM complaints
        ORDER BY ROWID DESC
        LIMIT 1
    """)

    result = cur.fetchone()

    conn.close()

    if not result:
        return "CMP001"

    try:

        number = int(
            result[0].replace("CMP", "")
        ) + 1

        return f"CMP{number:03d}"

    except:

        return "CMP001"


# =========================================================
# ADD COMPLAINT
# =========================================================

def add_complaint(
    student_name,
    department,
    building,
    room_no,
    category,
    problem,
    priority,
    complaint_date
):

    complaint_id = generate_complaint_id()

    conn = connect_db()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO complaints (
            complaint_id,
            student_name,
            department,
            building,
            room_no,
            category,
            problem,
            priority,
            status,
            complaint_date
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
        str(complaint_date)
    ))

    conn.commit()
    conn.close()

    return complaint_id


# =========================================================
# FIND COMPLAINT
# =========================================================

def find_complaint(complaint_id):

    conn = connect_db()

    cur = conn.cursor()

    cur.execute("PRAGMA table_info(complaints)")

    columns = [
        row[1] for row in cur.fetchall()
    ]

    if "complaint_date" in columns:
        date_column = "complaint_date"
    elif "date" in columns:
        date_column = "date"
    else:
        date_column = "NULL"

    query = f"""
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
            {date_column} AS complaint_date
        FROM complaints
        WHERE complaint_id = ?
    """

    df = pd.read_sql_query(
        query,
        conn,
        params=(complaint_id,)
    )

    conn.close()

    return df


# =========================================================
# UPDATE STATUS
# =========================================================

def update_status(
    complaint_id,
    status
):

    conn = connect_db()
    cur = conn.cursor()

    cur.execute("""
        UPDATE complaints
        SET status = ?
        WHERE complaint_id = ?
    """, (
        status,
        complaint_id
    ))

    changed = cur.rowcount

    conn.commit()
    conn.close()

    return changed > 0


# =========================================================
# SAVE MAINTENANCE
# =========================================================

def save_maintenance(
    complaint_id,
    staff_name,
    repair_date,
    repair_cost,
    remarks
):

    conn = connect_db()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO maintenance (
            complaint_id,
            staff_name,
            repair_date,
            repair_cost,
            remarks
        )
        VALUES (?, ?, ?, ?, ?)
    """, (
        complaint_id,
        staff_name,
        str(repair_date),
        repair_cost,
        remarks
    ))

    conn.commit()
    conn.close()


# =========================================================
# CUSTOM STYLE
# =========================================================

st.markdown("""
<style>

.stApp {
    background-color: #08111F;
    color: white;
}

[data-testid="stSidebar"] {
    background-color: #0B1728;
}

[data-testid="stSidebar"] * {
    color: white;
}

h1, h2, h3 {
    color: white !important;
}

.main-title {
    font-size: 42px;
    font-weight: 800;
    color: white;
}

.subtitle {
    color: #9AA8BA;
    font-size: 16px;
    margin-bottom: 25px;
}

.card {
    background-color: #101C2D;
    border: 1px solid #1D2B40;
    border-radius: 12px;
    padding: 20px;
    margin-bottom: 15px;
}

.metric-number {
    color: #F59E0B;
    font-size: 30px;
    font-weight: 800;
}

.metric-label {
    color: #9AA8BA;
    font-size: 14px;
}

</style>
""", unsafe_allow_html=True)


# =========================================================
# SIDEBAR
# =========================================================

st.sidebar.markdown(
    "# 🏫 CampusFix"
)

st.sidebar.caption(
    "Campus Maintenance System"
)

st.sidebar.divider()

page = st.sidebar.radio(
    "Navigation",
    [
        "Dashboard",
        "Register Complaint",
        "All Tickets",
        "Reports"
    ]
)

st.sidebar.divider()

st.sidebar.caption(
    "Complaint & Maintenance Tracking"
)


# =========================================================
# DASHBOARD
# =========================================================

if page == "Dashboard":

    complaints = get_complaints()

    st.markdown(
        '<div class="main-title">'
        'CAMPUS MAINTENANCE SYSTEM'
        '</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="subtitle">'
        'Complaint management and maintenance tracking dashboard'
        '</div>',
        unsafe_allow_html=True
    )

    total = len(complaints)

    pending = (
        len(
            complaints[
                complaints["status"] == "Pending"
            ]
        )
        if not complaints.empty
        else 0
    )

    progress = (
        len(
            complaints[
                complaints["status"] == "In Progress"
            ]
        )
        if not complaints.empty
        else 0
    )

    resolved = (
        len(
            complaints[
                complaints["status"] == "Resolved"
            ]
        )
        if not complaints.empty
        else 0
    )

    c1, c2, c3, c4 = st.columns(4)

    metrics = [
        (c1, total, "Total Complaints"),
        (c2, pending, "Pending"),
        (c3, progress, "In Progress"),
        (c4, resolved, "Resolved")
    ]

    for col, value, label in metrics:

        with col:

            st.markdown(
                f"""
                <div class="card">
                    <div class="metric-number">
                        {value}
                    </div>
                    <div class="metric-label">
                        {label}
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

    st.subheader("Complaint Workflow")

    st.info(
        "Enter Complaint → Save → View/Search → "
        "Update Status → Add Repair Details → Analyze Data"
    )

    st.subheader("Recent Complaints")

    if complaints.empty:

        st.info(
            "No complaints registered yet."
        )

    else:

        st.dataframe(
            complaints[
                [
                    "complaint_id",
                    "student_name",
                    "category",
                    "building",
                    "priority",
                    "status",
                    "complaint_date"
                ]
            ].head(10),
            use_container_width=True,
            hide_index=True
        )


# =========================================================
# REGISTER COMPLAINT
# =========================================================

elif page == "Register Complaint":

    st.markdown(
        '<div class="main-title">'
        'REGISTER A COMPLAINT'
        '</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="subtitle">'
        'Submit a new campus maintenance complaint'
        '</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="card">'
        '<b>NEW TICKET</b>'
        '</div>',
        unsafe_allow_html=True
    )

    col1, col2 = st.columns(2)

    with col1:

        student_name = st.text_input(
            "Student Name *"
        )

        department = st.text_input(
            "Department"
        )

        building = st.text_input(
            "Building"
        )

        room_no = st.text_input(
            "Room No."
        )

    with col2:

        category = st.selectbox(
            "Category",
            CATEGORIES
        )

        priority = st.selectbox(
            "Priority",
            PRIORITIES
        )

        complaint_date = st.date_input(
            "Date",
            value=date.today()
        )

        st.text_input(
            "Status",
            value="Pending",
            disabled=True
        )

    problem = st.text_area(
        "Problem Description *",
        height=150
    )

    if st.button(
        "SAVE / REGISTER COMPLAINT",
        type="primary",
        use_container_width=True
    ):

        if not student_name.strip():

            st.error(
                "Student Name is required."
            )

        elif not problem.strip():

            st.error(
                "Problem Description is required."
            )

        else:

            complaint_id = add_complaint(
                student_name.strip(),
                department.strip(),
                building.strip(),
                room_no.strip(),
                category,
                problem.strip(),
                priority,
                complaint_date
            )

            st.success(
                "Complaint registered successfully!"
            )

            st.success(
                f"Complaint ID: {complaint_id}"
            )

            st.info(
                "Initial Status: Pending"
            )


# =========================================================
# ALL TICKETS
# =========================================================

elif page == "All Tickets":

    st.markdown(
        '<div class="main-title">'
        'ALL TICKETS'
        '</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="subtitle">'
        'View, search and update complaints'
        '</div>',
        unsafe_allow_html=True
    )

    search_id = st.text_input(
        "Search by Complaint ID",
        placeholder="Example: CMP001"
    )

    if search_id.strip():

        result = find_complaint(
            search_id.strip().upper()
        )

        if result.empty:

            st.error(
                "Complaint Not Found"
            )

        else:

            complaint = result.iloc[0]

            st.success(
                f"Complaint {complaint['complaint_id']} found."
            )

            c1, c2 = st.columns(2)

            with c1:

                st.write(
                    f"**Student:** "
                    f"{complaint['student_name']}"
                )

                st.write(
                    f"**Department:** "
                    f"{complaint['department']}"
                )

                st.write(
                    f"**Building:** "
                    f"{complaint['building']}"
                )

                st.write(
                    f"**Room:** "
                    f"{complaint['room_no']}"
                )

                st.write(
                    f"**Category:** "
                    f"{complaint['category']}"
                )

            with c2:

                st.write(
                    f"**Priority:** "
                    f"{complaint['priority']}"
                )

                st.write(
                    f"**Status:** "
                    f"{complaint['status']}"
                )

                st.write(
                    f"**Date:** "
                    f"{complaint['complaint_date']}"
                )

            st.write(
                f"**Problem:** "
                f"{complaint['problem']}"
            )

            st.divider()

            new_status = st.selectbox(
                "Update Status",
                STATUSES,
                index=STATUSES.index(
                    complaint["status"]
                )
            )

            if st.button(
                "UPDATE STATUS"
            ):

                if update_status(
                    complaint["complaint_id"],
                    new_status
                ):

                    st.success(
                        f"Status updated to {new_status}."
                    )

                    st.rerun()

    complaints = get_complaints()

    st.subheader(
        "Complaint Records"
    )

    if complaints.empty:

        st.info(
            "No complaints available."
        )

    else:

        st.dataframe(
            complaints[
                [
                    "complaint_id",
                    "student_name",
                    "category",
                    "building",
                    "priority",
                    "status",
                    "complaint_date"
                ]
            ],
            use_container_width=True,
            hide_index=True
        )

    st.divider()

    # -----------------------------------------------------
    # MAINTENANCE
    # -----------------------------------------------------

    st.subheader(
        "Add Repair Details"
    )

    maintenance_id = st.text_input(
        "Complaint ID",
        key="maintenance_id"
    )

    c1, c2 = st.columns(2)

    with c1:

        staff_name = st.text_input(
            "Staff Name"
        )

        repair_date = st.date_input(
            "Repair Date",
            value=date.today()
        )

    with c2:

        repair_cost = st.number_input(
            "Repair Cost",
            min_value=0.0,
            step=100.0
        )

        remarks = st.text_input(
            "Remarks"
        )

    if st.button(
        "SAVE MAINTENANCE DETAILS"
    ):

        if not maintenance_id.strip():

            st.error(
                "Complaint ID is required."
            )

        else:

            result = find_complaint(
                maintenance_id.strip().upper()
            )

            if result.empty:

                st.error(
                    "Complaint Not Found"
                )

            else:

                save_maintenance(
                    maintenance_id.strip().upper(),
                    staff_name.strip(),
                    repair_date,
                    repair_cost,
                    remarks.strip()
                )

                st.success(
                    "Maintenance details saved successfully."
                )


# =========================================================
# REPORTS
# =========================================================

elif page == "Reports":

    st.markdown(
        '<div class="main-title">'
        'REPORTS & ANALYSIS'
        '</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="subtitle">'
        'Complaint and maintenance data analysis'
        '</div>',
        unsafe_allow_html=True
    )

    complaints = get_complaints()
    maintenance = get_maintenance()

    if complaints.empty:

        st.info(
            "No complaint data available for analysis."
        )

    else:

        total = len(complaints)

        pending = len(
            complaints[
                complaints["status"] == "Pending"
            ]
        )

        progress = len(
            complaints[
                complaints["status"] == "In Progress"
            ]
        )

        resolved = len(
            complaints[
                complaints["status"] == "Resolved"
            ]
        )

        if not complaints["category"].dropna().empty:

            most_common_category = (
                complaints["category"]
                .mode()
                .iloc[0]
            )

        else:

            most_common_category = "N/A"

        buildings = (
            complaints["building"]
            .replace("", "Unknown")
            .dropna()
        )

        if not buildings.empty:

            most_reported_building = (
                buildings.mode().iloc[0]
            )

        else:

            most_reported_building = "N/A"

        if maintenance.empty:

            total_cost = 0
            average_cost = 0

        else:

            maintenance["repair_cost"] = pd.to_numeric(
                maintenance["repair_cost"],
                errors="coerce"
            ).fillna(0)

            total_cost = (
                maintenance["repair_cost"].sum()
            )

            average_cost = (
                maintenance["repair_cost"].mean()
            )

        # -------------------------------------------------
        # METRICS
        # -------------------------------------------------

        c1, c2, c3, c4 = st.columns(4)

        values = [
            (c1, total, "Total Complaints"),
            (c2, pending, "Pending"),
            (c3, progress, "In Progress"),
            (c4, resolved, "Resolved")
        ]

        for col, value, label in values:

            with col:

                st.markdown(
                    f"""
                    <div class="card">
                        <div class="metric-number">
                            {value}
                        </div>
                        <div class="metric-label">
                            {label}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

        c1, c2, c3, c4 = st.columns(4)

        values = [
            (
                c1,
                f"₹{total_cost:,.2f}",
                "Total Maintenance Cost"
            ),
            (
                c2,
                f"₹{average_cost:,.2f}",
                "Average Repair Cost"
            ),
            (
                c3,
                most_common_category,
                "Most Common Category"
            ),
            (
                c4,
                most_reported_building,
                "Most Reported Building"
            )
        ]

        for col, value, label in values:

            with col:

                st.markdown(
                    f"""
                    <div class="card">
                        <div class="metric-number">
                            {value}
                        </div>
                        <div class="metric-label">
                            {label}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

        st.divider()

        # =================================================
        # CHART 1 - CATEGORY
        # =================================================

        st.subheader(
            "Complaints by Category"
        )

        category_data = (
            complaints["category"]
            .value_counts()
        )

        fig1, ax1 = plt.subplots(
            figsize=(10, 4)
        )

        category_data.plot(
            kind="bar",
            ax=ax1
        )

        ax1.set_xlabel(
            "Category"
        )

        ax1.set_ylabel(
            "Number of Complaints"
        )

        ax1.set_title(
            "Complaints by Category"
        )

        plt.xticks(
            rotation=35
        )

        plt.tight_layout()

        st.pyplot(fig1)

        plt.close(fig1)

        # =================================================
        # CHART 2 - STATUS
        # =================================================

        st.subheader(
            "Complaints by Status"
        )

        status_data = (
            complaints["status"]
            .value_counts()
        )

        fig2, ax2 = plt.subplots(
            figsize=(7, 5)
        )

        status_data.plot(
            kind="pie",
            autopct="%1.1f%%",
            ax=ax2
        )

        ax2.set_ylabel("")

        ax2.set_title(
            "Complaint Status Distribution"
        )

        plt.tight_layout()

        st.pyplot(fig2)

        plt.close(fig2)

        # =================================================
        # CHART 3 - BUILDING
        # =================================================

        st.subheader(
            "Complaints by Building"
        )

        building_data = (
            complaints["building"]
            .replace("", "Unknown")
            .value_counts()
        )

        fig3, ax3 = plt.subplots(
            figsize=(10, 4)
        )

        building_data.plot(
            kind="bar",
            ax=ax3
        )

        ax3.set_xlabel(
            "Building"
        )

        ax3.set_ylabel(
            "Number of Complaints"
        )

        ax3.set_title(
            "Complaints by Building"
        )

        plt.xticks(
            rotation=35
        )

        plt.tight_layout()

        st.pyplot(fig3)

        plt.close(fig3)

        # =================================================
        # CHART 4 - MONTHLY
        # =================================================

        st.subheader(
            "Monthly Complaints"
        )

        monthly = complaints.copy()

        monthly["complaint_date"] = pd.to_datetime(
            monthly["complaint_date"],
            errors="coerce"
        )

        monthly = monthly.dropna(
            subset=["complaint_date"]
        )

        if not monthly.empty:

            monthly_data = (
                monthly
                .set_index("complaint_date")
                .resample("ME")
                .size()
            )

            fig4, ax4 = plt.subplots(
                figsize=(10, 4)
            )

            monthly_data.plot(
                kind="line",
                marker="o",
                ax=ax4
            )

            ax4.set_xlabel(
                "Month"
            )

            ax4.set_ylabel(
                "Number of Complaints"
            )

            ax4.set_title(
                "Monthly Complaint Trend"
            )

            plt.tight_layout()

            st.pyplot(fig4)

            plt.close(fig4)

        else:

            st.info(
                "No valid complaint dates available."
            )

        # =================================================
        # CHART 5 - REPAIR COST
        # =================================================

        st.subheader(
            "Repair Cost by Category"
        )

        if maintenance.empty:

            st.info(
                "No maintenance records available."
            )

        else:

            repair = maintenance.merge(
                complaints[
                    [
                        "complaint_id",
                        "category"
                    ]
                ],
                on="complaint_id",
                how="left"
            )

            repair_cost = (
                repair
                .groupby("category")[
                    "repair_cost"
                ]
                .sum()
            )

            fig5, ax5 = plt.subplots(
                figsize=(10, 4)
            )

            repair_cost.plot(
                kind="bar",
                ax=ax5
            )

            ax5.set_xlabel(
                "Category"
            )

            ax5.set_ylabel(
                "Repair Cost"
            )

            ax5.set_title(
                "Repair Cost by Category"
            )

            plt.xticks(
                rotation=35
            )

            plt.tight_layout()

            st.pyplot(fig5)

            plt.close(fig5)