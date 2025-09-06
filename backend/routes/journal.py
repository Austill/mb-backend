from flask import Blueprint, request, jsonify, g, current_app
from backend.extensions import db
from backend.models import JournalEntry
from backend.decorators import token_required
from datetime import datetime
import traceback

journal_bp = Blueprint("journal_bp", __name__)

# Get all entries for current user
@journal_bp.route("/entries", methods=["GET"])
@token_required
def get_entries(current_user):
    entries = JournalEntry.query.filter_by(user_id=current_user.id).order_by(JournalEntry.created_at.desc()).all()
    return jsonify([entry.to_dict() for entry in entries])

# Create a new journal entry
@journal_bp.route("/entries", methods=["POST"])
@token_required
def create_entry(current_user):
    try:
        data = request.get_json()
        if not data or not data.get("content"):
            return jsonify({"message": "Content is required"}), 400

        entry = JournalEntry(
            user_id=current_user.id,
            title=data.get("title"),
            content=data["content"]
        )
        db.session.add(entry)
        db.session.commit()
        return jsonify(entry.to_dict()), 201
    except Exception as e:
        current_app.logger.error("Create journal entry error: %s\n%s", e, traceback.format_exc())
        db.session.rollback()
        return jsonify({"message": "Internal server error"}), 500

# Get a specific entry
@journal_bp.route("/entries/<int:entry_id>", methods=["GET"])
@token_required
def get_entry(current_user, entry_id):
    entry = JournalEntry.query.filter_by(id=entry_id, user_id=current_user.id).first()
    if not entry:
        return jsonify({"message": "Entry not found"}), 404
    return jsonify(entry.to_dict())

# Update an entry
@journal_bp.route("/entries/<int:entry_id>", methods=["PUT"])
@token_required
def update_entry(current_user, entry_id):
    try:
        entry = JournalEntry.query.filter_by(id=entry_id, user_id=current_user.id).first()
        if not entry:
            return jsonify({"message": "Entry not found"}), 404

        data = request.get_json()
        entry.title = data.get("title", entry.title)
        entry.content = data.get("content", entry.content)

        db.session.commit()
        return jsonify(entry.to_dict())
    except Exception as e:
        current_app.logger.error("Update journal entry error: %s\n%s", e, traceback.format_exc())
        db.session.rollback()
        return jsonify({"message": "Internal server error"}), 500

# Delete an entry
@journal_bp.route("/entries/<int:entry_id>", methods=["DELETE"])
@token_required
def delete_entry(current_user, entry_id):
    try:
        entry = JournalEntry.query.filter_by(id=entry_id, user_id=current_user.id).first()
        if not entry:
            return jsonify({"message": "Entry not found"}), 404

        db.session.delete(entry)
        db.session.commit()
        return jsonify({"message": "Entry deleted successfully"})
    except Exception as e:
        current_app.logger.error("Delete journal entry error: %s\n%s", e, traceback.format_exc())
        db.session.rollback()
        return jsonify({"message": "Internal server error"}), 500
