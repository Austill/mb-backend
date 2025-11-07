"""
AI Chat Routes
Conversational AI assistant (Sereni) endpoints.
"""

from flask import Blueprint, request, jsonify, current_app
from backend.decorators import token_required
from backend.models import ChatLog, SentimentHistory
from backend.services.llm_service import get_llm_service
from backend.services.sentiment_service import get_sentiment_analyzer
import traceback

chat_bp = Blueprint("ai_chat", __name__)

@chat_bp.route("/message", methods=["POST"])
@token_required
def send_message(current_user):
    """
    Send a message to the AI chatbot and get a response.
    POST /api/chat/message
    Body: { "message": "user message", "conversation_id": "optional_id" }
    """
    try:
        data = request.get_json()
        message = data.get("message")
        conversation_id = data.get("conversation_id")
        
        if not message or len(message.strip()) < 1:
            return jsonify({"message": "Message is required"}), 400
        
        current_app.logger.info(f"Chat message from user: {current_user._id}")
        
        # Analyze message sentiment (quick, for context)
        analyzer = get_sentiment_analyzer()
        message_sentiment = analyzer.analyze_sentiment(message)
        sentiment_label = message_sentiment.get('sentiment_label', 'neutral')
        
        # Get conversation context if conversation_id provided
        context = []
        if conversation_id:
            context = ChatLog.get_conversation_context(conversation_id, limit=5)
        
        # Generate AI response using LLM service
        llm_service = get_llm_service()
        if llm_service is None:
            return jsonify({'error': 'LLM service not available'}), 503

        # Convert context to messages format for LLM service
        messages = []
        if context:
            for msg in context[-5:]:  # Last 5 messages for context
                role = msg.get('role', 'user')
                content = msg.get('content', '')
                if role == 'user':
                    messages.append({"role": "user", "content": content})
                elif role == 'assistant':
                    messages.append({"role": "assistant", "content": content})

        # Add current message
        messages.append({"role": "user", "content": message})

        # Generate response
        ai_response = llm_service.generate_response(messages)

        # Check for crisis keywords in response
        requires_help = any(keyword in ai_response.lower() for keyword in [
            'suicide', 'kill yourself', 'seek professional help', 'emergency services'
        ])

        response_data = {
            'response': ai_response,
            'source': 'ai_model',
            'requires_professional_help': requires_help
        }
        
        # Save chat log
        chat_log = ChatLog(
            user_id=str(current_user._id),
            message=message,
            role='user',
            ai_response=response_data['response'],
            conversation_id=conversation_id
        )
        chat_log.sentiment = sentiment_label
        chat_log.save()
        
        # If new conversation, use the generated conversation_id
        if not conversation_id:
            conversation_id = chat_log.conversation_id
        
        return jsonify({
            "conversation_id": conversation_id,
            "user_message": message,
            "ai_response": response_data['response'],
            "sentiment": sentiment_label,
            "source": response_data.get('source', 'unknown'),
            "requires_professional_help": response_data.get('requires_professional_help', False),
            "chat_id": str(chat_log._id)
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Chat message error: {e}\n{traceback.format_exc()}")
        return jsonify({"message": "Internal server error"}), 500


@chat_bp.route("/conversations", methods=["GET"])
@token_required
def get_conversations(current_user):
    """
    Get recent conversations for the current user.
    GET /api/chat/conversations?limit=10
    """
    try:
        limit = request.args.get("limit", 10, type=int)
        limit = min(limit, 50)  # Max 50 conversations
        
        current_app.logger.info(f"Fetching conversations for user: {current_user._id}")
        
        # Get recent conversations
        conversations = ChatLog.get_recent_conversations(str(current_user._id), limit=limit)
        
        return jsonify({
            "conversations": conversations,
            "count": len(conversations)
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Get conversations error: {e}\n{traceback.format_exc()}")
        return jsonify({"message": "Internal server error"}), 500


@chat_bp.route("/conversation/<conversation_id>", methods=["GET"])
@token_required
def get_conversation(current_user, conversation_id):
    """
    Get all messages in a specific conversation.
    GET /api/chat/conversation/<conversation_id>?limit=50
    """
    try:
        limit = request.args.get("limit", 50, type=int)
        limit = min(limit, 100)  # Max 100 messages
        
        current_app.logger.info(f"Fetching conversation {conversation_id} for user: {current_user._id}")
        
        # Get conversation messages
        messages = ChatLog.find_by_conversation(conversation_id, limit=limit)
        
        # Verify user owns this conversation
        if messages and len(messages) > 0:
            first_message = messages[0]
            if str(first_message.get('user_id')) != str(current_user._id):
                return jsonify({"message": "Unauthorized"}), 403
        
        return jsonify({
            "conversation_id": conversation_id,
            "messages": [ChatLog.from_dict(m).to_dict() for m in messages],
            "count": len(messages)
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Get conversation error: {e}\n{traceback.format_exc()}")
        return jsonify({"message": "Internal server error"}), 500


@chat_bp.route("/history", methods=["GET"])
@token_required
def get_chat_history(current_user):
    """
    Get all chat messages for the current user.
    GET /api/chat/history?limit=50
    """
    try:
        limit = request.args.get("limit", 50, type=int)
        limit = min(limit, 200)  # Max 200 messages
        
        current_app.logger.info(f"Fetching chat history for user: {current_user._id}")
        
        # Get chat history
        chat_logs = ChatLog.find_by_user(str(current_user._id), limit=limit)
        
        return jsonify({
            "history": [ChatLog.from_dict(log).to_dict() for log in chat_logs],
            "count": len(chat_logs)
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Get chat history error: {e}\n{traceback.format_exc()}")
        return jsonify({"message": "Internal server error"}), 500


@chat_bp.route("/proactive-check-in", methods=["GET"])
@token_required
def proactive_check_in(current_user):
    """
    Get a proactive check-in message based on user's sentiment trends.
    GET /api/chat/proactive-check-in
    """
    try:
        current_app.logger.info(f"Generating proactive check-in for user: {current_user._id}")
        
        # Get recent sentiment trends
        sentiment_records = SentimentHistory.find_by_user(str(current_user._id), limit=10, days=7)
        
        if not sentiment_records or len(sentiment_records) == 0:
            # New user or no recent data
            message = (
                "Welcome! I'm Sereni, your mental wellness companion. "
                "I'm here to support you on your wellness journey. "
                "How are you feeling today?"
            )
        else:
            # Analyze trends and generate appropriate message
            analyzer = get_sentiment_analyzer()
            trend_analysis = analyzer.analyze_sentiment_trend(sentiment_records)
            
            # Use LLM service for proactive check-in
            llm_service = get_llm_service()
            if llm_service:
                # Generate a personalized message based on trends
                trend_message = f"Based on your recent mood patterns, you seem to be {trend_analysis.get('trend', 'stable')}. "
                if trend_analysis.get('risk_level') == 'high':
                    trend_message += "I'm here if you'd like to talk about what's been going on."
                elif trend_analysis.get('trend') == 'improving':
                    trend_message += "It's great to see things looking up! How are you feeling today?"
                else:
                    trend_message += "How are you doing today?"

                messages = [{"role": "user", "content": trend_message}]
                message = llm_service.generate_response(messages)
            else:
                message = (
                    "Welcome! I'm Sereni, your mental wellness companion. "
                    "I'm here to support you on your wellness journey. "
                    "How are you feeling today?"
                )
        
        return jsonify({
            "message": message,
            "type": "proactive_check_in"
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Proactive check-in error: {e}\n{traceback.format_exc()}")
        return jsonify({"message": "Internal server error"}), 500
