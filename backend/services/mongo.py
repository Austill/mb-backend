from pymongo import MongoClient
from pymongo.database import Database
from pymongo.collection import Collection
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

class MongoService:
    def __init__(self, mongo_uri: str, db_name: str):
        self.client: MongoClient = MongoClient(mongo_uri)
        self.db: Database = self.client[db_name]
        self.subscriptions: Collection = self.db.subscriptions
        self.users: Collection = self.db.users

    def create_subscription(self, doc: Dict[str, Any]) -> bool:
        """Inserts a new subscription document into the subscriptions collection."""
        try:
            result = self.subscriptions.insert_one(doc)
            return result.acknowledged
        except Exception as e:
            logger.error(f"Failed to create subscription: {e}")
            return False

    def get_subscription_by_payment_ref(self, ref: str) -> Optional[Dict[str, Any]]:
        """Finds a subscription by payment reference."""
        try:
            return self.subscriptions.find_one({"payment_ref": ref})
        except Exception as e:
            logger.error(f"Failed to get subscription by payment ref: {e}")
            return None

    def activate_subscription(self, subscription_id: str, renewal_date: Optional[datetime] = None) -> bool:
        """Updates a subscription to active status."""
        try:
            update_data = {"status": "active"}
            if renewal_date:
                update_data["renewal_date"] = renewal_date
            else:
                update_data["renewal_date"] = datetime.utcnow() + timedelta(days=30)

            result = self.subscriptions.update_one(
                {"_id": subscription_id},
                {"$set": update_data}
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Failed to activate subscription: {e}")
            return False

    def update_user_subscription(self, user_id: str, data: Dict[str, Any]) -> bool:
        """Updates user subscription status with upsert."""
        try:
            result = self.users.update_one(
                {"_id": user_id},
                {"$set": data},
                upsert=True
            )
            return result.acknowledged
        except Exception as e:
            logger.error(f"Failed to update user subscription: {e}")
            return False
