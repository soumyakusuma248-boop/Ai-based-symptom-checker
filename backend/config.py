import os
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "config.env"))

class Config:
    SECRET_KEY             = os.getenv("SECRET_KEY", "symptom-checker-dev-secret-2024")
    SQLALCHEMY_DATABASE_URI= os.getenv("DATABASE_URL", "sqlite:///symptom_checker.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    ENCRYPTION_KEY         = os.getenv("ENCRYPTION_KEY", "dGhpcy1pcy1hLTMyLWJ5dGUta2V5LWZvci1lbmM=")
    # Session cookie security
    SESSION_COOKIE_HTTPONLY= True
    SESSION_COOKIE_SAMESITE= "Lax"
