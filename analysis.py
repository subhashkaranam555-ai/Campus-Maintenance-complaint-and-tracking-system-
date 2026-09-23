import sqlite3
import pandas as pd

from database import DB_PATH


def get_complaints_dataframe():

    conn = sqlite3.connect(DB_PATH)

    df = pd.read_sql_query(
        "SELECT * FROM complaints",
        conn
    )

    conn.close()

    return df


def get_maintenance_dataframe():

    conn = sqlite3.connect(DB_PATH)

    df = pd.read_sql_query(
        "SELECT * FROM maintenance",
        conn
    )

    conn.close()

    return df


def get_report_data():

    complaints = get_complaints_dataframe()
    maintenance = get_maintenance_dataframe()

    total = len(complaints)

    pending = 0
    in_progress = 0
    resolved = 0

    if not complaints.empty:

        pending = int(
            (complaints["status"] == "Pending").sum()
        )

        in_progress = int(
            (complaints["status"] == "In Progress").sum()
        )

        resolved = int(
            (complaints["status"] == "Resolved").sum()
        )

    if not complaints.empty:
        common_category = (
            complaints["category"]
            .value_counts()
            .idxmax()
        )

        top_building = (
            complaints["building"]
            .value_counts()
            .idxmax()
        )

    else:
        common_category = "N/A"
        top_building = "N/A"

    if not maintenance.empty:

        total_cost = float(
            maintenance["cost"].sum()
        )

        average_cost = float(
            maintenance["cost"].mean()
        )

    else:

        total_cost = 0
        average_cost = 0

    return {
        "total": total,
        "pending": pending,
        "in_progress": in_progress,
        "resolved": resolved,
        "common_category": common_category,
        "top_building": top_building,
        "total_cost": total_cost,
        "average_cost": average_cost
    }


def category_data():

    df = get_complaints_dataframe()

    if df.empty:
        return pd.Series(dtype=int)

    return df["category"].value_counts()


def status_data():

    df = get_complaints_dataframe()

    if df.empty:
        return pd.Series(dtype=int)

    return df["status"].value_counts()


def building_data():

    df = get_complaints_dataframe()

    if df.empty:
        return pd.Series(dtype=int)

    return df["building"].value_counts()


def monthly_data():

    df = get_complaints_dataframe()

    if df.empty:
        return pd.Series(dtype=int)

    df["date"] = pd.to_datetime(
        df["date"],
        errors="coerce"
    )

    df = df.dropna(subset=["date"])

    return (
        df.groupby(
            df["date"].dt.to_period("M")
        )
        .size()
    )


def repair_cost_data():

    complaints = get_complaints_dataframe()
    maintenance = get_maintenance_dataframe()

    if complaints.empty or maintenance.empty:
        return pd.Series(dtype=float)

    merged = maintenance.merge(
        complaints[
            ["complaint_id", "category"]
        ],
        on="complaint_id",
        how="left"
    )

    return (
        merged.groupby("category")["cost"]
        .sum()
    )