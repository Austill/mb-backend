#!/usr/bin/env python3
import os
import logging
import torch
from transformers import BlenderbotTokenizer, BlenderbotForConditionalGeneration

# Optional Groq integration
try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False

logger = logging.getLogger(__name__)


class LLMService:
    def __init__(self, model_path=None, lazy_load=True):
        self.groq_key = os.getenv("GROQ_API_KEY")
        self.use_groq = False
        self.client = None
        self.model = None
        self.tokenizer = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"

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

        # Always prepare a local fallback
        self.model_path = model_path or os.path.expanduser(
            "~/.cache/huggingface/hub/models--facebook--blenderbot-400M-distill"
        )
        # === Try Groq first ===
        if GROQ_AVAILABLE and self.groq_key:
            try:
                self.client = Groq(api_key=self.groq_key)
                self.use_groq = True
                logger.info("Using Groq Cloud LLM backend")
            except Exception as e:
                logger.exception("Failed to init Groq client; falling back to local: %s", e)

        # === Local model fallback ===
        # Optionally defer loading of the heavy local model until first request
        self._loading = False
        self._lazy_load = lazy_load
        if not self.use_groq and not self._lazy_load:
            self._load_local_model()

        # Generation parameters
        self.MAX_NEW_TOKENS = 150
        self.TEMPERATURE = 0.7
        self.TOP_P = 0.9

    # =====================================================
    # === LOCAL MODEL HANDLING ===
    # =====================================================
    def _load_local_model(self):
        """Load Blenderbot model as local fallback."""
        try:
            logger.info("Loading local Blenderbot model from: %s", self.model_path)
            self.tokenizer = BlenderbotTokenizer.from_pretrained(self.model_path)
            self.model = BlenderbotForConditionalGeneration.from_pretrained(self.model_path)
            self.model.to(self.device)
            logger.info("Local model ready on %s", self.device.upper())
        except Exception as e:
            logger.exception("Failed to load local Blenderbot: %s", e)
            self.model, self.tokenizer = None, None

    # =====================================================
    # === RESPONSE GENERATION WITH MEMORY & INTENT ===
    # =====================================================
    def generate_response(self, messages, purpose="chat"):
        """
        Generates a response using Groq Cloud or local Blenderbot fallback.
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
                return "Hey again 😊 How’ve you been holding up since we last chatted?"
            else:
                self.last_intent = "greeting"
                return "Hey there 👋 It’s really good to see you. How are you feeling today?"

        # Fatigue intent
        if any(word in user_lower for word in ["tired", "exhausted", "fatigued", "burnt out", "drained"]):
            self.last_intent = "fatigue"
            return (
                "I hear you — exhaustion can really take a toll, both mentally and physically. "
                "Do you want to talk about what’s been wearing you down lately, or would you prefer "
                "some quick ways to recharge right now?"
            )

        # Sadness intent
        if any(word in user_lower for word in ["sad", "down", "depressed", "hopeless", "lonely"]):
            self.last_intent = "sadness"
            return (
                "That sounds really heavy 💭 — thank you for opening up about it. "
                "Would you like to talk about what’s been making you feel this way, or would you prefer "
                "some gentle mood-lifting activities?"
            )

        # Anger intent
        if any(word in user_lower for word in ["angry", "mad", "furious", "irritated", "upset"]):
            self.last_intent = "anger"
            return (
                "Anger’s totally valid — it’s your mind’s way of saying something’s not right. "
                "Do you want to unpack what triggered it, or should I walk you through a grounding technique first?"
            )

        # Default fallback
        self.last_intent = "chat"
        context_prompt = "\n".join(self.chat_history[-6:])
        user_input = f"Conversation so far:\n{context_prompt}\n\nUser: {user_message}\nSereni:"

        # ===== Try Groq Cloud =====
        if self.use_groq and self.client:
            try:
                completion = self.client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=[
                        {"role": "system", "content": self.SERENI_SYSTEM_PROMPT},
                        {"role": "user", "content": user_input}
                    ],
                    temperature=self.TEMPERATURE,
                    max_tokens=512,
                    top_p=self.TOP_P,
                    stream=False,
                )
                response = completion.choices[0].message.content.strip()
                if response:
                    self.chat_history.append(response)
                    return response
                return "[Empty response from Groq model.]"
            except Exception as e:
                logger.exception("Groq API error; switching to local model: %s", e)

        # ===== Local Blenderbot fallback =====
        # If lazy loading is enabled and model isn't ready, start background load and return a friendly message
        if not self.use_groq and (self.model is None or self.tokenizer is None):
            if self._lazy_load and not self._loading:
                # Start background loader
                import threading

                def _bg_load():
                    try:
                        self._loading = True
                        self._load_local_model()
                    finally:
                        self._loading = False

                threading.Thread(target=_bg_load, daemon=True).start()
                return "[LLM is starting up — please try again in a few seconds.]"

        if self.model and self.tokenizer:
            try:
                inputs = self.tokenizer(user_message, return_tensors="pt").to(self.device)
                with torch.no_grad():
                    outputs = self.model.generate(
                        **inputs,
                        max_new_tokens=self.MAX_NEW_TOKENS,
                        temperature=self.TEMPERATURE,
                        top_p=self.TOP_P,
                        do_sample=True,
                        pad_token_id=self.tokenizer.eos_token_id,
                        eos_token_id=self.tokenizer.eos_token_id,
                    )
                response = self.tokenizer.decode(outputs[0], skip_special_tokens=True).strip()
                self.chat_history.append(response)
                return response
            except Exception as e:
                logger.exception("Local model generation error: %s", e)
                return f"[Local model generation error: {e}]"

        return "[No LLM backend available — verify Groq API key or local model path.]"


# === GLOBAL SINGLETON ACCESS ===
_llm_service = None

def get_llm_service():
    """Lazy initializer for shared LLMService instance."""
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service


def init_llm_service(model_path=None):
    """Manual initializer (mainly for testing)."""
    return LLMService(model_path)
