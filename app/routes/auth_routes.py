from flask import Blueprint

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/ping')
def ping():
    return 'Pong!', 200