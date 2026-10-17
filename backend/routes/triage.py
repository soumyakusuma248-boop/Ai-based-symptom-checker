from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
import json
from extensions import db
from models.models import SymptomCheck, SymptomConditionMapping, User
from utils.triage_engine import run_triage
from utils.encryption import DataEncryptor

triage_bp = Blueprint("triage", __name__)


def get_encryptor(app=None):
    cfg = (app or current_app)._get_current_object()
    return DataEncryptor(cfg.config["ENCRYPTION_KEY"])


@triage_bp.route("/check", methods=["POST"])
@jwt_required()
def symptom_check():
    data = request.get_json()
    selected_symptoms = data.get("symptoms", [])    # List[str]
    free_text = data.get("free_text", "").strip()

    if not selected_symptoms and not free_text:
        return jsonify({"error": "Please provide at least one symptom."}), 400

    mappings = SymptomConditionMapping.query.all()
    result = run_triage(selected_symptoms, free_text, mappings)

    user_id = int(get_jwt_identity())
    encryptor = get_encryptor()

    check = SymptomCheck(
        user_id=user_id,
        symptoms_encrypted=encryptor.encrypt(json.dumps(selected_symptoms)),
        free_text_encrypted=encryptor.encrypt(free_text) if free_text else None,
        triage_level=result["triage_level"],
        matched_conditions=json.dumps(result["matched_conditions"]),
        confidence_score=result["confidence_score"]
    )
    db.session.add(check)
    db.session.commit()

    return jsonify({
        "check_id": check.id,
        "triage_level": result["triage_level"],
        "confidence_score": result["confidence_score"],
        "matched_conditions": result["matched_conditions"],
        "advice": result["advice"],
        "cautious_override": result["cautious_override"],
        "next_steps": get_next_steps(result["triage_level"]),
        "nearby_care": get_nearby_care(result["triage_level"])
    }), 200


def get_next_steps(triage_level: str):
    steps = {
        "self_care": [
            "Rest at home and monitor your symptoms.",
            "Stay hydrated and take over-the-counter medications as needed.",
            "Seek medical attention if symptoms worsen or persist beyond 5-7 days."
        ],
        "see_doctor": [
            "Schedule an appointment with your primary care physician.",
            "If symptoms worsen significantly, proceed to urgent care.",
            "Bring a list of your symptoms and when they started."
        ],
        "emergency": [
            "Call 911 (emergency services) immediately.",
            "Do not drive yourself — call for help or have someone take you.",
            "Go to the nearest Emergency Room without delay."
        ]
    }
    return steps.get(triage_level, steps["see_doctor"])


def get_nearby_care(triage_level: str):
    """Mock data for nearby care options."""
    if triage_level == "emergency":
        return [
            {"name": "City General Hospital ER", "type": "Emergency Room", "distance": "0.8 miles", "phone": "911", "wait": "Immediate"},
            {"name": "Metro Medical Center ER", "type": "Emergency Room", "distance": "1.2 miles", "phone": "911", "wait": "Immediate"}
        ]
    elif triage_level == "see_doctor":
        return [
            {"name": "QuickCare Urgent Care", "type": "Urgent Care", "distance": "0.5 miles", "phone": "(555) 234-5678", "wait": "~20 min"},
            {"name": "HealthFirst Primary Care", "type": "Primary Care", "distance": "1.1 miles", "phone": "(555) 987-6543", "wait": "By appointment"},
            {"name": "MedExpress Clinic", "type": "Walk-in Clinic", "distance": "1.9 miles", "phone": "(555) 456-7890", "wait": "~35 min"}
        ]
    else:
        return [
            {"name": "Community Pharmacy", "type": "Pharmacy", "distance": "0.3 miles", "phone": "(555) 111-2222", "wait": "No wait"},
            {"name": "Telehealth — Virtual Visit", "type": "Telehealth", "distance": "Online", "phone": "(555) 800-0000", "wait": "~5 min"}
        ]
