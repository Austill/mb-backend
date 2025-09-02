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
    cors.init_app(app, resources={r"/api/*": {"origins": "*"}})  # Configure origins for production

    # Import models here to ensure they are registered with SQLAlchemy for migrations
    from backend.models import user

    # Import and register blueprints
    from backend.routes.journal import journal_bp
    from backend.routes.user import user_bp
    from backend.routes.auth import auth  # Uncomment when auth.py exists

    app.register_blueprint(journal_bp, url_prefix="/api/journal")
    app.register_blueprint(user_bp, url_prefix="/api/user")
    app.register_blueprint(auth, url_prefix="/api/auth")

    # Health check route
    @app.route("/api/health")
    def health_check():
        return {"status": "healthy"}
    
    # Homepage route
    @app.route("/")
    def home():
        return "Hello, Mind Buddy!"

    return app
