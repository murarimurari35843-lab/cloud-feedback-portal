from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3

app = Flask(__name__)
app.secret_key = "my_secret_key_123"   # can be any string

DB_NAME = "portal.db"

def db_connect():
    return sqlite3.connect(DB_NAME)

def init_db():
    con = db_connect()
    cur = con.cursor()

    # USERS TABLE
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )
    """)

    # FEEDBACK TABLE
    cur.execute("""
    CREATE TABLE IF NOT EXISTS feedback (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_email TEXT NOT NULL,
        message TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    con.commit()
    con.close()

@app.route("/")
def home():
    return render_template("home.html")

# ---------------- REGISTER ----------------
@app.route("/register", methods=["GET","POST"])
def register():
    message = ""

    if request.method == "POST":
        name = request.form.get("name")   # ✅ NEW
        email = request.form.get("email")
        password = request.form.get("password")

        con = db_connect()
        cur = con.cursor()

        # check existing user
        cur.execute("SELECT * FROM users WHERE email=?", (email,))
        existing = cur.fetchone()

        if existing:
            message = "User already exists ❌"
        else:
            cur.execute(
                "INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
                (name, email, password)
            )
            con.commit()
            message = "Registration Successful ✅"

        con.close()

    return render_template("register.html", message=message)
# ---------------- LOGIN ----------------
@app.route("/login", methods=["GET", "POST"])
def login():
    msg = ""
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        con = db_connect()
        cur = con.cursor()

        cur.execute("SELECT * FROM users WHERE email=? AND password=?", (email, password))
        user = cur.fetchone()
        con.close()

        if user:
            session["user_email"] = email
            return redirect(url_for("dashboard"))
        else:
            msg = "❌ Invalid credentials"

    return render_template("login.html", msg=msg)

# ---------------- DASHBOARD ----------------
@app.route("/dashboard")
def dashboard():

    # 🔐 check login session
    if "user_email" not in session:
        return redirect(url_for("login"))

    email = session["user_email"]

    con = db_connect()
    cur = con.cursor()

    cur.execute(
        "SELECT message, created_at FROM feedback WHERE user_email=? ORDER BY id DESC",
        (email,)
    )

    feedback_list = cur.fetchall()
    con.close()

    return render_template(
        "dashboard.html",
        email=email,
        feedback_list=feedback_list
    )
# ---------------- SUBMIT FEEDBACK ----------------
@app.route("/submit_feedback", methods=["POST"])
def submit_feedback():
    if "user_email" not in session:
        return redirect(url_for("login"))

    message = request.form.get("message")
    email = session["user_email"]

    con = db_connect()
    cur = con.cursor()
    cur.execute("INSERT INTO feedback (user_email, message) VALUES (?, ?)", (email, message))
    con.commit()
    con.close()

    return redirect(url_for("dashboard"))

# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.pop("user_email", None)
    return redirect(url_for("login"))

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000)
