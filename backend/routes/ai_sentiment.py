"""
AI Sentiment Analysis Routes
Provides sentiment analysis for journal entries and mood tracking.
"""

from flask import Blueprint, request, jsonify, current_app
from backend.decorators import token_required
from backend.models import SentimentHistory, JournalEntry, WellnessInsight
from backend.services.sentiment_service import get_sentiment_analyzer
from backend.services.insights_service import get_insights_generator
import traceback

sentiment_bp = Blueprint("ai_sentiment", __name__)

@sentiment_bp.route("/analyze", methods=["POST"])
@token_required
def analyze_sentiment(current_user):
    """
    Analyze sentiment of provided text.
    POST /api/sentiment/analyze
    Body: { "text": "journal content", "journal_entry_id": "optional_id" }
    """
    try:
        data = request.get_json()
        text = data.get("text")
        journal_entry_id = data.get("journal_entry_id")
        
        if not text:
            return jsonify({"message": "Text is required"}), 400
        
        current_app.logger.info(f"Analyzing sentiment for user: {current_user._id}")
        
        # Get sentiment analyzer
        analyzer = get_sentiment_analyzer()
        
        # Analyze sentiment
        sentiment_result = analyzer.analyze_sentiment(text)
        
        # Save sentiment history
        sentiment_history = SentimentHistory(
            user_id=str(current_user._id),
            journal_entry_id=journal_entry_id,
            sentiment_label=sentiment_result['sentiment_label'],
            sentiment_scores=sentiment_result['sentiment_scores'],
            detected_emotions=sentiment_result['detected_emotions'],
            crisis_flag=sentiment_result['crisis_flag']
        )
        sentiment_history.crisis_keywords = sentiment_result['crisis_keywords']
        sentiment_history.save()
        
        # Generate insights if needed
        insights_generated = []
        insights_gen = get_insights_generator()
        
        # Check for crisis and generate urgent insight
        if sentiment_result['crisis_flag']:
            current_app.logger.warning(f"Crisis detected for user {current_user._id}")
            
            crisis_insight_data = insights_gen.generate_crisis_support_insight(
                sentiment_result['crisis_keywords']
            )
            
            crisis_insight = WellnessInsight(
                user_id=str(current_user._id),
                insight_type=crisis_insight_data['insight_type'],
                insight_text=crisis_insight_data['insight_text'],
                recommendation=crisis_insight_data['recommendation'],
                activity_suggestion=crisis_insight_data['activity_suggestion'],
                priority=crisis_insight_data['priority']
            )
            crisis_insight.based_on_pattern = crisis_insight_data['based_on_pattern']
            crisis_insight.save()
            
            insights_generated.append(crisis_insight.to_dict())
        
        # Generate wellness recommendation based on sentiment
        elif sentiment_result['sentiment_label'] == 'negative':
            recommendation_data = insights_gen.generate_wellness_recommendation(
                sentiment_result['sentiment_label'],
                sentiment_result['sentiment_scores'].get('negative', 0)
            )
            
            wellness_insight = WellnessInsight(
                user_id=str(current_user._id),
                insight_type=recommendation_data['insight_type'],
                insight_text=recommendation_data['insight_text'],
                recommendation=recommendation_data['recommendation'],
                activity_suggestion=recommendation_data['activity_suggestion'],
                priority=recommendation_data['priority']
            )
            wellness_insight.based_on_sentiment = recommendation_data['based_on_sentiment']
            wellness_insight.save()
            
            insights_generated.append(wellness_insight.to_dict())
        
        return jsonify({
            "sentiment": sentiment_history.to_dict(),
            "insights": insights_generated
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Sentiment analysis error: {e}\n{traceback.format_exc()}")
        return jsonify({"message": "Internal server error"}), 500


@sentiment_bp.route("/history", methods=["GET"])
@token_required
def get_sentiment_history(current_user):
    """
    Get sentiment history for the current user.
    GET /api/sentiment/history?limit=30&days=30
    """
    try:
        limit = request.args.get("limit", 30, type=int)
        days = request.args.get("days", 30, type=int)
        
        # Validate parameters
        limit = min(limit, 100)  # Max 100 records
        days = min(days, 365)  # Max 1 year
        
        current_app.logger.info(f"Fetching sentiment history for user: {current_user._id}")
        
        # Get sentiment history
        sentiment_records = SentimentHistory.find_by_user(
            str(current_user._id),
            limit=limit,
            days=days
        )
        
        return jsonify({
            "history": [SentimentHistory.from_dict(s).to_dict() for s in sentiment_records],
            "count": len(sentiment_records)
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Get sentiment history error: {e}\n{traceback.format_exc()}")
        return jsonify({"message": "Internal server error"}), 500


@sentiment_bp.route("/trends", methods=["GET"])
@token_required
def get_sentiment_trends(current_user):
    """
    Get sentiment trends and analysis.
    GET /api/sentiment/trends?days=30
    """
    try:
        days = request.args.get("days", 30, type=int)
        days = min(days, 365)  # Max 1 year
        
        current_app.logger.info(f"Analyzing sentiment trends for user: {current_user._id}")
        
        # Get sentiment history
        sentiment_records = SentimentHistory.find_by_user(
            str(current_user._id),
            days=days
        )
        
        if not sentiment_records or len(sentiment_records) < 2:
            return jsonify({
                "message": "Not enough data for trend analysis",
                "trend": None
            }), 200
        
        # Analyze trends
        analyzer = get_sentiment_analyzer()
        trend_analysis = analyzer.analyze_sentiment_trend(sentiment_records)
        
        # Get aggregated data
        trends_data = SentimentHistory.get_sentiment_trends(str(current_user._id), days=days)
        
        # Generate pattern insight if significant pattern detected
        insights_gen = get_insights_generator()
        pattern_insight = insights_gen.analyze_mood_patterns(sentiment_records)
        
        # Save pattern insight if appropriate
        if pattern_insight and trend_analysis.get('risk_level') != 'low':
            existing_insights = WellnessInsight.find_by_user(str(current_user._id), limit=10)
            
            if insights_gen.should_generate_insight(existing_insights, 'mood_pattern'):
                mood_insight = WellnessInsight(
                    user_id=str(current_user._id),
                    insight_type=pattern_insight['insight_type'],
                    insight_text=pattern_insight['insight_text'],
                    recommendation=pattern_insight.get('recommendation'),
                    activity_suggestion=pattern_insight.get('activity_suggestion'),
                    priority=pattern_insight['priority']
                )
                mood_insight.based_on_pattern = pattern_insight.get('based_on_pattern')
                mood_insight.save()
                
                pattern_insight = mood_insight.to_dict()
        
        return jsonify({
            "trend_analysis": trend_analysis,
            "sentiment_distribution": trends_data,
            "pattern_insight": pattern_insight
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Sentiment trends error: {e}\n{traceback.format_exc()}")
        return jsonify({"message": "Internal server error"}), 500


@sentiment_bp.route("/crisis-check", methods=["GET"])
@token_required
def check_crisis_flags(current_user):
    """
    Check for recent crisis flags.
    GET /api/sentiment/crisis-check?days=7
    """
    try:
        days = request.args.get("days", 7, type=int)
        days = min(days, 30)
        
        current_app.logger.info(f"Checking crisis flags for user: {current_user._id}")
        
        # Get recent crisis flags
        crisis_records = SentimentHistory.get_recent_crisis_flags(
            str(current_user._id),
            days=days
        )
        
        has_crisis = len(crisis_records) > 0
        
        return jsonify({
            "has_crisis_flags": has_crisis,
            "crisis_count": len(crisis_records),
            "recent_crises": [SentimentHistory.from_dict(c).to_dict() for c in crisis_records]
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Crisis check error: {e}\n{traceback.format_exc()}")
        return jsonify({"message": "Internal server error"}), 500
