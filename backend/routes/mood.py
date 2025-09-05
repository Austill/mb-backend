from flask import Blueprint, request, jsonify, current_app
from backend.extensions import db
from backend.models.user import User
from backend.models.mood_entry import MoodEntry
from backend.decorators import token_required
import traceback
from datetime import datetime, timedelta
from sqlalchemy import desc, func

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
            user_id=current_user.id,
            mood_level=mood_level,
            emoji=emoji,
            note=data.get('note', '').strip() or None
        )
        
        # Set triggers if provided
        triggers = data.get('triggers', [])
        if triggers:
            mood_entry.set_triggers(triggers)
        
        db.session.add(mood_entry)
        db.session.commit()
        
        return jsonify({
            "message": "Mood entry created successfully",
            "entry": mood_entry.to_dict()
        }), 201
        
    except Exception as e:
        current_app.logger.error("Create mood entry error: %s\n%s", e, traceback.format_exc())
        db.session.rollback()
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
        
        # Build query
        query = MoodEntry.query.filter_by(user_id=current_user.id)
        
        # Filter by days if provided
        if days:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            query = query.filter(MoodEntry.created_at >= cutoff_date)
        
        # Order by most recent first
        query = query.order_by(desc(MoodEntry.created_at))
        
        # Apply pagination
        total = query.count()
        entries = query.offset(offset).limit(limit).all()
        
        return jsonify({
            "entries": [entry.to_dict() for entry in entries],
            "total": total,
            "limit": limit,
            "offset": offset
        }), 200
        
    except Exception as e:
        current_app.logger.error("Get mood entries error: %s\n%s", e, traceback.format_exc())
        return jsonify({"message": "Internal server error"}), 500

@mood_bp.route("/entries/<int:entry_id>", methods=["GET"])
@token_required
def get_mood_entry(current_user, entry_id):
    """Get a specific mood entry"""
    try:
        entry = MoodEntry.query.filter_by(
            id=entry_id, 
            user_id=current_user.id
        ).first()
        
        if not entry:
            return jsonify({"message": "Mood entry not found"}), 404
        
        return jsonify({"entry": entry.to_dict()}), 200
        
    except Exception as e:
        current_app.logger.error("Get mood entry error: %s\n%s", e, traceback.format_exc())
        return jsonify({"message": "Internal server error"}), 500

@mood_bp.route("/entries/<int:entry_id>", methods=["PUT"])
@token_required
def update_mood_entry(current_user, entry_id):
    """Update a mood entry"""
    try:
        entry = MoodEntry.query.filter_by(
            id=entry_id, 
            user_id=current_user.id
        ).first()
        
        if not entry:
            return jsonify({"message": "Mood entry not found"}), 404
        
        data = request.get_json()
        if not data:
            return jsonify({"message": "No data provided"}), 400
        
        # Update fields if provided
        if 'moodLevel' in data:
            mood_level = data['moodLevel']
            if not isinstance(mood_level, int) or mood_level < 1 or mood_level > 5:
                return jsonify({"message": "moodLevel must be an integer between 1 and 5"}), 400
            entry.mood_level = mood_level
        
        if 'emoji' in data:
            entry.emoji = data['emoji']
        
        if 'note' in data:
            entry.note = data['note'].strip() or None
        
        if 'triggers' in data:
            entry.set_triggers(data['triggers'])
        
        entry.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            "message": "Mood entry updated successfully",
            "entry": entry.to_dict()
        }), 200
        
    except Exception as e:
        current_app.logger.error("Update mood entry error: %s\n%s", e, traceback.format_exc())
        db.session.rollback()
        return jsonify({"message": "Internal server error"}), 500

@mood_bp.route("/entries/<int:entry_id>", methods=["DELETE"])
@token_required
def delete_mood_entry(current_user, entry_id):
    """Delete a mood entry"""
    try:
        entry = MoodEntry.query.filter_by(
            id=entry_id, 
            user_id=current_user.id
        ).first()
        
        if not entry:
            return jsonify({"message": "Mood entry not found"}), 404
        
        db.session.delete(entry)
        db.session.commit()
        
        return jsonify({"message": "Mood entry deleted successfully"}), 200
        
    except Exception as e:
        current_app.logger.error("Delete mood entry error: %s\n%s", e, traceback.format_exc())
        db.session.rollback()
        return jsonify({"message": "Internal server error"}), 500

@mood_bp.route("/stats", methods=["GET"])
@token_required
def get_mood_stats(current_user):
    """Get mood statistics for the current user"""
    try:
        days = request.args.get('days', 30, type=int)
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Get mood entries for the specified period
        entries = MoodEntry.query.filter(
            MoodEntry.user_id == current_user.id,
            MoodEntry.created_at >= cutoff_date
        ).all()
        
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
        today = datetime.utcnow().date()
        
        entry = MoodEntry.query.filter(
            MoodEntry.user_id == current_user.id,
            func.date(MoodEntry.created_at) == today
        ).first()
        
        if entry:
            return jsonify({
                "hasEntry": True,
                "entry": entry.to_dict()
            }), 200
        else:
            return jsonify({
                "hasEntry": False,
                "entry": None
            }), 200
            
    except Exception as e:
        current_app.logger.error("Get today mood error: %s\n%s", e, traceback.format_exc())
        return jsonify({"message": "Internal server error"}), 500
