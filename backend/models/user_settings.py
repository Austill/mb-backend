from backend import mongo
from datetime import datetime
from bson import ObjectId

class UserSettings:
    collection = mongo.mindbuddy.user_settings

    def __init__(self, user_id):
        self._id = ObjectId()
        self.user_id = ObjectId(user_id) if isinstance(user_id, str) else user_id

        # Notification settings
        self.mood_reminders = True
        self.journal_reminders = True
        self.crisis_alerts = True
        self.weekly_reports = False

        # Privacy settings
        self.data_sharing = False
        self.analytics = True
        self.crash_reports = True

        # Preferences
        self.theme = 'system'  # light, dark, system
        self.language = 'en'
        self.timezone = 'UTC'

        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    @classmethod
    def find_by_user(cls, user_id):
        user_oid = ObjectId(user_id) if isinstance(user_id, str) else user_id
        return cls.collection.find_one({"user_id": user_oid})

    @classmethod
    def find_by_id(cls, settings_id):
        return cls.collection.find_one({"_id": ObjectId(settings_id)})

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
            "mood_reminders": self.mood_reminders,
            "journal_reminders": self.journal_reminders,
            "crisis_alerts": self.crisis_alerts,
            "weekly_reports": self.weekly_reports,
            "data_sharing": self.data_sharing,
            "analytics": self.analytics,
            "crash_reports": self.crash_reports,
            "theme": self.theme,
            "language": self.language,
            "timezone": self.timezone,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

    def to_dict_formatted(self):
        return {
            "notifications": {
                "moodReminders": self.mood_reminders,
                "journalReminders": self.journal_reminders,
                "crisisAlerts": self.crisis_alerts,
                "weeklyReports": self.weekly_reports
            },
            "privacy": {
                "dataSharing": self.data_sharing,
                "analytics": self.analytics,
                "crashReports": self.crash_reports
            },
            "preferences": {
                "theme": self.theme,
                "language": self.language,
                "timezone": self.timezone
            }
        }

    def update_from_dict(self, data):
        """Update settings from dictionary"""
        if 'notifications' in data:
            notifications = data['notifications']
            self.mood_reminders = notifications.get('moodReminders', self.mood_reminders)
            self.journal_reminders = notifications.get('journalReminders', self.journal_reminders)
            self.crisis_alerts = notifications.get('crisisAlerts', self.crisis_alerts)
            self.weekly_reports = notifications.get('weeklyReports', self.weekly_reports)

        if 'privacy' in data:
            privacy = data['privacy']
            self.data_sharing = privacy.get('dataSharing', self.data_sharing)
            self.analytics = privacy.get('analytics', self.analytics)
            self.crash_reports = privacy.get('crashReports', self.crash_reports)

        if 'preferences' in data:
            preferences = data['preferences']
            self.theme = preferences.get('theme', self.theme)
            self.language = preferences.get('language', self.language)
            self.timezone = preferences.get('timezone', self.timezone)

    @classmethod
    def from_dict(cls, data):
        settings = cls.__new__(cls)
        settings._id = data.get("_id")
        settings.user_id = data.get("user_id")
        settings.mood_reminders = data.get("mood_reminders", True)
        settings.journal_reminders = data.get("journal_reminders", True)
        settings.crisis_alerts = data.get("crisis_alerts", True)
        settings.weekly_reports = data.get("weekly_reports", False)
        settings.data_sharing = data.get("data_sharing", False)
        settings.analytics = data.get("analytics", True)
        settings.crash_reports = data.get("crash_reports", True)
        settings.theme = data.get("theme", 'system')
        settings.language = data.get("language", 'en')
        settings.timezone = data.get("timezone", 'UTC')
        settings.created_at = data.get("created_at")
        settings.updated_at = data.get("updated_at")
        return settings

    def __repr__(self):
        return f"<UserSettings for User {self.user_id}>"
