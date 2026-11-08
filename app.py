import os
import re
from datetime import datetime
from functools import wraps

from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

from analyzer import extract_text, analyze_resume

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
ALLOWED_EXTENSIONS = {"pdf", "docx", "txt"}

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "change-this-secret-key")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(BASE_DIR, "resume_analyzer.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024  # 5 MB
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

db = SQLAlchemy(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Analysis(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    job_title = db.Column(db.String(150), nullable=False)
    score = db.Column(db.Integer, nullable=False)
    matched_skills = db.Column(db.Text, default="")
    missing_skills = db.Column(db.Text, default="")
    suggestions = db.Column(db.Text, default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship("User", backref=db.backref("analyses", lazy=True))


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("user_id"):
            flash("Please sign in to continue.", "warning")
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/")
def index():
    if session.get("user_id"):
        return redirect(url_for("dashboard"))
    return render_template("index.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        if not name or not email or len(password) < 8:
            flash("Enter your name, a valid email, and a password of at least 8 characters.", "danger")
            return render_template("register.html")
        if User.query.filter_by(email=email).first():
            flash("An account with that email already exists.", "danger")
            return render_template("register.html")
        user = User(name=name, email=email, password_hash=generate_password_hash(password))
        db.session.add(user)
        db.session.commit()
        session["user_id"] = user.id
        session["user_name"] = user.name
        return redirect(url_for("dashboard"))
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password_hash, password):
            session.clear()
            session["user_id"] = user.id
            session["user_name"] = user.name
            return redirect(url_for("dashboard"))
        flash("Incorrect email or password.", "danger")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


@app.route("/dashboard")
@login_required
def dashboard():
    records = Analysis.query.filter_by(user_id=session["user_id"]).order_by(Analysis.created_at.desc()).all()
    return render_template("dashboard.html", records=records)


@app.route("/analyze", methods=["GET", "POST"])
@login_required
def analyze():
    if request.method == "POST":
        uploaded = request.files.get("resume")
        job_title = request.form.get("job_title", "").strip() or "Target role"
        job_description = request.form.get("job_description", "").strip()

        if not uploaded or not uploaded.filename:
            flash("Choose a resume file first.", "danger")
            return redirect(url_for("analyze"))
        if not allowed_file(uploaded.filename):
            flash("Supported formats: PDF, DOCX, and TXT.", "danger")
            return redirect(url_for("analyze"))
        if not job_description:
            flash("Paste the job description so the resume can be compared against it.", "danger")
            return redirect(url_for("analyze"))

        safe_name = secure_filename(uploaded.filename)
        stored_name = f"{session['user_id']}_{int(datetime.utcnow().timestamp())}_{safe_name}"
        path = os.path.join(app.config["UPLOAD_FOLDER"], stored_name)
        uploaded.save(path)

        try:
            resume_text = extract_text(path)
            if len(resume_text.strip()) < 40:
                raise ValueError("Not enough readable text was found. Try a text-based PDF or DOCX file.")
            result = analyze_resume(resume_text, job_description)
        except Exception as exc:
            if os.path.exists(path):
                os.remove(path)
            flash(str(exc), "danger")
            return redirect(url_for("analyze"))

        record = Analysis(
            user_id=session["user_id"],
            filename=safe_name,
            job_title=job_title[:150],
            score=result["score"],
            matched_skills=", ".join(result["matched_skills"]),
            missing_skills=", ".join(result["missing_skills"]),
            suggestions="\n".join(result["suggestions"])
        )
        db.session.add(record)
        db.session.commit()
        return render_template("result.html", result=result, record=record)

    return render_template("analyze.html")


@app.route("/history/<int:analysis_id>")
@login_required
def history_detail(analysis_id):
    record = Analysis.query.filter_by(id=analysis_id, user_id=session["user_id"]).first_or_404()
    result = {
        "score": record.score,
        "matched_skills": [x for x in record.matched_skills.split(", ") if x],
        "missing_skills": [x for x in record.missing_skills.split(", ") if x],
        "suggestions": [x for x in record.suggestions.splitlines() if x],
        "similarity": None,
    }
    return render_template("result.html", result=result, record=record, historical=True)


@app.errorhandler(413)
def too_large(_error):
    flash("File is too large. Maximum upload size is 5 MB.", "danger")
    return redirect(url_for("analyze"))


with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(debug=True)
