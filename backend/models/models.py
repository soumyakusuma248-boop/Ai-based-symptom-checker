from datetime import datetime
from extensions import db
import json


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    checks = db.relationship("SymptomCheck", backref="user", lazy=True, cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "is_admin": self.is_admin,
            "created_at": self.created_at.isoformat()
        }


class SymptomConditionMapping(db.Model):
    __tablename__ = "symptom_condition_mappings"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    symptoms = db.Column(db.Text, nullable=False)        # JSON list of symptom keywords
    condition = db.Column(db.String(200), nullable=False)
    urgency = db.Column(db.String(20), nullable=False)   # self_care | see_doctor | emergency
    description = db.Column(db.Text, nullable=True)
    advice = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def get_symptoms_list(self):
        return json.loads(self.symptoms)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "symptoms": self.get_symptoms_list(),
            "condition": self.condition,
            "urgency": self.urgency,
            "description": self.description,
            "advice": self.advice,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }


class SymptomCheck(db.Model):
    __tablename__ = "symptom_checks"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    # Encrypted storage for health data
    symptoms_encrypted = db.Column(db.Text, nullable=False)
    free_text_encrypted = db.Column(db.Text, nullable=True)
    triage_level = db.Column(db.String(20), nullable=False)
    matched_conditions = db.Column(db.Text, nullable=False)  # JSON list
    confidence_score = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def get_matched_conditions(self):
        return json.loads(self.matched_conditions)

    def to_dict_decrypted(self, encryptor):
        return {
            "id": self.id,
            "symptoms": encryptor.decrypt(self.symptoms_encrypted),
            "free_text": encryptor.decrypt(self.free_text_encrypted) if self.free_text_encrypted else "",
            "triage_level": self.triage_level,
            "matched_conditions": self.get_matched_conditions(),
            "confidence_score": self.confidence_score,
            "created_at": self.created_at.isoformat()
        }
