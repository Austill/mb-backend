import os
import logging
from flask import Flask
from .extensions import mongo, bcrypt, cors, jwt
from pymongo import MongoClient


def create_app(config_class="backend.config.Config"):
    app = Flask(__name__)
    # Load configuration from config object
    app.config.from_object(config_class)

    # Configure logging
    logging.basicConfig(
        level=getattr(logging, app.config["LOGGING_LEVEL"]),
        format=app.config["LOGGING_FORMAT"]
    )

    # Initialize extensions
    bcrypt.init_app(app)
    jwt.init_app(app)
    cors.init_app(
    app,
    resources={
        r"/api/*": {
            "origins": [origin.strip() for origin in app.config["CORS_ORIGINS"].split(",")]
        }
    },
    supports_credentials=True
)

    # Initialize MongoDB
    global mongo
    mongo = MongoClient(app.config["MONGO_URI"])
    db = mongo.mindbuddy

    # Validate database connection on startup
    with app.app_context():
        try:
            # Ping the database
            mongo.admin.command('ping')
            app.logger.info("MongoDB connection established successfully")
        except Exception as e:
            app.logger.error("Failed to connect to MongoDB: %s", e)
            raise

    # This will execute backend/models/__init__.py and register all models
    from . import models

    # Import and register blueprints
    from backend.routes.journal import journal_bp
    from backend.routes.user import user_bp
    from backend.routes.auth import auth
    from backend.routes.mood import mood_bp
    from backend.routes.subscribe import subscribe_bp
    from backend.routes.payments import payments_bp
    from backend.routes.webhook import webhook_bp
    from backend.routes.chat import chat_bp
    from backend.routes.ai_chat import chat_bp as ai_chat_bp
    from backend.routes.ai_insights import insights_bp

    app.register_blueprint(journal_bp, url_prefix="/api/journal")
    app.register_blueprint(user_bp, url_prefix="/api/user")
    app.register_blueprint(auth, url_prefix="/api/auth")
    app.register_blueprint(mood_bp, url_prefix="/api/mood")
    app.register_blueprint(subscribe_bp, url_prefix="/api")
    app.register_blueprint(payments_bp, url_prefix="/api/payments")
    app.register_blueprint(webhook_bp, url_prefix="/api")
    app.register_blueprint(chat_bp)
    app.register_blueprint(ai_chat_bp, url_prefix="/api/chat")
    app.register_blueprint(insights_bp, url_prefix="/api/ai_insights")

    # LLM service will be initialized lazily on first use
    app.logger.info("LLM service will be initialized on first use")

    # Health check route
    @app.route("/api/health")
    def health_check():
        return {"status": "healthy"}

    # Homepage route
    @app.route("/")
    def home():
        return "Hello, Mind Buddy!"

    return app
