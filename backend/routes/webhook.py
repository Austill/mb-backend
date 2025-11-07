from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
import json
from backend.services.mongo import MongoService
from backend.services.flutterwave import FlutterwaveService
import logging

logger = logging.getLogger(__name__)

webhook_bp = Blueprint('webhook', __name__)

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

@webhook_bp.route('/webhook', methods=['POST'])
def webhook():
    """Handles Flutterwave webhook events."""
    try:
        # Get raw body for signature validation
        raw_body = request.get_data()

        mongo_service, flutterwave_service = init_services()

        # Validate signature if signature key is set
        if not flutterwave_service.validate_webhook_signature(dict(request.headers), raw_body):
            logger.warning("Invalid webhook signature")
            return jsonify({"error": "Invalid signature"}), 401

        # Parse webhook data
        try:
            webhook_data = json.loads(raw_body.decode('utf-8'))
        except json.JSONDecodeError:
            logger.error("Invalid JSON in webhook")
            return jsonify({"error": "Invalid JSON"}), 400

        # Extract transaction reference
        event_data = webhook_data.get("data", {})
        tx_ref = event_data.get("tx_ref")

        if not tx_ref:
            logger.warning("No tx_ref in webhook data")
            return jsonify({"status": "ok"}), 200  # Return 200 to avoid retry storm

        # Find subscription
        subscription = mongo_service.get_subscription_by_payment_ref(tx_ref)
        if not subscription:
            logger.warning(f"Subscription not found for tx_ref: {tx_ref}")
            return jsonify({"status": "ok"}), 200

        # Check if already active (idempotency)
        if subscription.get("status") == "active":
            logger.info(f"Subscription already active for tx_ref: {tx_ref}")
            return jsonify({"status": "ok"}), 200

        # Check if payment was successful
        event_type = webhook_data.get("event")
        if event_type != "charge.completed" or event_data.get("status") != "successful":
            logger.info(f"Payment not successful for tx_ref: {tx_ref}, event: {event_type}")
            return jsonify({"status": "ok"}), 200

        # Activate subscription
        renewal_date = datetime.utcnow() + timedelta(days=30)
        if not mongo_service.activate_subscription(subscription["_id"], renewal_date):
            logger.error(f"Failed to activate subscription for tx_ref: {tx_ref}")
            return jsonify({"error": "Failed to activate subscription"}), 500

        # Update user record
        user_data = {
            "subscription_status": "active",
            "plan_id": subscription["plan_name"],
            "renewal_date": renewal_date
        }
        mongo_service.update_user_subscription(subscription["user_id"], user_data)

        logger.info(f"Successfully activated subscription for user {subscription['user_id']}")
        return jsonify({"status": "ok"}), 200

    except Exception as e:
        logger.error(f"Webhook processing error: {e}")
        return jsonify({"error": "Internal server error"}), 500
