from flask import Blueprint, request, jsonify
from app.models.user import User
from flask_jwt_extended import create_access_token

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
