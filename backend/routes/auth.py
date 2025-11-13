# backend/routes/auth.py
from flask import Blueprint, request, jsonify, current_app
from backend.models import User
from backend.decorators import token_required
import jwt, datetime, traceback

auth = Blueprint("auth", __name__)


def serialize_doc(doc):
    """Convert ObjectId to string for JSON serialization."""
    if "_id" in doc and hasattr(doc["_id"], '__str__'):
        doc["_id"] = str(doc["_id"])
    return doc


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
        current_app.logger.info("Register request received")
        data = request.get_json()
        if not data:
            current_app.logger.warning("Register failed: No JSON data provided")
            return jsonify({"message": "Request body must be JSON"}), 400

        firstName = data.get('firstName')
        lastName = data.get('lastName')
        email = data.get('email')
        password = data.get('password')

        current_app.logger.info("Register attempt for email: %s", email)

        if not all([firstName, lastName, email, password]):
            current_app.logger.warning("Register failed: Missing required fields for email: %s", email)
            return jsonify({"message": "firstName, lastName, email, and password are required"}), 400

        if User.find_by_email(email):
            current_app.logger.warning("Register failed: Email already exists: %s", email)
            return jsonify({"message": "Email already exists"}), 409

        new_user = User(
            first_name=firstName, last_name=lastName, email=email, password=password
        )
        new_user.save()

        current_app.logger.info("User registered successfully: user_id=%s, email=%s", str(new_user._id), email)
        return jsonify({"message": "User created successfully", "user": serialize_doc(new_user.to_dict())}), 201

    except Exception as e:
        current_app.logger.error("Register error for email: %s - %s\n%s", email if 'email' in locals() else 'unknown', e, traceback.format_exc())
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
        current_user.update({"password_hash": current_user.password_hash})

        return jsonify({"message": "Password changed successfully"}), 200

    except Exception as e:
        current_app.logger.error("Change password error: %s\n%s", e, traceback.format_exc())
        return jsonify({"message": "Internal server error"}), 500


@auth.route("/login", methods=["POST"])
def login():
    try:
        data = request.get_json(silent=True) or request.form or {}
        email, password = _extract_email_password(data)

        if not email or not password:
            return jsonify({"message": "email and password are required"}), 400

        user_data = User.find_by_email(email)
        if not user_data:
            return jsonify({"message": "Invalid credentials"}), 401

        user = User.from_dict(user_data)
        if not user.check_password(password):
            return jsonify({"message": "Invalid credentials"}), 401

        payload = {
            "user_id": str(user._id),
            "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=24),
        }

        token = jwt.encode(payload, current_app.config["SECRET_KEY"], algorithm="HS256")

        current_app.logger.info("User login successful: user_id=%s, email=%s, _id type=%s", str(user._id), user.email, type(user._id))
        current_app.logger.debug("User _id details: str(user._id)=%s, repr(user._id)=%s", str(user._id), repr(user._id))
        return jsonify({"token": token, "user": serialize_doc(user.to_dict())}), 200

    except Exception as e:
        current_app.logger.error("Login error: %s\n%s", e, traceback.format_exc())
        return jsonify({"message": "Internal server error"}), 500
