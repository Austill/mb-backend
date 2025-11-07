from backend import mongo
from datetime import datetime
from bson import ObjectId

class SentimentHistory:
    """
    Model to store sentiment analysis results from journal entries.
    Tracks emotional patterns over time for insights and crisis detection.
    """
    collection = mongo.mindbuddy.sentiment_history

    def __init__(self, user_id, journal_entry_id=None, sentiment_label=None, 
                 sentiment_scores=None, detected_emotions=None, crisis_flag=False):
        self._id = ObjectId()
        self.user_id = ObjectId(user_id) if isinstance(user_id, str) else user_id
        self.journal_entry_id = ObjectId(journal_entry_id) if isinstance(journal_entry_id, str) and journal_entry_id else journal_entry_id
        
        # Sentiment data
        self.sentiment_label = sentiment_label  # 'positive', 'negative', 'neutral'
        self.sentiment_scores = sentiment_scores or {}  # {'positive': 0.8, 'negative': 0.1, 'neutral': 0.1}
        self.detected_emotions = detected_emotions or []  # ['joy', 'sadness', 'anger', etc.]
        
        # Crisis detection
        self.crisis_flag = crisis_flag
        self.crisis_keywords = []  # Keywords that triggered crisis detection
        
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    @classmethod
    def find_by_user(cls, user_id, limit=None, days=None):
        """Find sentiment history for a user, optionally limited or filtered by days"""
        user_oid = ObjectId(user_id) if isinstance(user_id, str) else user_id
        query = {"user_id": user_oid}
        
        if days:
            from datetime import timedelta
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            query["created_at"] = {"$gte": cutoff_date}
        
        cursor = cls.collection.find(query).sort("created_at", -1)
        if limit:
            cursor = cursor.limit(limit)
        
        return list(cursor)

    @classmethod
    def find_by_id(cls, sentiment_id):
        return cls.collection.find_one({"_id": ObjectId(sentiment_id)})
    
    @classmethod
    def find_by_journal_entry(cls, journal_entry_id):
        """Find sentiment for a specific journal entry"""
        entry_oid = ObjectId(journal_entry_id) if isinstance(journal_entry_id, str) else journal_entry_id
        return cls.collection.find_one({"journal_entry_id": entry_oid})
    
    @classmethod
    def get_recent_crisis_flags(cls, user_id, days=7):
        """Get recent crisis flags for a user"""
        user_oid = ObjectId(user_id) if isinstance(user_id, str) else user_id
        from datetime import timedelta
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        return list(cls.collection.find({
            "user_id": user_oid,
            "crisis_flag": True,
            "created_at": {"$gte": cutoff_date}
        }).sort("created_at", -1))
    
    @classmethod
    def get_sentiment_trends(cls, user_id, days=30):
        """Get sentiment trends for analytics"""
        user_oid = ObjectId(user_id) if isinstance(user_id, str) else user_id
        from datetime import timedelta
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        pipeline = [
            {
                "$match": {
                    "user_id": user_oid,
                    "created_at": {"$gte": cutoff_date}
                }
            },
            {
                "$group": {
                    "_id": "$sentiment_label",
                    "count": {"$sum": 1},
                    "avg_score": {"$avg": "$sentiment_scores.positive"}
                }
            }
        ]
        
        return list(cls.collection.aggregate(pipeline))

    def save(self):
        self.updated_at = datetime.utcnow()
        result = self.collection.insert_one(self.to_dict())
        self._id = result.inserted_id
        return result

    def update(self, data):
        self.updated_at = datetime.utcnow()
        data["updated_at"] = self.updated_at
        return self.collection.update_one({"_id": self._id}, {"$set": data})

    def delete(self):
        return self.collection.delete_one({"_id": self._id})

    def to_dict(self):
        return {
            "_id": str(self._id),
            "user_id": str(self.user_id),
            "journal_entry_id": str(self.journal_entry_id) if self.journal_entry_id else None,
            "sentiment_label": self.sentiment_label,
            "sentiment_scores": self.sentiment_scores,
            "detected_emotions": self.detected_emotions,
            "crisis_flag": self.crisis_flag,
            "crisis_keywords": self.crisis_keywords,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

    @classmethod
    def from_dict(cls, data):
        sentiment = cls.__new__(cls)
        sentiment._id = data.get("_id")
        sentiment.user_id = data.get("user_id")
        sentiment.journal_entry_id = data.get("journal_entry_id")
        sentiment.sentiment_label = data.get("sentiment_label")
        sentiment.sentiment_scores = data.get("sentiment_scores", {})
        sentiment.detected_emotions = data.get("detected_emotions", [])
        sentiment.crisis_flag = data.get("crisis_flag", False)
        sentiment.crisis_keywords = data.get("crisis_keywords", [])
        sentiment.created_at = data.get("created_at")
        sentiment.updated_at = data.get("updated_at")
        return sentiment

    def __repr__(self):
        return f"<SentimentHistory {self._id}: {self.sentiment_label} for User {self.user_id}>"
