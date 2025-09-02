from flask import Blueprint, request, jsonify, g
from backend import db
from backend.models.journal_entry import JournalEntry   # <-- ADDED
from backend.decorators import token_required
import datetime

journal_bp = Blueprint("journal_bp", __name__)

# Get all entries for current user
@journal_bp.route("/entries", methods=["GET"])
@token_required
def get_entries():
    entries = JournalEntry.query.filter_by(user_id=g.current_user.id).order_by(JournalEntry.created_at.desc()).all()
    return jsonify([entry.to_dict() for entry in entries])

# Create a new journal entry
@journal_bp.route("/entries", methods=["POST"])
@token_required
def create_entry():
    data = request.get_json()
    if not data or not data.get("content"):
        return jsonify({"message": "Content is required"}), 400

    entry = JournalEntry(
        user_id=g.current_user.id,
        title=data.get("title"),
        content=data["content"],
        mood=data.get("mood")
    )
    db.session.add(entry)
    db.session.commit()
    return jsonify(entry.to_dict()), 201

# Get a specific entry
@journal_bp.route("/entries/<int:entry_id>", methods=["GET"])
@token_required
def get_entry(entry_id):
    entry = JournalEntry.query.filter_by(id=entry_id, user_id=g.current_user.id).first()
    if not entry:
        return jsonify({"message": "Entry not found"}), 404
    return jsonify(entry.to_dict())

# Update an entry
@journal_bp.route("/entries/<int:entry_id>", methods=["PUT"])
@token_required
def update_entry(entry_id):
    entry = JournalEntry.query.filter_by(id=entry_id, user_id=g.current_user.id).first()
    if not entry:
        return jsonify({"message": "Entry not found"}), 404

    data = request.get_json()
    entry.title = data.get("title", entry.title)
    entry.content = data.get("content", entry.content)
    entry.mood = data.get("mood", entry.mood)
    entry.updated_at = datetime.datetime.utcnow()

    db.session.commit()
    return jsonify(entry.to_dict())

# Delete an entry
@journal_bp.route("/entries/<int:entry_id>", methods=["DELETE"])
@token_required
def delete_entry(entry_id):
    entry = JournalEntry.query.filter_by(id=entry_id, user_id=g.current_user.id).first()
    if not entry:
        return jsonify({"message": "Entry not found"}), 404

    db.session.delete(entry)
    db.session.commit()
    return jsonify({"message": "Entry deleted successfully"})
