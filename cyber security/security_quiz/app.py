import os
import re
import secrets
from datetime import timedelta
from functools import wraps

import mysql.connector
from flask import Flask, abort, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
app.config.update(
    SECRET_KEY=os.environ.get("SECRET_KEY", "dev-only-change-this-secret-key"),
    PERMANENT_SESSION_LIFETIME=timedelta(hours=8),
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=os.environ.get("FLASK_ENV") == "production",
)


def get_connection():
    return mysql.connector.connect(
        host=os.environ.get("DB_HOST", "127.0.0.1"),
        port=int(os.environ.get("DB_PORT", "3306")),
        user=os.environ.get("DB_USER", "root"),
        password=os.environ.get("DB_PASSWORD", ""),
        database=os.environ.get("DB_NAME", "security_quiz"),
    )


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            flash("Please sign in to continue.", "warning")
            return redirect(url_for("login", next=request.path))
        return view(*args, **kwargs)

    return wrapped


def admin_required(view):
    @wraps(view)
    @login_required
    def wrapped(*args, **kwargs):
        if session.get("role") != "admin":
            abort(403)
        return view(*args, **kwargs)

    return wrapped


@app.before_request
def protect_post_requests():
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_urlsafe(32)
    if request.method == "POST":
        token = request.form.get("csrf_token", "")
        if not secrets.compare_digest(token, session["csrf_token"]):
            abort(400, description="The form expired or could not be verified. Please try again.")


@app.context_processor
def inject_template_values():
    return {"csrf_token": session.get("csrf_token", ""), "current_user": session.get("name")}


def is_valid_email(email):
    return bool(re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email))


@app.get("/")
def index():
    return redirect(url_for("dashboard" if session.get("user_id") else "login"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if session.get("user_id"):
        return redirect(url_for("dashboard"))
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        if not name or not email or not password:
            flash("All fields are required.", "danger")
        elif len(name) > 100 or len(email) > 254 or not is_valid_email(email):
            flash("Enter a valid name and email address.", "danger")
        elif len(password) < 10 or len(password) > 128:
            flash("Use a password between 10 and 128 characters.", "danger")
        else:
            connection = get_connection()
            try:
                cursor = connection.cursor()
                cursor.execute(
                    "INSERT INTO users (name, email, password, role) VALUES (%s, %s, %s, 'user')",
                    (name, email, generate_password_hash(password)),
                )
                connection.commit()
                flash("Account created. Sign in to start your first quiz.", "success")
                return redirect(url_for("login"))
            except mysql.connector.IntegrityError:
                connection.rollback()
                flash("An account with that email already exists.", "warning")
            finally:
                connection.close()
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("user_id"):
        return redirect(url_for("dashboard"))
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        if not email or not password:
            flash("Enter both your email and password.", "danger")
        else:
            connection = get_connection()
            try:
                cursor = connection.cursor(dictionary=True)
                cursor.execute("SELECT id, name, email, password, role FROM users WHERE email = %s", (email,))
                user = cursor.fetchone()
                if user and check_password_hash(user["password"], password):
                    session.clear()
                    session["user_id"] = user["id"]
                    session["name"] = user["name"]
                    session["role"] = user["role"]
                    session.permanent = True
                    destination = request.args.get("next", "")
                    if destination.startswith("/") and not destination.startswith("//"):
                        return redirect(destination)
                    return redirect(url_for("admin_dashboard" if user["role"] == "admin" else "dashboard"))
                flash("Email or password is incorrect.", "danger")
            finally:
                connection.close()
    return render_template("login.html")


@app.post("/logout")
@login_required
def logout():
    session.clear()
    flash("You have been signed out.", "info")
    return redirect(url_for("login"))


@app.get("/dashboard")
@login_required
def dashboard():
    connection = get_connection()
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            "SELECT COUNT(*) AS attempts, COALESCE(ROUND(AVG(percentage), 1), 0) AS average_score "
            "FROM quiz_results WHERE user_id = %s",
            (session["user_id"],),
        )
        stats = cursor.fetchone()
        cursor.execute(
            "SELECT score, total_questions, percentage, attempted_at FROM quiz_results "
            "WHERE user_id = %s ORDER BY attempted_at DESC, id DESC LIMIT 1",
            (session["user_id"],),
        )
        latest = cursor.fetchone()
        cursor.execute(
            "SELECT id, score, total_questions, percentage, attempted_at FROM quiz_results "
            "WHERE user_id = %s ORDER BY attempted_at DESC, id DESC LIMIT 5",
            (session["user_id"],),
        )
        history_rows = cursor.fetchall()
    finally:
        connection.close()
    average = float(stats["average_score"])
    level = "Getting started" if not stats["attempts"] else "Aware" if average < 60 else "Security-minded" if average < 85 else "Security champion"
    return render_template("dashboard.html", stats=stats, latest=latest, history=history_rows, level=level)


@app.get("/quiz")
@login_required
def quiz():
    connection = get_connection()
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            "SELECT id, question, option_a, option_b, option_c, option_d "
            "FROM questions ORDER BY RAND() LIMIT 10"
        )
        questions = cursor.fetchall()
    finally:
        connection.close()
    if not questions:
        flash("No quiz questions are available yet.", "warning")
        return redirect(url_for("dashboard"))
    session["active_quiz_ids"] = [question["id"] for question in questions]
    return render_template("quiz.html", questions=questions)


@app.post("/quiz/result")
@login_required
def quiz_result():
    submitted_ids = request.form.getlist("question_id")
    if not submitted_ids:
        flash("Start a quiz before submitting answers.", "warning")
        return redirect(url_for("quiz"))
    try:
        question_ids = [int(question_id) for question_id in submitted_ids]
    except ValueError:
        abort(400)
    if question_ids != session.get("active_quiz_ids"):
        abort(400, description="This quiz is no longer active. Please start a new quiz.")
    placeholders = ",".join(["%s"] * len(question_ids))
    connection = get_connection()
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            "SELECT id, question, option_a, option_b, option_c, option_d, correct_answer, explanation "
            f"FROM questions WHERE id IN ({placeholders})",
            tuple(question_ids),
        )
        questions = cursor.fetchall()
        if len(questions) != len(set(question_ids)):
            abort(400, description="One or more quiz questions are no longer available.")
        questions_by_id = {question["id"]: question for question in questions}
        questions = [questions_by_id[question_id] for question_id in question_ids]
        reviewed = []
        score = 0
        for question in questions:
            selected = request.form.get(f"answer_{question['id']}", "")
            correct = selected == question["correct_answer"]
            score += int(correct)
            reviewed.append({**question, "selected": selected, "is_correct": correct})
        total = len(questions)
        percentage = round(score * 100 / total, 1) if total else 0
        cursor.execute(
            "INSERT INTO quiz_results (user_id, score, total_questions, percentage) VALUES (%s, %s, %s, %s)",
            (session["user_id"], score, total, percentage),
        )
        connection.commit()
    finally:
        connection.close()
    session.pop("active_quiz_ids", None)
    tips = [
        "Pause before opening unexpected links or attachments.",
        "Use a unique passphrase for every account and store it in a trusted password manager.",
        "Turn on multi-factor authentication and keep your devices and browser updated.",
    ]
    return render_template("result.html", score=score, total=total, percentage=percentage, reviewed=reviewed, tips=tips)


@app.get("/history")
@login_required
def history():
    connection = get_connection()
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            "SELECT id, score, total_questions, percentage, attempted_at FROM quiz_results "
            "WHERE user_id = %s ORDER BY attempted_at DESC, id DESC",
            (session["user_id"],),
        )
        results = cursor.fetchall()
    finally:
        connection.close()
    return render_template("history.html", results=results)


@app.get("/admin")
@admin_required
def admin_dashboard():
    connection = get_connection()
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT COUNT(*) AS total FROM users")
        users_count = cursor.fetchone()["total"]
        cursor.execute("SELECT COUNT(*) AS total FROM questions")
        questions_count = cursor.fetchone()["total"]
        cursor.execute("SELECT COUNT(*) AS total, COALESCE(ROUND(AVG(percentage), 1), 0) AS average FROM quiz_results")
        result_stats = cursor.fetchone()
        cursor.execute(
            "SELECT r.id, u.name, u.email, r.score, r.total_questions, r.percentage, r.attempted_at "
            "FROM quiz_results r JOIN users u ON u.id = r.user_id "
            "ORDER BY r.attempted_at DESC, r.id DESC LIMIT 10"
        )
        recent = cursor.fetchall()
    finally:
        connection.close()
    return render_template(
        "admin.html", users_count=users_count, questions_count=questions_count,
        result_stats=result_stats, recent=recent,
    )


@app.get("/admin/questions")
@admin_required
def questions():
    connection = get_connection()
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM questions ORDER BY id DESC")
        question_rows = cursor.fetchall()
    finally:
        connection.close()
    return render_template("questions.html", questions=question_rows)


def read_question_form():
    data = {key: request.form.get(key, "").strip() for key in (
        "question", "option_a", "option_b", "option_c", "option_d", "correct_answer", "explanation"
    )}
    limits = {"option_a": 500, "option_b": 500, "option_c": 500, "option_d": 500}
    if any(not value for value in data.values()) or any(
        len(value) > limits.get(key, 1000) for key, value in data.items()
    ):
        return None
    if data["correct_answer"] not in {"A", "B", "C", "D"}:
        return None
    return data


@app.route("/admin/questions/add", methods=["GET", "POST"])
@admin_required
def add_question():
    if request.method == "POST":
        data = read_question_form()
        if data is None:
            flash("Complete every field. The correct answer must be A, B, C, or D.", "danger")
        else:
            connection = get_connection()
            try:
                cursor = connection.cursor()
                cursor.execute(
                    "INSERT INTO questions (question, option_a, option_b, option_c, option_d, correct_answer, explanation) "
                    "VALUES (%(question)s, %(option_a)s, %(option_b)s, %(option_c)s, %(option_d)s, %(correct_answer)s, %(explanation)s)",
                    data,
                )
                connection.commit()
                flash("Question added to the quiz bank.", "success")
                return redirect(url_for("questions"))
            finally:
                connection.close()
    return render_template("add_question.html", question=None)


@app.route("/admin/questions/edit/<int:question_id>", methods=["GET", "POST"])
@admin_required
def edit_question(question_id):
    connection = get_connection()
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM questions WHERE id = %s", (question_id,))
        question = cursor.fetchone()
        if question is None:
            abort(404)
        if request.method == "POST":
            data = read_question_form()
            if data is None:
                flash("Complete every field. The correct answer must be A, B, C, or D.", "danger")
            else:
                cursor.execute(
                    "UPDATE questions SET question=%(question)s, option_a=%(option_a)s, option_b=%(option_b)s, "
                    "option_c=%(option_c)s, option_d=%(option_d)s, correct_answer=%(correct_answer)s, "
                    "explanation=%(explanation)s WHERE id=%(id)s",
                    {**data, "id": question_id},
                )
                connection.commit()
                flash("Question updated.", "success")
                return redirect(url_for("questions"))
    finally:
        connection.close()
    return render_template("edit_question.html", question=question)


@app.post("/admin/questions/delete/<int:question_id>")
@admin_required
def delete_question(question_id):
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute("DELETE FROM questions WHERE id = %s", (question_id,))
        connection.commit()
        flash("Question deleted." if cursor.rowcount else "Question not found.", "info")
    finally:
        connection.close()
    return redirect(url_for("questions"))


@app.errorhandler(403)
def forbidden(_error):
    return render_template("error.html", code=403, message="You do not have permission to view this page."), 403


@app.errorhandler(404)
def not_found(_error):
    return render_template("error.html", code=404, message="The requested page could not be found."), 404


@app.errorhandler(400)
def bad_request(error):
    return render_template("error.html", code=400, message=getattr(error, "description", "The request could not be processed.")), 400


if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_DEBUG") == "1")