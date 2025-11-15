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
    # If the process already has handlers (e.g. Gunicorn in production), don't add
    # a new basicConfig handler which would otherwise duplicate logs. Instead
    # respect existing handlers and only set the level.
    desired_level = getattr(logging, app.config["LOGGING_LEVEL"].upper(), logging.INFO)

    if not logging.getLogger().handlers:
        logging.basicConfig(
            level=desired_level,
            format=app.config["LOGGING_FORMAT"]
        )
    else:
        # Running under Gunicorn or another WSGI server that configured logging.
        logging.getLogger().setLevel(desired_level)

    # Quiet down very noisy third-party loggers unless explicitly DEBUG
    if desired_level != logging.DEBUG:
        logging.getLogger('werkzeug').setLevel(logging.WARNING)
        logging.getLogger('gunicorn.error').setLevel(logging.WARNING)
        logging.getLogger('gunicorn.access').setLevel(logging.WARNING)
        logging.getLogger('pymongo').setLevel(logging.WARNING)

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
            # Log error but allow app to continue starting for local development.
            # The app will run with `app.config['MONGO_AVAILABLE'] = False` and
            # routes that require the DB should handle the missing connection.
            app.logger.error("Failed to connect to MongoDB: %s", e)
            app.logger.warning("Continuing without MongoDB connection. Some features will be disabled.")
            app.config['MONGO_AVAILABLE'] = False

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

    # Groq LLM service will be initialized lazily on first use
    app.logger.info("Groq LLM service initialized and ready for chat functionality")

    # Health check route
    @app.route("/api/health")
    def health_check():
        return {"status": "healthy"}

    # Homepage route
    @app.route("/")
    def home():
        return "Hello, Mind Buddy!"

    return app
