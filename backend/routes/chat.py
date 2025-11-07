from flask import Blueprint, request, jsonify, Response
from backend.services.llm_service import get_llm_service
import logging

logger = logging.getLogger(__name__)

chat_bp = Blueprint('chat', __name__)

@chat_bp.route('/api/chat', methods=['POST'])
def chat():
    """Non-streaming chat endpoint."""
    try:
        data = request.get_json()
        if not data or 'messages' not in data:
            return jsonify({'error': 'Missing messages in request'}), 400

        messages = data['messages']
        if not isinstance(messages, list) or not messages:
            return jsonify({'error': 'Messages must be a non-empty list'}), 400

        llm_service = get_llm_service()
        if llm_service is None:
            return jsonify({'error': 'LLM service not available'}), 503

        reply = llm_service.generate_response(messages)
        return jsonify({'reply': reply})

    except Exception as e:
        logger.error(f'Error in chat endpoint: {e}')
        return jsonify({'error': 'Internal server error'}), 500

@chat_bp.route('/api/chat/stream', methods=['POST'])
def chat_stream():
    """Streaming chat endpoint using Server-Sent Events."""
    try:
        data = request.get_json()
        if not data or 'messages' not in data:
            return jsonify({'error': 'Missing messages in request'}), 400

        messages = data['messages']
        if not isinstance(messages, list) or not messages:
            return jsonify({'error': 'Messages must be a non-empty list'}), 400

        llm_service = get_llm_service()
        if llm_service is None:
            return jsonify({'error': 'LLM service not available'}), 503

        def generate():
            try:
                for chunk in llm_service.generate_streaming_response(messages):
                    yield f"data: {chunk}\n\n"
                yield "data: [DONE]\n\n"
            except Exception as e:
                logger.error(f'Error in streaming: {e}')
                yield f"data: Error: {str(e)}\n\n"

        return Response(generate(), mimetype='text/event-stream')

    except Exception as e:
        logger.error(f'Error in chat stream endpoint: {e}')
        return jsonify({'error': 'Internal server error'}), 500
