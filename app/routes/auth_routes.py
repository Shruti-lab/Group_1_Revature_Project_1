from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token
from app import db,bcrypt
from app.models import User
from app.schema.auth_schema import SignUpSchema,LoginSchema
from pydantic import ValidationError
from app.utils.jwtUtil import generate_jwt

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()
    try:
        validated_data = SignUpSchema(**data)
    except ValidationError as e:
        return jsonify({"errors": e.errors()}), 400
    
    existing_user = User.query.filter_by(email=validated_data.email).first()
    if existing_user:
        return jsonify({"message": "Email already registered"}), 400

    new_user = User(name=validated_data.name, email=validated_data.email)
    new_user.set_password(validated_data.password)
    db.session.add(new_user)
    db.session.commit()

    return jsonify({"message": "User registered successfully"}), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    try:
        validated_data = LoginSchema(**data)
    except ValidationError as e:
        return jsonify({"errors": e.errors()}), 400

    user = User.query.filter_by(email=validated_data.email).first()
    if not user or not user.check_password(validated_data.password):
        return jsonify({"message": "Invalid email or password"}), 401

    access_token = generate_jwt(user.user_id)
    return jsonify({
        "message": "Login successful",
        "access_token": access_token,
        "user": {
            "user_id": user.user_id,
            "name": user.name,
            "email": user.email
        }
    }), 200





