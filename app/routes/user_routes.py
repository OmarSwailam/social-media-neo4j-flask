from flask import request, jsonify
from flask.views import MethodView
from app.models.user import User
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from passlib.hash import pbkdf2_sha256
from app.models.utils.follow_manager import FollowManager
from flask_restx import Namespace, fields, Resource

user_nc = Namespace("posts", description="User-related operations")

user_model = user_nc.model(
    "User",
    {
        "first_name": fields.String(required=True, description="First name"),
        "last_name": fields.String(required=True, description="Last name"),
        "email": fields.String(required=True, description="Email address"),
        "password": fields.String(required=True, description="Password"),
    },
)

token_model = user_nc.model(
    "Token",
    {
        "token_type": fields.String(description="Type of the token (e.g., Bearer)"),
        "access_token": fields.String(
            description="Access token to be used for authentication"
        ),
        "expires_in": fields.Integer(
            description="Duration of the token's validity in seconds"
        ),
    },
)

login_model = user_nc.model(
    "LoginModel",
    {
        "email": fields.String(required=True, description="User's email address"),
        "password": fields.String(required=True, description="User's password"),
    },
)


@user_nc.route("register")
class UserRegistration(MethodView):
    @user_nc.doc(description="Register a new user")
    @user_nc.expect(user_model)
    @user_nc.response(201, "User registered successfully", model=user_model)
    @user_nc.response(
        400, "Bad Request: All fields are required or email is already in use"
    )
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


@user_nc.route("/login")
class UserLogin(MethodView):
    @user_nc.doc(description="User login")
    @user_nc.expect(login_model)
    @user_nc.response(200, "User logged in successfully", model=token_model)
    @user_nc.response(400, "Bad Request: Email and password are required")
    @user_nc.response(401, "Unauthorized: Invalid credentials")
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


@user_nc.route("/users")
class UserAPI(Resource):
    @jwt_required()
    @user_nc.doc(description="Get a list of all users")
    @user_nc.marshal_list_with(user_model)
    def get(self):
        users = User.get_all_users()
        return users, 200

    @jwt_required()
    @user_nc.doc(description="Get user details by UUID")
    @user_nc.param("uuid", "User UUID")
    @user_nc.marshal_with(user_model)
    def get(self, uuid):
        user = User.find_by_id(uuid)
        if not user:
            user_nc.abort(404, "User not found")

        followers_count = FollowManager.get_followers_count(user.uuid)
        following_count = FollowManager.get_following_count(user.uuid)
        user_data = {
            "uuid": user["uuid"],
            "first_name": user["first_name"],
            "last_name": user["last_name"],
            "email": user["email"],
            "followers_count": followers_count,
            "following_count": following_count,
        }
        return user_data, 200


@user_nc.route("/users/<user_id>/follow")
@user_nc.doc(params={"user_id": "User ID"})
class FollowUserAPI(Resource):
    @jwt_required()
    @user_nc.doc(description="Follow a user by user ID")
    @user_nc.response(200, "User followed successfully")
    @user_nc.response(404, "User(s) not found")
    def post(self, user_id):
        current_user_identity = get_jwt_identity()
        followed_successful = FollowManager.follow_user(current_user_identity, user_id)
        if followed_successful:
            return {"message": "User followed successfully"}, 200
        else:
            user_nc.abort(404, "User(s) not found")

    @jwt_required()
    @user_nc.doc(description="Unfollow a user by user ID")
    @user_nc.response(200, "User unfollowed successfully")
    @user_nc.response(404, "User(s) not found")
    def delete(self, user_id):
        current_user_identity = get_jwt_identity()
        unfollowed_successful = FollowManager.unfollow_user(
            current_user_identity, user_id
        )
        if unfollowed_successful:
            return {"message": "User unfollowed successfully"}, 200
        else:
            user_nc.abort(404, "User(s) not found")


@user_nc.route("/users/<user_id>/<action>")
@user_nc.doc(params={"user_id": "User ID", "action": "Action (followers or following)"})
class FollowAPI(Resource):
    @jwt_required()
    @user_nc.doc(description="Get followers or following of a user")
    @user_nc.response(200, "List of followers or following")
    @user_nc.response(400, "Invalid action")
    def get(self, user_id, action):
        if action == "followers":
            followers = FollowManager.get_followers(user_id)
            follower_data = [
                {"uuid": follower["uuid"], "username": follower["username"]}
                for follower in followers
            ]
            return {"followers": follower_data}, 200
        elif action == "following":
            following = FollowManager.get_following(user_id)
            following_data = [
                {"uuid": followed["uuid"], "username": followed["username"]}
                for followed in following
            ]
            return {"following": following_data}, 200
        else:
            user_nc.abort(400, "Invalid action")
