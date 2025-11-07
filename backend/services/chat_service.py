"""
Chat Service - Conversational AI Assistant (Sereni)
Uses Hugging Face Inference API with free open-source models.
No API key required for public models.
"""

import logging
import requests
from typing import Dict, List, Optional
import time

logger = logging.getLogger(__name__)

class ChatBot:
    """
    Conversational AI chatbot using Hugging Face models.
    Uses free inference API - no authentication required for public models.
    """
    
    def __init__(self):
        # Using free Hugging Face Inference API
        self.api_url = "https://api-inference.huggingface.co/models"
        
        # Model options (all free, no API key needed):
        # 1. facebook/blenderbot-400M-distill - conversational, lightweight
        # 2. microsoft/DialoGPT-medium - dialogue generation
        # 3. google/flan-t5-base - instruction-following
        self.model_name = "facebook/blenderbot-400M-distill"
        self.model_url = f"{self.api_url}/{self.model_name}"
        
        # System prompt for mental wellness context
        self.system_context = (
            "You are Sereni, a compassionate mental wellness assistant. "
            "You provide supportive, empathetic responses to help users with their emotional well-being. "
            "You listen without judgment, offer gentle guidance, and encourage healthy coping strategies. "
            "If someone is in crisis, you remind them to seek professional help immediately."
        )
        
        # Crisis response template
        self.crisis_response = (
            "I'm really concerned about what you're sharing. Please know that you're not alone, "
            "and there are people who want to help. I strongly encourage you to:\n\n"
            "🆘 **Immediate Help:**\n"
            "- Call the National Suicide Prevention Lifeline: 988 (US)\n"
            "- Text 'HELLO' to 741741 (Crisis Text Line)\n"
            "- Call emergency services: 911\n\n"
            "Your life matters, and professional support is available 24/7. "
            "Would you like me to help you find local mental health resources?"
        )
        
        logger.info(f"ChatBot initialized with model: {self.model_name}")
    
    def generate_response(self, message: str, conversation_context: List[Dict] = None,
                         user_sentiment: str = None) -> Dict:
        """
        Generate a response to user message.
        
        Args:
            message: User's message
            conversation_context: Previous messages in conversation
            user_sentiment: Detected sentiment of the message
            
        Returns:
            Dict with response text and metadata
        """
        try:
            # Check for crisis keywords first
            if self._is_crisis_message(message):
                return {
                    'response': self.crisis_response,
                    'source': 'crisis_protocol',
                    'requires_professional_help': True
                }
            
            # Build context-aware prompt
            prompt = self._build_prompt(message, conversation_context, user_sentiment)
            
            # Call Hugging Face Inference API
            response = self._call_inference_api(prompt)
            
            if response:
                return {
                    'response': response,
                    'source': 'ai_model',
                    'requires_professional_help': False
                }
            else:
                # Fallback response if API fails
                return self._get_fallback_response(user_sentiment)
                
        except Exception as e:
            logger.error(f"Error generating chat response: {e}")
            return self._get_fallback_response(user_sentiment)
    
    def _call_inference_api(self, prompt: str, max_retries: int = 2) -> Optional[str]:
        """
        Call Hugging Face Inference API.
        The API is free but may have rate limits or loading times.
        """
        headers = {"Content-Type": "application/json"}
        payload = {
            "inputs": prompt,
            "parameters": {
                "max_length": 200,
                "temperature": 0.7,
                "top_p": 0.9,
                "do_sample": True
            }
        }
        
        for attempt in range(max_retries):
            try:
                response = requests.post(
                    self.model_url,
                    headers=headers,
                    json=payload,
                    timeout=30
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    # Handle different response formats
                    if isinstance(result, list) and len(result) > 0:
                        if 'generated_text' in result[0]:
                            return result[0]['generated_text'].strip()
                        elif 'translation_text' in result[0]:
                            return result[0]['translation_text'].strip()
                    elif isinstance(result, dict):
                        if 'generated_text' in result:
                            return result['generated_text'].strip()
                    
                    logger.warning(f"Unexpected API response format: {result}")
                    return None
                    
                elif response.status_code == 503:
                    # Model is loading, wait and retry
                    logger.info(f"Model loading, waiting... (attempt {attempt + 1})")
                    time.sleep(5)
                    continue
                else:
                    logger.error(f"API error {response.status_code}: {response.text}")
                    return None
                    
            except requests.exceptions.Timeout:
                logger.warning(f"API timeout (attempt {attempt + 1})")
                if attempt < max_retries - 1:
                    time.sleep(2)
                    continue
                return None
            except Exception as e:
                logger.error(f"Error calling inference API: {e}")
                return None
        
        return None
    
    def _build_prompt(self, message: str, context: List[Dict] = None,
                     sentiment: str = None) -> str:
        """Build a context-aware prompt for the model"""
        prompt_parts = [self.system_context]
        
        # Add conversation context if available
        if context and len(context) > 0:
            prompt_parts.append("\nRecent conversation:")
            for msg in context[-3:]:  # Last 3 messages for context
                role = msg.get('role', 'user')
                content = msg.get('content', '')
                if role == 'user':
                    prompt_parts.append(f"User: {content}")
                else:
                    prompt_parts.append(f"Sereni: {content}")
        
        # Add sentiment context if available
        if sentiment:
            if sentiment == 'negative':
                prompt_parts.append("\n(User seems to be feeling down. Be extra supportive.)")
            elif sentiment == 'positive':
                prompt_parts.append("\n(User seems to be feeling good. Encourage this positivity.)")
        
        # Add current message
        prompt_parts.append(f"\nUser: {message}")
        prompt_parts.append("\nSereni:")
        
        return "\n".join(prompt_parts)
    
    def _is_crisis_message(self, message: str) -> bool:
        """Check if message contains crisis indicators"""
        crisis_keywords = [
            'suicide', 'suicidal', 'kill myself', 'end it all',
            'want to die', 'better off dead', 'no reason to live',
            'self harm', 'hurt myself', 'overdose'
        ]
        message_lower = message.lower()
        return any(keyword in message_lower for keyword in crisis_keywords)
    
    def _get_fallback_response(self, sentiment: str = None) -> Dict:
        """
        Provide a fallback response when AI model is unavailable.
        Uses rule-based responses based on sentiment.
        """
        responses = {
            'negative': (
                "I hear that you're going through a difficult time. "
                "Your feelings are valid, and it's okay to not be okay. "
                "Remember that challenging moments are temporary, and you have the strength to get through this. "
                "Have you tried any relaxation techniques like deep breathing or meditation? "
                "I'm here to listen if you'd like to share more."
            ),
            'positive': (
                "I'm so glad to hear you're feeling good! "
                "It's wonderful to see you in a positive space. "
                "Keep nurturing this feeling - maybe through gratitude journaling or spending time on activities you enjoy. "
                "What's been bringing you joy lately?"
            ),
            'neutral': (
                "Thank you for sharing with me. I'm here to support you on your mental wellness journey. "
                "Whether you'd like to talk about your day, explore your feelings, or get suggestions for self-care, "
                "I'm here to help. What would you like to discuss?"
            )
        }
        
        response_text = responses.get(sentiment, responses['neutral'])
        
        return {
            'response': response_text,
            'source': 'fallback',
            'requires_professional_help': False
        }
    
    def get_supportive_message(self, sentiment_trend: Dict) -> str:
        """
        Generate a supportive message based on sentiment trends.
        Used for proactive check-ins.
        """
        risk_level = sentiment_trend.get('risk_level', 'low')
        trend = sentiment_trend.get('trend', 'stable')
        consecutive_negative = sentiment_trend.get('consecutive_negative', 0)
        
        if risk_level == 'high':
            return (
                "I've noticed you've been having some challenging days lately. "
                "I want you to know that I'm here for you, and your well-being matters. "
                "Sometimes talking to a professional can really help - would you like some resources? "
                "In the meantime, have you tried any calming activities today?"
            )
        elif risk_level == 'medium':
            return (
                "I've noticed things might be a bit tough for you right now. "
                "Remember that it's okay to have difficult days, and you're doing the best you can. "
                "Would you like to try a short breathing exercise or meditation? "
                "I'm here if you need someone to talk to."
            )
        elif trend == 'improving':
            return (
                "I've noticed some positive changes in your recent entries! "
                "It's wonderful to see you making progress. Keep up the great work! "
                "What strategies have been helping you feel better?"
            )
        else:
            return (
                "How are you feeling today? I'm here to support you on your wellness journey. "
                "Whether you want to chat, journal, or try some calming exercises, I'm here to help."
            )


# Singleton instance
_chatbot = None

def get_chatbot() -> ChatBot:
    """Get or create the global chatbot instance"""
    global _chatbot
    if _chatbot is None:
        _chatbot = ChatBot()
    return _chatbot
