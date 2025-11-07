from backend import mongo
from datetime import datetime
from bson import ObjectId

class WellnessInsight:
    """
    Model to store AI-generated wellness insights and recommendations.
    Provides personalized tips based on user's mood and journal patterns.
    """
    collection = mongo.mindbuddy.wellness_insights

    def __init__(self, user_id, insight_type, insight_text, 
                 recommendation=None, activity_suggestion=None, priority='normal'):
        self._id = ObjectId()
        self.user_id = ObjectId(user_id) if isinstance(user_id, str) else user_id
        
        # Insight data
        self.insight_type = insight_type  # 'daily_tip', 'mood_pattern', 'crisis_support', 'wellness_recommendation'
        self.insight_text = insight_text  # The actual insight message
        self.recommendation = recommendation  # Specific recommendation (e.g., "Try breathing exercises")
        self.activity_suggestion = activity_suggestion  # 'meditation', 'breathing', 'journaling', 'exercise'
        
        # Metadata
        self.priority = priority  # 'low', 'normal', 'high', 'urgent'
        self.is_read = False
        self.is_dismissed = False
        
        # Context for generation
        self.based_on_sentiment = None  # Sentiment that triggered this insight
        self.based_on_pattern = None  # Pattern detected (e.g., "3 consecutive negative days")
        
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        self.read_at = None

    @classmethod
    def find_by_user(cls, user_id, limit=10, unread_only=False):
        """Find insights for a user"""
        user_oid = ObjectId(user_id) if isinstance(user_id, str) else user_id
        query = {"user_id": user_oid, "is_dismissed": False}
        
        if unread_only:
            query["is_read"] = False
        
        return list(cls.collection.find(query)
                   .sort("created_at", -1)
                   .limit(limit))

    @classmethod
    def find_by_id(cls, insight_id):
        return cls.collection.find_one({"_id": ObjectId(insight_id)})
    
    @classmethod
    def get_urgent_insights(cls, user_id):
        """Get urgent/high priority insights for a user"""
        user_oid = ObjectId(user_id) if isinstance(user_id, str) else user_id
        return list(cls.collection.find({
            "user_id": user_oid,
            "priority": {"$in": ["high", "urgent"]},
            "is_read": False,
            "is_dismissed": False
        }).sort("created_at", -1))
    
    @classmethod
    def get_daily_insight(cls, user_id):
        """Get the most recent daily insight for a user"""
        user_oid = ObjectId(user_id) if isinstance(user_id, str) else user_id
        from datetime import timedelta
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        
        return cls.collection.find_one({
            "user_id": user_oid,
            "insight_type": "daily_tip",
            "created_at": {"$gte": today_start},
            "is_dismissed": False
        })
    
    @classmethod
    def mark_old_insights_as_read(cls, user_id, days=7):
        """Mark old insights as read automatically"""
        user_oid = ObjectId(user_id) if isinstance(user_id, str) else user_id
        from datetime import timedelta
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        return cls.collection.update_many(
            {
                "user_id": user_oid,
                "created_at": {"$lte": cutoff_date},
                "is_read": False
            },
            {
                "$set": {
                    "is_read": True,
                    "read_at": datetime.utcnow()
                }
            }
        )

    def save(self):
        self.updated_at = datetime.utcnow()
        result = self.collection.insert_one(self.to_dict())
        self._id = result.inserted_id
        return result

    def update(self, data):
        self.updated_at = datetime.utcnow()
        data["updated_at"] = self.updated_at
        return self.collection.update_one({"_id": self._id}, {"$set": data})
    
    def mark_as_read(self):
        """Mark insight as read"""
        self.is_read = True
        self.read_at = datetime.utcnow()
        return self.update({
            "is_read": True,
            "read_at": self.read_at
        })
    
    def dismiss(self):
        """Dismiss/hide insight"""
        self.is_dismissed = True
        return self.update({"is_dismissed": True})

    def delete(self):
        return self.collection.delete_one({"_id": self._id})

    def to_dict(self):
        return {
            "_id": str(self._id),
            "user_id": str(self.user_id),
            "insight_type": self.insight_type,
            "insight_text": self.insight_text,
            "recommendation": self.recommendation,
            "activity_suggestion": self.activity_suggestion,
            "priority": self.priority,
            "is_read": self.is_read,
            "is_dismissed": self.is_dismissed,
            "based_on_sentiment": self.based_on_sentiment,
            "based_on_pattern": self.based_on_pattern,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "read_at": self.read_at.isoformat() if self.read_at else None
        }

    @classmethod
    def from_dict(cls, data):
        insight = cls.__new__(cls)
        insight._id = data.get("_id")
        insight.user_id = data.get("user_id")
        insight.insight_type = data.get("insight_type")
        insight.insight_text = data.get("insight_text")
        insight.recommendation = data.get("recommendation")
        insight.activity_suggestion = data.get("activity_suggestion")
        insight.priority = data.get("priority", "normal")
        insight.is_read = data.get("is_read", False)
        insight.is_dismissed = data.get("is_dismissed", False)
        insight.based_on_sentiment = data.get("based_on_sentiment")
        insight.based_on_pattern = data.get("based_on_pattern")
        insight.created_at = data.get("created_at")
        insight.updated_at = data.get("updated_at")
        insight.read_at = data.get("read_at")
        return insight

    def __repr__(self):
        return f"<WellnessInsight {self._id}: {self.insight_type} for User {self.user_id}>"
