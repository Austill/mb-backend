import logging
from functools import wraps
from flask import request, jsonify, g, current_app
import jwt
from backend.models import User
from .config import Config

logger = logging.getLogger(__name__)

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            token = request.headers['Authorization'].split(" ")[1]

        if not token:
            logger.warning("Token missing for request: %s %s", request.method, request.path)
            return jsonify({'message': 'Token is missing!'}), 401

        try:
            data = jwt.decode(token, Config.SECRET_KEY, algorithms=["HS256"])
            user_id = data.get('user_id')
            logger.info("Token decoded for user_id: %s, request: %s %s", user_id, request.method, request.path)
            user_data = User.find_by_id(user_id)
            if not user_data:
                logger.warning("User not found for user_id: %s, request: %s %s", user_id, request.method, request.path)
                logger.info("Available user data: %s", user_data)
                return jsonify({'message': 'User not found!'}), 401
            current_user = User.from_dict(user_data)
            logger.info("Token validation successful for user_id: %s (%s %s)", user_id, current_user.email, request.method, request.path)
        except jwt.ExpiredSignatureError:
            logger.warning("Token expired for request: %s %s", request.method, request.path)
            return jsonify({'message': 'Token has expired!'}), 401
        except jwt.InvalidTokenError:
            logger.warning("Invalid token for request: %s %s", request.method, request.path)
            return jsonify({'message': 'Token is invalid!'}), 401

        return f(current_user, *args, **kwargs)

    return decorated
