from flask import request, json, Response
from app.models.user import User
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    jwt_required,
    get_jwt_identity,
)
from passlib.hash import pbkdf2_sha256
from flask_restx import Namespace, fields, Resource

user_nc = Namespace("users", description="User-related operations")

register_model = user_nc.model(
    "User",
    {
        "first_name": fields.String(description="First name"),
        "last_name": fields.String(description="Last name"),
        "email": fields.String(description="Email address"),
        "password": fields.String(description="Password"),
    },
)

login_model = user_nc.model(
    "LoginModel",
    {
        "email": fields.String(required=True, description="User's email address"),
        "password": fields.String(required=True, description="User's password"),
    },
)


@user_nc.route("/register")
class UserRegistration(Resource):
    @user_nc.expect(register_model)
    def post(self):
        """Register a new user"""
        data = request.get_json()
        first_name = data.get("first_name")
        last_name = data.get("last_name")
        email = data.get("email")
        password = data.get("password")

        if not first_name or not last_name or not email or not password:
            error = json.dumps({"error": "All fields are required"})
            return Response(error, status=400, mimetype="application/json")

        existing_user = User.find_by_email(email)
        if existing_user:
            error = json.dumps({"error": "Email is already in use"})
            return Response(error, status=400, mimetype="application/json")

        hashed_password = pbkdf2_sha256.hash(password)
        new_user = User(
            first_name=first_name,
            last_name=last_name,
            email=email,
            password=hashed_password,
        )
        new_user.save()

        access_token = create_access_token(identity=new_user.email)
        response = json.dumps(
            {
                "user": {
                    "uuid": new_user.uuid,
                    "first_name": new_user.first_name,
                    "last_name": new_user.last_name,
                    "email": new_user.email,
                },
                "access_token": access_token,
            }
        )

        return Response(response, status=201, mimetype="application/json")


@user_nc.route("/login")
class UserLogin(Resource):
    @user_nc.expect(login_model)
    def post(self):
        """Login to account"""
        data = request.get_json()
        email = data.get("email")
        password = data.get("password")

        if not email or not password:
            error = json.dumps({"error": "Email and password are required"})
            return Response(error, status=400, mimetype="application/json")

        user = User.find_by_email(email)

        if not user or not pbkdf2_sha256.verify(password, user.password):
            error = json.dumps({"error": "Invalid credentials"})
            return Response(error, status=401, mimetype="application/json")

        access_token = create_access_token(identity=user.email)
        refresh_token = create_refresh_token(identity=user.email)

        response = json.dumps(
            {
                "access_token": access_token,
                "refresh_token": refresh_token,
            }
        )
        return Response(response, status=200, mimetype="application/json")


@user_nc.route("/")
class UserList(Resource):
    @jwt_required()
    def get(self):
        """Get a list of all users"""
        users = User.nodes.all()
        users_list = [
            {
                "uuid": user.uuid,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "email": user.email,
            }
            for user in users
        ]
        return Response(json.dumps(users_list), status=200)


@user_nc.route("/<user_id>")
class UserDetail(Resource):
    @jwt_required()
    def get(self, user_id):
        """Get a specific user by UUID"""
        user = User.find_by_id(user_id)
        if not user:
            return Response(json.dumps({"error": "User not found"}), status=404)

        user_data = {
            "uuid": user.uuid,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email,
            "followers_count": user.get_followers_count(),
            "following_count": user.get_following_count(),
        }
        return Response(json.dumps(user_data), status=200)


@user_nc.route("/<user_id>/follow")
class FollowUserAPI(Resource):
    @jwt_required()
    def post(self, user_id):
        """Follow a user"""
        current_user = User.find_by_email(get_jwt_identity())
        user_to_follow = User.find_by_id(user_id)
        followed_successful = current_user.follow(user_to_follow)
        if followed_successful:
            return Response(
                json.dumps({"response": "Follow created successfully"}), status=201
            )
        else:
            return Response(json.dumps({"error": "User not found"}), status=404)

    @jwt_required()
    def delete(self, user_id):
        """Unfollow a user"""
        current_user = User.find_by_email(get_jwt_identity())
        user_to_unfollow = User.find_by_id(user_id)
        unfollowed_successful = current_user.unfollow(user_to_unfollow)
        if unfollowed_successful:
            return Response(
                json.dumps({"response": "Unfollowed successfully"}), status=200
            )
        else:
            return Response(json.dumps({"error": "User not found"}), status=404)


@user_nc.route("/<user_id>/<action>")
@user_nc.doc(params={"user_id": "User ID", "action": "Action (followers or following)"})
class FollowAPI(Resource):
    @jwt_required()
    def get(self, user_id, action):
        """Get followers/following of a user by a user UUID"""
        user = User.find_by_id(user_id)
        if not user:
            return Response(json.dumps({"error": "User not found"}), status=404)

        if action == "followers":
            followers = user.get_followers()
            followers_list = [
                {
                    "uuid": user.uuid,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "email": user.email,
                }
                for user in followers
            ]
            return Response(json.dumps({"followers": followers_list}), status=200)
        elif action == "following":
            following = user.get_following()
            following_list = [
                {
                    "uuid": user.uuid,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "email": user.email,
                }
                for user in following
            ]
            return Response(json.dumps({"following": following_list}), status=200)
        else:
            return Response(json.dumps({"error": "error"}), status=404)
