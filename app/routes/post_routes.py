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
