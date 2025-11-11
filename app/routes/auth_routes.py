from flask import Blueprint, request, jsonify
from flask_jwt_extended import get_jwt_identity, jwt_required
from app import db,bcrypt
from app.models import User
from app.schema.auth_schema import SignUpSchema,LoginSchema
from pydantic import ValidationError
from app.utils.jwtUtil import generate_jwt
import logging

auth_bp = Blueprint('auth', __name__)
logger = logging.getLogger(__name__)

@auth_bp.route('/signup', methods=['POST'])
def signup():
    logger.info("User signup attempt started")
    data = request.get_json()
    try:
        validated_data = SignUpSchema(**data)
        logger.info(f"Signup pydantic data validation successful for email: {validated_data.email}")
    except ValidationError as e:
        logger.warning(f"Signup pydantic validation failed: {e.errors()}")
        return jsonify({"errors": e.errors()}), 400
    
    existing_user = User.query.filter_by(email=validated_data.email).first()
    if existing_user:
        logger.warning(f"Signup failed - email already exists: {validated_data.email}")
        return jsonify({"message": "Email already registered"}), 400

    try:
        new_user = User(name=validated_data.name, email=validated_data.email)
        new_user.set_password(validated_data.password)
        db.session.add(new_user)
        db.session.commit()
        logger.info(f"User registered successfully: {validated_data.email}")
        return jsonify({"message": "User registered successfully"}), 201
    except Exception as e:
        db.session.rollback()
        logger.error(f"Database error during signup: {str(e)}")
        return jsonify({"message": "Registration failed"}), 500




@auth_bp.route('/login', methods=['POST'])
def login():
    logger.info("User login attempt started")
    data = request.get_json()
    try:
        validated_data = LoginSchema(**data)
        logger.info(f"Login pydantic data validation successful for email: {validated_data.email}")
    except ValidationError as e:
        logger.warning(f"Login validation failed: {e.errors()}")
        return jsonify({"errors": e.errors()}), 400

    user = User.query.filter_by(email=validated_data.email).first()
    if not user or not user.check_password(validated_data.password):
        logger.warning(f"Login failed - invalid credentials for email: {validated_data.email}")
        return jsonify({"message": "Invalid email or password"}), 401

    try:
        access_token = generate_jwt(user_id=str(user.user_id))
        logger.info(f"User logged in successfully: {user.email}")
        return jsonify({
            "message": "Login successful",
            "access_token": access_token,
            "user": {
                "user_id": user.user_id,
                "name": user.name,
                "email": user.email
            }
        }), 200
    except Exception as e:
        logger.error(f"JWT generation failed for user {user.email}: {str(e)}")
        return jsonify({"message": "Login failed"}), 500



@auth_bp.route('/user', methods=['GET'])
@jwt_required()
def get_current_user():
    user_id = get_jwt_identity()
    logger.info(f"Fetching current user details for user_id: {user_id}")
    user = User.query.get(user_id)
    if not user:
        logger.warning(f"User not found for user id: {user_id}")
        return jsonify({"message": "User not found"}), 404

    logger.info(f"User details fetched successfully for user_id: {user_id}")
    return jsonify({
        "user_id": user.user_id,
        "name": user.name,
        "email": user.email
    }), 200



@auth_bp.route('/user', methods=['PUT'])
@jwt_required()
def update_current_user():
    user_id = get_jwt_identity()
    logger.info(f"Updating user details for user_id: {user_id}")
    user = User.query.get(user_id)
    if not user:
        logger.warning(f"User not found for update - user_id: {user_id}")
        return jsonify({"message": "User not found"}), 404
    
    data = request.get_json()
    updated_fields = []

    try:
        if 'name' in data:
            user.name = data['name']
            updated_fields.append('name')

        if 'password' in data:
            user.set_password(data['password'])
            updated_fields.append('password')
            
        db.session.commit()
        logger.info(f"User updated successfully - user id: {user_id}, fields: {updated_fields}")
        return jsonify({"message": "User updated successfully"}), 200
    except Exception as e:
        db.session.rollback()
        logger.error(f"Failed to update user {user_id}: {str(e)}")
        return jsonify({"message": "Update failed"}), 500








