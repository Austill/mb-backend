import os
import logging
from flask import Flask, request
from .extensions import mongo, bcrypt, cors, jwt
from pymongo import MongoClient

# Reduce pymongo logging verbosity
logging.getLogger('pymongo').setLevel(logging.WARNING)


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

    # Initialize MongoDB (don't block on connect; set reasonable timeouts)
    global mongo
    try:
        mongo = MongoClient(
            app.config["MONGO_URI"],
            serverSelectionTimeoutMS=5000,
            socketTimeoutMS=20000,
            connect=False
        )
    except TypeError:
        # Some pymongo versions may not accept connect=False; fall back gracefully
        mongo = MongoClient(
            app.config["MONGO_URI"],
            serverSelectionTimeoutMS=5000,
            socketTimeoutMS=20000,
        )
    db = mongo.mindbuddy
    
    # Ensure an index on users.email to speed up lookups (best-effort)
    try:
        db.users.create_index("email", unique=True, background=True)
        app.logger.info("Ensured index on users.email")
    except Exception as e:
        app.logger.warning("Could not create index on users.email: %s", e)

    app.logger.info("MongoDB client initialized")

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

    # Global CORS enforcement (defensive fallback in case Flask-CORS misses something)
    allowed_origins = [origin.strip() for origin in app.config["CORS_ORIGINS"].split(",")]

    @app.before_request
    def _handle_options_preflight():
        # Return a default CORS preflight response if needed
        if request.method == 'OPTIONS':
            resp = app.make_default_options_response()
            origin = request.headers.get('Origin')
            if origin and (origin in allowed_origins or '*' in allowed_origins):
                headers = resp.headers
                headers['Access-Control-Allow-Origin'] = origin
                headers['Access-Control-Allow-Credentials'] = 'true'
                headers['Access-Control-Allow-Headers'] = 'Authorization,Content-Type'
                headers['Access-Control-Allow-Methods'] = 'GET,POST,PUT,DELETE,OPTIONS'
                headers['Vary'] = 'Origin'
            return resp

    @app.after_request
    def _apply_cors_headers(response):
        origin = request.headers.get('Origin')
        if origin and (origin in allowed_origins or '*' in allowed_origins):
            response.headers['Access-Control-Allow-Origin'] = origin
            response.headers['Access-Control-Allow-Credentials'] = 'true'
            response.headers['Access-Control-Allow-Headers'] = 'Authorization,Content-Type'
            response.headers['Access-Control-Allow-Methods'] = 'GET,POST,PUT,DELETE,OPTIONS'
            # Ensure caching proxies vary by Origin
            response.headers['Vary'] = 'Origin'
        return response

    # Homepage route
    @app.route("/")
    def home():
        return "Hello, Mind Buddy!"

    return app
