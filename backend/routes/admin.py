from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import json
from extensions import db
from models.models import SymptomConditionMapping, User

admin_bp = Blueprint("admin", __name__)


def require_admin():
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if not user or not user.is_admin:
        return None, (jsonify({"error": "Admin access required."}), 403)
    return user, None


@admin_bp.route("/mappings", methods=["GET"])
@jwt_required()
def list_mappings():
    _, err = require_admin()
    if err:
        return err

    mappings = SymptomConditionMapping.query.order_by(SymptomConditionMapping.id).all()
    return jsonify({"mappings": [m.to_dict() for m in mappings]}), 200


@admin_bp.route("/mappings", methods=["POST"])
@jwt_required()
def create_mapping():
    _, err = require_admin()
    if err:
        return err

    data = request.get_json()
    required = ["name", "symptoms", "condition", "urgency"]
    for field in required:
        if not data.get(field):
            return jsonify({"error": f"Field '{field}' is required."}), 400

    if data["urgency"] not in ("self_care", "see_doctor", "emergency"):
        return jsonify({"error": "Urgency must be self_care, see_doctor, or emergency."}), 400

    mapping = SymptomConditionMapping(
        name=data["name"],
        symptoms=json.dumps(data["symptoms"]),
        condition=data["condition"],
        urgency=data["urgency"],
        description=data.get("description", ""),
        advice=data.get("advice", "")
    )
    db.session.add(mapping)
    db.session.commit()
    return jsonify(mapping.to_dict()), 201


@admin_bp.route("/mappings/<int:mapping_id>", methods=["PUT"])
@jwt_required()
def update_mapping(mapping_id):
    _, err = require_admin()
    if err:
        return err

    mapping = SymptomConditionMapping.query.get(mapping_id)
    if not mapping:
        return jsonify({"error": "Mapping not found."}), 404

    data = request.get_json()
    if "name" in data:
        mapping.name = data["name"]
    if "symptoms" in data:
        mapping.symptoms = json.dumps(data["symptoms"])
    if "condition" in data:
        mapping.condition = data["condition"]
    if "urgency" in data:
        if data["urgency"] not in ("self_care", "see_doctor", "emergency"):
            return jsonify({"error": "Invalid urgency level."}), 400
        mapping.urgency = data["urgency"]
    if "description" in data:
        mapping.description = data["description"]
    if "advice" in data:
        mapping.advice = data["advice"]

    db.session.commit()
    return jsonify(mapping.to_dict()), 200


@admin_bp.route("/mappings/<int:mapping_id>", methods=["DELETE"])
@jwt_required()
def delete_mapping(mapping_id):
    _, err = require_admin()
    if err:
        return err

    mapping = SymptomConditionMapping.query.get(mapping_id)
    if not mapping:
        return jsonify({"error": "Mapping not found."}), 404

    db.session.delete(mapping)
    db.session.commit()
    return jsonify({"message": "Mapping deleted."}), 200


@admin_bp.route("/users", methods=["GET"])
@jwt_required()
def list_users():
    _, err = require_admin()
    if err:
        return err

    users = User.query.order_by(User.id).all()
    return jsonify({"users": [u.to_dict() for u in users]}), 200


@admin_bp.route("/stats", methods=["GET"])
@jwt_required()
def stats():
    _, err = require_admin()
    if err:
        return err

    from models.models import SymptomCheck
    total_checks = SymptomCheck.query.count()
    emergency_count = SymptomCheck.query.filter_by(triage_level="emergency").count()
    see_doctor_count = SymptomCheck.query.filter_by(triage_level="see_doctor").count()
    self_care_count = SymptomCheck.query.filter_by(triage_level="self_care").count()
    total_users = User.query.count()
    total_mappings = SymptomConditionMapping.query.count()

    return jsonify({
        "total_checks": total_checks,
        "triage_breakdown": {
            "emergency": emergency_count,
            "see_doctor": see_doctor_count,
            "self_care": self_care_count
        },
        "total_users": total_users,
        "total_mappings": total_mappings
    }), 200
