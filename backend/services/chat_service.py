"""
Chat Service (Groq-backed)
Replaced Hugging Face inference usage with Groq API calls so the project relies on Groq
for chatbot generation. Keeps similar interface (get_chatbot / generate_response).
"""

import os
import logging
from typing import Dict, List, Optional

from groq import Groq

logger = logging.getLogger(__name__)


class ChatBot:
    """Conversational chatbot using Groq Cloud LLM."""

    def __init__(self):
        key = os.getenv("GROQ_API_KEY")
        if not key:
            raise ValueError("GROQ_API_KEY environment variable is required for chat service")
        self.client = Groq(api_key=key)
        self.model = os.getenv("GROQ_CHAT_MODEL", "llama-3.1-8b-instant")

        self.system_context = (
            "You are Sereni, a compassionate mental wellness assistant. "
            "You provide supportive, empathetic responses to help users with their emotional well-being. "
            "You listen without judgment, offer gentle guidance, and encourage healthy coping strategies. "
            "If someone is in crisis, you remind them to seek professional help immediately."
        )

        self.crisis_response = (
            "I'm really concerned about what you're sharing. Please know that you're not alone, "
            "and there are people who want to help. I strongly encourage you to seek immediate help if you're in danger."
        )

        logger.info(f"ChatBot initialized using Groq model: {self.model}")

    def generate_response(self, message: str, conversation_context: List[Dict] = None,
                         user_sentiment: str = None) -> Dict:
        try:
            if self._is_crisis_message(message):
                return {
                    'response': self.crisis_response,
                    'source': 'crisis_protocol',
                    'requires_professional_help': True
                }

            prompt_parts = [self.system_context]
            if conversation_context:
                prompt_parts.append("\nRecent conversation:")
                for msg in conversation_context[-3:]:
                    role = msg.get('role', 'user')
                    content = msg.get('content', '')
                    if role == 'user':
                        prompt_parts.append(f"User: {content}")
                    else:
                        prompt_parts.append(f"Sereni: {content}")

            if user_sentiment == 'negative':
                prompt_parts.append("\n(User seems to be feeling down. Be extra supportive.)")
            elif user_sentiment == 'positive':
                prompt_parts.append("\n(User seems to be feeling good. Encourage this positivity.)")

            prompt_parts.append(f"\nUser: {message}")
            prompt_parts.append("\nSereni:")
            prompt = "\n".join(prompt_parts)

            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_context},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=256,
                top_p=0.9,
                stream=False,
            )

            response = completion.choices[0].message.content.strip()
            return {
                'response': response,
                'source': 'ai_model',
                'requires_professional_help': False
            }

        except Exception as e:
            logger.error(f"Chat generation error (Groq): {e}")
            # fallback
            return {
                'response': (
                    "Thanks for sharing — I'm here to listen. Can you tell me a little more?"
                ),
                'source': 'fallback',
                'requires_professional_help': False
            }

    def _is_crisis_message(self, message: str) -> bool:
        crisis_keywords = [
            'suicide', 'suicidal', 'kill myself', 'end it all',
            'want to die', 'better off dead', 'no reason to live',
            'self harm', 'hurt myself', 'overdose'
        ]
        lower = message.lower()
        return any(k in lower for k in crisis_keywords)


# Singleton
_chatbot = None

def get_chatbot() -> ChatBot:
    global _chatbot
    if _chatbot is None:
        _chatbot = ChatBot()
    return _chatbot
