from neomodel import (
    ArrayProperty,
    DateTimeProperty,
    RelationshipFrom,
    StringProperty,
    StructuredNode,
    UniqueIdProperty,
    db,
)

from .user import User


class Post(StructuredNode):
    uuid = UniqueIdProperty()
    text = StringProperty(required=True)
    images = ArrayProperty(StringProperty())
    created_at = DateTimeProperty(default_now=True)
    updated_at = DateTimeProperty(default_now=True)

    created_by = RelationshipFrom(User, "CREATED_POST")
    liked_by = RelationshipFrom("User", "LIKES")

    @classmethod
    def find_by_uuid(cls, post_uuid: str, current_user_uuid: str):
        query = """
        MATCH (p:Post {uuid: $post_uuid})<-[:CREATED_POST]-(u:User)
        OPTIONAL MATCH (p)<-[:ON]-(c:Comment)
        OPTIONAL MATCH (p)<-[:LIKES]-(l:User)
        OPTIONAL MATCH (cu:User {uuid: $current_user_uuid}), (cu)-[cl:LIKES]->(p)
        WITH p, u, COUNT(DISTINCT c) AS comments_count, COUNT(DISTINCT l) AS likes_count, COUNT(cl) > 0 AS liked
        RETURN {
            post: p,
            comments_count: comments_count,
            likes_count: likes_count,
            liked: liked,
            creator: {
                uuid: u.uuid,
                first_name: u.first_name,
                last_name: u.last_name,
                profile_image: u.profile_image,
                title: u.title
            }
        } AS result
        """

        results, _ = db.cypher_query(
            query,
            {
                "post_uuid": post_uuid,
                "current_user_uuid": current_user_uuid,
            },
        )

        if not results:
            return None

        row = results[0][0]
        if not row or "post" not in row:
            return None

        post = Post.inflate(row["post"])
        post._comments_count = row["comments_count"]
        post._likes_count = row["likes_count"]
        post._liked = row["liked"]
        post._creator = row["creator"]

        return post

    @classmethod
    def get_all_posts(cls, skip=0, limit=10):
        all_posts = cls.nodes.order_by("-created_at")
        return all_posts[skip : skip + limit]

    def get_comments_count(self):
        query = """
        MATCH (p:Post {uuid: $uuid})<-[:ON]-(c:Comment)
        RETURN COUNT(c) AS comments_count
        """
        results, _ = db.cypher_query(query, {"uuid": self.uuid})
        return results[0][0] or 0

    def get_likes_count(self):
        query = """
        MATCH (p:Post {uuid: $uuid})<-[:LIKES]-(:User)
        RETURN count(*) as like_count
        """
        result, _ = db.cypher_query(query, {"uuid": self.uuid})
        return result[0][0]
