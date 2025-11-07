from backend import mongo, bcrypt
from datetime import datetime
from bson import ObjectId

class User:
    collection = mongo.mindbuddy.users

    def __init__(self, email, first_name, last_name, phone=None, password=None, is_premium=False):
        self._id = ObjectId()
        self.email = email
        self.password_hash = None
        self.first_name = first_name
        self.last_name = last_name
        self.phone = phone
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        self.is_premium = is_premium

        if password:
            self.set_password(password)

    @classmethod
    def find_by_email(cls, email):
        return cls.collection.find_one({"email": email})

    @classmethod
    def find_by_id(cls, user_id):
        import logging
        logger = logging.getLogger(__name__)
        logger.debug("find_by_id called with user_id: %s", user_id)

        # Try ObjectId search first (new format)
        try:
            result = cls.collection.find_one({"_id": ObjectId(user_id)})
            if result:
                logger.debug("find_by_id result (ObjectId): %s", result)
                return result
        except Exception as e:
            logger.debug("ObjectId search failed: %s", e)

        # Fallback to string search (legacy format)
        result = cls.collection.find_one({"_id": user_id})
        logger.debug("find_by_id result (string): %s", result)
        return result

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

    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode("utf-8")

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            "_id": self._id,  # Don't convert to string, let MongoDB handle ObjectId
            "email": self.email,
            "password_hash": self.password_hash,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "phone": self.phone,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "is_premium": self.is_premium
        }

    @classmethod
    def from_dict(cls, data):
        user = cls.__new__(cls)
        user._id = ObjectId(data.get("_id")) if isinstance(data.get("_id"), str) else data.get("_id")
        user.email = data.get("email")
        user.password_hash = data.get("password_hash")
        user.first_name = data.get("first_name")
        user.last_name = data.get("last_name")
        user.phone = data.get("phone")
        created_at = data.get("created_at")
        if isinstance(created_at, str):
            user.created_at = datetime.fromisoformat(created_at)
        else:
            user.created_at = created_at
        updated_at = data.get("updated_at")
        if isinstance(updated_at, str):
            user.updated_at = datetime.fromisoformat(updated_at)
        else:
            user.updated_at = updated_at
        user.is_premium = data.get("is_premium", False)
        return user
