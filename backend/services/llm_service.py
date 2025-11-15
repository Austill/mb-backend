#!/usr/bin/env python3
"""
Groq-only LLM Service for Sereni mental wellness chatbot.
Uses Groq API exclusively for all AI-powered chat and insights functionality.
"""

import os
import logging
from groq import Groq


class LLMService:
    def __init__(self):
        """Initialize Groq-only LLM service."""
        self.groq_key = os.getenv("GROQ_API_KEY")
        if not self.groq_key:
            raise ValueError("GROQ_API_KEY environment variable is not set")
        
        self.client = Groq(api_key=self.groq_key)
        
        # === Short-term memory for Sereni ===
        self.chat_history = []
        self.last_intent = None

        # === Sereni system personality prompt ===
        self.SERENI_SYSTEM_PROMPT = (
            "You are Sereni — a calm, kind, emotionally intelligent mental wellness companion. "
            "You speak naturally, like a caring friend who truly listens. "
            "Always show empathy, understanding, and warmth. "
            "You help users reflect, ground themselves, and find calm without sounding robotic or overbearing. "
            "Avoid medical advice. Focus on comfort, perspective, and emotional clarity. "
            "Use soft, human-like tone and short, mindful sentences."
        )

        # Generation parameters
        self.MAX_NEW_TOKENS = 512
        self.TEMPERATURE = 0.7
        self.TOP_P = 0.9
        self.MODEL = "llama-3.1-8b-instant"

    # =====================================================
    # === RESPONSE GENERATION WITH MEMORY & INTENT ===
    # =====================================================
    def generate_response(self, messages, purpose="chat"):
        """
        Generates a response using Groq API.
        Adds memory context, intent detection, and greeting handling.
        messages: [{"role": "user", "content": "text"}]
        """
        # Safety checks
        if not hasattr(self, "chat_history"):
            self.chat_history = []
        if not hasattr(self, "last_intent"):
            self.last_intent = None
        if not messages or "content" not in messages[-1]:
            return "[Invalid input — expected a list of chat messages.]"

        user_message = messages[-1]["content"].strip()
        self.chat_history.append(user_message)
        # Keep last 10 messages
        self.chat_history = self.chat_history[-10:]

        user_lower = user_message.lower()

        # ===== Intent detection =====
        # Greeting intent
        if user_lower in ["hi", "hello", "hey", "yo", "sup", "hiya", "hi there"]:
            if self.last_intent == "greeting":
                self.last_intent = "followup"
                return "Hey again 😊 How've you been holding up since we last chatted?"
            else:
                self.last_intent = "greeting"
                return "Hey there 👋 It's really good to see you. How are you feeling today?"

        # Fatigue intent
        if any(word in user_lower for word in ["tired", "exhausted", "fatigued", "burnt out", "drained"]):
            self.last_intent = "fatigue"
            return (
                "I hear you — exhaustion can really take a toll, both mentally and physically. "
                "Do you want to talk about what's been wearing you down lately, or would you prefer "
                "some quick ways to recharge right now?"
            )

        # Sadness intent
        if any(word in user_lower for word in ["sad", "down", "depressed", "hopeless", "lonely"]):
            self.last_intent = "sadness"
            return (
                "That sounds really heavy 💭 — thank you for opening up about it. "
                "Would you like to talk about what's been making you feel this way, or would you prefer "
                "some gentle mood-lifting activities?"
            )

        # Anger intent
        if any(word in user_lower for word in ["angry", "mad", "furious", "irritated", "upset"]):
            self.last_intent = "anger"
            return (
                "Anger's totally valid — it's your mind's way of saying something's not right. "
                "Do you want to unpack what triggered it, or should I walk you through a grounding technique first?"
            )

        # Default fallback
        self.last_intent = "chat"
        context_prompt = "\n".join(self.chat_history[-6:])
        user_input = f"Conversation so far:\n{context_prompt}\n\nUser: {user_message}\nSereni:"

        # ===== Call Groq API =====
        try:
            completion = self.client.chat.completions.create(
                model=self.MODEL,
                messages=[
                    {"role": "system", "content": self.SERENI_SYSTEM_PROMPT},
                    {"role": "user", "content": user_input}
                ],
                temperature=self.TEMPERATURE,
                max_tokens=self.MAX_NEW_TOKENS,
                top_p=self.TOP_P,
                stream=False,
            )
            response = completion.choices[0].message.content.strip()
            if response:
                self.chat_history.append(response)
                return response
            return "[Empty response from Groq model.]"
        except Exception as e:
            raise RuntimeError(f"Groq API error: {e}")

    def generate_streaming_response(self, messages):
        """
        Generates a streaming response using Groq API.
        Yields chunks of the response for real-time updates.
        """
        if not messages or "content" not in messages[-1]:
            yield "[Invalid input — expected a list of chat messages.]"
            return

        user_message = messages[-1]["content"].strip()
        self.chat_history.append(user_message)
        self.chat_history = self.chat_history[-10:]

        context_prompt = "\n".join(self.chat_history[-6:])
        user_input = f"Conversation so far:\n{context_prompt}\n\nUser: {user_message}\nSereni:"

        try:
            with self.client.chat.completions.create(
                model=self.MODEL,
                messages=[
                    {"role": "system", "content": self.SERENI_SYSTEM_PROMPT},
                    {"role": "user", "content": user_input}
                ],
                temperature=self.TEMPERATURE,
                max_tokens=self.MAX_NEW_TOKENS,
                top_p=self.TOP_P,
                stream=True,
            ) as stream:
                full_response = ""
                for text in stream.text_stream:
                    full_response += text
                    yield text
                self.chat_history.append(full_response)
        except Exception as e:
            yield f"[Groq streaming error: {e}]"


# === GLOBAL SINGLETON ACCESS ===
_llm_service = None

def get_llm_service():
    """Lazy initializer for shared LLMService instance."""
    global _llm_service
    if _llm_service is None:
        try:
            _llm_service = LLMService()
        except Exception as e:
            # Fail gracefully: log a helpful error and return None so callers
            # can respond with a 503 (service unavailable) instead of crashing
            logging.getLogger("backend.llm_service").error(
                "Failed to initialize LLMService: %s", e, exc_info=True
            )
            _llm_service = None
    return _llm_service


def init_llm_service():
    """Manual initializer (mainly for testing)."""
    return LLMService()
