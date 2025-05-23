from flask import Response, json, request
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    get_jwt_identity,
    jwt_required,
)
from flask_restx import Namespace, Resource, fields
from passlib.hash import pbkdf2_sha256

from app.models.user import User

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
        "email": fields.String(
            required=True, description="User's email address"
        ),
        "password": fields.String(
            required=True, description="User's password"
        ),
    },
)

user_update_model = user_nc.model(
    "UpdateUser",
    {
        "first_name": fields.String(required=False, description="First name"),
        "last_name": fields.String(required=False, description="Last name"),
        "profile_image": fields.String(
            required=False, description="Profile image URL"
        ),
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


@user_nc.route("/me")
class UserMe(Resource):
    @jwt_required()
    @user_nc.doc(
        description="Get authenticated user's info",
        responses={
            200: "User info retrieved successfully",
            401: "Unauthorized - JWT token required",
            404: "User not found",
        },
    )
    def get(self):
        """Get the authenticated user's info"""
        current_user = User.find_by_email(get_jwt_identity())
        if not current_user:
            return Response(
                json.dumps({"error": "User not found"}), status=404
            )

        user_data = {
            "uuid": current_user.uuid,
            "first_name": current_user.first_name,
            "last_name": current_user.last_name,
            "email": current_user.email,
            "profile_image": current_user.profile_image,
            "followers_count": current_user.get_followers_count(),
            "following_count": current_user.get_following_count(),
        }
        return Response(json.dumps(user_data), status=200)

    @jwt_required()
    @user_nc.expect(user_update_model)
    @user_nc.doc(
        description="Update authenticated user's info",
        responses={
            200: "User info updated successfully",
            400: "No valid fields to update",
            401: "Unauthorized - JWT token required",
            404: "User not found",
        },
    )
    def patch(self):
        """Update the authenticated user's info"""
        current_user = User.find_by_email(get_jwt_identity())
        if not current_user:
            return Response(
                json.dumps({"error": "User not found"}), status=404
            )

        data = request.get_json()
        updated = False

        if "first_name" in data:
            current_user.first_name = data["first_name"].strip()
            updated = True
        if "last_name" in data:
            current_user.last_name = data["last_name"].strip()
            updated = True
        if "profile_image" in data:
            current_user.profile_image = data["profile_image"].strip()
            updated = True

        if updated:
            current_user.save()
            return Response(
                json.dumps({"message": "User info updated"}), status=200
            )
        else:
            return Response(
                json.dumps({"error": "No valid fields to update"}), status=400
            )


@user_nc.route("/me/<action>")
@user_nc.doc(
    params={
        "action": "Action (followers or following)",
        "page": "Page number (default 1)",
        "page_size": "Page size (default 10)",
    }
)
class MeFollowersFollowing(Resource):
    @jwt_required()
    def get(self, action):
        """Get followers/following of the authenticated user (paginated)"""
        user = User.find_by_email(get_jwt_identity())
        page = int(request.args.get("page", 1))
        page_size = int(request.args.get("page_size", 10))

        if action == "followers":
            data = user.get_followers(
                user.uuid, page=page, page_size=page_size
            )
        elif action == "following":
            data = user.get_following(
                user.uuid, page=page, page_size=page_size
            )
        else:
            return Response(
                json.dumps(
                    {
                        "error": "Invalid action, must be 'followers' or 'following'"
                    }
                ),
                status=400,
            )

        results = [
            {
                "uuid": u.uuid,
                "first_name": u.first_name,
                "last_name": u.last_name,
                "email": u.email,
                "profile_image": u.profile_image,
            }
            for u in data["results"]
        ]

        return Response(
            json.dumps(
                {
                    "page": data["page"],
                    "page_size": data["page_size"],
                    "total": data["total"],
                    "results": results,
                }
            ),
            status=200,
        )


@user_nc.route("/")
@user_nc.doc(
    params={
        "page": "Page number (default 1)",
        "page_size": "Page size (default 10)",
    }
)
class UserList(Resource):
    @jwt_required()
    def get(self):
        """Get a list of all users"""
        page = int(request.args.get("page", 1))
        page_size = int(request.args.get("page_size", 10))

        current_user = User.find_by_email(get_jwt_identity())
        data = current_user.get_users_list(page=page, page_size=page_size)
        return Response(json.dumps(data), status=200)


@user_nc.route("/<user_uuid>")
class UserDetail(Resource):
    @jwt_required()
    def get(self, user_uuid):
        """Get a specific user by UUID"""
        current_user = User.find_by_email(get_jwt_identity())
        user = User.find_by_uuid(user_uuid)
        if not user:
            return Response(
                json.dumps({"error": "User not found"}), status=404
            )

        user_data = {
            "uuid": user.uuid,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email,
            "profile_image": user.profile_image,
            "followers_count": user.get_followers_count(),
            "following_count": user.get_following_count(),
            "is_following": current_user.is_following(user),
            "follows_me": user.is_following(current_user),
        }
        return Response(json.dumps(user_data), status=200)


@user_nc.route("/<user_uuid>/follow")
class FollowUserAPI(Resource):
    @jwt_required()
    def post(self, user_uuid):
        """Follow a user"""
        current_user = User.find_by_email(get_jwt_identity())
        user_to_follow = User.find_by_uuid(user_uuid)
        followed_successful = current_user.follow(user_to_follow)
        if followed_successful:
            return Response(
                json.dumps({"response": "Follow created successfully"}),
                status=201,
            )
        else:
            return Response(
                json.dumps({"error": "User not found"}), status=404
            )

    @jwt_required()
    def delete(self, user_uuid):
        """Unfollow a user"""
        current_user = User.find_by_email(get_jwt_identity())
        user_to_unfollow = User.find_by_uuid(user_uuid)
        unfollowed_successful = current_user.unfollow(user_to_unfollow)
        if unfollowed_successful:
            return Response(
                json.dumps({"response": "Unfollowed successfully"}), status=200
            )
        else:
            return Response(
                json.dumps({"error": "User not found"}), status=404
            )


@user_nc.route("/<user_uuid>/<action>")
@user_nc.doc(
    params={
        "user_uuid": "User UUID",
        "action": "Action (followers or following)",
        "page": "Page number (default 1)",
        "page_size": "Page size (default 10)",
    }
)
class FollowAPI(Resource):
    @jwt_required()
    def get(self, user_uuid, action):
        """Get followers/following of a user by UUID (paginated)"""
        page = int(request.args.get("page", 1))
        page_size = int(request.args.get("page_size", 10))

        user = User.find_by_uuid(user_uuid)
        if not user:
            return Response(
                json.dumps({"error": "User not found"}), status=404
            )

        if action == "followers":
            data = user.get_followers(
                user_uuid, page=page, page_size=page_size
            )
        elif action == "following":
            data = user.get_following(
                user_uuid, page=page, page_size=page_size
            )
        else:
            return Response(
                json.dumps(
                    {
                        "error": "Invalid action, must be 'followers' or 'following'"
                    }
                ),
                status=400,
            )

        results = [
            {
                "uuid": u.uuid,
                "first_name": u.first_name,
                "last_name": u.last_name,
                "email": u.email,
                "profile_image": u.profile_image,
            }
            for u in data["results"]
        ]

        return Response(
            json.dumps(
                {
                    "page": data["page"],
                    "page_size": data["page_size"],
                    "total": data["total"],
                    "results": results,
                }
            ),
            status=200,
        )


@user_nc.route("/suggested-friends")
@user_nc.doc(
    description="Get suggested users to follow (friends of friends +2, and +3 level connections).",
    responses={
        200: "List of suggested users returned successfully",
        401: "Unauthorized - JWT token required",
    },
)
class SuggestedFriends(Resource):
    @jwt_required()
    def get(self):
        user = User.find_by_email(get_jwt_identity())
        suggestions = user.get_suggested_friends()
        return Response(
            json.dumps(
                [
                    {
                        "uuid": s["user"].uuid,
                        "first_name": s["user"].first_name,
                        "last_name": s["user"].last_name,
                        "email": s["user"].email,
                        "degree": s["degree"],
                    }
                    for s in suggestions
                ]
            ),
            status=200,
            mimetype="application/json",
        )


@user_nc.route("/suggested-posts")
@user_nc.doc(
    description="Get posts created by second-degree connections (users followed by your followings).",
    responses={
        200: "List of posts returned successfully",
        401: "Unauthorized - JWT token required",
    },
    params={
        "page": "Page number for pagination (default: 1)",
        "page_size": "Number of items per page (default: 10)",
    },
)
class SuggestedPosts(Resource):
    @jwt_required()
    def get(self):
        user = User.find_by_email(get_jwt_identity())

        page = int(request.args.get("page", 1))
        page_size = int(request.args.get("page_size", 10))

        data = user.get_posts_from_second_degree_connections(
            page=page, page_size=page_size
        )

        posts_list = []
        for post in data["results"]:
            posts_list.append(
                {
                    "uuid": post.uuid,
                    "text": post.text,
                    "images": post.images,
                    "created_at": str(post.created_at),
                    "updated_at": str(post.updated_at),
                    "comments_count": getattr(post, "_comments_count", 0),
                    "likes_count": getattr(post, "_likes_count", 0),
                }
            )

        return Response(
            json.dumps(
                {
                    "page": data["page"],
                    "page_size": data["page_size"],
                    "total": data["total"],
                    "results": posts_list,
                }
            ),
            status=200,
            mimetype="application/json",
        )
