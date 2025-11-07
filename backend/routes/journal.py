from flask import Blueprint, request, jsonify, current_app
from backend.models import JournalEntry
from backend.decorators import token_required
import traceback

journal_bp = Blueprint("journal_bp", __name__)

@journal_bp.route("/ping", methods=["GET"])
def ping_journal():
    return jsonify({"message": "journal blueprint is alive"}), 200

@journal_bp.route("/entries", methods=["GET"])
@token_required
def get_entries(current_user):
    try:
        entries_data = JournalEntry.find_by_user(str(current_user._id))
        entries = [JournalEntry.from_dict(entry) for entry in entries_data]
        entries.sort(key=lambda x: x.created_at, reverse=True)
        return jsonify([entry.to_dict() for entry in entries])
    except Exception as e:
        current_app.logger.error("Get journal entries error: %s\n%s", e, traceback.format_exc())
        return jsonify({"message": "Internal server error"}), 500

@journal_bp.route("/entries", methods=["POST"])
@token_required
def create_entry(current_user):
    try:
        data = request.get_json() or {}
        if not data.get("content"):
            return jsonify({"message": "Content is required"}), 400

        is_private = data.get("isPrivate", data.get("is_private", False))

        entry = JournalEntry(
            user_id=str(current_user._id),
            title=data.get("title", "").strip(),
            content=data["content"].strip(),
            is_private=is_private
        )
        entry.save()
        return jsonify(entry.to_dict()), 201
    except Exception as e:
        current_app.logger.error("Create journal entry error: %s\n%s", e, traceback.format_exc())
        return jsonify({"message": "Internal server error"}), 500
