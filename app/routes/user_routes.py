from flask import Response, json, request
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    get_jwt_identity,
    jwt_required,
)
from flask_restx import Namespace, Resource, fields
from passlib.hash import pbkdf2_sha256

from app.models.user import Skill, User, user_to_dict
from app.permissions import jwt_guard

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
        "title": fields.String(required=False, descriptions="Title"),
    },
)

skill_input = user_nc.model(
    "SkillInput",
    {
        "name": fields.String(
            required=True, description="Name of the skill to add or remove"
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
        refresh_token = create_refresh_token(identity=new_user.email)
        response = json.dumps(
            {"access_token": access_token, "refresh_token": refresh_token}
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
            return Response(error, status=400, mimetype="application/json")

        access_token = create_access_token(identity=user.email)
        refresh_token = create_refresh_token(identity=user.email)

        response = json.dumps(
            {"access_token": access_token, "refresh_token": refresh_token}
        )

        return Response(response, status=200, mimetype="application/json")


@user_nc.route("/refresh")
class TokenRefresh(Resource):
    @jwt_required(refresh=True)
    def post(self):
        """Refresh access token using refresh token"""
        current_user = get_jwt_identity()
        new_access_token = create_access_token(identity=current_user)

        response = json.dumps({"access_token": new_access_token})
        return Response(response, status=200, mimetype="application/json")


@user_nc.route("/me")
class UserMe(Resource):
    @jwt_guard
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

        skills = [skill.name for skill in current_user.skills.all()]

        user_data = {
            "uuid": current_user.uuid,
            "first_name": current_user.first_name,
            "last_name": current_user.last_name,
            "email": current_user.email,
            "profile_image": current_user.profile_image,
            "title": current_user.title,
            "followers_count": current_user.get_followers_count(),
            "following_count": current_user.get_following_count(),
            "skills": skills,
        }
        return Response(json.dumps(user_data), status=200)

    @jwt_guard
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
        if "title" in data:
            current_user.title = data["title"].strip()
            updated = True

        if updated:
            current_user.save()
            return Response(
                json.dumps(
                    {
                        "message": "User info updated",
                        "user": user_to_dict(current_user),
                    }
                ),
                status=200,
            )
        else:
            return Response(
                json.dumps({"error": "No valid fields to update"}), status=400
            )


@user_nc.route("/me/skill")
class MeSkill(Resource):
    @jwt_guard
    @user_nc.expect(skill_input)
    @user_nc.response(200, "Skill added successfully")
    @user_nc.response(400, "Skill name is required")
    def post(self):
        """Add a skill to the current user"""
        current_user = User.find_by_email(get_jwt_identity())
        data = request.get_json()
        skill_name = data.get("name")

        if not skill_name:
            return Response(
                json.dumps({"error": "Skill name is required"}), status=400
            )

        skill = Skill.nodes.first_or_none(name=skill_name)
        if not skill:
            skill = Skill(name=skill_name).save()

        current_user.skills.connect(skill)
        return Response(
            json.dumps({"message": f"Skill '{skill_name}' added"}), status=200
        )

    @jwt_guard
    @user_nc.expect(skill_input)
    @user_nc.response(200, "Skill removed successfully")
    @user_nc.response(400, "Skill name is required")
    @user_nc.response(404, "Skill not found or not linked to user")
    @jwt_guard
    def delete(self):
        """Remove a skill from the current user (by name)"""
        current_user = User.find_by_email(get_jwt_identity())
        data = request.get_json()
        skill_name = data.get("name")

        if not skill_name:
            return Response(
                json.dumps({"error": "Skill name is required"}), status=400
            )

        skill = Skill.nodes.first_or_none(name=skill_name)
        if not skill:
            return Response(
                json.dumps({"error": f"Skill '{skill_name}' not found"}),
                status=404,
            )

        if current_user.skills.is_connected(skill):
            current_user.skills.disconnect(skill)
            return Response(
                json.dumps({"message": f"Skill '{skill_name}' removed"}),
                status=200,
            )
        else:
            return Response(
                json.dumps(
                    {"error": f"Skill '{skill_name}' not linked to user"}
                ),
                status=404,
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
    @jwt_guard
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
                "title": u.title,
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
        "title": "Filter by title",
        "skills": "Comma-separated list of skills (e.g., Python,React)",
    }
)
class UserList(Resource):
    @jwt_guard
    def get(self):
        """Get a list of all users"""
        page = int(request.args.get("page", 1))
        page_size = int(request.args.get("page_size", 10))

        title = request.args.get("title")
        skills_str = request.args.get("skills")
        skills = (
            [s.strip() for s in skills_str.split(",")] if skills_str else None
        )

        current_user = User.find_by_email(get_jwt_identity())
        data = current_user.get_users_list(
            page=page,
            page_size=page_size,
            title=title,
            skills=skills,
        )
        return Response(json.dumps(data), status=200)


@user_nc.route("/<user_uuid>")
class UserDetail(Resource):
    @jwt_guard
    def get(self, user_uuid):
        """Get a specific user by UUID"""
        current_user = User.find_by_email(get_jwt_identity())
        user = User.find_by_uuid(user_uuid)
        if not user:
            return Response(
                json.dumps({"error": "User not found"}), status=404
            )

        skills = [skill.name for skill in user.skills.all()]

        user_data = {
            "uuid": user.uuid,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email,
            "profile_image": user.profile_image,
            "title": user.title,
            "followers_count": user.get_followers_count(),
            "following_count": user.get_following_count(),
            "is_following": current_user.is_following(user),
            "follows_me": user.is_following(current_user),
            "skills": skills,
        }
        return Response(json.dumps(user_data), status=200)


@user_nc.route("/<user_uuid>/follow")
class FollowUserAPI(Resource):
    @jwt_guard
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

    @jwt_guard
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
    @jwt_guard
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
                "about": u.about,
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


@user_nc.route("/suggested")
@user_nc.doc(
    description="Get suggested users to follow (+2, and +3 level connections).",
    responses={
        200: "List of suggested users returned successfully",
        401: "Unauthorized - JWT token required",
    },
)
class Suggested(Resource):
    @jwt_guard
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
                        "profile_image": s["user"].profile_image,
                        "title": s["user"].title,
                        "degree": s["degree"],
                        "follows_me": s["follows_me"],
                    }
                    for s in suggestions
                ]
            ),
            status=200,
            mimetype="application/json",
        )
