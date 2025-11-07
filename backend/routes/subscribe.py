from flask import Blueprint, request, jsonify
from datetime import datetime
import uuid
import asyncio
from backend.models import SubscribeRequest, SubscribeResponse
from backend.services.mongo import MongoService
from backend.services.flutterwave import FlutterwaveService
import logging

logger = logging.getLogger(__name__)

subscribe_bp = Blueprint('subscribe', __name__)

def init_services():
    """Initialize services with config."""
    from flask import current_app
    config = current_app.config
    mongo_service = MongoService(config['MONGO_URI'], config['MONGODB_DB_NAME'])
    flutterwave_service = FlutterwaveService(
        config['FLW_SECRET_KEY'],
        config.get('FLW_SIGNATURE_KEY')
    )
    return mongo_service, flutterwave_service

@subscribe_bp.route('/subscribe', methods=['POST'])
def subscribe():
    """Creates a Flutterwave payment link and pending subscription."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400

        # Validate request data
        subscribe_req = SubscribeRequest(**data)

        mongo_service, flutterwave_service = init_services()

        # Generate unique tx_ref
        tx_ref = f"mindbuddy-{uuid.uuid4().hex[:16]}-{int(datetime.utcnow().timestamp())}"

        # Create payment link asynchronously
        from flask import current_app
        redirect_url = current_app.config.get('REDIRECT_URL') or (request.root_url.rstrip('/') + "/payment/callback")
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        payment_link = loop.run_until_complete(
            flutterwave_service.create_payment_link(
                amount=subscribe_req.amount,
                currency=subscribe_req.currency,
                tx_ref=tx_ref,
                email=subscribe_req.email,
                name=subscribe_req.name,
                redirect_url=redirect_url
            )
        )
        loop.close()

        if not payment_link:
            return jsonify({"error": "Failed to create payment link"}), 500

        # Create subscription document
        subscription_doc = {
            "user_id": subscribe_req.user_id,
            "email": subscribe_req.email,
            "plan_name": subscribe_req.plan_name,
            "plan_amount": subscribe_req.amount,
            "payment_ref": tx_ref,
            "status": "pending",
            "created_at": datetime.utcnow()
        }

        if not mongo_service.create_subscription(subscription_doc):
            return jsonify({"error": "Failed to create subscription"}), 500

        response = SubscribeResponse(
            payment_link=payment_link,
            tx_ref=tx_ref,
            status="pending"
        )

        return jsonify(response.dict()), 200

    except Exception as e:
        logger.error(f"Subscribe endpoint error: {e}")
        return jsonify({"error": "Internal server error"}), 500
