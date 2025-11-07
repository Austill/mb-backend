"""
Insights Generation Service
Generates personalized wellness insights based on user data.
Uses sentiment analysis and pattern detection.
"""

import logging
import random
from typing import Dict, List
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class InsightsGenerator:
    """
    Generates personalized wellness insights and recommendations
    based on user's mood patterns and journal entries.
    """
    
    def __init__(self):
        # Daily wellness tips (general advice)
        self.daily_tips = [
            "Remember to take deep breaths throughout your day. Even 5 minutes of mindful breathing can reduce stress.",
            "Try to get some sunlight today. Natural light can boost your mood and energy levels.",
            "Stay hydrated! Drinking enough water can improve your mood and cognitive function.",
            "Take a short walk today. Physical movement can help clear your mind and boost endorphins.",
            "Practice gratitude - write down three things you're thankful for today.",
            "Reach out to a friend or loved one. Social connection is vital for mental health.",
            "Set one small, achievable goal for today. Accomplishing it can boost your confidence.",
            "Be kind to yourself today. You're doing better than you think.",
            "Take breaks from screens. Give your mind a rest from digital stimulation.",
            "Try a new relaxation technique today - maybe progressive muscle relaxation or visualization."
        ]
        
        # Mood pattern insights
        self.pattern_insights = {
            'improving': [
                "Your mood has been improving lately! Keep up whatever you're doing - it's working.",
                "I've noticed positive changes in your emotional patterns. You're making great progress!",
                "Your recent entries show an upward trend. Celebrate these small victories!"
            ],
            'declining': [
                "I've noticed some challenging patterns in your recent entries. Remember, it's okay to have difficult days.",
                "Your mood has been lower lately. Consider trying some self-care activities or reaching out for support.",
                "I see you're going through a tough time. Be gentle with yourself and don't hesitate to ask for help."
            ],
            'stable': [
                "Your mood has been relatively stable. That's great! Keep maintaining your wellness routine.",
                "You've been maintaining emotional balance. Continue with the strategies that work for you.",
                "Your emotional patterns show consistency. Keep up your self-care practices!"
            ]
        }
        
        # Activity recommendations based on mood
        self.activity_suggestions = {
            'negative_high': {
                'activities': ['breathing', 'meditation', 'crisis_support'],
                'message': "When feelings are intense, grounding techniques can help. Try a breathing exercise or meditation."
            },
            'negative_medium': {
                'activities': ['journaling', 'breathing', 'meditation'],
                'message': "It's okay to feel down sometimes. Journaling or a short meditation might help process these feelings."
            },
            'neutral': {
                'activities': ['exercise', 'meditation', 'journaling'],
                'message': "Stay balanced with activities that promote overall wellness."
            },
            'positive': {
                'activities': ['gratitude', 'exercise', 'social'],
                'message': "Keep this positive energy going! Maybe try some gratitude journaling or connect with friends."
            }
        }
        
        logger.info("InsightsGenerator initialized")
    
    def generate_daily_insight(self, user_id: str, sentiment_history: List[Dict] = None) -> Dict:
        """
        Generate a daily wellness tip, optionally personalized based on recent sentiment.
        
        Args:
            user_id: User ID
            sentiment_history: Recent sentiment data
            
        Returns:
            Dict with insight data
        """
        # Base daily tip
        tip = random.choice(self.daily_tips)
        
        # Personalize based on recent sentiment if available
        if sentiment_history and len(sentiment_history) > 0:
            recent_sentiment = sentiment_history[0].get('sentiment_label', 'neutral')
            
            if recent_sentiment == 'negative':
                tip = (
                    "I noticed you might be having a challenging day. " + tip +
                    " And remember, it's perfectly okay to not be okay sometimes."
                )
            elif recent_sentiment == 'positive':
                tip = (
                    "I'm glad you're feeling good today! " + tip +
                    " Keep nurturing your positive energy."
                )
        
        return {
            'insight_type': 'daily_tip',
            'insight_text': tip,
            'recommendation': None,
            'activity_suggestion': None,
            'priority': 'normal'
        }
    
    def analyze_mood_patterns(self, sentiment_history: List[Dict]) -> Dict:
        """
        Analyze mood patterns and generate insights.
        
        Args:
            sentiment_history: List of sentiment records
            
        Returns:
            Dict with pattern analysis and insight
        """
        if not sentiment_history or len(sentiment_history) < 2:
            return None
        
        # Calculate pattern metrics
        negative_count = sum(1 for s in sentiment_history if s.get('sentiment_label') == 'negative')
        positive_count = sum(1 for s in sentiment_history if s.get('sentiment_label') == 'positive')
        total_count = len(sentiment_history)
        
        # Determine trend
        if negative_count > total_count * 0.6:
            trend = 'declining'
            priority = 'high'
        elif positive_count > total_count * 0.6:
            trend = 'improving'
            priority = 'normal'
        else:
            trend = 'stable'
            priority = 'normal'
        
        # Get appropriate insight message
        insight_text = random.choice(self.pattern_insights.get(trend, self.pattern_insights['stable']))
        
        # Add specific recommendation
        if trend == 'declining':
            recommendation = "Consider scheduling regular check-ins with yourself or a trusted friend."
            activity = 'meditation'
        elif trend == 'improving':
            recommendation = "Keep doing what you're doing! Your strategies are working well."
            activity = 'journaling'
        else:
            recommendation = "Maintain your current self-care routine for continued balance."
            activity = None
        
        return {
            'insight_type': 'mood_pattern',
            'insight_text': insight_text,
            'recommendation': recommendation,
            'activity_suggestion': activity,
            'priority': priority,
            'based_on_pattern': f"{trend} trend over {total_count} entries"
        }
    
    def generate_wellness_recommendation(self, sentiment: str, 
                                        sentiment_score: float = None) -> Dict:
        """
        Generate activity recommendation based on current sentiment.
        
        Args:
            sentiment: Current sentiment (positive, negative, neutral)
            sentiment_score: Confidence score
            
        Returns:
            Dict with wellness recommendation
        """
        # Determine intensity level
        if sentiment == 'negative':
            if sentiment_score and sentiment_score > 0.8:
                level = 'negative_high'
            else:
                level = 'negative_medium'
        else:
            level = sentiment
        
        suggestion = self.activity_suggestions.get(level, self.activity_suggestions['neutral'])
        
        # Pick a specific activity
        activity = random.choice(suggestion['activities'])
        
        # Activity-specific messages
        activity_messages = {
            'breathing': "Try a 5-minute breathing exercise: Breathe in for 4, hold for 4, out for 4.",
            'meditation': "A short 10-minute guided meditation can help center your thoughts.",
            'journaling': "Writing about your feelings can provide clarity and release.",
            'exercise': "A 20-minute walk or gentle exercise can boost your mood naturally.",
            'gratitude': "List three things you're grateful for today.",
            'social': "Reach out to someone you care about - connection is healing.",
            'crisis_support': "Please consider reaching out to a crisis helpline for immediate support."
        }
        
        detail = activity_messages.get(activity, suggestion['message'])
        
        priority = 'high' if level == 'negative_high' else 'normal'
        
        return {
            'insight_type': 'wellness_recommendation',
            'insight_text': suggestion['message'],
            'recommendation': detail,
            'activity_suggestion': activity,
            'priority': priority,
            'based_on_sentiment': sentiment
        }
    
    def generate_crisis_support_insight(self, crisis_keywords: List[str]) -> Dict:
        """
        Generate urgent support message when crisis is detected.
        
        Args:
            crisis_keywords: Keywords that triggered crisis detection
            
        Returns:
            Dict with crisis support insight
        """
        insight_text = (
            "I'm concerned about what you've shared. Please know that you don't have to face this alone. "
            "There are people who care and want to help you through this difficult time."
        )
        
        recommendation = (
            "**Immediate Resources:**\n"
            "• National Suicide Prevention Lifeline: 988\n"
            "• Crisis Text Line: Text 'HELLO' to 741741\n"
            "• Emergency Services: 911\n\n"
            "Please reach out to one of these resources right away. Your life matters."
        )
        
        return {
            'insight_type': 'crisis_support',
            'insight_text': insight_text,
            'recommendation': recommendation,
            'activity_suggestion': 'crisis_support',
            'priority': 'urgent',
            'based_on_pattern': f"Crisis keywords detected: {', '.join(crisis_keywords[:3])}"
        }
    
    def generate_check_in_message(self, days_since_login: int) -> Dict:
        """
        Generate a check-in message for inactive users.
        
        Args:
            days_since_login: Number of days since last login
            
        Returns:
            Dict with check-in insight
        """
        if days_since_login >= 7:
            message = (
                f"We haven't seen you in {days_since_login} days. "
                "Your mental wellness journey matters, and we're here for you. "
                "Even small steps count - how about a quick check-in today?"
            )
            priority = 'high'
        elif days_since_login >= 3:
            message = (
                f"It's been {days_since_login} days since your last visit. "
                "How are you feeling? Taking a moment to check in with yourself can be valuable."
            )
            priority = 'normal'
        else:
            message = "Welcome back! How has your day been?"
            priority = 'low'
        
        return {
            'insight_type': 'daily_tip',
            'insight_text': message,
            'recommendation': "Try journaling about your current feelings or mood.",
            'activity_suggestion': 'journaling',
            'priority': priority
        }
    
    def should_generate_insight(self, existing_insights: List[Dict], 
                               insight_type: str) -> bool:
        """
        Check if a new insight of given type should be generated.
        Prevents spam by checking recency.
        
        Args:
            existing_insights: User's existing insights
            insight_type: Type of insight to check
            
        Returns:
            Boolean indicating if new insight should be generated
        """
        if not existing_insights:
            return True
        
        # Check for recent insights of same type
        now = datetime.utcnow()
        cooldown_hours = {
            'daily_tip': 24,  # Once per day
            'mood_pattern': 48,  # Every 2 days
            'wellness_recommendation': 6,  # Every 6 hours
            'crisis_support': 0  # No cooldown for crisis
        }
        
        cooldown = cooldown_hours.get(insight_type, 24)
        cutoff_time = now - timedelta(hours=cooldown)
        
        for insight in existing_insights:
            if insight.get('insight_type') == insight_type:
                created_str = insight.get('created_at')
                if created_str:
                    try:
                        created_at = datetime.fromisoformat(created_str.replace('Z', '+00:00'))
                        if created_at > cutoff_time:
                            return False
                    except:
                        pass
        
        return True


# Singleton instance
_insights_generator = None

def get_insights_generator() -> InsightsGenerator:
    """Get or create the global insights generator instance"""
    global _insights_generator
    if _insights_generator is None:
        _insights_generator = InsightsGenerator()
    return _insights_generator
