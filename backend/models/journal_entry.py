from backend import mongo
from datetime import datetime
from bson import ObjectId

class JournalEntry:
    collection = mongo.mindbuddy.journal_entries

    def __init__(self, user_id, title, content, is_private=False, sentiment=None, ai_insights=None, tags=None):
        self._id = ObjectId()
        self.user_id = ObjectId(user_id) if isinstance(user_id, str) else user_id
        self.title = title or ""
        self.content = content or ""
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        self.is_private = is_private
        self.sentiment = sentiment
        self.ai_insights = ai_insights
        self.tags = tags or []

    @classmethod
    def find_by_user(cls, user_id):
        user_oid = ObjectId(user_id) if isinstance(user_id, str) else user_id
        return list(cls.collection.find({"user_id": user_oid}))

    @classmethod
    def find_by_id(cls, entry_id):
        return cls.collection.find_one({"_id": ObjectId(entry_id)})

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
        # return both snake_case (for backward compatibility) and camelCase (for React)
        return {
            "_id": str(self._id),
            "id": str(self._id),
            "user_id": str(self.user_id),
            "userId": str(self.user_id),
            "title": self.title,
            "content": self.content,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "createdAt": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "updatedAt": self.updated_at.isoformat() if self.updated_at else None,
            "is_private": self.is_private,
            "isPrivate": self.is_private,
            "sentiment": self.sentiment,
            "ai_insights": self.ai_insights,
            "aiInsights": self.ai_insights,
            "tags": self.tags
        }

    @classmethod
    def from_dict(cls, data):
        entry = cls.__new__(cls)
        entry._id = data.get("_id") or data.get("id")
        if isinstance(entry._id, str):
            entry._id = ObjectId(entry._id)

        uid = data.get("user_id") or data.get("userId")
        entry.user_id = ObjectId(uid) if isinstance(uid, str) else uid

        entry.title = data.get("title", "")
        entry.content = data.get("content", "")
        entry.is_private = data.get("is_private", data.get("isPrivate", False))
        entry.sentiment = data.get("sentiment")
        entry.ai_insights = data.get("ai_insights") or data.get("aiInsights")
        entry.tags = data.get("tags", [])

        # handle dates
        created = data.get("created_at") or data.get("createdAt")
        updated = data.get("updated_at") or data.get("updatedAt")

        if isinstance(created, str):
            entry.created_at = datetime.fromisoformat(created.replace("Z", "+00:00"))
        else:
            entry.created_at = created

        if isinstance(updated, str):
            entry.updated_at = datetime.fromisoformat(updated.replace("Z", "+00:00"))
        else:
            entry.updated_at = updated

        return entry
