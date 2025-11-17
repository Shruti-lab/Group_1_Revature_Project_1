from flask import Flask,jsonify
from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from app.config import Config
from .utils.logger import setup_logging
from flask_cors import CORS

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

    
    # register notifications blueprint
    from app.notifications.routes import notifications_bp
    app.register_blueprint(notifications_bp, url_prefix='/notifications')

    # start background scheduler (after app setup is complete)
    from app.notifications.scheduler import start_scheduler
    start_scheduler(app)

    @app.errorhandler(404)
    def not_found_error(error):
        return jsonify({
        "status": "error",
        "code": 404,
        "message": "The requested resource was not found on the server."
    }), 404

    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({
        "status": "error",
        "code": 500,
        "message": "An internal server error occurred."
    }), 500
    CORS(
    app,
    resources={r"/auth/*": {"origins": "http://localhost:5173"},
               r"/user/*": {"origins": "http://localhost:5173"},
               r"/notifications/*": {"origins": "http://localhost:5173"}},
    supports_credentials=True,
    allow_headers=["Content-Type", "Authorization"],
    methods=["GET", "POST", "PUT", "DELETE", "OPTIONS" ]
    )
    return app