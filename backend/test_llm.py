#!/usr/bin/env python3
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.services.llm_service import init_llm_service

def test_llm():
    print("Testing LLM service initialization...")

    try:
        llm_service = init_llm_service()

        # Detect which LLM backend is in use
        if hasattr(llm_service, "model_path"):
            print(f"✅ Local Blenderbot model detected: {llm_service.model_path}")
        elif hasattr(llm_service, "client"):
            print("⚡ Using Groq Cloud LLM backend")
        else:
            print("⚠️ Unknown backend, continuing anyway...")

        print("✓ LLM service initialized successfully")

        # Test a simple message
        messages = [{"role": "user", "content": "Hello, how are you?"}]
        print("Testing response generation...")
        response = llm_service.generate_response(messages)

        if response and isinstance(response, str):
            print(f"✓ Response generated: {response[:100]}...")
            print("✓ All tests passed!")
            return True
        else:
            print("✗ No valid response returned")
            return False

    except Exception as e:
        print(f"✗ Error: {e}")
        return False


if __name__ == "__main__":
    test_llm()
