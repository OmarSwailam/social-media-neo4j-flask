from flask import Blueprint, request
from flask_restx import Namespace, Resource, fields

from app.models.post import Post
from flask_jwt_extended import jwt_required, get_jwt_identity

posts_bp = Blueprint("posts_bp", __name__)

api = Namespace("posts", description="Post-related operations")

post_model = api.model(
    "Post",
    {
        "uuid": fields.String(description="Post UUID"),
        "user_uuid": fields.String(description="User UUID"),
        "text": fields.String(description="Post text"),
        "images": fields.List(fields.String(description="Image URLs")),
    },
)


@api.route("/posts")
class PostList(Resource):
    @jwt_required()
    @api.marshal_list_with(post_model)
    def get(self):
        """Get a list of all posts"""
        posts = Post.get_all_posts()
        return posts, 200

    @jwt_required()
    @api.expect(post_model)
    def post(self):
        """Create a new post"""
        current_user_uuid = get_jwt_identity()
        data = request.get_json()
        text = data.get("text", "")
        images = data.get("images", [])

        if not text and not images:
            return {"error": "A post must have text and/or images"}, 400

        new_post = Post(current_user_uuid, text, images)
        new_post.create()

        return {"message": "Post created successfully"}, 201


@api.route("/posts/<post_uuid>")
@api.param("post_uuid", "Post UUID")
class PostDetail(Resource):
    @jwt_required()
    @api.marshal_with(post_model)
    def get(self, post_uuid):
        """Get a specific post by UUID"""
        post = Post.find_by_id(post_uuid)
        if not post:
            api.abort(404, "Post not found")
        return post, 200

    @jwt_required()
    @api.expect(post_model)
    def put(self, post_uuid):
        """Edit a specific post by UUID"""
        post = Post.find_by_id(post_uuid)
        if not post:
            api.abort(404, "Post not found")

        current_user_identity = get_jwt_identity()

        if current_user_identity != post["user_uuid"]:
            api.abort(403, "You can only edit your own posts")

        data = request.get_json()
        new_text = data.get("text", "")
        new_images = data.get("images", [])

        if not new_text and not new_images:
            return {"error": "A post must have text and/or images"}, 400

        post.edit(new_text, new_images)
        return {"message": "Post edited successfully"}, 200

    @jwt_required()
    def delete(self, post_uuid):
        """Delete a specific post by UUID"""
        current_user_identity = get_jwt_identity()
        post = Post.find_by_id(post_uuid)

        if not post:
            api.abort(404, "Post not found")

        if current_user_identity != post["user_uuid"]:
            api.abort(403, "You can only delete your own posts")

        post.delete()
        return {"message": "Post deleted successfully"}, 200
