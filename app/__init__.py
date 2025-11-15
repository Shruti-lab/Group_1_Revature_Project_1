from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from app.config import Config
from .utils.logger import setup_logging

db = SQLAlchemy()
bcrypt = Bcrypt()
migrate = Migrate()
jwt = JWTManager()

def create_app():
    app = Flask(__name__)

    # loading the config file
    app.config.from_object(Config)

    # setting up logging
    setup_logging(app)

    # initializing the plugins
    db.init_app(app)
    bcrypt.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)

    # JWT error handlers: return clear JSON messages and 401 for auth issues
    try:
        @jwt.unauthorized_loader
        def unauthorized_callback(callback):
            return jsonify({"msg": "Missing Authorization Header"}), 401

        @jwt.invalid_token_loader
        def invalid_token_callback(reason):
            return jsonify({"msg": "Invalid token", "reason": reason}), 401

        @jwt.expired_token_loader
        def expired_token_callback(jwt_header, jwt_payload):
            return jsonify({"msg": "Token has expired"}), 401

        @jwt.revoked_token_loader
        def revoked_token_callback(jwt_header, jwt_payload):
            return jsonify({"msg": "Token has been revoked"}), 401
    except Exception:
        # If JWT version doesn't support these callbacks, skip silently
        pass

    # importing models for migrations
    from app.models.user import User
    from app.models.task import Task

    # importing and registering the blueprints
    from app.routes import register_routes
    register_routes(app)

    return app