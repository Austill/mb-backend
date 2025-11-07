from backend import mongo
from datetime import datetime
from bson import ObjectId

class MoodEntry:
    collection = mongo.mindbuddy.mood_entries

    def __init__(self, user_id, mood_level, emoji, note=None, triggers=None):
        self._id = ObjectId()
        self.user_id = ObjectId(user_id) if isinstance(user_id, str) else user_id
        self.mood_level = mood_level
        self.emoji = emoji
        self.note = note
        self.triggers = triggers or []
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

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

    def set_triggers(self, triggers):
        if isinstance(triggers, list):
            self.triggers = triggers
        else:
            self.triggers = [triggers] if triggers else []

    def get_triggers(self):
        return self.triggers or []

    def to_dict(self):
        # normalize to camelCase for frontend
        return {
            "_id": str(self._id),
            "id": str(self._id),
            "user_id": str(self.user_id),
            "userId": str(self.user_id),
            "mood_level": self.mood_level,
            "moodLevel": self.mood_level,
            "emoji": self.emoji,
            "note": self.note,
            "triggers": self.triggers,
            "created_at": self.created_at.isoformat() + "Z" if self.created_at else datetime.utcnow().isoformat() + "Z",
            "createdAt": self.created_at.isoformat() + "Z" if self.created_at else datetime.utcnow().isoformat() + "Z",
            "updated_at": self.updated_at.isoformat() + "Z" if self.updated_at else datetime.utcnow().isoformat() + "Z",
            "updatedAt": self.updated_at.isoformat() + "Z" if self.updated_at else datetime.utcnow().isoformat() + "Z"
        }

    @classmethod
    def from_dict(cls, data):
        entry = cls.__new__(cls)
        entry._id = data.get("_id") or data.get("id")
        if isinstance(entry._id, str):
            entry._id = ObjectId(entry._id)

        uid = data.get("user_id") or data.get("userId")
        entry.user_id = ObjectId(uid) if isinstance(uid, str) else uid

        entry.mood_level = data.get("mood_level", data.get("moodLevel"))
        entry.emoji = data.get("emoji")
        entry.note = data.get("note")
        entry.triggers = data.get("triggers", [])

        created = data.get("created_at") or data.get("createdAt")
        updated = data.get("updated_at") or data.get("updatedAt")

        # Handle created_at with fallbacks
        if isinstance(created, str):
            try:
                entry.created_at = datetime.fromisoformat(created.replace("Z", "+00:00"))
            except (ValueError, TypeError):
                entry.created_at = datetime.utcnow()
        elif isinstance(created, datetime):
            entry.created_at = created
        else:
            entry.created_at = datetime.utcnow()

        # Handle updated_at with fallbacks
        if isinstance(updated, str):
            try:
                entry.updated_at = datetime.fromisoformat(updated.replace("Z", "+00:00"))
            except (ValueError, TypeError):
                entry.updated_at = datetime.utcnow()
        elif isinstance(updated, datetime):
            entry.updated_at = updated
        else:
            entry.updated_at = datetime.utcnow()

        return entry

    def __repr__(self):
        return f"<MoodEntry {self._id}: Level {self.mood_level} for User {self.user_id}>"
