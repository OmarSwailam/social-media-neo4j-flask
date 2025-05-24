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
    def find_by_uuid(cls, post_uuid):
        post = cls.nodes.get_or_none(uuid=post_uuid)
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