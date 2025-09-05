from backend import db
from datetime import datetime
import json

class UserSettings(db.Model):
    __tablename__ = "user_settings"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    
    # Notification settings
    mood_reminders = db.Column(db.Boolean, default=True)
    journal_reminders = db.Column(db.Boolean, default=True)
    crisis_alerts = db.Column(db.Boolean, default=True)
    weekly_reports = db.Column(db.Boolean, default=False)
    
    # Privacy settings
    data_sharing = db.Column(db.Boolean, default=False)
    analytics = db.Column(db.Boolean, default=True)
    crash_reports = db.Column(db.Boolean, default=True)
    
    # Preferences
    theme = db.Column(db.String(20), default='system')  # light, dark, system
    language = db.Column(db.String(10), default='en')
    timezone = db.Column(db.String(50), default='UTC')
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
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

    def __repr__(self):
        return f"<UserSettings for User {self.user_id}>"
