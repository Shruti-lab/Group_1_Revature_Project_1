from flask import Flask,jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from app.config import Config, TestingConfig  
from .utils.logger import setup_logging

db = SQLAlchemy()
bcrypt = Bcrypt()
migrate = Migrate()
jwt = JWTManager()

def create_app(testing=False):

    app = Flask(__name__)

    if testing:
        app.config.from_object(TestingConfig)
    else:
        app.config.from_object(Config)

    #setting up logging
    setup_logging(app)

    ## initializing the plugins
    db.init_app(app)
    bcrypt.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)

    from app.models import User, Task  # Ensure models are imported for migrations

    ## importing and registering the blueprints
    from app.routes import register_routes
    register_routes(app)

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

    return app