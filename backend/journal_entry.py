from app import db
from datetime import datetime

class JournalEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    content = db.Column(db.Text, nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    is_private = db.Column(db.Boolean, default=False)
    sentiment = db.Column(db.String(20))
    ai_insights = db.Column(db.Text)
    tags = db.Column(db.JSON)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'date': self.date.isoformat(),
            'isPrivate': self.is_private,
            'sentiment': self.sentiment,
            'aiInsights': self.ai_insights,
            'tags': self.tags
        }