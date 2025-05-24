from neomodel import (
    DateTimeProperty,
    RelationshipFrom,
    RelationshipTo,
    StringProperty,
    StructuredNode,
    UniqueIdProperty,
    db,
)

from app.models.post import Post
from app.models.user import User


class Comment(StructuredNode):
    uuid = UniqueIdProperty()
    text = StringProperty(required=True)
    created_at = DateTimeProperty(default_now=True)

    created_by = RelationshipFrom(User, "CREATED_COMMENT")
    liked_by = RelationshipFrom("User", "LIKES")

    on_post = RelationshipTo(Post, "ON")
    reply_to = RelationshipTo("Comment", "REPLY_TO")

    @classmethod
    def get_comments(
        cls, *, post_uuid=None, comment_uuid=None, page=1, page_size=10
    ):
        if not post_uuid and not comment_uuid:
            raise ValueError(
                "Either post_uuid or comment_uuid must be provided."
            )

        skip = (page - 1) * page_size

        match_clause = ""
        params = {"skip": skip, "limit": page_size}

        if post_uuid:
            match_clause = "MATCH (p:Post {uuid: $uuid})<-[:ON]-(c:Comment)"
            params["uuid"] = post_uuid
        elif comment_uuid:
            match_clause = (
                "MATCH (parent:Comment {uuid: $uuid})<-[:REPLY_TO]-(c:Comment)"
            )
            params["uuid"] = comment_uuid

        query = f"""
        {match_clause}
        WITH COLLECT(c) AS all_comments, SIZE(COLLECT(c)) AS total
        RETURN all_comments[$skip..$skip+$limit] AS paginated_comments, total
        """

        results, _ = db.cypher_query(query, params)

        paginated_comments_raw = results[0][0]
        total = results[0][1]

        comments = [cls.inflate(comment) for comment in paginated_comments_raw]

        return {
            "page": page,
            "page_size": page_size,
            "total": total,
            "results": comments,
        }

    def get_replies(self):
        query = """
        MATCH (reply:Comment)-[:REPLY_TO]->(parent:Comment {uuid: $uuid})
        RETURN reply
        ORDER BY reply.created_at ASC
        """
        results, _ = db.cypher_query(query, {"uuid": self.uuid})
        return [Comment.inflate(r[0]) for r in results]

    def get_likes_count(self):
        query = """
        MATCH (c:Comment {uuid: $uuid})<-[:LIKES]-(:User)
        RETURN count(*) as like_count
        """
        result, _ = db.cypher_query(query, {'uuid': self.uuid})
        return result[0][0]