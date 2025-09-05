# backend/routes/auth.py
from flask import Blueprint, request, jsonify, current_app
from backend.extensions import db
from backend.models.user import User
from backend.decorators import token_required
import jwt, datetime, traceback

auth = Blueprint("auth", __name__)


def _extract_email_password(data):
    """
    Accepts request JSON shaped as:
      - {"email": "a@b.com", "password": "pw"}
      - {"email": {"email": "a@b.com", "password": "pw"}}  (what your frontend is sending)
      - or other minor variants
    Returns (email, password) or (None, None).
    """
    if not data:
        return None, None

    # If email key holds a nested object with both email & password
    nested = data.get("email")
    if isinstance(nested, dict):
        email = nested.get("email") or nested.get("value")
        password = nested.get("password") or nested.get("pass")
        return (email, password)

    # flat shape
    email = data.get("email") or data.get("username") or data.get("emailAddress")
    password = data.get("password") or data.get("pass")
    return (email, password)


@auth.route("/ping", methods=["GET"])
def ping_auth():
    return jsonify({"message": "auth blueprint is alive"}), 200


@auth.route("/register", methods=["POST"])
def register():
    try:
        data = request.get_json(silent=True) or request.form or {}
        email, password = _extract_email_password(data)

        if not email or not password:
            return jsonify({"message": "email and password are required"}), 400

        if User.query.filter_by(email=email).first():
            return jsonify({"message": "User already exists"}), 400

        # create user: use model's methods to set password
        new_user = User(email=email, first_name="", last_name="", phone=None)
        new_user.set_password(password)

        db.session.add(new_user)
        db.session.commit()

        return jsonify({"message": "User created successfully", "user": new_user.to_dict()}), 201

    except Exception as e:
        current_app.logger.error("Register error: %s\n%s", e, traceback.format_exc())
        return jsonify({"message": "Internal server error"}), 500


@auth.route("/profile", methods=["GET"])
@token_required
def get_profile(current_user):
    """Get current user profile"""
    try:
        return jsonify(current_user.to_dict()), 200
    except Exception as e:
        current_app.logger.error("Get profile error: %s\n%s", e, traceback.format_exc())
        return jsonify({"message": "Internal server error"}), 500


@auth.route("/change-password", methods=["PUT"])
@token_required
def change_password(current_user):
    """Change user password"""
    try:
        data = request.get_json(silent=True) or {}
        
        current_password = data.get('currentPassword')
        new_password = data.get('newPassword')
        
        if not current_password or not new_password:
            return jsonify({"message": "Current password and new password are required"}), 400
        
        # Verify current password
        if not current_user.check_password(current_password):
            return jsonify({"message": "Current password is incorrect"}), 400
        
        # Validate new password
        if len(new_password) < 8:
            return jsonify({"message": "New password must be at least 8 characters long"}), 400
        
        # Update password
        current_user.set_password(new_password)
        current_user.updated_at = datetime.datetime.utcnow()
        db.session.commit()
        
        return jsonify({"message": "Password changed successfully"}), 200
        
    except Exception as e:
        current_app.logger.error("Change password error: %s\n%s", e, traceback.format_exc())
        db.session.rollback()
        return jsonify({"message": "Internal server error"}), 500


@auth.route("/login", methods=["POST"])
def login():
    try:
        data = request.get_json(silent=True) or request.form or {}
        email, password = _extract_email_password(data)

        if not email or not password:
            return jsonify({"message": "email and password are required"}), 400

        user = User.query.filter_by(email=email).first()
        if not user or not user.check_password(password):
            return jsonify({"message": "Invalid credentials"}), 401

        secret = current_app.config.get("SECRET_KEY", "dev-secret")
        payload = {
            "user_id": user.id,
            "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=24),
            "iat": datetime.datetime.utcnow(),
        }

        token = jwt.encode(payload, secret, algorithm="HS256")
        if isinstance(token, bytes):
            token = token.decode("utf-8")

        return jsonify({"token": token, "user": user.to_dict()}), 200

    except Exception as e:
        current_app.logger.error("Login error: %s\n%s", e, traceback.format_exc())
        return jsonify({"message": "Internal server error"}), 500
