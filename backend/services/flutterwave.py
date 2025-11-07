import httpx
import hashlib
import hmac
import json
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

class FlutterwaveService:
    BASE_URL = "https://api.flutterwave.com/v3"

    def __init__(self, secret_key: str, signature_key: Optional[str] = None):
        self.secret_key = secret_key
        self.signature_key = signature_key

    async def create_payment_link(
        self,
        amount: int,
        currency: str,
        tx_ref: str,
        email: str,
        name: str,
        redirect_url: str
    ) -> Optional[str]:
        """Creates a payment link using Flutterwave API."""
        payload = {
            "tx_ref": tx_ref,
            "amount": amount,
            "currency": currency,
            "redirect_url": redirect_url,
            "customer": {
                "email": email,
                "name": name
            },
            "customizations": {
                "title": "Mind Buddy Subscription",
                "description": "Premium subscription payment"
            }
        }

        headers = {
            "Authorization": f"Bearer {self.secret_key}",
            "Content-Type": "application/json"
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.BASE_URL}/payments",
                    json=payload,
                    headers=headers
                )
                response.raise_for_status()
                data = response.json()
                return data.get("data", {}).get("link")
            except httpx.HTTPStatusError as e:
                logger.error(f"Flutterwave API error: {e.response.status_code} - {e.response.text}")
                return None
            except Exception as e:
                logger.error(f"Failed to create payment link: {e}")
                return None

    def validate_webhook_signature(self, request_headers: Dict[str, Any], raw_body: bytes) -> bool:
        """Validates the webhook signature using Flutterwave's signature key."""
        if not self.signature_key:
            logger.warning("FLW_SIGNATURE_KEY not set, skipping signature validation")
            return True

        signature = request_headers.get("verif-hash")
        if not signature:
            logger.error("Missing verif-hash header in webhook")
            return False

        expected_signature = hmac.new(
            self.signature_key.encode(),
            raw_body,
            hashlib.sha256
        ).hexdigest()

        return hmac.compare_digest(signature, expected_signature)
