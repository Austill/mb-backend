from backend import db
from datetime import datetime

class JournalEntry(db.Model):
    __tablename__ = "journal_entries"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    title = db.Column(db.String(150), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Merged fields
    is_private = db.Column(db.Boolean, default=False)
    sentiment = db.Column(db.String(20))
    ai_insights = db.Column(db.Text)
    tags = db.Column(db.JSON)

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "createdAt": self.created_at.isoformat() if self.created_at else None,
            "updatedAt": self.updated_at.isoformat() if self.updated_at else None,
            "isPrivate": self.is_private,
            "sentiment": self.sentiment,
            "aiInsights": self.ai_insights,
            "tags": self.tags
        }
