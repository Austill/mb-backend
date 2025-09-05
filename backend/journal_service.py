from textblob import TextBlob
import random

def analyze_sentiment(text: str) -> str:
    analysis = TextBlob(text)
    if analysis.sentiment.polarity > 0.1:
        return 'positive'
    elif analysis.sentiment.polarity < -0.1:
        return 'negative'
    return 'neutral'

def generate_ai_insights(sentiment: str) -> str:
    insights = {
      "positive": [
        "Your entry shows strong positive sentiment. Consider maintaining this momentum by continuing the practices that led to these feelings.",
        "Great to see such optimism! This positive mindset can help you tackle future challenges.",
        "Your positive outlook is evident. Try to remember this feeling during more difficult times."
      ],
      "negative": [
        "Your entry indicates some challenges. Consider practicing mindfulness or reaching out to someone you trust.",
        "It's normal to have difficult days. Remember that these feelings are temporary and will pass.",
        "Consider breaking down overwhelming tasks into smaller, manageable steps to reduce stress."
      ],
      "neutral": [
        "Your entry shows balanced reflection. Consider what small changes might enhance your wellbeing.",
        "Neutral days are part of life's natural rhythm. Notice what might shift your energy positively.",
        "This seems like a day of steady progress. Consider celebrating small wins along the way."
      ]
    }
    options = insights.get(sentiment, insights['neutral'])
    return random.choice(options)

def extract_tags(content: str) -> list:
    common_tags = ['work', 'family', 'health', 'stress', 'happiness', 'goals', 'relationships', 'anxiety', 'accomplishment']
    found_tags = set()
    text = content.lower()
    for tag in common_tags:
        if tag in text:
            found_tags.add(tag)
    return list(found_tags)[:3]