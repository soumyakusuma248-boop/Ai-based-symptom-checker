# SymptomAI — AI-Based Symptom Checker

A complete, production-quality **Flask web application** that accepts patient-reported symptoms and returns a safe, rule-based triage recommendation along with possible related conditions.

---

## Features

| Feature | Details |
|---|---|
| ✅ Symptom input | Checkbox grid (50 symptoms) + free-text description |
| 🚦 Triage engine | Rule-based classifier → `self_care` / `see_doctor` / `emergency` |
| ⚠️ Cautious mode | When confidence < 35%, auto-escalates to higher urgency |
| 🔴 Red-flag override | 25 critical keywords (chest pain, seizure…) force emergency instantly |
| 🩺 Related conditions | Top-5 matched conditions with match %, urgency, description |
| 📋 Next steps | Tailored action list per triage level |
| 📍 Nearby care | Mocked care options (pharmacy, urgent care, ER) based on urgency |
| 📜 History log | Paginated per-user history with expandable details and delete |
| 🔒 Data encryption | Fernet symmetric encryption on all stored health data |
| 👤 User auth | Session-based register/login/logout with bcrypt-hashed passwords |
| 🔑 Admin panel | Add/edit/delete symptom-condition mappings, view users, live stats |
| ♿ Accessibility | WCAG 2.1 AA: skip links, focus-visible, ARIA labels throughout |
| ⚕️ Disclaimer | Prominent medical disclaimer on every health-facing page |

---

## Quick Start

### Prerequisites
- Python 3.9+ installed
- Internet access for the first `pip install` run

### 1 — Install dependencies

```bat
cd backend
venv\Scripts\pip install Flask Flask-SQLAlchemy Flask-Bcrypt cryptography python-dotenv
```

> **Or** double-click **`start.bat`** in the project root — it activates the venv and starts the server automatically.

### 2 — Run the server

```bat
# From project root:
start.bat

# Or manually:
cd backend
venv\Scripts\python app.py
```

### 3 — Open in browser

```
http://127.0.0.1:5000
```

The database is created automatically on first run and seeded with **20 symptom-condition mappings**.

---

## Default Accounts

| Role | Email | Password |
|---|---|---|
| Admin | `admin@symptomchecker.com` | `Admin@1234` |
| User | *(register your own)* | — |

---

## Project Structure

```
Ai based symptom checker/
├── start.bat                    ← Double-click to launch
└── backend/
    ├── app.py                   ← Main Flask app (routes, models, auth)
    ├── config.py                ← Configuration (loads config.env)
    ├── config.env               ← Environment variables (SECRET_KEY etc.)
    ├── requirements.txt         ← Python dependencies
    ├── venv/                    ← Python virtual environment
    ├── templates/
    │   ├── base.html            ← Navbar, flash messages, shared CSS
    │   ├── home.html            ← Landing page
    │   ├── login.html           ← Login form
    │   ├── register.html        ← Registration form
    │   ├── checker.html         ← Symptom checker + triage result
    │   ├── history.html         ← User history log
    │   ├── admin.html           ← Admin dashboard (stats, mappings, users)
    │   └── mapping_form.html    ← Add/edit mapping form
    └── utils/
        ├── triage_engine.py     ← Core rule-based triage classifier
        ├── encryption.py        ← Fernet data encryption helper
        └── seed_data.py         ← 20 initial symptom-condition mappings
```

---

## Triage Logic

The triage engine (`utils/triage_engine.py`) works in three phases:

### Phase 1 — Red-flag override
25 critical phrases (e.g. "chest pain", "seizure", "coughing blood") are checked against all input. Any match **immediately** returns `emergency` with 100% confidence.

### Phase 2 — Keyword matching
Each mapping's symptom keywords are scored against the user's selected symptoms and parsed free-text:
```
score = matched_keywords / total_mapping_keywords
```
All mappings with score > 0 are ranked. The top 5 are returned as related conditions.

### Phase 3 — Cautious override
If the best match score < **35%**, the system:
1. Escalates the urgency one level (self_care → see_doctor, or see_doctor → emergency)
2. Adds a ⚠️ cautious mode banner in the result
3. Sets `cautious_override: True` in the response

This satisfies the requirement: *"System must default to a cautious (higher urgency) recommendation when confidence is low."*

---

## Knowledge Base

20 pre-seeded conditions covering:

| Category | Examples |
|---|---|
| Respiratory | Common Cold, Influenza, Pneumonia, Asthma Attack |
| Cardiac | Heart Attack, Hypertensive Emergency |
| Neurological | Migraine, Stroke, Sepsis Warning |
| Gastrointestinal | Gastroenteritis, Appendicitis |
| Urinary | UTI |
| Musculoskeletal | Sprain, Fracture |
| Allergic | Mild Allergy, Anaphylaxis |
| Metabolic | Possible Diabetes |
| Mental Health | Depression/Anxiety |
| Eye | Conjunctivitis |

**Admins can add/edit/delete mappings** at `/admin` without touching code.

---

## Security

| Control | Implementation |
|---|---|
| Password hashing | bcrypt via Flask-Bcrypt |
| Health data encryption | Fernet symmetric encryption (cryptography library) |
| Session security | `SESSION_COOKIE_HTTPONLY=True`, `SESSION_COOKIE_SAMESITE=Lax` |
| Access control | `@login_required` and `@admin_required` decorators on all protected routes |
| CSRF-like protection | Admin destructive actions use POST forms with `onsubmit=confirm()` |

---

## Non-Functional Requirements

| Requirement | Implementation |
|---|---|
| Triage in < 3 seconds | Pure in-memory rule matching, no external API calls |
| Cautious default | Confidence threshold at 35% auto-escalates urgency |
| Encrypted health data | Fernet encryption on `symptoms_json` and `free_text` columns |
| WCAG 2.1 AA | Skip link, `:focus-visible` outline, ARIA roles/labels, semantic HTML |
| Mobile responsive | CSS grid with `auto-fill` + `@media (max-width: 640px)` breakpoints |

---

## Medical Disclaimer

> **SymptomAI provides general health information and triage guidance only. It is NOT a substitute for professional medical advice, diagnosis, or treatment. Always seek the advice of a qualified healthcare professional. In a medical emergency, call 911 immediately.**
