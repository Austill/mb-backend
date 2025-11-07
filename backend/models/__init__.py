# backend/models/__init__.py

# Import payment models first to avoid circular imports
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
import payment_models
SubscribeRequest = payment_models.SubscribeRequest
SubscribeResponse = payment_models.SubscribeResponse
WebhookResponse = payment_models.WebhookResponse
SubscriptionDoc = payment_models.SubscriptionDoc
UserDoc = payment_models.UserDoc

from .user import User
from .user_settings import UserSettings
from .mood_entry import MoodEntry
from .journal_entry import JournalEntry
from .sentiment_history import SentimentHistory
from .chat_log import ChatLog
from .wellness_insight import WellnessInsight

# Export all models
__all__ = [
    "User",
    "JournalEntry",
    "UserSettings",
    "MoodEntry",
    "SentimentHistory",
    "ChatLog",
    "WellnessInsight",
    "SubscribeRequest",
    "SubscribeResponse",
    "WebhookResponse",
    "SubscriptionDoc",
    "UserDoc"
]
