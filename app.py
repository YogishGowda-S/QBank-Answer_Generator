from flask import Flask, render_template, request, redirect, session, send_file
import sqlite3
import os
import re

app = Flask(__name__)
app.secret_key = "qbank_secret_key"
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

DATABASE = 'qbank_app.db'

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, email TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)')
    cursor.execute('CREATE TABLE IF NOT EXISTS subjects (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, name TEXT NOT NULL, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY (user_id) REFERENCES users(id))')
    cursor.execute('CREATE TABLE IF NOT EXISTS questions (id INTEGER PRIMARY KEY AUTOINCREMENT, subject_id INTEGER NOT NULL, question_text TEXT NOT NULL, marks INTEGER, unit TEXT, FOREIGN KEY (subject_id) REFERENCES subjects(id))')
    cursor.execute('CREATE TABLE IF NOT EXISTS note_chunks (id INTEGER PRIMARY KEY AUTOINCREMENT, subject_id INTEGER NOT NULL, source_file TEXT, chunk_text TEXT NOT NULL, FOREIGN KEY (subject_id) REFERENCES subjects(id))')
    cursor.execute('CREATE TABLE IF NOT EXISTS answers (id INTEGER PRIMARY KEY AUTOINCREMENT, question_id INTEGER NOT NULL, answer_text TEXT, word_count INTEGER, FOREIGN KEY (question_id) REFERENCES questions(id))')
    conn.commit()
    conn.close()

init_db()

def generate_sample_answer(question):
    marks = question["marks"] if question["marks"] > 0 else 10
    return f"<strong>Answer ({marks} marks):</strong><br><p>Sample Answer - AI generation feature coming soon. Please refer to your course materials and notes for complete answers.</p>"

@app.route("/")
def home():
    return redirect("/login") if "user_id" not in session else redirect("/dashboard")

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        db = get_db()
        cursor = db.cursor()
        try:
            cursor.execute("INSERT INTO users (email, password_hash) VALUES (?, ?)", (email, password))
            db.commit()
            return redirect("/login")
        except:
            return "Email already exists. <a href='/signup'>Try again</a>"
        finally:
            db.close()
    return render_template("signup.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT id FROM users WHERE email=? AND password_hash=?", (email, password))
        user = cursor.fetchone()
        db.close()
        if user:
            session["user_id"] = user[0]
            return redirect("/dashboard")
        return "Invalid credentials. <a href='/login'>Try again</a>"
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect("/login")
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT id, name FROM subjects WHERE user_id=?", (session["user_id"],))
    subjects = cursor.fetchall()
    db.close()
    return render_template("dashboard.html", subjects=subjects)

@app.route("/add_subject", methods=["GET", "POST"])
def add_subject():
    if "user_id" not in session:
        return redirect("/login")
    if request.method == "POST":
        name = request.form["name"]
        db = get_db()
        cursor = db.cursor()
        cursor.execute("INSERT INTO subjects (user_id, name) VALUES (?, ?)", (session["user_id"], name))
        db.commit()
        db.close()
        return redirect("/dashboard")
    return render_template("add_subject.html")

@app.route("/subject/<int:subject_id>")
def subject_detail(subject_id):
    if "user_id" not in session:
        return redirect("/login")
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT id, name FROM subjects WHERE id=? AND user_id=?", (subject_id, session["user_id"]))
    subject = cursor.fetchone()
    cursor.execute("SELECT q.question_text, q.marks, a.answer_text FROM questions q LEFT JOIN answers a ON q.id = a.question_id WHERE q.subject_id=?", (subject_id,))
    qa_pairs = cursor.fetchall()
    db.close()
    return render_template("subject.html", subject=subject, qa_pairs=qa_pairs) if subject else "Not found"

@app.route("/upload/<int:subject_id>", methods=["GET", "POST"])
def upload(subject_id):
    if "user_id" not in session:
        return redirect("/login")
    
    if request.method == "POST":
        try:
            db = get_db()
            cursor = db.cursor()
            
            # Add sample questions
            sample_questions = [
                {"text": "Explain the concept of normalization in DBMS", "marks": 10},
                {"text": "What is a transaction and its properties?", "marks": 10},
                {"text": "Define indexing and its types", "marks": 5},
            ]
            
            cursor.execute("DELETE FROM answers WHERE question_id IN (SELECT id FROM questions WHERE subject_id=?)", (subject_id,))
            cursor.execute("DELETE FROM questions WHERE subject_id=?", (subject_id,))
            db.commit()
            
            for q in sample_questions:
                cursor.execute("INSERT INTO questions (subject_id, question_text, marks) VALUES (?, ?, ?)", (subject_id, q["text"], q["marks"]))
                question_id = cursor.lastrowid
                answer = generate_sample_answer(q)
                cursor.execute("INSERT INTO answers (question_id, answer_text, word_count) VALUES (?, ?, ?)", (question_id, answer, len(answer.split())))
            
            db.commit()
            db.close()
            
            return redirect(f"/subject/{subject_id}")
        except Exception as e:
            return f"Error: {str(e)}"
    
    return render_template("upload.html", subject_id=subject_id)

@app.route("/download/<int:subject_id>")
def download(subject_id):
    if "user_id" not in session:
        return redirect("/login")
    
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT q.question_text, q.marks, a.answer_text FROM questions q LEFT JOIN answers a ON q.id = a.question_id WHERE q.subject_id=?", (subject_id,))
    rows = cursor.fetchall()
    cursor.execute("SELECT name FROM subjects WHERE id=?", (subject_id,))
    subject = cursor.fetchone()
    db.close()
    
    if not rows:
        return "No answers to download"
    
    return "PDF download feature coming soon"

if __name__ == "__main__":
    app.run(debug=True)
