"""Quick non-blocking test for LLMService.generate_response
This script creates an instance without running the heavy __init__ and verifies
that generate_response returns a predictable fallback when no backend is available.
Run: python -m backend.test_llm_quick
"""
from backend.services.llm_service import LLMService

# Create object without running __init__ to avoid model downloads
svc = object.__new__(LLMService)
# Minimal attributes expected by generate_response
svc.chat_history = []
svc.last_intent = None
svc.SERENI_SYSTEM_PROMPT = "You are Sereni."
svc.use_groq = False
svc.client = None
svc.model = None
svc.tokenizer = None
svc.MAX_NEW_TOKENS = 150
svc.TEMPERATURE = 0.7
svc.TOP_P = 0.9

print("Calling generate_response with no backends...")
resp = LLMService.generate_response(svc, [{"role":"user","content":"Hello"}])
print("Response:", resp)
