"""
Lightweight Sentiment Analyzer
Replaced heavy Hugging Face / torch dependency with a small rule-based analyzer.
This keeps basic sentiment labels and crisis detection while removing the need for
transformers/torch in the project.
"""

import logging
from typing import Dict, List

logger = logging.getLogger(__name__)


class SentimentAnalyzer:
    def __init__(self):
        # Simple keyword lists
        self.positive_words = set([
            'happy', 'good', 'great', 'fantastic', 'joy', 'joyful', 'glad', 'pleased', 'love', 'excited'
        ])
        self.negative_words = set([
            'sad', 'down', 'depressed', 'unhappy', 'angry', 'annoyed', 'tired', 'anxious', 'stressed', 'lonely'
        ])

        self.crisis_keywords = [
            'suicide', 'suicidal', 'kill myself', 'end it all', 'want to die', 'hurt myself', 'overdose'
        ]

        logger.info("SentimentAnalyzer initialized (lightweight)")

    def analyze_sentiment(self, text: str) -> Dict:
        if not text or len(text.strip()) < 3:
            return {
                'sentiment_label': 'neutral',
                'sentiment_scores': {'negative': 0.33, 'neutral': 0.34, 'positive': 0.33},
                'detected_emotions': [],
                'crisis_flag': False,
                'crisis_keywords': []
            }

        txt = text.lower()
        words = txt.split()
        pos = sum(1 for w in words if w.strip(".,!?\"')(") in self.positive_words)
        neg = sum(1 for w in words if w.strip(".,!?\"')(") in self.negative_words)

        # Basic scoring
        total = max(1, pos + neg)
        pos_score = pos / total
        neg_score = neg / total
        neu_score = max(0.0, 1.0 - (pos_score + neg_score))

        if pos > neg:
            label = 'positive'
        elif neg > pos:
            label = 'negative'
        else:
            label = 'neutral'

        detected = []
        for w in list(self.negative_words):
            if w in txt:
                detected.append(w)
        for w in list(self.positive_words):
            if w in txt and w not in detected:
                detected.append(w)

        crisis_found = [k for k in self.crisis_keywords if k in txt]

        result = {
            'sentiment_label': label,
            'sentiment_scores': {
                'negative': round(neg_score, 3),
                'neutral': round(neu_score, 3),
                'positive': round(pos_score, 3)
            },
            'detected_emotions': detected[:5],
            'crisis_flag': len(crisis_found) > 0,
            'crisis_keywords': crisis_found
        }

        if result['crisis_flag']:
            logger.warning(f"Crisis keywords detected: {crisis_found}")

        return result

    def analyze_sentiment_trend(self, sentiments: List[Dict]) -> Dict:
        if not sentiments:
            return {'trend': 'neutral', 'average_negative_score': 0.0, 'consecutive_negative': 0, 'risk_level': 'low'}

        negative_count = sum(1 for s in sentiments if s.get('sentiment_label') == 'negative')
        positive_count = sum(1 for s in sentiments if s.get('sentiment_label') == 'positive')

        consecutive_negative = 0
        current = 0
        for s in reversed(sentiments):
            if s.get('sentiment_label') == 'negative':
                current += 1
                consecutive_negative = max(consecutive_negative, current)
            else:
                current = 0

        if negative_count > len(sentiments) * 0.6:
            trend = 'declining'
        elif positive_count > len(sentiments) * 0.6:
            trend = 'improving'
        else:
            trend = 'stable'

        risk = 'low'
        if consecutive_negative >= 5 or negative_count > len(sentiments) * 0.8:
            risk = 'high'
        elif consecutive_negative >= 3 or negative_count > len(sentiments) * 0.6:
            risk = 'medium'

        avg_neg = sum(s.get('sentiment_scores', {}).get('negative', 0) for s in sentiments) / len(sentiments)

        return {
            'trend': trend,
            'average_negative_score': avg_neg,
            'consecutive_negative': consecutive_negative,
            'risk_level': risk,
            'total_entries': len(sentiments),
            'negative_count': negative_count,
            'positive_count': positive_count
        }


# Singleton instance
_sentiment_analyzer = None

def get_sentiment_analyzer() -> SentimentAnalyzer:
    global _sentiment_analyzer
    if _sentiment_analyzer is None:
        _sentiment_analyzer = SentimentAnalyzer()
    return _sentiment_analyzer
