from backend import mongo
from datetime import datetime
from bson import ObjectId

class ChatLog:
    """
    Model to store chat conversations with the AI assistant (Sereni).
    Maintains conversation context and history.
    """
    collection = mongo.mindbuddy.chat_logs

    def __init__(self, user_id, message, role='user', ai_response=None, 
                 conversation_id=None, context_summary=None):
        self._id = ObjectId()
        self.user_id = ObjectId(user_id) if isinstance(user_id, str) else user_id
        
        # Conversation data
        self.conversation_id = conversation_id or str(ObjectId())  # Group related messages
        self.message = message  # User's message
        self.role = role  # 'user' or 'assistant'
        self.ai_response = ai_response  # AI's response (if role is 'user')
        
        # Context and metadata
        self.context_summary = context_summary  # Brief summary for context window
        self.sentiment = None  # Detected sentiment of the message
        self.tokens_used = 0  # Track token usage for optimization
        
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    @classmethod
    def find_by_user(cls, user_id, limit=50):
        """Find recent chat messages for a user"""
        user_oid = ObjectId(user_id) if isinstance(user_id, str) else user_id
        return list(cls.collection.find({"user_id": user_oid})
                   .sort("created_at", -1)
                   .limit(limit))

    @classmethod
    def find_by_conversation(cls, conversation_id, limit=20):
        """Find messages in a specific conversation"""
        return list(cls.collection.find({"conversation_id": conversation_id})
                   .sort("created_at", 1)
                   .limit(limit))

    @classmethod
    def find_by_id(cls, chat_id):
        return cls.collection.find_one({"_id": ObjectId(chat_id)})
    
    @classmethod
    def get_recent_conversations(cls, user_id, limit=10):
        """Get recent unique conversations for a user"""
        user_oid = ObjectId(user_id) if isinstance(user_id, str) else user_id
        
        pipeline = [
            {"$match": {"user_id": user_oid}},
            {"$sort": {"created_at": -1}},
            {
                "$group": {
                    "_id": "$conversation_id",
                    "last_message": {"$first": "$message"},
                    "last_updated": {"$first": "$created_at"},
                    "message_count": {"$sum": 1}
                }
            },
            {"$sort": {"last_updated": -1}},
            {"$limit": limit}
        ]
        
        return list(cls.collection.aggregate(pipeline))
    
    @classmethod
    def get_conversation_context(cls, conversation_id, limit=5):
        """Get recent messages for conversation context (for AI)"""
        messages = cls.find_by_conversation(conversation_id, limit=limit)
        
        # Format for AI context
        context = []
        for msg in messages:
            context.append({
                "role": msg.get("role", "user"),
                "content": msg.get("message") if msg.get("role") == "user" else msg.get("ai_response")
            })
        
        return context

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
            "conversation_id": self.conversation_id,
            "message": self.message,
            "role": self.role,
            "ai_response": self.ai_response,
            "context_summary": self.context_summary,
            "sentiment": self.sentiment,
            "tokens_used": self.tokens_used,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

    @classmethod
    def from_dict(cls, data):
        chat = cls.__new__(cls)
        chat._id = data.get("_id")
        chat.user_id = data.get("user_id")
        chat.conversation_id = data.get("conversation_id")
        chat.message = data.get("message")
        chat.role = data.get("role", "user")
        chat.ai_response = data.get("ai_response")
        chat.context_summary = data.get("context_summary")
        chat.sentiment = data.get("sentiment")
        chat.tokens_used = data.get("tokens_used", 0)
        chat.created_at = data.get("created_at")
        chat.updated_at = data.get("updated_at")
        return chat

    def __repr__(self):
        return f"<ChatLog {self._id}: {self.role} in conversation {self.conversation_id}>"
