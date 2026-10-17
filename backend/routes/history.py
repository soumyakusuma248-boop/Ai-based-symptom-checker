from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import db
from models.models import SymptomCheck, User
from utils.encryption import DataEncryptor
import json

history_bp = Blueprint("history", __name__)


def get_encryptor():
    return DataEncryptor(current_app.config["ENCRYPTION_KEY"])


@history_bp.route("/", methods=["GET"])
@jwt_required()
def get_history():
    user_id = int(get_jwt_identity())
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 10, type=int)

    pagination = (
        SymptomCheck.query
        .filter_by(user_id=user_id)
        .order_by(SymptomCheck.created_at.desc())
        .paginate(page=page, per_page=per_page, error_out=False)
    )

    encryptor = get_encryptor()
    records = [check.to_dict_decrypted(encryptor) for check in pagination.items]

    return jsonify({
        "checks": records,
        "total": pagination.total,
        "page": pagination.page,
        "pages": pagination.pages,
        "per_page": per_page
    }), 200


@history_bp.route("/<int:check_id>", methods=["GET"])
@jwt_required()
def get_check(check_id):
    user_id = int(get_jwt_identity())
    check = SymptomCheck.query.filter_by(id=check_id, user_id=user_id).first()
    if not check:
        return jsonify({"error": "Record not found."}), 404

    encryptor = get_encryptor()
    return jsonify(check.to_dict_decrypted(encryptor)), 200


@history_bp.route("/<int:check_id>", methods=["DELETE"])
@jwt_required()
def delete_check(check_id):
    user_id = int(get_jwt_identity())
    check = SymptomCheck.query.filter_by(id=check_id, user_id=user_id).first()
    if not check:
        return jsonify({"error": "Record not found."}), 404

    db.session.delete(check)
    db.session.commit()
    return jsonify({"message": "Record deleted."}), 200
