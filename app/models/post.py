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
        MATCH (p:Post {uuid: $post_uuid})
        OPTIONAL MATCH (p)<-[:CREATED]-(creator:User)
        OPTIONAL MATCH (p)<-[:COMMENTED_ON]-(:Comment)
        WITH p, creator, count(DISTINCT (p)<-[:COMMENTED_ON]-(:Comment)) AS comments_count
        OPTIONAL MATCH (p)<-[:LIKES]-(:User)
        WITH p, creator, comments_count, count(DISTINCT (p)<-[:LIKES]-(:User)) AS likes_count
        OPTIONAL MATCH (:User {uuid: $current_user_uuid})-[:LIKES]->(p)
        WITH p, creator, comments_count, likes_count, COUNT(*) > 0 AS liked
        RETURN p, creator, comments_count, likes_count, liked
        """

        results, _ = db.cypher_query(query, {
            "post_uuid": post_uuid,
            "current_user_uuid": current_user_uuid,
        })

        if not results:
            return None

        p_node, creator_node, comments_count, likes_count, liked = results[0]

        post = cls.inflate(p_node)
        creator = User.inflate(creator_node)

        setattr(post, "comments_count", comments_count)
        setattr(post, "likes_count", likes_count)
        setattr(post, "liked", liked)
        setattr(post, "_creator", creator)

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
        result, _ = db.cypher_query(query, {'uuid': self.uuid})
        return result[0][0]