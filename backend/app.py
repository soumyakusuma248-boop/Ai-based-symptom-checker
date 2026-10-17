"""
SymptomAI — Complete Python-only Flask Web Application
Server-rendered with Jinja2 templates, session-based auth, SQLite DB.
Run: python app.py  (inside /backend)
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from flask import (Flask, render_template, request, redirect, url_for,
                   session, flash, jsonify, abort)
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from config import Config
import json
from datetime import datetime
from functools import wraps

# ── App factory ──────────────────────────────────────────────────────────────
app = Flask(__name__)
app.config.from_object(Config)

db     = SQLAlchemy(app)
bcrypt = Bcrypt(app)

# ── Models ───────────────────────────────────────────────────────────────────
class User(db.Model):
    __tablename__ = "users"
    id            = db.Column(db.Integer, primary_key=True)
    username      = db.Column(db.String(80),  unique=True, nullable=False)
    email         = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    is_admin      = db.Column(db.Boolean, default=False)
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)
    checks = db.relationship("SymptomCheck", backref="user", lazy=True,
                             cascade="all, delete-orphan")

class SymptomConditionMapping(db.Model):
    __tablename__ = "symptom_condition_mappings"
    id          = db.Column(db.Integer, primary_key=True)
    name        = db.Column(db.String(120), nullable=False)
    symptoms    = db.Column(db.Text,  nullable=False)   # JSON list
    condition   = db.Column(db.String(200), nullable=False)
    urgency     = db.Column(db.String(20),  nullable=False)
    description = db.Column(db.Text, nullable=True)
    advice      = db.Column(db.Text, nullable=True)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at  = db.Column(db.DateTime, default=datetime.utcnow,
                             onupdate=datetime.utcnow)

    def symptoms_list(self):
        return json.loads(self.symptoms)

    # Alias used by triage_engine.py
    def get_symptoms_list(self):
        return self.symptoms_list()

class SymptomCheck(db.Model):
    __tablename__ = "symptom_checks"
    id                = db.Column(db.Integer, primary_key=True)
    user_id           = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    symptoms_json     = db.Column(db.Text, nullable=False)   # encrypted or plain
    free_text         = db.Column(db.Text, nullable=True)
    triage_level      = db.Column(db.String(20), nullable=False)
    matched_json      = db.Column(db.Text, nullable=False)   # JSON list
    confidence_score  = db.Column(db.Float, default=0.0)
    created_at        = db.Column(db.DateTime, default=datetime.utcnow)

    def symptoms(self):
        try: return json.loads(self.symptoms_json)
        except: return []

    def matched_conditions(self):
        try: return json.loads(self.matched_json)
        except: return []

# ── Encryption (optional, graceful fallback) ─────────────────────────────────
try:
    from utils.encryption import DataEncryptor
    _enc = DataEncryptor(app.config.get("ENCRYPTION_KEY",""))
    def encrypt(s): return _enc.encrypt(s) if s else ""
    def decrypt(s): return _enc.decrypt(s) if s else ""
except Exception:
    def encrypt(s): return s or ""
    def decrypt(s): return s or ""

# ── Triage engine ─────────────────────────────────────────────────────────────
from utils.triage_engine import run_triage

# ── Auth helpers ──────────────────────────────────────────────────────────────
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to continue.", "warning")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        user = db.session.get(User, session["user_id"])
        if not user or not user.is_admin:
            flash("Admin access required.", "danger")
            return redirect(url_for("home"))
        return f(*args, **kwargs)
    return decorated

def current_user():
    if "user_id" in session:
        return db.session.get(User, session["user_id"])
    return None

# ── Symptom list ──────────────────────────────────────────────────────────────
AVAILABLE_SYMPTOMS = sorted([
    "Fever", "Chills", "Cough", "Sore throat", "Runny nose", "Nasal congestion",
    "Shortness of breath", "Difficulty breathing", "Chest pain", "Chest tightness",
    "Headache", "Severe headache", "Body aches", "Muscle pain", "Fatigue",
    "Nausea", "Vomiting", "Diarrhea", "Stomach pain", "Abdominal pain",
    "Loss of appetite", "Itching", "Rash", "Hives", "Swelling",
    "Blurred vision", "Red eyes", "Eye discharge", "Dizziness", "Fainting",
    "Confusion", "Seizure", "Numbness", "Weakness", "Joint pain",
    "Back pain", "Frequent urination", "Burning urination", "Blood in urine",
    "Excessive thirst", "Unexplained weight loss", "Wheezing",
    "Persistent sadness", "Anxiety", "Panic attacks", "Loss of interest",
    "Bruising", "Severe bleeding", "Rapid heart rate",
])

# ── Mocked care data ──────────────────────────────────────────────────────────
def nearby_care(triage_level):
    if triage_level == "emergency":
        return [
            {"name":"City General Hospital ER","type":"Emergency Room","distance":"0.8 mi","phone":"911","wait":"Immediate"},
            {"name":"Metro Medical Center ER","type":"Emergency Room","distance":"1.2 mi","phone":"911","wait":"Immediate"},
        ]
    elif triage_level == "see_doctor":
        return [
            {"name":"QuickCare Urgent Care","type":"Urgent Care","distance":"0.5 mi","phone":"(555) 234-5678","wait":"~20 min"},
            {"name":"HealthFirst Primary Care","type":"Primary Care","distance":"1.1 mi","phone":"(555) 987-6543","wait":"By appt"},
            {"name":"MedExpress Walk-in","type":"Walk-in Clinic","distance":"1.9 mi","phone":"(555) 456-7890","wait":"~35 min"},
        ]
    else:
        return [
            {"name":"Community Pharmacy","type":"Pharmacy","distance":"0.3 mi","phone":"(555) 111-2222","wait":"No wait"},
            {"name":"Telehealth – Virtual Visit","type":"Telehealth","distance":"Online","phone":"(555) 800-0000","wait":"~5 min"},
        ]

def next_steps(triage_level):
    return {
        "emergency":  ["Call 911 (emergency services) immediately.",
                       "Do not drive yourself — call for help.",
                       "Go to the nearest Emergency Room without delay."],
        "see_doctor": ["Schedule an appointment with your primary care physician.",
                       "If symptoms worsen significantly, go to urgent care.",
                       "Bring a list of your symptoms and their start date."],
        "self_care":  ["Rest at home and monitor your symptoms.",
                       "Stay hydrated and use OTC medications as needed.",
                       "See a doctor if symptoms worsen or persist beyond 5–7 days."],
    }.get(triage_level, [])

# ── Routes: Public ────────────────────────────────────────────────────────────
@app.route("/")
def home():
    return render_template("home.html", user=current_user())

@app.route("/register", methods=["GET","POST"])
def register():
    if "user_id" in session:
        return redirect(url_for("checker"))
    error = None
    if request.method == "POST":
        username = request.form.get("username","").strip()
        email    = request.form.get("email","").strip().lower()
        password = request.form.get("password","")
        confirm  = request.form.get("confirm","")
        if not username or not email or not password:
            error = "All fields are required."
        elif password != confirm:
            error = "Passwords do not match."
        elif len(password) < 6:
            error = "Password must be at least 6 characters."
        elif User.query.filter_by(email=email).first():
            error = "Email already registered."
        elif User.query.filter_by(username=username).first():
            error = "Username already taken."
        else:
            pw_hash = bcrypt.generate_password_hash(password).decode("utf-8")
            u = User(username=username, email=email, password_hash=pw_hash)
            db.session.add(u); db.session.commit()
            session["user_id"] = u.id
            session["username"] = u.username
            session["is_admin"] = u.is_admin
            flash("Account created! Welcome to SymptomAI.", "success")
            return redirect(url_for("checker"))
    return render_template("register.html", error=error)

@app.route("/login", methods=["GET","POST"])
def login():
    if "user_id" in session:
        return redirect(url_for("checker"))
    error = None
    if request.method == "POST":
        email    = request.form.get("email","").strip().lower()
        password = request.form.get("password","")
        u = User.query.filter_by(email=email).first()
        if not u or not bcrypt.check_password_hash(u.password_hash, password):
            error = "Invalid email or password."
        else:
            session["user_id"]  = u.id
            session["username"] = u.username
            session["is_admin"] = u.is_admin
            flash(f"Welcome back, {u.username}!", "success")
            return redirect(url_for("checker"))
    return render_template("login.html", error=error)

@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("home"))

# ── Routes: Symptom Checker ───────────────────────────────────────────────────
@app.route("/checker", methods=["GET","POST"])
@login_required
def checker():
    result = None
    selected = []
    free_text = ""
    error = None

    if request.method == "POST":
        selected  = request.form.getlist("symptoms")
        free_text = request.form.get("free_text","").strip()

        if not selected and not free_text:
            error = "Please select at least one symptom or describe your symptoms."
        else:
            mappings = SymptomConditionMapping.query.all()
            triage   = run_triage(selected, free_text, mappings)

            # Persist encrypted check
            check = SymptomCheck(
                user_id          = session["user_id"],
                symptoms_json    = encrypt(json.dumps(selected)),
                free_text        = encrypt(free_text) if free_text else None,
                triage_level     = triage["triage_level"],
                matched_json     = json.dumps(triage["matched_conditions"]),
                confidence_score = triage["confidence_score"],
            )
            db.session.add(check); db.session.commit()

            result = {
                **triage,
                "next_steps":  next_steps(triage["triage_level"]),
                "nearby_care": nearby_care(triage["triage_level"]),
            }

    return render_template(
        "checker.html",
        user=current_user(),
        available_symptoms=AVAILABLE_SYMPTOMS,
        selected=selected,
        free_text=free_text,
        result=result,
        error=error,
    )

# ── Routes: History ───────────────────────────────────────────────────────────
@app.route("/history")
@login_required
def history():
    page  = request.args.get("page", 1, type=int)
    query = (SymptomCheck.query
             .filter_by(user_id=session["user_id"])
             .order_by(SymptomCheck.created_at.desc())
             .paginate(page=page, per_page=10, error_out=False))
    checks = []
    for c in query.items:
        raw_syms = decrypt(c.symptoms_json)
        if isinstance(raw_syms, list):
            syms = raw_syms
        elif isinstance(raw_syms, str):
            try: syms = json.loads(raw_syms)
            except: syms = [raw_syms] if raw_syms else []
        else:
            syms = []
        checks.append({
            "id":               c.id,
            "triage_level":     c.triage_level,
            "confidence_score": c.confidence_score,
            "created_at":       c.created_at,
            "symptoms":         syms,
            "free_text":        decrypt(c.free_text) if c.free_text else "",
            "matched_conditions": c.matched_conditions(),
        })
    return render_template("history.html", user=current_user(),
                           checks=checks, pagination=query)

@app.route("/history/delete/<int:check_id>", methods=["POST"])
@login_required
def history_delete(check_id):
    c = SymptomCheck.query.filter_by(id=check_id,
                                     user_id=session["user_id"]).first_or_404()
    db.session.delete(c); db.session.commit()
    flash("Record deleted.", "success")
    return redirect(url_for("history"))

# ── Routes: Admin ─────────────────────────────────────────────────────────────
@app.route("/admin")
@admin_required
def admin_dashboard():
    from sqlalchemy import func
    stats = {
        "total_checks":    SymptomCheck.query.count(),
        "emergency":       SymptomCheck.query.filter_by(triage_level="emergency").count(),
        "see_doctor":      SymptomCheck.query.filter_by(triage_level="see_doctor").count(),
        "self_care":       SymptomCheck.query.filter_by(triage_level="self_care").count(),
        "total_users":     User.query.count(),
        "total_mappings":  SymptomConditionMapping.query.count(),
    }
    mappings = SymptomConditionMapping.query.order_by(
                   SymptomConditionMapping.id).all()
    users    = User.query.order_by(User.id).all()
    return render_template("admin.html", user=current_user(),
                           stats=stats, mappings=mappings, users=users)

@app.route("/admin/mapping/add", methods=["GET","POST"])
@admin_required
def admin_add_mapping():
    error = None
    if request.method == "POST":
        name        = request.form.get("name","").strip()
        symptoms_raw= request.form.get("symptoms","").strip()
        condition   = request.form.get("condition","").strip()
        urgency     = request.form.get("urgency","see_doctor")
        description = request.form.get("description","").strip()
        advice      = request.form.get("advice","").strip()
        if not name or not symptoms_raw or not condition:
            error = "Name, symptoms, and condition are required."
        elif urgency not in ("self_care","see_doctor","emergency"):
            error = "Invalid urgency level."
        else:
            syms = [s.strip() for s in symptoms_raw.split(",") if s.strip()]
            m = SymptomConditionMapping(
                    name=name, symptoms=json.dumps(syms),
                    condition=condition, urgency=urgency,
                    description=description, advice=advice)
            db.session.add(m); db.session.commit()
            flash(f"Mapping '{name}' added.", "success")
            return redirect(url_for("admin_dashboard"))
    return render_template("mapping_form.html", user=current_user(),
                           mapping=None, error=error, action="Add")

@app.route("/admin/mapping/edit/<int:mid>", methods=["GET","POST"])
@admin_required
def admin_edit_mapping(mid):
    m = db.session.get(SymptomConditionMapping, mid) or abort(404)
    error = None
    if request.method == "POST":
        m.name        = request.form.get("name","").strip()
        symptoms_raw  = request.form.get("symptoms","").strip()
        m.condition   = request.form.get("condition","").strip()
        m.urgency     = request.form.get("urgency","see_doctor")
        m.description = request.form.get("description","").strip()
        m.advice      = request.form.get("advice","").strip()
        if not m.name or not symptoms_raw or not m.condition:
            error = "Name, symptoms, and condition are required."
        elif m.urgency not in ("self_care","see_doctor","emergency"):
            error = "Invalid urgency level."
        else:
            syms = [s.strip() for s in symptoms_raw.split(",") if s.strip()]
            m.symptoms  = json.dumps(syms)
            m.updated_at = datetime.utcnow()
            db.session.commit()
            flash(f"Mapping '{m.name}' updated.", "success")
            return redirect(url_for("admin_dashboard"))
    return render_template("mapping_form.html", user=current_user(),
                           mapping=m, error=error, action="Edit")

@app.route("/admin/mapping/delete/<int:mid>", methods=["POST"])
@admin_required
def admin_delete_mapping(mid):
    m = db.session.get(SymptomConditionMapping, mid) or abort(404)
    db.session.delete(m); db.session.commit()
    flash(f"Mapping deleted.", "success")
    return redirect(url_for("admin_dashboard"))

# ── Template filters ──────────────────────────────────────────────────────────
@app.template_filter("symptom_list")
def symptom_list_filter(val):
    """Decrypt & decode symptoms JSON → Python list"""
    try:
        raw = decrypt(val)
        if isinstance(raw, list): return raw
        return json.loads(raw)
    except: return []

@app.template_filter("fmt_date")
def fmt_date_filter(dt):
    if not dt: return ""
    return dt.strftime("%b %d, %Y  %I:%M %p")

# ── DB init & seed ────────────────────────────────────────────────────────────
def init_db():
    db.create_all()
    # Seed condition mappings
    if SymptomConditionMapping.query.count() == 0:
        from utils.seed_data import INITIAL_MAPPINGS
        for data in INITIAL_MAPPINGS:
            db.session.add(SymptomConditionMapping(
                name=data["name"], symptoms=json.dumps(data["symptoms"]),
                condition=data["condition"], urgency=data["urgency"],
                description=data.get("description",""),
                advice=data.get("advice","")))
        db.session.commit()
        print(f"✅ Seeded {SymptomConditionMapping.query.count()} mappings.")
    # Default admin
    if not User.query.filter_by(email="admin@symptomchecker.com").first():
        pw = bcrypt.generate_password_hash("Admin@1234").decode("utf-8")
        db.session.add(User(username="admin",
                            email="admin@symptomchecker.com",
                            password_hash=pw, is_admin=True))
        db.session.commit()
        print("✅ Admin user: admin@symptomchecker.com / Admin@1234")

# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    with app.app_context():
        init_db()
    print("\n🩺 SymptomAI is running → http://127.0.0.1:5000\n")
    app.run(host="127.0.0.1", port=5000, debug=True)
