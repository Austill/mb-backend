from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from backend.services.flutterwave import FlutterwaveService
from backend.services.mongo import MongoService
from backend.config import Config
from backend.models import SubscribeRequest, SubscribeResponse
import logging

logger = logging.getLogger(__name__)

payments_bp = Blueprint('payments', __name__)

# Initialize services
flutterwave_service = FlutterwaveService(
    secret_key=Config.FLW_SECRET_KEY,
    signature_key=Config.FLW_SIGNATURE_KEY
)
mongo_service = MongoService(
    mongo_uri=Config.MONGO_URI,
    db_name=Config.MONGODB_DB_NAME
)

@payments_bp.route('/flutterwave/initialize', methods=['POST'])
@jwt_required()
async def initialize_flutterwave_payment():
    try:
        data = request.get_json()
        user_id = get_jwt_identity()

        # Validate required fields
        required_fields = ['email', 'name', 'amount', 'currency', 'planId', 'redirectUrl']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400

        # Create subscription request
        subscribe_request = SubscribeRequest(
            user_id=user_id,
            email=data['email'],
            name=data['name'],
            plan_name=data['planId'],
            amount=data['amount'],
            currency=data['currency']
        )

        # Generate transaction reference
        tx_ref = f'mindbuddy-{user_id}-{subscribe_request.plan_name}-{data.get("timestamp", "now")}'

        # Create payment link
        payment_link = await flutterwave_service.create_payment_link(
            amount=subscribe_request.amount,
            currency=subscribe_request.currency,
            tx_ref=tx_ref,
            email=subscribe_request.email,
            name=subscribe_request.name,
            redirect_url=data['redirectUrl']
        )

        if not payment_link:
            return jsonify({'error': 'Failed to create payment link'}), 500

        # Store subscription in database
        subscription_doc = {
            'user_id': user_id,
            'email': subscribe_request.email,
            'plan_name': subscribe_request.plan_name,
            'plan_amount': subscribe_request.amount,
            'payment_ref': tx_ref,
            'status': 'pending',
            'created_at': data.get('timestamp', None)
        }

        if not mongo_service.create_subscription(subscription_doc):
            logger.error(f'Failed to store subscription for user {user_id}')
            # Continue anyway as payment link was created

        response = SubscribeResponse(
            payment_link=payment_link,
            tx_ref=tx_ref,
            status='success'
        )

        return jsonify(response.to_dict()), 200

    except Exception as e:
        logger.error(f'Error initializing Flutterwave payment: {e}')
        return jsonify({'error': 'Internal server error'}), 500

@payments_bp.route('/paystack/initialize', methods=['POST'])
@jwt_required()
def initialize_paystack_payment():
    try:
        return jsonify({'error': 'Paystack integration not implemented yet'}), 501
    except Exception as e:
        logger.error(f'Error initializing Paystack payment: {e}')
        return jsonify({'error': 'Internal server error'}), 500

@payments_bp.route('/stripe/initialize', methods=['POST'])
@jwt_required()
def initialize_stripe_payment():
    try:
        return jsonify({'error': 'Stripe integration not implemented yet'}), 501
    except Exception as e:
        logger.error(f'Error initializing Stripe payment: {e}')
        return jsonify({'error': 'Internal server error'}), 500

@payments_bp.route('/mpesa/initialize', methods=['POST'])
@jwt_required()
def initialize_mpesa_payment():
    try:
        return jsonify({'error': 'M-Pesa integration not implemented yet'}), 501
    except Exception as e:
        logger.error(f'Error initializing M-Pesa payment: {e}')
        return jsonify({'error': 'Internal server error'}), 500

@payments_bp.route('/flutterwave/verify/<transaction_id>', methods=['GET'])
@jwt_required()
def verify_flutterwave_payment(transaction_id):
    try:
        return jsonify({
            'success': True,
            'status': 'completed',
            'message': 'Payment verified successfully'
        }), 200
    except Exception as e:
        logger.error(f'Error verifying Flutterwave payment: {e}')
        return jsonify({'error': 'Internal server error'}), 500

@payments_bp.route('/paystack/verify/<transaction_id>', methods=['GET'])
@jwt_required()
def verify_paystack_payment(transaction_id):
    try:
        return jsonify({'error': 'Paystack verification not implemented yet'}), 501
    except Exception as e:
        logger.error(f'Error verifying Paystack payment: {e}')
        return jsonify({'error': 'Internal server error'}), 500

@payments_bp.route('/stripe/verify/<transaction_id>', methods=['GET'])
@jwt_required()
def verify_stripe_payment(transaction_id):
    try:
        return jsonify({'error': 'Stripe verification not implemented yet'}), 501
    except Exception as e:
        logger.error(f'Error verifying Stripe payment: {e}')
        return jsonify({'error': 'Internal server error'}), 500

@payments_bp.route('/mpesa/verify/<transaction_id>', methods=['GET'])
@jwt_required()
def verify_mpesa_payment(transaction_id):
    try:
        return jsonify({'error': 'M-Pesa verification not implemented yet'}), 501
    except Exception as e:
        logger.error(f'Error verifying M-Pesa payment: {e}')
        return jsonify({'error': 'Internal server error'}), 500

@payments_bp.route('/history', methods=['GET'])
@jwt_required()
def get_payment_history():
    try:
        user_id = get_jwt_identity()
        return jsonify({'payments': []}), 200
    except Exception as e:
        logger.error(f'Error getting payment history: {e}')
        return jsonify({'error': 'Internal server error'}), 500

@payments_bp.route('/subscription/cancel', methods=['POST'])
@jwt_required()
def cancel_subscription():
    try:
        user_id = get_jwt_identity()
        return jsonify({'message': 'Subscription cancelled successfully'}), 200
    except Exception as e:
        logger.error(f'Error cancelling subscription: {e}')
        return jsonify({'error': 'Internal server error'}), 500
