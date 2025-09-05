from backend import db
from datetime import datetime
import json

class MoodEntry(db.Model):
    __tablename__ = "mood_entries"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    mood_level = db.Column(db.Integer, nullable=False)  # 1-5 scale
    emoji = db.Column(db.String(10), nullable=False)
    note = db.Column(db.Text, nullable=True)
    triggers = db.Column(db.Text, nullable=True)  # JSON string of triggers
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def set_triggers(self, triggers_list):
        """Set triggers as JSON string"""
        if triggers_list:
            self.triggers = json.dumps(triggers_list)
        else:
            self.triggers = None

    def get_triggers(self):
        """Get triggers as Python list"""
        if self.triggers:
            try:
                return json.loads(self.triggers)
            except json.JSONDecodeError:
                return []
        return []

    def to_dict(self):
        return {
            "id": self.id,
            "userId": self.user_id,
            "moodLevel": self.mood_level,
            "emoji": self.emoji,
            "note": self.note,
            "triggers": self.get_triggers(),
            "createdAt": self.created_at.isoformat() if self.created_at else None,
            "updatedAt": self.updated_at.isoformat() if self.updated_at else None
        }

    def __repr__(self):
        return f"<MoodEntry {self.id}: Level {self.mood_level} for User {self.user_id}>"
