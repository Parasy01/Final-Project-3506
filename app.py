from flask import Flask, render_template, request, redirect
import sqlite3
from datetime import datetime

app = Flask(__name__)

DAILY_GOAL = 2000

def init_db():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS food (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            calories INTEGER,
            created_at TEXT,
            category TEXT
        )
    """)

    existing_columns = [col[1] for col in cursor.execute("PRAGMA table_info(food)").fetchall()]

    if "created_at" not in existing_columns:
        cursor.execute("ALTER TABLE food ADD COLUMN created_at TEXT")

    if "category" not in existing_columns:
        cursor.execute("ALTER TABLE food ADD COLUMN category TEXT")

    conn.commit()
    conn.close()

init_db()

@app.route("/")
def index():
    search = request.args.get("search", "").strip()

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    if search:
        cursor.execute("""
            SELECT id, name, calories, created_at, category
            FROM food
            WHERE name LIKE ? OR category LIKE ?
            ORDER BY id DESC
        """, ('%' + search + '%', '%' + search + '%'))
    else:
        cursor.execute("""
            SELECT id, name, calories, created_at, category
            FROM food
            ORDER BY id DESC
        """)

    foods = cursor.fetchall()
    conn.close()

    total = sum(food[2] for food in foods)
    count = len(foods)
    remaining = max(DAILY_GOAL - total, 0)
    progress = min(int((total / DAILY_GOAL) * 100), 100) if DAILY_GOAL > 0 else 0

    if total < DAILY_GOAL:
        status_message = f"You are under your goal by {DAILY_GOAL - total} calories."
        status_type = "good"
    elif total == DAILY_GOAL:
        status_message = "Perfect! You reached your daily calorie goal."
        status_type = "perfect"
    else:
        status_message = f"You are over your goal by {total - DAILY_GOAL} calories."
        status_type = "warning"

    chart_labels = [f"{food[1]} ({food[4] or 'Other'})" for food in foods[:6]]
    chart_data = [food[2] for food in foods[:6]]

    return render_template(
        "index.html",
        foods=foods,
        total=total,
        count=count,
        goal=DAILY_GOAL,
        remaining=remaining,
        progress=progress,
        search=search,
        status_message=status_message,
        status_type=status_type,
        chart_labels=chart_labels,
        chart_data=chart_data
    )

@app.route("/add", methods=["GET", "POST"])
def add():
    if request.method == "POST":
        name = request.form["name"]
        calories = int(request.form["calories"])
        category = request.form["category"]
        created_at = datetime.now().strftime("%Y-%m-%d")

        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO food (name, calories, created_at, category)
            VALUES (?, ?, ?, ?)
        """, (name, calories, created_at, category))
        conn.commit()
        conn.close()

        return redirect("/")

    return render_template("add.html")

@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit(id):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    if request.method == "POST":
        name = request.form["name"]
        calories = int(request.form["calories"])
        category = request.form["category"]

        cursor.execute("""
            UPDATE food
            SET name=?, calories=?, category=?
            WHERE id=?
        """, (name, calories, category, id))
        conn.commit()
        conn.close()
        return redirect("/")

    cursor.execute("""
        SELECT id, name, calories, created_at, category
        FROM food
        WHERE id=?
    """, (id,))
    food = cursor.fetchone()
    conn.close()

    return render_template("edit.html", food=food)

@app.route("/delete/<int:id>")
def delete(id):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM food WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True)