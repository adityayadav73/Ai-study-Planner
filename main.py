from flask import Flask, render_template, request, redirect, session
import sqlite3
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "secret123"

# ================= DATABASE =================
def init_db():
    conn = sqlite3.connect("study.db")
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS study_data (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user TEXT,
        subject TEXT,
        preferred_time TEXT,
        reminder_time TEXT,
        revision_time INTEGER,
        response TEXT,
        study_time INTEGER,
        date TEXT
    )
    """)

    conn.commit()
    conn.close()

init_db()

# ================= ROUTES =================

# 🏠 Home
@app.route("/")
def home():
    return render_template("blog.html")


# 🔐 Register
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if len(username) < 4:
            return render_template("register.html", error="Username must be at least 4 characters")

        if len(password) < 6:
            return render_template("register.html", error="Password must be at least 6 characters")

        conn = sqlite3.connect("study.db")
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM users WHERE username=?", (username,))
        if cursor.fetchone():
            conn.close()
            return render_template("register.html", error="User already exists ❌")

        hashed_password = generate_password_hash(password)

        cursor.execute(
            "INSERT INTO users (username, password) VALUES (?, ?)",
            (username, hashed_password)
        )

        conn.commit()
        conn.close()

        return redirect("/login")

    return render_template("register.html")


# 🔐 Login
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = sqlite3.connect("study.db")
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM users WHERE username=?", (username,))
        user = cursor.fetchone()
        conn.close()

        if user and check_password_hash(user[2], password):
            session["user"] = username
            return redirect("/form")
        else:
            return render_template("login.html", error="Invalid login ❌")

    return render_template("login.html")


# 🚪 Logout
@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect("/login")


# 📋 Form Page
@app.route("/form")
def form():
    if "user" not in session:
        return redirect("/login")

    return render_template("reminder.html", user=session["user"])


# 📥 Save Study Data
@app.route("/submit", methods=["POST"])
def submit():
    if "user" not in session:
        return redirect("/login")

    user = session["user"]

    subject = request.form["subject"]
    preferred_time = request.form["preferred_time"]
    reminder_time = request.form["reminder_time"]
    revision_time = request.form["revision_time"]
    response = request.form["response"]
    study_time = int(request.form["study_time"])

    date = datetime.now().strftime("%Y-%m-%d")

    conn = sqlite3.connect("study.db")
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO study_data 
    (user, subject, preferred_time, reminder_time, revision_time, response, study_time, date)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (user, subject, preferred_time, reminder_time, revision_time, response, study_time, date))

    conn.commit()
    conn.close()

    return redirect("/dashboard")


# 📊 Dashboard
@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/login")

    user = session["user"]

    conn = sqlite3.connect("study.db")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT subject, study_time, date FROM study_data WHERE user=?",
        (user,)
    )
    data = cursor.fetchall()
    conn.close()

    total_time = sum([row[1] for row in data]) if data else 0

    labels = [row[2] for row in data]
    values = [row[1] for row in data]

    # 🔥 Streak
    streak = 0
    for row in reversed(data):
        if row[1] > 0:
            streak += 1
        else:
            break

    # 🤖 AI Prediction
    if len(data) >= 5:
        avg = total_time / len(data)
        if avg > 60:
            prediction = "🔥 High performance expected!"
        elif avg > 30:
            prediction = "👍 Moderate performance"
        else:
            prediction = "⚠️ Improve consistency"
    else:
        prediction = "Not enough data"

    return render_template(
        "dashboard.html",
        user=user,
        data=data,
        total_time=total_time,
        labels=labels,
        values=values,
        streak=streak,
        prediction=prediction
    )


# ================= RUN =================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)