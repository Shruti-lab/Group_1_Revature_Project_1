from flask import Flask,jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from app.config import Config
from .utils.logger import setup_logging
from authlib.integrations.flask_client import OAuth

db = SQLAlchemy()
bcrypt = Bcrypt()
migrate = Migrate()
jwt = JWTManager()
oauth = OAuth()

def create_app():

    app = Flask(__name__)
    ## loading the config file
    app.config.from_object(Config)

    #setting up logging
    setup_logging(app)

    ## initializing the plugins
    db.init_app(app)
    bcrypt.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    oauth.init_app(app)

    from app.models import User, Task  # Ensure models are imported for migrations

    ## importing and registering the blueprints
    from app.routes import register_routes
    register_routes(app)

    # Register Google OAuth
    oauth.register(
        name='google',
        client_id=app.config['GOOGLE_CLIENT_ID'],
        client_secret=app.config['GOOGLE_CLIENT_SECRET'],
        access_token_url='https://oauth2.googleapis.com/token',   # ✅ Fixed Google endpoint
        authorize_url='https://accounts.google.com/o/oauth2/auth', # ✅ Fixed Google endpoint
        api_base_url='https://www.googleapis.com/oauth2/v1/',      # ✅ For fetching user profile
        client_kwargs={'scope': 'openid email profile'},            # ✅ Scopes tell Google what info you want
        server_metadata_url='https://accounts.google.com/.well-known/openid-configuration', # ✅ Discovery endpoint
        redirect_uri=app.config['GOOGLE_REDIRECT_URI']              # ✅ You control this (must match your console)
    )

    # Register GitHub OAuth
    oauth.register(
        name='github',
        client_id=app.config['GITHUB_CLIENT_ID'],
        client_secret=app.config['GITHUB_CLIENT_SECRET'],
        access_token_url='https://github.com/login/oauth/access_token',  # ✅ GitHub’s token endpoint
        authorize_url='https://github.com/login/oauth/authorize',        # ✅ GitHub’s authorize endpoint
        api_base_url='https://api.github.com/',                          # ✅ Base URL to fetch user info
        client_kwargs={'scope': 'user:email'},                           # ✅ Ask permission for user email
        redirect_uri=app.config['GITHUB_REDIRECT_URI']                   # ✅ Must match your GitHub App config
    )

#     ✅ What this does:
#        It tells Authlib:
#       “Hey, here’s how to connect to Google OAuth.
#       Use these URLs and credentials whenever I call oauth.google.authorize_redirect().”

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