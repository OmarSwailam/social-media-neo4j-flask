from flask import request, json, Response
from flask_restx import Namespace, Resource, fields

from app.models.post import Post
from app.models.user import User
from flask_jwt_extended import jwt_required, get_jwt_identity


post_nc = Namespace("posts", description="Post-related operations")

post_model = post_nc.model(
    "Post",
    {
        "text": fields.String(description="Post text"),
        "images": fields.List(fields.String(description="Image URLs")),
    },
)


@post_nc.route("/")
class PostList(Resource):
    @jwt_required()
    def get(self):
        """Get a list of all posts"""
        posts = Post.get_all_posts()
        posts_list = [
            {
                "uuid": post.uuid,
                "created_by": post.user.uuid,
                "text": post.text,
                "images": post.images,
            }
            for post in posts
        ]
        return Response(json.dumps(posts_list), status=200)

    @jwt_required()
    @post_nc.expect(post_model)
    def post(self):
        """Create a new post"""
        user = User.find_by_email(get_jwt_identity())
        data = request.get_json()
        text = data.get("text", "")
        images = data.get("images", [])

        if not text and not images:
            return Response(
                json.dumps({"error": "A post must have text and/or images"}), status=400
            )

        new_post = Post(text=text, images=images)
        new_post.save()
        new_post.user.connect(user)
        response = json.dumps(
            {
                "post_uuid": new_post.uuid,
                "user_uuid": new_post.uuid,
                "text": new_post.text,
                "images": new_post.images,
                "created_at": new_post.created_at,
                "updated_at": new_post.updated_at,
            }
        )
        return Response(response, status=201, mimetype="application/json")


@post_nc.route("/<post_uuid>")
@post_nc.param("post_uuid", "Post UUID")
class PostDetail(Resource):
    @jwt_required()
    @post_nc.marshal_with(post_model)
    def get(self, post_uuid):
        """Get a specific post by UUID"""
        post = Post.find_by_id(post_uuid)
        if not post:
            return Response(json.dumps({"error": "Post not found"}), status=404)
        post_data = {
            "uuid": post.uuid,
            "text": post.text,
            "images": post.images,
            "created_At": post.created_At,
            "updated_At": post.updated_At,
        }
        return Response(json.dumps(post_data), status=200)

    @jwt_required()
    @post_nc.expect(post_model)
    def put(self, post_uuid):
        """Edit a specific post by UUID"""
        post = Post.find_by_id(post_uuid)
        if not post:
            return Response(json.dumps({"error": "Post not found"}), status=404)

        user = User.find_by_email(get_jwt_identity())

        if user.uuid != post.user_uuid:
            return Response(json.dumps({"error": "Not allowed"}), status=403)

        data = request.get_json()
        new_text = data.get("text", "")
        new_images = data.get("images", [])

        if not new_text and not new_images:
            return Response(
                json.dumps({"error": "Must contain text or/and images"}), status=400
            )

        post.text = new_text
        post.images = new_images
        post.save()
        return Response(json.dumps({"message": "Post edited successfully"}), status=200)

    @jwt_required()
    def delete(self, post_uuid):
        """Delete a specific post by UUID"""
        post = Post.find_by_id(post_uuid)
        user = User.find_by_email(get_jwt_identity())

        if user.uuid != post.user_uuid:
            return Response(json.dumps({"error": "Not allowed"}), status=403)

        if not post:
            return Response(json.dumps({"error": "Post not found"}), status=404)

        post.delete()
        return Response(json.dumps({"message": "Post deleted successfully"}), 204)
