from flask import Blueprint, request, jsonify
from app.models.user import User
from app.models.post import Post
from flask_jwt_extended import jwt_required, get_jwt_identity

posts_bp = Blueprint("posts_bp", __name__)


@posts_bp.route("/posts", methods=["POST"])
@jwt_required()
def create_post():
    current_user_uuid = get_jwt_identity()
    data = request.get_json()
    text = data.get("text", "")
    images = data.get("images", [])

    if not text and not images:
        return jsonify({"error": "A post must have text and/or images"}), 400

    new_post = Post(current_user_uuid, text, images)
    new_post.create()

    return jsonify({"message": "Post created successfully"}), 201


@posts_bp.route("/post/<post_uuid>", methods=["PUT"])
@jwt_required()
def edit_post(post_uuid):
    post = Post.find_by_id(post_uuid)

    if not post:
        return jsonify({"error": "Post not found"}), 404

    current_user_identity = get_jwt_identity()

    if current_user_identity != post["user_uuid"]:
        return jsonify({"error": "You can only edit your own posts"}), 403

    data = request.get_json()
    new_text = data.get("text", "")
    new_images = data.get("images", [])

    if not new_text and not new_images:
        return jsonify({"error": "A post must have text and/or images"}), 400

    post.edit(new_text, new_images)

    return jsonify({"message": "Post edited successfully"}), 200
