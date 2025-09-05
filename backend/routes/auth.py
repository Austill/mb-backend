# backend/routes/auth.py
from flask import Blueprint, request, jsonify, current_app
from backend.extensions import db
from backend.models import User
from backend.decorators import token_required
import jwt, datetime, traceback

auth = Blueprint("auth", __name__)


def _extract_email_password(data):
    """Helper to extract email and password from request data."""
    if not data:
        return None, None
    
    email = data.get("email")
    password = data.get("password")
    return (email, password)


@auth.route("/register", methods=["POST"])
def register():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"message": "Request body must be JSON"}), 400

        firstName = data.get('firstName')
        lastName = data.get('lastName')
        email = data.get('email')
        password = data.get('password')

        if not all([firstName, lastName, email, password]):
            return jsonify({"message": "firstName, lastName, email, and password are required"}), 400

        if User.query.filter_by(email=email).first():
            return jsonify({"message": "Email already exists"}), 409

        new_user = User(
            first_name=firstName, last_name=lastName, email=email
        )
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()

        return jsonify({"message": "User created successfully", "user": new_user.to_dict()}), 201

    except Exception as e:
        current_app.logger.error("Register error: %s\n%s", e, traceback.format_exc())
        db.session.rollback()
        return jsonify({"message": "Internal server error"}), 500


@auth.route("/change-password", methods=["PUT"])
@token_required
def change_password(current_user):
    try:
        data = request.get_json(silent=True) or {}
        current_password = data.get("currentPassword")
        new_password = data.get("newPassword")

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

        payload = {
            "user_id": user.id,
            "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=24),
        }

        token = jwt.encode(payload, current_app.config["SECRET_KEY"], algorithm="HS256")

        return jsonify({"token": token, "user": user.to_dict()}), 200

    except Exception as e:
        current_app.logger.error("Login error: %s\n%s", e, traceback.format_exc())
        return jsonify({"message": "Internal server error"}), 500
