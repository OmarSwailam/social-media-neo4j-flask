from flask import Blueprint, request, jsonify
from app.models.user import User
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from passlib.hash import pbkdf2_sha256
from app.models.utils.follow_manager import FollowManager

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


@user_bp.route("/users", methods=["GET"])
@jwt_required()
def get_all_users():
    users = User.get_all_users()

    user_list = []
    for user in users:
        user_data = {
            "uuid": user["uuid"],
            "first_name": user["first_name"],
            "last_name": user["last_name"],
            "email": user["email"],
        }
        user_list.append(user_data)

    return jsonify(user_list), 200


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


@user_bp.route("/users/<user_id>/follow", methods=["POST"])
@jwt_required()
def follow_user(user_id):
    current_user_identity = get_jwt_identity()
    followed_successful = FollowManager.follow_user(current_user_identity, user_id)
    if followed_successful:
        return jsonify({"message": "User followed successfully"}), 200
    else:
        return jsonify({"error": "User(s) not found"}), 404


@user_bp.route("/users/<user_id>/unfollow", methods=["POST"])
@jwt_required()
def unfollow_user(user_id):
    current_user_identity = get_jwt_identity()
    unfollowed_successful = FollowManager.unfollow_user(current_user_identity, user_id)
    if unfollowed_successful:
        return jsonify({"message": "User unfollowed successfully"}), 200
    else:
        return jsonify({"error": "User(s) not found"}), 404


@user_bp.route("/users/<user_id>/followers", methods=["GET"])
@jwt_required()
def get_followers(user_id):
    followers = FollowManager.get_followers(user_id)
    follower_data = [
        {"uuid": follower["uuid"], "username": follower["username"]}
        for follower in followers
    ]
    return jsonify({"followers": follower_data}), 200


@user_bp.route("/users/<user_id>/following", methods=["GET"])
@jwt_required()
def get_following(user_id):
    following = FollowManager.get_following(user_id)
    following_data = [
        {"uuid": followed["uuid"], "username": followed["username"]}
        for followed in following
    ]
    return jsonify({"following": following_data}), 200
