from flask import Blueprint, request, jsonify
from app.models.user import User
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from passlib.hash import pbkdf2_sha256

user_bp = Blueprint("user_bp", __name__)


@user_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    first_name = data.get("first_name")
    last_name = data.get("last_name")
    email = data.get("email")
    password = data.get("password")

    if not first_name or not last_name or not email or not password:
        return jsonify({"error": "All fields are required"}), 400

    existing_user = User.find_by_email(email)
    if existing_user:
        return jsonify({"error": "Email is already in use"}), 400

    new_user = User(first_name, last_name, email, password)
    new_user.create()

    token = create_access_token(identity=email)

    return jsonify({"message": "User registered successfully", "token": token}), 201


@user_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    user = User.find_by_email(email)

    if not user or not pbkdf2_sha256.verify(password, user["password"]):
        return jsonify({"error": "Invalid credentials"}), 401

    token = create_access_token(identity=email)

    return jsonify({"token": token}), 200


@user_bp.route("/profile", methods=["GET"])
@jwt_required()
def profile():
    current_user_identity = get_jwt_identity()
    if not current_user_identity:
        return jsonify({"error": "Authentication required"}), 401

    user = User.find_by_email(current_user_identity)
    if not user:
        return jsonify({"error": "User not found"}), 404

    user_data = {
        "first_name": user["first_name"],
        "last_name": user["last_name"],
        "email": user["email"],
    }

    return jsonify(user_data), 200


@user_bp.route("/user/<uuid>", methods=["GET"])
@jwt_required()
def get_user_by_uuid(uuid):
    user = User.find_by_id(uuid)

    if not user:
        return jsonify({"error": "User not found"}), 404

    user_data = {
        "first_name": user["first_name"],
        "last_name": user["last_name"],
        "email": user["email"],
    }

    return jsonify(user_data), 200
