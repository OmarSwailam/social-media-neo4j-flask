from flask import Response, json, request
from flask_jwt_extended import get_jwt_identity
from flask_restx import Namespace, Resource, fields

from app.models.post import Post
from app.models.user import User
from app.permissions import jwt_guard

post_nc = Namespace("posts", description="Post-related operations")

post_creator_model = post_nc.model(
    "PostCreator",
    {
        "uuid": fields.String,
        "name": fields.String,
        "profile_image": fields.String,
        "title": fields.String,
    },
)

post_model = post_nc.model(
    "Post",
    {
        "uuid": fields.String,
        "text": fields.String,
        "images": fields.List(fields.String),
        "created_at": fields.String,
        "created_by": fields.Nested(post_creator_model),
        "comments_count": fields.Integer,
    },
)

paginated_posts_model = post_nc.model(
    "MyPostsResponse",
    {
        "page": fields.Integer,
        "page_size": fields.Integer,
        "total": fields.Integer,
        "results": fields.List(fields.Nested(post_model)),
    },
)


@post_nc.route("/")
class PostList(Resource):
    @jwt_guard
    @post_nc.expect(post_model)
    def post(self):
        """Create a new post"""
        user: User = User.find_by_email(get_jwt_identity())
        data = request.get_json()
        text = data.get("text", "")
        images = data.get("images", [])

        if not text and not images:
            return Response(
                json.dumps({"error": "A post must have text and/or images"}),
                status=400,
            )

        new_post = Post(text=text, images=images)
        new_post.save()
        relation = new_post.created_by.connect(user)
        response = json.dumps(
            {
                "post_uuid": new_post.uuid,
                "user_uuid": user.uuid,
                "text": new_post.text,
                "images": new_post.images,
                "created_at": new_post.created_at,
                "updated_at": new_post.updated_at,
                "created_by": {
                    "uuid": user.uuid,
                    "name": f"{user.first_name} {user.last_name}",
                    "profile_image": user.profile_image,
                    "title": user.title,
                },
            }
        )
        return Response(response, status=201, mimetype="application/json")


@post_nc.route("/<post_uuid>")
@post_nc.param("post_uuid", "Post UUID")
class PostDetail(Resource):
    @jwt_guard
    def get(self, post_uuid):
        """Get a specific post by UUID"""
        post: Post = Post.find_by_uuid(post_uuid)
        if not post:
            return Response(
                json.dumps({"error": "Post not found"}), status=404
            )

        comments_count = post.get_comments_count()
        likes_count = post.get_likes_count()

        user = post.created_by.all()[0]
        post_data = {
            "uuid": post.uuid,
            "text": post.text,
            "images": post.images,
            "created_at": post.created_at,
            "updated_at": post.updated_at,
            "created_by": {
                "uuid": user.uuid,
                "name": f"{user.first_name} {user.last_name}",
                "profile_image": user.profile_image,
                "title": "user.title",
            },
            "comments_count": comments_count,
            "likes_count": likes_count,
        }
        return Response(json.dumps(post_data), status=200)

    @jwt_guard
    @post_nc.expect(post_model)
    def put(self, post_uuid):
        """Edit a specific post by UUID"""
        post: Post = Post.find_by_uuid(post_uuid)
        if not post:
            return Response(
                json.dumps({"error": "Post not found"}), status=404
            )

        user: User = User.find_by_email(get_jwt_identity())

        if user.uuid != (post.created_by.all()[0]).uuid:
            return Response(json.dumps({"error": "Not allowed"}), status=403)

        data = request.get_json()
        new_text = data.get("text", "")
        new_images = data.get("images", [])

        if not new_text and not new_images:
            return Response(
                json.dumps({"error": "Must contain text or/and images"}),
                status=400,
            )
        if new_text:
            post.text = new_text
        if new_images:
            post.images = new_images
        post.save()
        return Response(
            json.dumps({"message": "Post edited successfully"}), status=200
        )

    @jwt_guard
    def delete(self, post_uuid):
        """Delete a specific post by UUID"""
        post: Post = Post.find_by_uuid(post_uuid)
        user: User = User.find_by_email(get_jwt_identity())

        if not post:
            return Response(
                json.dumps({"error": "Post not found"}), status=404
            )

        if user.uuid != (post.created_by.all()[0]).uuid:
            return Response(json.dumps({"error": "Not allowed"}), status=403)

        post.delete()
        return Response(
            json.dumps({"message": "Post deleted successfully"}), 200
        )


@post_nc.route("/<post_uuid>/comments")
@post_nc.doc(
    params={
        "page": "Page number (default 1)",
        "page_size": "Number of comments per page (default 10)",
    }
)
class PostComments(Resource):
    @jwt_guard
    def get(self, post_uuid):
        post = Post.find_by_uuid(post_uuid)
        if not post:
            return Response(
                json.dumps({"error": "Post not found"}), status=404
            )

        page = int(request.args.get("page", 1))
        page_size = int(request.args.get("page_size", 10))

        from app.models.comment import Comment

        data = Comment.get_comments(
            post_uuid=post_uuid, page=page, page_size=page_size
        )

        comments_list = []
        for comment in data["results"]:
            creator = comment._creator
            comments_list.append(
                {
                    "uuid": comment.uuid,
                    "text": comment.text,
                    "created_at": str(comment.created_at),
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
            "total": data["total"],
            "results": comments_list,
        }

        return Response(json.dumps(response), status=200)


@post_nc.route("/<post_uuid>/like")
class PostLike(Resource):
    @jwt_guard
    def post(self, post_uuid):
        user = User.find_by_email(get_jwt_identity())
        post = Post.find_by_uuid(post_uuid)
        if not post:
            return Response(
                json.dumps({"error": "Post not found."}), status=404
            )

        if user.likes.is_connected(post):
            return Response(
                json.dumps({"message": "You have already liked this post."}),
                status=200,
            )
        else:
            user.likes.connect(post)
            return Response(
                json.dumps({"message": "Post liked successfully."}), status=201
            )

    @jwt_guard
    def delete(self, post_uuid):
        """Unlike a post"""
        user = User.find_by_email(get_jwt_identity())
        post = Post.find_by_uuid(post_uuid)
        if not post:
            return Response(
                json.dumps({"error": "Post not found."}), status=404
            )

        if not user.likes.is_connected(post):
            return Response(
                json.dumps({"message": "You haven't liked this post yet."}),
                status=200,
            )

        if user.likes.is_connected(post):
            user.likes.disconnect(post)

        return Response(
            json.dumps({"message": "Post unliked successfully."}), status=200
        )


@post_nc.route("/my-posts")
@post_nc.doc(
    params={
        "page": "Page number (default 1)",
        "page_size": "Number of comments per page (default 10)",
    },
    responses={
        200: ("Success", paginated_posts_model),
        401: "Unauthorized",
    },
)
class MyPosts(Resource):
    @jwt_guard
    def get(self):
        user = User.find_by_email(get_jwt_identity())
        page = int(request.args.get("page", 1))
        page_size = int(request.args.get("page_size", 10))

        data = User.get_user_posts(user.uuid, user.uuid, page, page_size)

        posts_list = []
        for post in data["results"]:
            creator = post._creator
            posts_list.append(
                {
                    "uuid": post.uuid,
                    "text": post.text,
                    "images": post.images,
                    "created_at": str(post.created_at),
                    "created_by": {
                        "uuid": creator["uuid"],
                        "name": f"{creator['first_name']} {creator['last_name']}",
                        "profile_image": creator.get("profile_image"),
                        "title": creator.get("title"),
                    },
                    "comments_count": getattr(post, "_comments_count", 0),
                    "likes_count": getattr(post, "_likes_count", 0),
                    "liked": getattr(post, "liked", False),
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
        )


@post_nc.route("/following-posts")
class FollowingPosts(Resource):
    @jwt_guard
    def get(self):
        user = User.find_by_email(get_jwt_identity())
        page = int(request.args.get("page", 1))
        page_size = int(request.args.get("page_size", 10))

        data = user.get_posts_from_following(page=page, page_size=page_size)

        posts_list = []
        for post in data["results"]:
            creator = post._creator
            posts_list.append(
                {
                    "uuid": post.uuid,
                    "text": post.text,
                    "images": post.images,
                    "created_at": str(post.created_at),
                    "created_by": {
                        "uuid": creator["uuid"],
                        "name": f"{creator['first_name']} {creator['last_name']}",
                        "profile_image": creator.get("profile_image"),
                        "title": creator.get("title"),
                    },
                    "comments_count": getattr(post, "_comments_count", 0),
                    "likes_count": getattr(post, "_likes_count", 0),
                    "liked": getattr(post, "_liked", False),
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
        )


@post_nc.route("/suggested")
@post_nc.doc(
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
class Suggested(Resource):
    @jwt_guard
    def get(self):
        user = User.find_by_email(get_jwt_identity())

        page = int(request.args.get("page", 1))
        page_size = int(request.args.get("page_size", 10))

        data = user.get_posts_from_second_degree_connections(
            page=page, page_size=page_size
        )

        posts_list = []
        for post in data["results"]:
            creator = post._creator
            posts_list.append(
                {
                    "uuid": post.uuid,
                    "text": post.text,
                    "images": post.images,
                    "created_at": str(post.created_at),
                    "updated_at": str(post.updated_at),
                    "created_by": {
                        "uuid": creator["uuid"],
                        "name": f"{creator['first_name']} {creator['last_name']}",
                        "profile_image": creator.get("profile_image"),
                        "title": creator.get("title"),
                    },
                    "comments_count": getattr(post, "_comments_count", 0),
                    "likes_count": getattr(post, "_likes_count", 0),
                    "liked": getattr(post, "_liked", False),
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
