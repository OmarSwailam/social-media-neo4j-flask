from flask import Response, json, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from flask_restx import Namespace, Resource, fields

from app.models.comment import Comment
from app.models.post import Post
from app.models.user import User

comment_nc = Namespace("comments", description="Comment-related operations")


comment_create_model = comment_nc.model(
    "CreateComment",
    {
        "text": fields.String(required=True),
        "post_uuid": fields.String(required=False),
        "comment_uuid": fields.String(required=False),
    },
)


@comment_nc.route("/")
class CommentList(Resource):
    @jwt_required()
    @comment_nc.expect(comment_create_model)
    def post(self):
        user = User.find_by_email(get_jwt_identity())
        data = request.get_json()
        text = data.get("text", "").strip()
        post_uuid = data.get("post_uuid")
        comment_uuid = data.get("comment_uuid")

        if not text:
            return Response(
                json.dumps({"error": "Comment text is required"}), status=400
            )

        if bool(post_uuid) == bool(comment_uuid):
            return Response(
                json.dumps(
                    {
                        "error": "Provide either post_uuid or comment_uuid, not both"
                    }
                ),
                status=400,
            )

        comment = Comment(text=text).save()
        comment.created_by.connect(user)

        if post_uuid:
            post = Post.find_by_uuid(post_uuid)
            if not post:
                return Response(
                    json.dumps({"error": "Post not found"}), status=404
                )
            comment.on_post.connect(post)

        if comment_uuid:
            parent = Comment.nodes.get_or_none(uuid=comment_uuid)
            if not parent:
                return Response(
                    json.dumps({"error": "Parent comment not found"}),
                    status=404,
                )

            if parent.reply_to:
                return Response(
                    json.dumps(
                        {
                            "error": "Cannot reply to a reply; only top-level comments allowed"
                        }
                    ),
                    status=400,
                )

            comment.reply_to.connect(parent)

        return Response(
            json.dumps(
                {"message": "Comment created", "comment_uuid": comment.uuid}
            ),
            status=201,
        )


@comment_nc.route("/<comment_uuid>")
class CommentDetail(Resource):
    @jwt_required()
    def get(self, comment_uuid):
        comment: Comment = Comment.nodes.get_or_none(uuid=comment_uuid)
        if not comment:
            return Response(
                json.dumps({"error": "Comment not found"}), status=404
            )

        user = comment.created_by.all()[0]
        parent = comment.reply_to.all()
        on_post = comment.on_post.all()

        parent_info = None
        if parent:
            parent = parent[0]
            parent_info = {"uuid": parent.uuid, "text": parent.text}

        post_info = None
        if on_post:
            post = on_post[0]
            post_info = {"uuid": post.uuid, "text": post.text}

        likes_count = comment.get_likes_count()
        return Response(
            json.dumps(
                {
                    "uuid": comment.uuid,
                    "text": comment.text,
                    "created_at": str(comment.created_at),
                    "created_by": {
                        "uuid": user.uuid,
                        "name": f"{user.first_name} {user.last_name}",
                        "profile_image": user.profile_image,
                    },
                    "parent_comment": parent_info,
                    "post": post_info,
                    "likes_count": likes_count,
                }
            ),
            status=200,
        )

    @jwt_required()
    def delete(self, comment_uuid):
        user = User.find_by_email(get_jwt_identity())
        comment = Comment.nodes.get_or_none(uuid=comment_uuid)
        if not comment:
            return Response(
                json.dumps({"error": "Comment not found"}), status=404
            )

        if not comment.created_by.is_connected(user):
            return Response(
                json.dumps({"error": "Not authorized"}), status=403
            )

        comment.delete()
        return Response(json.dumps({"message": "Comment deleted"}), status=200)


@comment_nc.route("/<comment_uuid>/replies")
class CommentReplies(Resource):
    @jwt_required()
    def get(self, comment_uuid):
        comment = Comment.nodes.get_or_none(uuid=comment_uuid)
        if not comment:
            return Response(
                json.dumps({"error": "Comment not found"}), status=404
            )

        replies = comment.get_replies()

        replies_list = []
        for reply in replies:
            user = reply.created_by.all()[0]
            replies_list.append(
                {
                    "uuid": reply.uuid,
                    "text": reply.text,
                    "created_at": str(reply.created_at),
                    "created_by": {
                        "uuid": user.uuid,
                        "name": f"{user.first_name} {user.last_name}",
                        "profile_image": user.profile_image,
                    },
                }
            )

        return Response(json.dumps(replies_list), status=200)


@comment_nc.route("/<comment_uuid>/like")
class CommentLike(Resource):
    @jwt_required()
    def post(self, comment_uuid):
        user = User.find_by_email(get_jwt_identity())
        comment = Comment.nodes.get_or_none(uuid=comment_uuid)
        if not comment:
            return Response(
                json.dumps({"error": "Comment not found"}), status=404
            )

        if user.likes_comment.is_connected(comment):
            user.likes_comment.disconnect(comment)
            return Response(
                json.dumps({"message": "Comment unliked"}), status=200
            )
        else:
            user.likes_comment.connect(comment)
            return Response(
                json.dumps({"message": "Comment liked"}), status=201
            )

    @jwt_required()
    def delete(self, comment_uuid):
        """Unlike a comment"""
        user = User.find_by_email(get_jwt_identity())
        comment = Comment.nodes.get_or_none(uuid=comment_uuid)
        if not comment:
            return Response(
                json.dumps({"error": "Comment not found"}), status=404
            )

        if user.likes_comment.is_connected(comment):
            user.likes_comment.disconnect(comment)

        return Response(json.dumps({"message": "Comment unliked"}), status=200)
