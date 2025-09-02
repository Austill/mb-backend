from flask import Blueprint, request, jsonify, g
from backend import db, bcrypt
from backend.models import User
from backend.decorators import token_required
import jwt
import datetime
from backend.config import Config  # make sure you have a SECRET_KEY here

user_bp = Blueprint("user_bp", __name__)

# Register a new user
@user_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    if not data or not all(k in data for k in ("email", "password", "first_name", "last_name")):
        return jsonify({"error": "Missing required fields"}), 400

    if User.query.filter_by(email=data["email"]).first():
        return jsonify({"error": "Email already exists"}), 400

    user = User(
        email=data["email"],
        first_name=data["first_name"],
        last_name=data["last_name"],
        phone=data.get("phone")
    )
    user.set_password(data["password"])

    db.session.add(user)
    db.session.commit()
    return jsonify({"message": "User registered successfully"}), 201

# Login user and generate JWT
@user_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    if not data or not data.get("email") or not data.get("password"):
        return jsonify({"error": "Email and password required"}), 400

    user = User.query.filter_by(email=data["email"]).first()
    if not user or not user.check_password(data["password"]):
        return jsonify({"error": "Invalid credentials"}), 401

    token = jwt.encode(
        {"user_id": user.id, "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=24)},
        Config.SECRET_KEY,
        algorithm="HS256"
    )
    return jsonify({"token": token})

# Get current logged-in user
@user_bp.route("/me", methods=["GET"])
@token_required
def get_current_user():
    return jsonify(g.current_user.to_dict())

# Optional: List all users (admin only)
@user_bp.route("/", methods=["GET"])
def list_users():
    users = User.query.all()
    return jsonify([user.to_dict() for user in users])
