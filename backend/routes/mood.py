from flask import Blueprint, request, jsonify, current_app
from backend.models import MoodEntry
from backend.decorators import token_required
import traceback
from datetime import datetime, timedelta
from bson import ObjectId

mood_bp = Blueprint("mood", __name__)

@mood_bp.route("/ping", methods=["GET"])
def ping_mood():
    return jsonify({"message": "mood blueprint is alive"}), 200

@mood_bp.route("/entries", methods=["POST"])
@token_required
def create_mood_entry(current_user):
    """Create a new mood entry"""
    try:
        data = request.get_json()

        if not data:
            return jsonify({"message": "No data provided"}), 400

        # Validate required fields
        mood_level = data.get('moodLevel')
        emoji = data.get('emoji')

        if mood_level is None or not emoji:
            return jsonify({"message": "moodLevel and emoji are required"}), 400

        if not isinstance(mood_level, int) or mood_level < 1 or mood_level > 5:
            return jsonify({"message": "moodLevel must be an integer between 1 and 5"}), 400

        # Create new mood entry
        mood_entry = MoodEntry(
            user_id=str(current_user._id),
            mood_level=mood_level,
            emoji=emoji,
            note=data.get('note', '').strip() or None
        )

        # Set triggers if provided
        triggers = data.get('triggers', [])
        if triggers:
            mood_entry.set_triggers(triggers)

        mood_entry.save()

        return jsonify({
            "message": "Mood entry created successfully",
            "entry": mood_entry.to_dict()
        }), 201

    except Exception as e:
        current_app.logger.error("Create mood entry error: %s\n%s", e, traceback.format_exc())
        return jsonify({"message": "Internal server error"}), 500

@mood_bp.route("/entries", methods=["GET"])
@token_required
def get_mood_entries(current_user):
    """Get mood entries for the current user"""
    try:
        # Get query parameters
        limit = request.args.get('limit', 10, type=int)
        offset = request.args.get('offset', 0, type=int)
        days = request.args.get('days', type=int)  # Filter by last N days

        # Get entries from MongoDB
        entries_data = MoodEntry.find_by_user(str(current_user._id))

        # Convert to objects and filter by date if needed
        entries = []
        cutoff_date = None
        if days:
            cutoff_date = datetime.utcnow() - timedelta(days=days)

        for entry_data in entries_data:
            entry = MoodEntry.from_dict(entry_data)
            if cutoff_date and entry.created_at < cutoff_date:
                continue
            entries.append(entry)

        # Sort by most recent first, handle None dates
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
        current_app.logger.error("Get mood entries error: %s\n%s", e, traceback.format_exc())
        return jsonify({"message": "Internal server error"}), 500

@mood_bp.route("/entries/<entry_id>", methods=["GET"])
@token_required
def get_mood_entry(current_user, entry_id):
    """Get a specific mood entry"""
    try:
        entry_data = MoodEntry.find_by_id(entry_id)

        if not entry_data or str(entry_data.get("user_id")) != str(current_user._id):
            return jsonify({"message": "Mood entry not found"}), 404

        entry = MoodEntry.from_dict(entry_data)
        return jsonify({"entry": entry.to_dict()}), 200

    except Exception as e:
        current_app.logger.error("Get mood entry error: %s\n%s", e, traceback.format_exc())
        return jsonify({"message": "Internal server error"}), 500

@mood_bp.route("/entries/<entry_id>", methods=["PUT"])
@token_required
def update_mood_entry(current_user, entry_id):
    """Update a mood entry"""
    try:
        entry_data = MoodEntry.find_by_id(entry_id)

        if not entry_data or str(entry_data.get("user_id")) != str(current_user._id):
            return jsonify({"message": "Mood entry not found"}), 404

        data = request.get_json()
        if not data:
            return jsonify({"message": "No data provided"}), 400

        # Prepare update data
        update_data = {}
        if 'moodLevel' in data:
            mood_level = data['moodLevel']
            if not isinstance(mood_level, int) or mood_level < 1 or mood_level > 5:
                return jsonify({"message": "moodLevel must be an integer between 1 and 5"}), 400
            update_data["mood_level"] = mood_level

        if 'emoji' in data:
            update_data["emoji"] = data['emoji']

        if 'note' in data:
            update_data["note"] = data['note'].strip() or None

        if 'triggers' in data:
            update_data["triggers"] = data['triggers']

        if update_data:
            update_data["updated_at"] = datetime.utcnow()
            entry = MoodEntry.from_dict(entry_data)
            entry.update(update_data)

            # Get updated entry
            updated_entry_data = MoodEntry.find_by_id(entry_id)
            updated_entry = MoodEntry.from_dict(updated_entry_data)

            return jsonify({
                "message": "Mood entry updated successfully",
                "entry": updated_entry.to_dict()
            }), 200
        else:
            entry = MoodEntry.from_dict(entry_data)
            return jsonify({
                "message": "Mood entry updated successfully",
                "entry": entry.to_dict()
            }), 200

    except Exception as e:
        current_app.logger.error("Update mood entry error: %s\n%s", e, traceback.format_exc())
        return jsonify({"message": "Internal server error"}), 500

@mood_bp.route("/entries/<entry_id>", methods=["DELETE"])
@token_required
def delete_mood_entry(current_user, entry_id):
    """Delete a mood entry"""
    try:
        entry_data = MoodEntry.find_by_id(entry_id)

        if not entry_data or str(entry_data.get("user_id")) != str(current_user._id):
            return jsonify({"message": "Mood entry not found"}), 404

        entry = MoodEntry.from_dict(entry_data)
        entry.delete()

        return jsonify({"message": "Mood entry deleted successfully"}), 200

    except Exception as e:
        current_app.logger.error("Delete mood entry error: %s\n%s", e, traceback.format_exc())
        return jsonify({"message": "Internal server error"}), 500

@mood_bp.route("/stats", methods=["GET"])
@token_required
def get_mood_stats(current_user):
    """Get mood statistics for the current user"""
    try:
        days = request.args.get('days', 30, type=int)
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        # Get mood entries for the specified period
        entries_data = MoodEntry.find_by_user(str(current_user._id))
        entries = []

        for entry_data in entries_data:
            entry = MoodEntry.from_dict(entry_data)
            if entry.created_at >= cutoff_date:
                entries.append(entry)

        if not entries:
            return jsonify({
                "stats": {
                    "totalEntries": 0,
                    "averageMood": 0,
                    "moodDistribution": {},
                    "commonTriggers": [],
                    "period": days
                }
            }), 200

        # Calculate statistics
        total_entries = len(entries)
        mood_levels = [entry.mood_level for entry in entries]
        average_mood = sum(mood_levels) / len(mood_levels)

        # Mood distribution
        mood_distribution = {}
        for level in mood_levels:
            mood_distribution[str(level)] = mood_distribution.get(str(level), 0) + 1

        # Common triggers
        all_triggers = []
        for entry in entries:
            triggers = entry.get_triggers()
            if triggers:
                all_triggers.extend(triggers)

        # Count trigger frequency
        trigger_counts = {}
        for trigger in all_triggers:
            trigger_counts[trigger] = trigger_counts.get(trigger, 0) + 1

        # Get top 5 most common triggers
        common_triggers = sorted(
            trigger_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]

        return jsonify({
            "stats": {
                "totalEntries": total_entries,
                "averageMood": round(average_mood, 2),
                "moodDistribution": mood_distribution,
                "commonTriggers": [{"trigger": t[0], "count": t[1]} for t in common_triggers],
                "period": days
            }
        }), 200

    except Exception as e:
        current_app.logger.error("Get mood stats error: %s\n%s", e, traceback.format_exc())
        return jsonify({"message": "Internal server error"}), 500

@mood_bp.route("/today", methods=["GET"])
@token_required
def get_today_mood(current_user):
    """Check if user has logged mood today"""
    try:
        current_app.logger.info("Get today mood request for user_id: %s", str(current_user._id))
        today = datetime.utcnow().date()

        # Get all entries for user and check today's date
        entries_data = MoodEntry.find_by_user(str(current_user._id))

        for entry_data in entries_data:
            entry = MoodEntry.from_dict(entry_data)
            if entry.created_at.date() == today:
                current_app.logger.info("Today mood entry found for user_id: %s", str(current_user._id))
                return jsonify({
                    "hasEntry": True,
                    "entry": entry.to_dict()
                }), 200

        current_app.logger.info("No today mood entry for user_id: %s", str(current_user._id))
        return jsonify({
            "hasEntry": False,
            "entry": None
        }), 200

    except Exception as e:
        current_app.logger.error("Get today mood error for user_id: %s - %s\n%s", str(current_user._id), e, traceback.format_exc())
        return jsonify({"message": "Internal server error"}), 500
