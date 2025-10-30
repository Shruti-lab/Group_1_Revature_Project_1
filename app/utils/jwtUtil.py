from flask_jwt_extended import create_access_token,decode_token
from datetime import timedelta

def generate_jwt(user_id, expires_delta=timedelta(hours=1)):
    """
    Generate a JWT token for a given user ID with an expiration time.
    """
    access_token = create_access_token(identity=user_id, expires_delta=expires_delta)
    return access_token