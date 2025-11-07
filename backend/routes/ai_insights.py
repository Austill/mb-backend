"""
AI Insights Routes
Wellness insights and recommendations endpoints.
"""

from flask import Blueprint, request, jsonify, current_app
from backend.decorators import token_required
from backend.models import WellnessInsight, SentimentHistory
from backend.services.insights_service import get_insights_generator
import traceback

insights_bp = Blueprint("ai_insights", __name__)

@insights_bp.route("/", methods=["GET"])
@token_required
def get_insights(current_user):
    """
    Get wellness insights for the current user.
    GET /api/insights?limit=10&unread_only=false
    """
    try:
        limit = request.args.get("limit", 10, type=int)
        unread_only = request.args.get("unread_only", "false").lower() == "true"
        
        limit = min(limit, 50)  # Max 50 insights
        
        current_app.logger.info(f"Fetching insights for user: {current_user._id}")
        
        # Get insights
        insights = WellnessInsight.find_by_user(
            str(current_user._id),
            limit=limit,
            unread_only=unread_only
        )
        
        return jsonify({
            "insights": [WellnessInsight.from_dict(i).to_dict() for i in insights],
            "count": len(insights)
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Get insights error: {e}\n{traceback.format_exc()}")
        return jsonify({"message": "Internal server error"}), 500


@insights_bp.route("/urgent", methods=["GET"])
@token_required
def get_urgent_insights(current_user):
    """
    Get urgent/high priority insights for the current user.
    GET /api/insights/urgent
    """
    try:
        current_app.logger.info(f"Fetching urgent insights for user: {current_user._id}")
        
        # Get urgent insights
        urgent = WellnessInsight.get_urgent_insights(str(current_user._id))
        
        return jsonify({
            "urgent_insights": [WellnessInsight.from_dict(i).to_dict() for i in urgent],
            "count": len(urgent),
            "has_urgent": len(urgent) > 0
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Get urgent insights error: {e}\n{traceback.format_exc()}")
        return jsonify({"message": "Internal server error"}), 500


@insights_bp.route("/daily", methods=["GET"])
@token_required
def get_daily_insight(current_user):
    """
    Get or generate today's daily insight.
    GET /api/insights/daily
    """
    try:
        current_app.logger.info(f"Fetching daily insight for user: {current_user._id}")
        
        # Check for existing daily insight
        daily_insight = WellnessInsight.get_daily_insight(str(current_user._id))
        
        if daily_insight:
            return jsonify({
                "insight": WellnessInsight.from_dict(daily_insight).to_dict(),
                "is_new": False
            }), 200
        
        # Generate new daily insight
        insights_gen = get_insights_generator()
        
        # Get recent sentiment for personalization
        recent_sentiment = SentimentHistory.find_by_user(
            str(current_user._id),
            limit=5,
            days=7
        )
        
        insight_data = insights_gen.generate_daily_insight(
            str(current_user._id),
            sentiment_history=recent_sentiment
        )
        
        # Save the insight
        new_insight = WellnessInsight(
            user_id=str(current_user._id),
            insight_type=insight_data['insight_type'],
            insight_text=insight_data['insight_text'],
            recommendation=insight_data.get('recommendation'),
            activity_suggestion=insight_data.get('activity_suggestion'),
            priority=insight_data['priority']
        )
        new_insight.save()
        
        return jsonify({
            "insight": new_insight.to_dict(),
            "is_new": True
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Get daily insight error: {e}\n{traceback.format_exc()}")
        return jsonify({"message": "Internal server error"}), 500


@insights_bp.route("/<insight_id>/read", methods=["PUT"])
@token_required
def mark_insight_read(current_user, insight_id):
    """
    Mark an insight as read.
    PUT /api/insights/<insight_id>/read
    """
    try:
        current_app.logger.info(f"Marking insight {insight_id} as read for user: {current_user._id}")
        
        # Get the insight
        insight_data = WellnessInsight.find_by_id(insight_id)
        
        if not insight_data:
            return jsonify({"message": "Insight not found"}), 404
        
        insight = WellnessInsight.from_dict(insight_data)
        
        # Verify user owns this insight
        if str(insight.user_id) != str(current_user._id):
            return jsonify({"message": "Unauthorized"}), 403
        
        # Mark as read
        insight.mark_as_read()
        
        return jsonify({
            "message": "Insight marked as read",
            "insight": insight.to_dict()
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Mark insight read error: {e}\n{traceback.format_exc()}")
        return jsonify({"message": "Internal server error"}), 500


@insights_bp.route("/<insight_id>/dismiss", methods=["PUT"])
@token_required
def dismiss_insight(current_user, insight_id):
    """
    Dismiss an insight.
    PUT /api/insights/<insight_id>/dismiss
    """
    try:
        current_app.logger.info(f"Dismissing insight {insight_id} for user: {current_user._id}")
        
        # Get the insight
        insight_data = WellnessInsight.find_by_id(insight_id)
        
        if not insight_data:
            return jsonify({"message": "Insight not found"}), 404
        
        insight = WellnessInsight.from_dict(insight_data)
        
        # Verify user owns this insight
        if str(insight.user_id) != str(current_user._id):
            return jsonify({"message": "Unauthorized"}), 403
        
        # Dismiss
        insight.dismiss()
        
        return jsonify({
            "message": "Insight dismissed",
            "insight": insight.to_dict()
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Dismiss insight error: {e}\n{traceback.format_exc()}")
        return jsonify({"message": "Internal server error"}), 500


@insights_bp.route("/generate", methods=["POST"])
@token_required
def generate_insight(current_user):
    """
    Manually trigger insight generation based on current mood/sentiment.
    POST /api/insights/generate
    Body: { "type": "wellness_recommendation" | "mood_pattern" }
    """
    try:
        data = request.get_json()
        insight_type = data.get("type", "wellness_recommendation")

        current_app.logger.info(f"Generating {insight_type} insight for user: {current_user._id}")

        insights_gen = get_insights_generator()

        # Get recent sentiment data
        sentiment_records = SentimentHistory.find_by_user(
            str(current_user._id),
            limit=10,
            days=7
        )

        insight_data = None

        if insight_type == "mood_pattern" and len(sentiment_records) >= 2:
            # Generate mood pattern insight
            insight_data = insights_gen.analyze_mood_patterns(sentiment_records)

        elif insight_type == "wellness_recommendation":
            # Generate wellness recommendation based on most recent sentiment
            if sentiment_records and len(sentiment_records) > 0:
                recent = sentiment_records[0]
                sentiment_label = recent.get('sentiment_label', 'neutral')
                sentiment_scores = recent.get('sentiment_scores', {})
                score = sentiment_scores.get(sentiment_label, 0)

                insight_data = insights_gen.generate_wellness_recommendation(
                    sentiment_label,
                    score
                )
            else:
                # No sentiment data, generate generic recommendation
                insight_data = insights_gen.generate_wellness_recommendation('neutral')

        if not insight_data:
            return jsonify({
                "message": "Unable to generate insight with current data"
            }), 400

        # Save the insight
        new_insight = WellnessInsight(
            user_id=str(current_user._id),
            insight_type=insight_data['insight_type'],
            insight_text=insight_data['insight_text'],
            recommendation=insight_data.get('recommendation'),
            activity_suggestion=insight_data.get('activity_suggestion'),
            priority=insight_data['priority']
        )

        if 'based_on_sentiment' in insight_data:
            new_insight.based_on_sentiment = insight_data['based_on_sentiment']
        if 'based_on_pattern' in insight_data:
            new_insight.based_on_pattern = insight_data['based_on_pattern']

        new_insight.save()

        return jsonify({
            "message": "Insight generated successfully",
            "insight": new_insight.to_dict()
        }), 201

    except Exception as e:
        current_app.logger.error(f"Generate insight error: {e}\n{traceback.format_exc()}")
        return jsonify({"message": "Internal server error"}), 500


@insights_bp.route("/analyze", methods=["POST"])
@token_required
def analyze_journal_entry(current_user):
    """
    Analyze a journal entry and provide AI insights.
    POST /api/insights/analyze
    Body: { "entry": "journal entry text" }
    """
    try:
        data = request.get_json()

        # Validate input
        if not data or "entry" not in data:
            return jsonify({"error": "Journal entry is required"}), 400

        entry_text = data["entry"].strip()
        if not entry_text:
            return jsonify({"error": "Journal entry cannot be empty"}), 400

        current_app.logger.info("Received journal entry for analysis")

        # Import LLM service
        from backend.services.llm_service import get_llm_service
        llm = get_llm_service()

        # Construct the structured AI prompt
        prompt = f"""You are Sereni, a warm, empathetic wellness companion.
Analyze the following journal entry and provide gentle, helpful insights.

Focus on:
- The user's emotional tone and state
- Possible underlying thoughts or stressors
- One short motivational message
- One practical self-care suggestion

Journal Entry:
"{entry_text}"
"""

        # Generate insight using LLM
        messages = [{"role": "user", "content": prompt}]
        insight = llm.generate_response(messages)

        current_app.logger.info("Generated insight successfully")

        return jsonify({"insight": insight}), 200

    except Exception as e:
        current_app.logger.error(f"Error generating insight: {e}\n{traceback.format_exc()}")
        return jsonify({"error": "Failed to generate insight"}), 500
