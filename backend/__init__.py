import os
from flask import Flask
from .extensions import db, migrate, bcrypt, cors


def create_app(config_class="backend.config.Config"):
    app = Flask(__name__)
    # Load configuration from config object
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    bcrypt.init_app(app)
    cors.init_app(
    app,
    resources={
        r"/api/*": {
            "origins": [origin.strip() for origin in app.config["CORS_ORIGINS"].split(",")]
        }
    },
    supports_credentials=True
)

    # Validate database connection on startup
    with app.app_context():
        try:
            with db.engine.connect() as connection:
                connection.execute(db.text("SELECT 1"))
            app.logger.info("Database connection established successfully")
        except Exception as e:
            app.logger.error("Failed to connect to database: %s", e)
            raise

    # This will execute backend/models/__init__.py and register all models
    from . import models

    # Import and register blueprints
    from backend.routes.journal import journal_bp
    # from backend.routes.user import user_bp  # This file was not provided
    from backend.routes.auth import auth
    # from backend.routes.mood import mood_bp    # This file was not provided

    app.register_blueprint(journal_bp, url_prefix="/api/journal")
    # app.register_blueprint(user_bp, url_prefix="/api/user")
    app.register_blueprint(auth, url_prefix="/api/auth")
    # app.register_blueprint(mood_bp, url_prefix="/api/mood")

    # Health check route
    @app.route("/api/health")
    def health_check():
        return {"status": "healthy"}

    # Homepage route
    @app.route("/")
    def home():
        return "Hello, Mind Buddy!"

    return app
