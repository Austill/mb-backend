from flask import Blueprint, request, jsonify, current_app
from backend.models import JournalEntry
from backend.decorators import token_required
import traceback
from datetime import datetime
from bson import ObjectId

journal_bp = Blueprint("journal_bp", __name__)
# Legacy compatibility: support old /entries paths
@journal_bp.route("/entries", methods=["GET", "POST"])
@token_required
def journal_entries_legacy(current_user=None):
    # If GET, forward to the existing GET handler
    from flask import request
    if request.method == "GET":
        return get_entries(current_user)
    elif request.method == "POST":
        return create_entry(current_user)
@journal_bp.route("/ping", methods=["GET"])
def ping_journal():
    return jsonify({"message": "journal blueprint is alive"}), 200

@journal_bp.route("", methods=["GET"])
@token_required
def get_entries(current_user):
    """Get all journal entries for the current user (ordered by date, newest first)"""
    try:
        # Get query parameters
        limit = request.args.get('limit', 10, type=int)
        offset = request.args.get('offset', 0, type=int)

        entries_data = JournalEntry.find_by_user(str(current_user._id))
        entries = [JournalEntry.from_dict(entry) for entry in entries_data]
        
        # Sort by most recent first
        entries.sort(key=lambda x: x.created_at or datetime.min, reverse=True)

        # Apply pagination
        total = len(entries)
        paginated_entries = entries[offset:offset + limit]

        return jsonify({
            "entries": [entry.to_dict() for entry in paginated_entries],
            "total": total,
            "limit": limit,
            "offset": offset
        }), 200
    except Exception as e:
        current_app.logger.error("Get journal entries error: %s\n%s", e, traceback.format_exc())
        return jsonify({"message": "Internal server error"}), 500

@journal_bp.route("", methods=["POST"])
@token_required
def create_entry(current_user):
    """Create a new journal entry"""
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
        
        return jsonify({
            "message": "Journal entry created successfully",
            "entry": entry.to_dict()
        }), 201
    except Exception as e:
        current_app.logger.error("Create journal entry error: %s\n%s", e, traceback.format_exc())
        return jsonify({"message": "Internal server error"}), 500

@journal_bp.route("/<entry_id>", methods=["GET"])
@token_required
def get_entry(current_user, entry_id):
    """Get a specific journal entry"""
    try:
        entry_data = JournalEntry.find_by_id(entry_id)

        if not entry_data or str(entry_data.get("user_id")) != str(current_user._id):
            return jsonify({"message": "Journal entry not found"}), 404

        entry = JournalEntry.from_dict(entry_data)
        return jsonify({"entry": entry.to_dict()}), 200

    except Exception as e:
        current_app.logger.error("Get journal entry error: %s\n%s", e, traceback.format_exc())
        return jsonify({"message": "Internal server error"}), 500

@journal_bp.route("/<entry_id>", methods=["PUT"])
@token_required
def update_entry(current_user, entry_id):
    """Update a journal entry"""
    try:
        entry_data = JournalEntry.find_by_id(entry_id)

        if not entry_data or str(entry_data.get("user_id")) != str(current_user._id):
            return jsonify({"message": "Journal entry not found"}), 404

        data = request.get_json()
        if not data:
            return jsonify({"message": "No data provided"}), 400

        update_data = {}
        
        if 'title' in data:
            update_data["title"] = data['title'].strip()
        if 'content' in data:
            update_data["content"] = data['content'].strip()
        if 'isPrivate' in data:
            update_data["is_private"] = data['isPrivate']
        if 'is_private' in data:
            update_data["is_private"] = data['is_private']
        if 'tags' in data:
            update_data["tags"] = data['tags']

        if update_data:
            update_data["updated_at"] = datetime.utcnow()
            entry = JournalEntry.from_dict(entry_data)
            entry.update(update_data)

            # Get updated entry
            updated_entry_data = JournalEntry.find_by_id(entry_id)
            updated_entry = JournalEntry.from_dict(updated_entry_data)

            return jsonify({
                "message": "Journal entry updated successfully",
                "entry": updated_entry.to_dict()
            }), 200
        else:
            entry = JournalEntry.from_dict(entry_data)
            return jsonify({
                "message": "Journal entry updated successfully",
                "entry": entry.to_dict()
            }), 200

    except Exception as e:
        current_app.logger.error("Update journal entry error: %s\n%s", e, traceback.format_exc())
        return jsonify({"message": "Internal server error"}), 500

@journal_bp.route("/<entry_id>", methods=["DELETE"])
@token_required
def delete_entry(current_user, entry_id):
    """Delete a journal entry"""
    try:
        entry_data = JournalEntry.find_by_id(entry_id)

        if not entry_data or str(entry_data.get("user_id")) != str(current_user._id):
            return jsonify({"message": "Journal entry not found"}), 404

        entry = JournalEntry.from_dict(entry_data)
        entry.delete()

        return jsonify({"message": "Journal entry deleted successfully"}), 200

    except Exception as e:
        current_app.logger.error("Delete journal entry error: %s\n%s", e, traceback.format_exc())
        return jsonify({"message": "Internal server error"}), 500
