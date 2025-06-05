import os
import logging
from flask import Flask
from werkzeug.middleware.proxy_fix import ProxyFix
from extensions import db, login_manager

# Set up logging
logging.basicConfig(level=logging.DEBUG)

def create_app():
    # Create the app
    app = Flask(__name__)
    app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-change-in-production")
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

    # Configure the database
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///sponsors.db")
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_recycle": 300,
        "pool_pre_ping": True,
    }

    # Configure upload settings
    app.config['UPLOAD_FOLDER'] = 'uploads'
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'main.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'

    # Create upload directory if it doesn't exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    with app.app_context():
        # Import models to ensure tables are created
        from models import User, Sponsor, Activity, SponsorFile
        db.create_all()
        
        # Import and register blueprints
        from routes import main_bp
        app.register_blueprint(main_bp)

        @login_manager.user_loader
        def load_user(user_id):
            return User.query.get(int(user_id))

    return app 