from flask import Blueprint, request, jsonify, current_app, send_file
from backend.models.user import User
from backend.models.user_settings import UserSettings
from backend.models.mood_entry import MoodEntry
from backend.models.journal_entry import JournalEntry
from backend.decorators import token_required
import traceback
import json
import io
from datetime import datetime
from bson import ObjectId

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

        update_data = {}

        # Update allowed fields
        if 'firstName' in data:
            update_data['first_name'] = data['firstName'].strip()
        if 'lastName' in data:
            update_data['last_name'] = data['lastName'].strip()
        if 'email' in data:
            email = data['email'].strip().lower()
            # Check if email is already taken by another user
            existing_user = User.find_by_email(email)
            if existing_user and str(existing_user['_id']) != str(current_user._id):
                return jsonify({"message": "Email already in use"}), 400
            update_data['email'] = email
        if 'phone' in data:
            update_data['phone'] = data['phone'].strip() or None

        if update_data:
            current_user.update(update_data)
            # Refresh current_user data
            current_user_data = User.find_by_id(str(current_user._id))
            if current_user_data:
                current_user = User.from_dict(current_user_data)

        return jsonify({
            "message": "Profile updated successfully",
            "user": current_user.to_dict()
        }), 200

    except Exception as e:
        current_app.logger.error("Update profile error: %s\n%s", e, traceback.format_exc())
        return jsonify({"message": "Internal server error"}), 500

@user_bp.route("/settings", methods=["GET"])
@token_required
def get_settings(current_user):
    """Get user settings"""
    try:
        settings_data = UserSettings.find_by_user(str(current_user._id))

        if not settings_data:
            # Create default settings for user
            settings = UserSettings(str(current_user._id))
            settings.save()
            return jsonify(settings.to_dict_formatted()), 200

        settings = UserSettings.from_dict(settings_data)
        return jsonify(settings.to_dict_formatted()), 200

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

        settings_data = UserSettings.find_by_user(str(current_user._id))

        if not settings_data:
            settings = UserSettings(str(current_user._id))
            settings.update_from_dict(data)
            settings.save()
        else:
            settings = UserSettings.from_dict(settings_data)
            settings.update_from_dict(data)
            settings.update(settings.to_dict())

        return jsonify({
            "message": "Settings updated successfully",
            "settings": settings.to_dict_formatted()
        }), 200

    except Exception as e:
        current_app.logger.error("Update settings error: %s\n%s", e, traceback.format_exc())
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
        settings_data = UserSettings.find_by_user(str(current_user._id))
        if settings_data:
            settings = UserSettings.from_dict(settings_data)
            user_data["settings"] = settings.to_dict_formatted()

        # Get mood entries
        mood_entries_data = MoodEntry.find_by_user(str(current_user._id))
        user_data["moodEntries"] = [entry for entry in mood_entries_data]

        # Get journal entries
        journal_entries_data = JournalEntry.find_by_user(str(current_user._id))
        user_data["journalEntries"] = [entry for entry in journal_entries_data]

        # Create JSON file in memory
        json_data = json.dumps(user_data, indent=2, default=str)
        json_bytes = json_data.encode('utf-8')

        # Create a file-like object
        file_obj = io.BytesIO(json_bytes)
        file_obj.seek(0)

        return send_file(
            file_obj,
            as_attachment=True,
            download_name=f'mindbuddy-data-{str(current_user._id)}-{datetime.utcnow().strftime("%Y%m%d")}.json',
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
        # Delete all related data first
        MoodEntry.collection.delete_many({"user_id": current_user._id})
        JournalEntry.collection.delete_many({"user_id": current_user._id})
        UserSettings.collection.delete_many({"user_id": current_user._id})

        # Delete the user
        current_user.delete()

        return jsonify({"message": "Account deleted successfully"}), 200

    except Exception as e:
        current_app.logger.error("Delete account error: %s\n%s", e, traceback.format_exc())
        return jsonify({"message": "Internal server error"}), 500

@user_bp.route("/stats", methods=["GET"])
@token_required
def get_user_stats(current_user):
    """Get user statistics"""
    try:
        # Count entries
        mood_count = MoodEntry.collection.count_documents({"user_id": current_user._id})
        journal_count = JournalEntry.collection.count_documents({"user_id": current_user._id})

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
