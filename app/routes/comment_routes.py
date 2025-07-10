from flask import Response, json, request
from flask_jwt_extended import get_jwt_identity
from flask_restx import Namespace, Resource, fields

from app.models.comment import Comment
from app.models.post import Post
from app.models.user import User
from app.permissions import jwt_guard

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
    @jwt_guard
    @comment_nc.expect(comment_create_model)
    def post(self):
        user: User = User.find_by_email(get_jwt_identity())
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

        comment: Comment = Comment(text=text).save()
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
                {
                    "uuid": comment.uuid,
                    "text": comment.text,
                    "created_at": comment.created_at,
                    "likes_count": 0,
                    "replies_count": 0,
                    "liked": False,
                    "created_by": {
                        "uuid": user.uuid,
                        "name": f"{user.first_name} {user.last_name}",
                        "profile_image": user.profile_image,
                        "title": user.title,
                    },
                }
            ),
            status=201,
        )


@comment_nc.route("/<comment_uuid>")
class CommentDetail(Resource):
    @jwt_guard
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

    @jwt_guard
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
@comment_nc.doc(
    params={
        "page": "Page number (default 1)",
        "page_size": "Number of replies per page (default 10)",
    }
)
class CommentReplies(Resource):
    @jwt_guard
    def get(self, comment_uuid):
        comment: Comment = Comment.nodes.get_or_none(uuid=comment_uuid)
        if not comment:
            return Response(
                json.dumps({"error": "Comment not found"}), status=404
            )

        page = int(request.args.get("page", 1))
        page_size = int(request.args.get("page_size", 10))
        current_user: User = User.find_by_email(get_jwt_identity())

        replies = comment.get_replies(
            current_user_uuid=current_user.uuid,
            page=page,
            page_size=page_size,
        )

        replies_list = []
        for reply in replies["results"]:
            creator = reply._creator
            replies_list.append(
                {
                    "uuid": reply.uuid,
                    "text": reply.text,
                    "created_at": str(reply.created_at),
                    "likes_count": getattr(reply, "_likes_count", 0),
                    "liked": getattr(reply, "_liked", False),
                    "created_by": {
                        "uuid": creator["uuid"],
                        "name": f"{creator['first_name']} {creator['last_name']}",
                        "profile_image": creator.get("profile_image"),
                        "title": creator.get("title"),
                    },
                }
            )

        response = {
            "page": page,
            "page_size": page_size,
            "total": replies["total"],
            "results": replies_list,
        }

        return Response(json.dumps(response), status=200)


@comment_nc.route("/<comment_uuid>/like")
class CommentLike(Resource):
    @jwt_guard
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

    @jwt_guard
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
