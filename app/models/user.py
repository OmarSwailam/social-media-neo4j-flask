from neomodel import (
    RelationshipFrom,
    RelationshipTo,
    StringProperty,
    StructuredNode,
    UniqueIdProperty,
    db,
)


class User(StructuredNode):
    uuid = UniqueIdProperty()
    first_name = StringProperty(required=True)
    last_name = StringProperty(required=True)
    email = StringProperty(required=True, unique_index=True)
    password = StringProperty(required=True)

    follows = RelationshipTo("User", "FOLLOWS")
    followed_by = RelationshipFrom("User", "FOLLOWS")

    @classmethod
    def find_by_email(cls, email):
        user = cls.nodes.get_or_none(email=email)
        return user

    @classmethod
    def find_by_id(cls, uuid):
        user = cls.nodes.get_or_none(uuid=uuid)
        return user

    def is_following(self, user):
        return self.follows.is_connected(user)

    def follow(self, user_to_follow):
        if self != user_to_follow and not self.is_following(user_to_follow):
            self.follows.connect(user_to_follow)
            return True
        return False

    def unfollow(self, user_to_unfollow):
        if self != user_to_unfollow and self.is_following(user_to_unfollow):
            self.follows.disconnect(user_to_unfollow)
            return True
        return False

    def get_followers(self):
        return self.followed_by.all()

    def get_following(self):
        return self.follows.all()

    def get_followers_count(self):
        return len(self.followed_by)

    def get_following_count(self):
        return len(self.follows)

    def get_suggested_friends(self):
        query = """
        MATCH (me:User {uuid: $user_uuid})
        
        // +2 connections (friends of friends)
        OPTIONAL MATCH (me)-[:FOLLOWS]->(friend)-[:FOLLOWS]->(friend_of_friend)
        WHERE NOT (me)-[:FOLLOWS]->(friend_of_friend) 
        AND me <> friend_of_friend
        WITH me, COLLECT(DISTINCT {user: friend_of_friend, degree: 2}) as second_degree
        
        // +3 connections (friends of friends of friends)
        OPTIONAL MATCH (me)-[:FOLLOWS]->()-[:FOLLOWS]->()-[:FOLLOWS]->(third_degree)
        WHERE NOT (me)-[:FOLLOWS]->(third_degree) 
        AND me <> third_degree
        AND NOT third_degree IN second_degree
        WITH me, second_degree, COLLECT(DISTINCT {user: third_degree, degree: 3}) as third_degree
        
        // combine
        WITH second_degree + third_degree as all_suggestions
        UNWIND all_suggestions as suggestion
        WITH suggestion
        WHERE suggestion.user IS NOT NULL
        RETURN suggestion.user as user, suggestion.degree as degree
        ORDER BY degree ASC, user.first_name ASC
        """

        results, meta = db.cypher_query(query, {"user_uuid": self.uuid})

        suggested_users = []
        for record in results:
            user_data = record[0]
            degree = record[1]

            user = User.inflate(user_data)
            suggested_users.append({"user": user, "degree": degree})

        return suggested_users

    def get_posts_from_second_degree_connections(self):
        query = """
        MATCH (me:User {uuid: $user_uuid})
        MATCH (me)-[:FOLLOWS]->(friend)-[:FOLLOWS]->(friend_of_friend)
        WHERE NOT (me)-[:FOLLOWS]->(friend_of_friend) 
        AND me <> friend_of_friend
        MATCH (post:Post)<-[:CREATED_POST]-(friend_of_friend)
        RETURN DISTINCT post
        ORDER BY post.created_at DESC
        """

        results, meta = db.cypher_query(query, {"user_uuid": self.uuid})

        from .post import Post

        posts = []
        for record in results:
            post_data = record[0]
            post = Post.inflate(post_data)
            posts.append(post)

        return posts
