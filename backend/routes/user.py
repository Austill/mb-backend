from flask import Blueprint, request, jsonify, current_app, send_file
from backend.extensions import db
from backend.models.user import User
from backend.models.user_settings import UserSettings
from backend.models.mood_entry import MoodEntry
from backend.models.journal_entry import JournalEntry
from backend.decorators import token_required
import traceback
import json
import io
from datetime import datetime

user_bp = Blueprint("user", __name__)

@user_bp.route("/ping", methods=["GET"])
def ping_user():
    return jsonify({"message": "user blueprint is alive"}), 200

@user_bp.route("/profile", methods=["GET"])
@token_required
def get_profile(current_user):
    """Get user profile"""
    try:
        return jsonify(current_user.to_dict()), 200
    except Exception as e:
        current_app.logger.error("Get profile error: %s\n%s", e, traceback.format_exc())
        return jsonify({"message": "Internal server error"}), 500

@user_bp.route("/profile", methods=["PUT"])
@token_required
def update_profile(current_user):
    """Update user profile"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"message": "No data provided"}), 400

        # Update allowed fields
        if 'firstName' in data:
            current_user.first_name = data['firstName'].strip()
        if 'lastName' in data:
            current_user.last_name = data['lastName'].strip()
        if 'email' in data:
            email = data['email'].strip().lower()
            # Check if email is already taken by another user
            existing_user = User.query.filter(
                User.email == email,
                User.id != current_user.id
            ).first()
            if existing_user:
                return jsonify({"message": "Email already in use"}), 400
            current_user.email = email
        if 'phone' in data:
            current_user.phone = data['phone'].strip() or None

        current_user.updated_at = datetime.utcnow()
        db.session.commit()

        return jsonify({
            "message": "Profile updated successfully",
            "user": current_user.to_dict()
        }), 200

    except Exception as e:
        current_app.logger.error("Update profile error: %s\n%s", e, traceback.format_exc())
        db.session.rollback()
        return jsonify({"message": "Internal server error"}), 500

@user_bp.route("/settings", methods=["GET"])
@token_required
def get_settings(current_user):
    """Get user settings"""
    try:
        settings = UserSettings.query.filter_by(user_id=current_user.id).first()
        
        if not settings:
            # Create default settings for user
            settings = UserSettings(user_id=current_user.id)
            db.session.add(settings)
            db.session.commit()

        return jsonify(settings.to_dict()), 200

    except Exception as e:
        current_app.logger.error("Get settings error: %s\n%s", e, traceback.format_exc())
        return jsonify({"message": "Internal server error"}), 500

@user_bp.route("/settings", methods=["PUT"])
@token_required
def update_settings(current_user):
    """Update user settings"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"message": "No data provided"}), 400

        settings = UserSettings.query.filter_by(user_id=current_user.id).first()
        
        if not settings:
            settings = UserSettings(user_id=current_user.id)
            db.session.add(settings)

        # Update settings from the provided data
        settings.update_from_dict(data)
        settings.updated_at = datetime.utcnow()
        
        db.session.commit()

        return jsonify({
            "message": "Settings updated successfully",
            "settings": settings.to_dict()
        }), 200

    except Exception as e:
        current_app.logger.error("Update settings error: %s\n%s", e, traceback.format_exc())
        db.session.rollback()
        return jsonify({"message": "Internal server error"}), 500

@user_bp.route("/export-data", methods=["GET"])
@token_required
def export_user_data(current_user):
    """Export all user data as JSON"""
    try:
        # Collect all user data
        user_data = {
            "profile": current_user.to_dict(),
            "settings": None,
            "moodEntries": [],
            "journalEntries": [],
            "exportedAt": datetime.utcnow().isoformat()
        }

        # Get user settings
        settings = UserSettings.query.filter_by(user_id=current_user.id).first()
        if settings:
            user_data["settings"] = settings.to_dict()

        # Get mood entries
        mood_entries = MoodEntry.query.filter_by(user_id=current_user.id).all()
        user_data["moodEntries"] = [entry.to_dict() for entry in mood_entries]

        # Get journal entries
        journal_entries = JournalEntry.query.filter_by(user_id=current_user.id).all()
        user_data["journalEntries"] = [entry.to_dict() for entry in journal_entries]

        # Create JSON file in memory
        json_data = json.dumps(user_data, indent=2, default=str)
        json_bytes = json_data.encode('utf-8')
        
        # Create a file-like object
        file_obj = io.BytesIO(json_bytes)
        file_obj.seek(0)

        return send_file(
            file_obj,
            as_attachment=True,
            download_name=f'serenity-tree-data-{current_user.id}-{datetime.utcnow().strftime("%Y%m%d")}.json',
            mimetype='application/json'
        )

    except Exception as e:
        current_app.logger.error("Export data error: %s\n%s", e, traceback.format_exc())
        return jsonify({"message": "Internal server error"}), 500

@user_bp.route("/account", methods=["DELETE"])
@token_required
def delete_account(current_user):
    """Delete user account and all associated data"""
    try:
        # Due to cascade relationships, deleting the user will delete all related data
        db.session.delete(current_user)
        db.session.commit()

        return jsonify({"message": "Account deleted successfully"}), 200

    except Exception as e:
        current_app.logger.error("Delete account error: %s\n%s", e, traceback.format_exc())
        db.session.rollback()
        return jsonify({"message": "Internal server error"}), 500

@user_bp.route("/stats", methods=["GET"])
@token_required
def get_user_stats(current_user):
    """Get user statistics"""
    try:
        # Count entries
        mood_count = MoodEntry.query.filter_by(user_id=current_user.id).count()
        journal_count = JournalEntry.query.filter_by(user_id=current_user.id).count()
        
        # Calculate days since joining
        days_since_joining = (datetime.utcnow() - current_user.created_at).days if current_user.created_at else 0

        stats = {
            "totalMoodEntries": mood_count,
            "totalJournalEntries": journal_count,
            "daysSinceJoining": days_since_joining,
            "isPremium": current_user.is_premium,
            "memberSince": current_user.created_at.isoformat() if current_user.created_at else None
        }

        return jsonify({"stats": stats}), 200

    except Exception as e:
        current_app.logger.error("Get user stats error: %s\n%s", e, traceback.format_exc())
        return jsonify({"message": "Internal server error"}), 500

# Legacy endpoints for backward compatibility
@user_bp.route("/register", methods=["POST"])
def register():
    """Legacy register endpoint - redirects to auth blueprint"""
    return jsonify({"message": "Please use /api/auth/register endpoint"}), 301

@user_bp.route("/login", methods=["POST"])
def login():
    """Legacy login endpoint - redirects to auth blueprint"""
    return jsonify({"message": "Please use /api/auth/login endpoint"}), 301

@user_bp.route("/me", methods=["GET"])
@token_required
def get_current_user(current_user):
    """Legacy endpoint - use /profile instead"""
    return jsonify(current_user.to_dict()), 200

@user_bp.route("/", methods=["GET"])
def list_users():
    """List all users - admin only (placeholder)"""
    return jsonify({"message": "Admin functionality not implemented"}), 501
