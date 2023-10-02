from flask import Blueprint, request, jsonify
from flask.views import MethodView
from app.models.user import User
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from passlib.hash import pbkdf2_sha256
from app.models.utils.follow_manager import FollowManager

user_bp = Blueprint("user_bp", __name__)


class UserRegistration(MethodView):
    def post(self):
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


class UserLogin(MethodView):
    def post(self):
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


class UserAPI(MethodView):
    @jwt_required()
    def get(self, uuid=None):
        if uuid is None:
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
        else:
            user = User.find_by_id(uuid)
            if not user:
                return jsonify({"error": "User not found"}), 404
            followers_count = FollowManager.get_followers_count(user.uuid)
            following_count = FollowManager.get_following_count(user.uuid)
            user_data = {
                "first_name": user["first_name"],
                "last_name": user["last_name"],
                "email": user["email"],
                "followers_count": followers_count,
                "following_count": following_count,
            }
            return jsonify(user_data), 200


class FollowUserAPI(MethodView):
    @jwt_required()
    def post(self, user_id):
        current_user_identity = get_jwt_identity()
        followed_successful = FollowManager.follow_user(current_user_identity, user_id)
        if followed_successful:
            return jsonify({"message": "User followed successfully"}), 200
        else:
            return jsonify({"error": "User(s) not found"}), 404

    @jwt_required()
    def delete(self, user_id):
        current_user_identity = get_jwt_identity()
        unfollowed_successful = FollowManager.unfollow_user(
            current_user_identity, user_id
        )
        if unfollowed_successful:
            return jsonify({"message": "User unfollowed successfully"}), 200
        else:
            return jsonify({"error": "User(s) not found"}), 404


class FollowAPI(MethodView):
    @jwt_required()
    def get(self, user_id, action):
        if action == "followers":
            followers = FollowManager.get_followers(user_id)
            follower_data = [
                {"uuid": follower["uuid"], "username": follower["username"]}
                for follower in followers
            ]
            return jsonify({"followers": follower_data}), 200
        elif action == "following":
            following = FollowManager.get_following(user_id)
            following_data = [
                {"uuid": followed["uuid"], "username": followed["username"]}
                for followed in following
            ]
            return jsonify({"following": following_data}), 200
        else:
            return jsonify({"error": "Invalid action"}), 400


user_bp.add_url_rule("/register", view_func=UserRegistration.as_view("register"))
user_bp.add_url_rule("/login", view_func=UserLogin.as_view("login"))

user_view = UserAPI.as_view("user_api")
user_bp.add_url_rule("/users", view_func=user_view, methods=["GET"])
user_bp.add_url_rule("/user/<uuid>", view_func=user_view, methods=["GET"])


follow_user_view = FollowUserAPI.as_view("follow_user_api")
user_bp.add_url_rule(
    "/users/<user_id>/follow", view_func=follow_user_view, methods=["POST"]
)
user_bp.add_url_rule(
    "/users/<user_id>/unfollow", view_func=follow_user_view, methods=["DELETE"]
)

follow_view = FollowAPI.as_view("follow_api")
user_bp.add_url_rule(
    "/users/<user_id>/<action>", view_func=follow_view, methods=["GET"]
)
