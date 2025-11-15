from flask import Blueprint, request, jsonify, current_app
from backend.models import MoodEntry, JournalEntry
from backend.decorators import token_required
import traceback
from datetime import datetime, timedelta
from bson import ObjectId

progress_bp = Blueprint("progress", __name__)

# Mood level mappings for categorization
MOOD_LABELS = {
    5: "excellent",
    4: "good",
    3: "neutral",
    2: "low",
    1: "poor"
}

@progress_bp.route("/ping", methods=["GET"])
def ping_progress():
    return jsonify({"message": "progress blueprint is alive"}), 200

@progress_bp.route("", methods=["GET"])
@token_required
def get_progress(current_user):
    """
    Get aggregated progress analytics for the user:
    - average mood (0-5 scale)
    - mood trend breakdown (excellent/good/neutral/low/poor)
    - number of check-ins this week
    - total journal entries
    - all entries (moods and journals)
    """
    try:
        user_id = str(current_user._id)
        
        # Calculate date ranges
        now = datetime.utcnow()
        today = now.date()
        week_start = now - timedelta(days=7)
        month_start = now - timedelta(days=30)

        # Fetch all mood entries for the user
        all_mood_data = MoodEntry.find_by_user(user_id)
        mood_entries = [MoodEntry.from_dict(m) for m in all_mood_data]

        # Fetch all journal entries for the user
        all_journal_data = JournalEntry.find_by_user(user_id)
        journal_entries = [JournalEntry.from_dict(j) for j in all_journal_data]

        # ========== MOOD ANALYTICS ==========
        
        # Calculate average mood (all time)
        average_mood = 0
        if mood_entries:
            total_mood = sum(entry.mood_level for entry in mood_entries)
            average_mood = round(total_mood / len(mood_entries), 2)

        # Mood trend breakdown (all time)
        mood_trend = {
            "excellent": 0,  # level 5
            "good": 0,       # level 4
            "neutral": 0,    # level 3
            "low": 0,        # level 2
            "poor": 0        # level 1
        }

        for entry in mood_entries:
            label = MOOD_LABELS.get(entry.mood_level, "neutral")
            mood_trend[label] += 1

        # Check-ins this week
        week_checkins = 0
        for entry in mood_entries:
            if entry.created_at >= week_start:
                week_checkins += 1

        # Check-ins today
        today_checkins = 0
        for entry in mood_entries:
            if entry.created_at.date() == today:
                today_checkins += 1

        # Today's mood if exists
        today_mood = None
        for entry in mood_entries:
            if entry.created_at.date() == today:
                today_mood = entry.to_dict()
                break

        # ========== JOURNAL ANALYTICS ==========
        
        total_journals = len(journal_entries)
        
        # Journals this week
        week_journals = 0
        for entry in journal_entries:
            if entry.created_at >= week_start:
                week_journals += 1

        # Journals today
        today_journals = 0
        for entry in journal_entries:
            if entry.created_at.date() == today:
                today_journals += 1

        # ========== COMBINED ENTRIES ==========
        
        # Combine and sort all entries by date (newest first)
        all_entries = []
        
        for mood in mood_entries:
            all_entries.append({
                "type": "mood",
                "id": mood._id,
                "userId": str(mood.user_id),
                "moodLevel": mood.mood_level,
                "emoji": mood.emoji,
                "note": mood.note,
                "triggers": mood.triggers,
                "createdAt": mood.created_at.isoformat() if mood.created_at else None,
                "updatedAt": mood.updated_at.isoformat() if mood.updated_at else None,
                "fullEntry": mood.to_dict()
            })
        
        for journal in journal_entries:
            all_entries.append({
                "type": "journal",
                "id": journal._id,
                "userId": str(journal.user_id),
                "title": journal.title,
                "content": journal.content,
                "isPrivate": journal.is_private,
                "tags": journal.tags,
                "createdAt": journal.created_at.isoformat() if journal.created_at else None,
                "updatedAt": journal.updated_at.isoformat() if journal.updated_at else None,
                "fullEntry": journal.to_dict()
            })

        # Sort by date (newest first)
        all_entries.sort(
            key=lambda x: datetime.fromisoformat(x['createdAt'].replace('Z', '+00:00')) if x['createdAt'] else datetime.min,
            reverse=True
        )

        # ========== BUILD RESPONSE ==========

        response = {
            "analytics": {
                "mood": {
                    "averageMood": average_mood,
                    "trend": mood_trend,
                    "totalEntries": len(mood_entries),
                    "weekCheckins": week_checkins,
                    "todayCheckins": today_checkins,
                    "todayMood": today_mood
                },
                "journal": {
                    "totalEntries": total_journals,
                    "weekEntries": week_journals,
                    "todayEntries": today_journals
                },
                "summary": {
                    "totalMoodEntries": len(mood_entries),
                    "totalJournalEntries": total_journals,
                    "weekActivity": week_checkins + week_journals,
                    "todayActivity": today_checkins + today_journals
                }
            },
            "entries": all_entries,
            "stats": {
                "generatedAt": now.isoformat()
            }
        }

        return jsonify(response), 200

    except Exception as e:
        current_app.logger.error("Get progress analytics error: %s\n%s", e, traceback.format_exc())
        return jsonify({"message": "Internal server error", "error": str(e)}), 500


@progress_bp.route("/summary", methods=["GET"])
@token_required
def get_progress_summary(current_user):
    """
    Get a quick summary of progress (without full entries list)
    """
    try:
        user_id = str(current_user._id)
        
        # Calculate date ranges
        now = datetime.utcnow()
        today = now.date()
        week_start = now - timedelta(days=7)

        # Fetch all entries
        all_mood_data = MoodEntry.find_by_user(user_id)
        mood_entries = [MoodEntry.from_dict(m) for m in all_mood_data]

        all_journal_data = JournalEntry.find_by_user(user_id)
        journal_entries = [JournalEntry.from_dict(j) for j in all_journal_data]

        # Calculate statistics
        average_mood = 0
        if mood_entries:
            total_mood = sum(entry.mood_level for entry in mood_entries)
            average_mood = round(total_mood / len(mood_entries), 2)

        mood_trend = {
            "excellent": sum(1 for e in mood_entries if e.mood_level == 5),
            "good": sum(1 for e in mood_entries if e.mood_level == 4),
            "neutral": sum(1 for e in mood_entries if e.mood_level == 3),
            "low": sum(1 for e in mood_entries if e.mood_level == 2),
            "poor": sum(1 for e in mood_entries if e.mood_level == 1)
        }

        week_checkins = sum(1 for e in mood_entries if e.created_at >= week_start)
        today_checkins = sum(1 for e in mood_entries if e.created_at.date() == today)

        week_journals = sum(1 for e in journal_entries if e.created_at >= week_start)
        today_journals = sum(1 for e in journal_entries if e.created_at.date() == today)

        summary = {
            "mood": {
                "averageMood": average_mood,
                "trend": mood_trend,
                "totalEntries": len(mood_entries),
                "weekCheckins": week_checkins,
                "todayCheckins": today_checkins
            },
            "journal": {
                "totalEntries": len(journal_entries),
                "weekEntries": week_journals,
                "todayEntries": today_journals
            },
            "overview": {
                "totalMoodEntries": len(mood_entries),
                "totalJournalEntries": len(journal_entries),
                "weekActivity": week_checkins + week_journals,
                "todayActivity": today_checkins + today_journals,
                "generatedAt": now.isoformat()
            }
        }

        return jsonify(summary), 200

    except Exception as e:
        current_app.logger.error("Get progress summary error: %s\n%s", e, traceback.format_exc())
        return jsonify({"message": "Internal server error"}), 500
