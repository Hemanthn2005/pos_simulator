from flask import Flask
from flask_cors import CORS
from .config import Config
from .database import init_db
import os


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Ensure secret key
    app.secret_key = os.environ.get("SECRET_KEY", "pos-simulator-key-2024")

    # Initialize CORS
    CORS(app)

    # Initialize Database
    init_db()

    # Register Blueprints
    from .auth import auth_bp
    from .routes import main

    app.register_blueprint(auth_bp)
    app.register_blueprint(main)

    return app
