import sqlite3
from pathlib import Path

DB_NAME = Path(__file__).with_name("expenses.db")


def row_to_dict(row):
    return dict(row) if row else None

def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def create_tables():
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            amount REAL NOT NULL,
            category TEXT NOT NULL,
            subcategory TEXT,
            date TEXT NOT NULL
        )
    """)
    
    conn.commit()
    conn.close()


def add_expense(title, amount, category, subcategory, date):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO expenses (title, amount, category, subcategory, date)
        VALUES (?, ?, ?, ?, ?)
        """,
        (title, amount, category, subcategory, date),
    )

    expense_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return get_expense(expense_id)


def get_expenses():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, title, amount, category, subcategory, date
        FROM expenses
        ORDER BY date DESC, id DESC
    """)
    expenses = [row_to_dict(row) for row in cursor.fetchall()]

    conn.close()
    return expenses


def search_expenses(category=None, from_date=None, to_date=None):
    conn = get_connection()
    cursor = conn.cursor()

    filters = []
    params = []

    if category:
        filters.append("LOWER(category) = LOWER(?)")
        params.append(category)
    if from_date:
        filters.append("date >= ?")
        params.append(from_date)
    if to_date:
        filters.append("date <= ?")
        params.append(to_date)

    where_clause = f"WHERE {' AND '.join(filters)}" if filters else ""
    cursor.execute(
        f"""
        SELECT id, title, amount, category, subcategory, date
        FROM expenses
        {where_clause}
        ORDER BY date DESC, id DESC
        """,
        params,
    )
    expenses = [row_to_dict(row) for row in cursor.fetchall()]

    conn.close()
    return expenses


def get_expense(expense_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT id, title, amount, category, subcategory, date
        FROM expenses
        WHERE id = ?
        """,
        (expense_id,),
    )
    expense = row_to_dict(cursor.fetchone())

    conn.close()
    return expense


def update_expense(expense_id, title, amount, category, subcategory, date):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE expenses
        SET title = ?, amount = ?, category = ?, subcategory = ?, date = ?
        WHERE id = ?
        """,
        (title, amount, category, subcategory, date, expense_id),
    )
    updated = cursor.rowcount > 0

    conn.commit()
    conn.close()

    return get_expense(expense_id) if updated else None


def delete_expense(expense_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
    deleted = cursor.rowcount > 0

    conn.commit()
    conn.close()
    return deleted


def get_summary_by_category():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT category, COUNT(*) AS count, SUM(amount) AS total_amount
        FROM expenses
        GROUP BY category
        ORDER BY total_amount DESC
    """)
    summary = [row_to_dict(row) for row in cursor.fetchall()]

    conn.close()
    return summary


def get_summary_by_month():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT substr(date, 1, 7) AS month, COUNT(*) AS count, SUM(amount) AS total_amount
        FROM expenses
        GROUP BY month
        ORDER BY month DESC
    """)
    summary = [row_to_dict(row) for row in cursor.fetchall()]

    conn.close()
    return summary
