"""
Sentiment Analysis Service
Uses Hugging Face transformers for sentiment analysis on journal entries.
Model: cardiffnlp/twitter-roberta-base-sentiment-latest (free, no API key needed)
"""

import logging
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
from typing import Dict, List, Tuple
import re

logger = logging.getLogger(__name__)

class SentimentAnalyzer:
    """
    Sentiment analyzer using pre-trained RoBERTa model.
    Analyzes text sentiment and detects crisis keywords.
    """
    
    def __init__(self):
        self.model_name = "cardiffnlp/twitter-roberta-base-sentiment-latest"
        self.tokenizer = None
        self.model = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
        # Crisis keywords for detection
        self.crisis_keywords = [
            'suicide', 'suicidal', 'kill myself', 'end it all', 'no reason to live',
            'want to die', 'better off dead', 'hopeless', 'can\'t go on',
            'self harm', 'hurt myself', 'cut myself', 'overdose', 'give up'
        ]
        
        # Negative emotion indicators
        self.negative_emotions = [
            'depressed', 'depression', 'anxious', 'anxiety', 'scared', 'fear',
            'sad', 'lonely', 'isolated', 'worthless', 'helpless', 'desperate'
        ]
        
        logger.info(f"SentimentAnalyzer initialized. Using device: {self.device}")
    
    def load_model(self):
        """Lazy load the model to save memory"""
        if self.model is None:
            try:
                logger.info(f"Loading sentiment model: {self.model_name}")
                self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
                self.model = AutoModelForSequenceClassification.from_pretrained(self.model_name)
                self.model.to(self.device)
                self.model.eval()
                logger.info("Sentiment model loaded successfully")
            except Exception as e:
                logger.error(f"Error loading sentiment model: {e}")
                raise
    
    def analyze_sentiment(self, text: str) -> Dict:
        """
        Analyze sentiment of text.
        
        Args:
            text: Text to analyze
            
        Returns:
            Dict with sentiment_label, sentiment_scores, detected_emotions, crisis_flag
        """
        if not text or len(text.strip()) < 3:
            return {
                'sentiment_label': 'neutral',
                'sentiment_scores': {'negative': 0.33, 'neutral': 0.34, 'positive': 0.33},
                'detected_emotions': [],
                'crisis_flag': False,
                'crisis_keywords': []
            }
        
        # Load model if not already loaded
        self.load_model()
        
        try:
            # Tokenize and get predictions
            inputs = self.tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            with torch.no_grad():
                outputs = self.model(**inputs)
                scores = torch.nn.functional.softmax(outputs.logits, dim=-1)
            
            # Get scores (model outputs: negative, neutral, positive)
            scores_dict = {
                'negative': float(scores[0][0]),
                'neutral': float(scores[0][1]),
                'positive': float(scores[0][2])
            }
            
            # Determine primary sentiment
            sentiment_label = max(scores_dict, key=scores_dict.get)
            
            # Detect emotions and crisis keywords
            detected_emotions = self._detect_emotions(text)
            crisis_flag, crisis_keywords_found = self._detect_crisis(text)
            
            result = {
                'sentiment_label': sentiment_label,
                'sentiment_scores': scores_dict,
                'detected_emotions': detected_emotions,
                'crisis_flag': crisis_flag,
                'crisis_keywords': crisis_keywords_found
            }
            
            logger.debug(f"Sentiment analysis result: {sentiment_label} (confidence: {scores_dict[sentiment_label]:.2f})")
            
            return result
            
        except Exception as e:
            logger.error(f"Error during sentiment analysis: {e}")
            # Return neutral sentiment on error
            return {
                'sentiment_label': 'neutral',
                'sentiment_scores': {'negative': 0.33, 'neutral': 0.34, 'positive': 0.33},
                'detected_emotions': [],
                'crisis_flag': False,
                'crisis_keywords': []
            }
    
    def _detect_emotions(self, text: str) -> List[str]:
        """Detect emotional keywords in text"""
        text_lower = text.lower()
        detected = []
        
        # Check for negative emotions
        for emotion in self.negative_emotions:
            if emotion in text_lower:
                detected.append(emotion)
        
        return detected[:5]  # Limit to top 5
    
    def _detect_crisis(self, text: str) -> Tuple[bool, List[str]]:
        """
        Detect crisis keywords indicating potential self-harm or suicide risk.
        
        Returns:
            Tuple of (crisis_flag, list of matched keywords)
        """
        text_lower = text.lower()
        found_keywords = []
        
        for keyword in self.crisis_keywords:
            if keyword in text_lower:
                found_keywords.append(keyword)
        
        crisis_flag = len(found_keywords) > 0
        
        if crisis_flag:
            logger.warning(f"Crisis keywords detected: {found_keywords}")
        
        return crisis_flag, found_keywords
    
    def analyze_sentiment_trend(self, sentiments: List[Dict]) -> Dict:
        """
        Analyze trend from multiple sentiment results.
        
        Args:
            sentiments: List of sentiment analysis results
            
        Returns:
            Dict with trend analysis
        """
        if not sentiments:
            return {
                'trend': 'neutral',
                'average_score': 0.0,
                'consecutive_negative': 0,
                'risk_level': 'low'
            }
        
        # Calculate averages
        negative_count = sum(1 for s in sentiments if s.get('sentiment_label') == 'negative')
        positive_count = sum(1 for s in sentiments if s.get('sentiment_label') == 'positive')
        
        # Calculate consecutive negative entries
        consecutive_negative = 0
        current_streak = 0
        for s in reversed(sentiments):
            if s.get('sentiment_label') == 'negative':
                current_streak += 1
                consecutive_negative = max(consecutive_negative, current_streak)
            else:
                current_streak = 0
        
        # Determine trend
        if negative_count > len(sentiments) * 0.6:
            trend = 'declining'
        elif positive_count > len(sentiments) * 0.6:
            trend = 'improving'
        else:
            trend = 'stable'
        
        # Calculate risk level
        risk_level = 'low'
        if consecutive_negative >= 5 or negative_count > len(sentiments) * 0.8:
            risk_level = 'high'
        elif consecutive_negative >= 3 or negative_count > len(sentiments) * 0.6:
            risk_level = 'medium'
        
        # Average negative sentiment score
        avg_negative_score = 0.0
        if sentiments:
            avg_negative_score = sum(
                s.get('sentiment_scores', {}).get('negative', 0) 
                for s in sentiments
            ) / len(sentiments)
        
        return {
            'trend': trend,
            'average_negative_score': avg_negative_score,
            'consecutive_negative': consecutive_negative,
            'risk_level': risk_level,
            'total_entries': len(sentiments),
            'negative_count': negative_count,
            'positive_count': positive_count
        }


# Singleton instance
_sentiment_analyzer = None

def get_sentiment_analyzer() -> SentimentAnalyzer:
    """Get or create the global sentiment analyzer instance"""
    global _sentiment_analyzer
    if _sentiment_analyzer is None:
        _sentiment_analyzer = SentimentAnalyzer()
    return _sentiment_analyzer
