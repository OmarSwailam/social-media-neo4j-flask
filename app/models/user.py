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
    profile_image = StringProperty()

    follows = RelationshipTo("User", "FOLLOWS")
    followed_by = RelationshipFrom("User", "FOLLOWS")

    @classmethod
    def find_by_email(cls, email):
        user = cls.nodes.get_or_none(email=email)
        return user

    @classmethod
    def find_by_uuid(cls, uuid):
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

    def get_users_list(self, page=1, page_size=10):
        skip = (page - 1) * page_size

        query = """
        MATCH (u:User)
        WHERE u.uuid <> $current_uuid
        OPTIONAL MATCH (me:User {uuid: $current_uuid})
        OPTIONAL MATCH (me)-[f:FOLLOWS]->(u)
        OPTIONAL MATCH (u)-[f2:FOLLOWS]->(me)
        WITH u, count(f) > 0 AS is_following, count(f2) > 0 AS follows_me
        ORDER BY u.first_name
        WITH collect({user: u, is_following: is_following, follows_me: follows_me}) AS all_users
        RETURN all_users[$skip..$skip+$limit] AS paginated, size(all_users) AS total
        """

        params = {"current_uuid": self.uuid, "skip": skip, "limit": page_size}
        results, _ = db.cypher_query(query, params)

        paginated_raw = results[0][0]
        total = results[0][1]

        users = []
        for item in paginated_raw:
            user_node = item["user"]
            user = User.inflate(user_node)
            users.append(
                {
                    "uuid": user.uuid,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "email": user.email,
                    "profile_image": user.profile_image,
                    "is_following": item["is_following"],
                    "follows_me": item["follows_me"],
                }
            )

        return {
            "page": page,
            "page_size": page_size,
            "total": total,
            "results": users,
        }

    def get_followers(self, user_uuid, page=1, page_size=10):
        skip = (page - 1) * page_size

        query = """
        MATCH (u:User {uuid: $uuid})<-[:FOLLOWS]-(follower:User)
        WITH collect(follower) AS all_followers
        RETURN all_followers[$skip..$skip+$limit] AS paginated, size(all_followers) AS total
        """

        params = {"uuid": user_uuid, "skip": skip, "limit": page_size}
        results, _ = db.cypher_query(query, params)

        paginated_raw = results[0][0]
        total = results[0][1]

        results = [User.inflate(node) for node in paginated_raw]
        return {
            "page": page,
            "page_size": page_size,
            "total": total,
            "results": results,
        }

    def get_following(self, user_uuid, page=1, page_size=10):
        skip = (page - 1) * page_size

        query = """
        MATCH (u:User {uuid: $uuid})-[:FOLLOWS]->(following:User)
        WITH collect(following) AS all_following
        RETURN all_following[$skip..$skip+$limit] AS paginated, size(all_following) AS total
        """

        params = {"uuid": user_uuid, "skip": skip, "limit": page_size}
        results, _ = db.cypher_query(query, params)

        paginated_raw = results[0][0]
        total = results[0][1]

        results = [User.inflate(node) for node in paginated_raw]
        return {
            "page": page,
            "page_size": page_size,
            "total": total,
            "results": results,
        }

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

    def get_posts_from_second_degree_connections(self, page=1, page_size=10):
        skip = (page - 1) * page_size
        query = """
        MATCH (me:User {uuid: $user_uuid})
        MATCH (me)-[:FOLLOWS]->(friend:User)-[:FOLLOWS]->(friend_of_friend:User)
        WHERE NOT (me)-[:FOLLOWS]->(friend_of_friend) 
        AND me <> friend_of_friend
        MATCH (post:Post)<-[:CREATED_POST]-(friend_of_friend)
        OPTIONAL MATCH (post)<-[:ON]-(c:Comment)
        WITH post, COUNT(c) AS comments_count
        ORDER BY post.created_at DESC
        WITH COLLECT({post: post, comments_count: comments_count}) AS all_posts, SIZE(COLLECT(post)) AS total
        RETURN all_posts[$skip..$skip+$limit] AS paginated_posts, total
        """

        results, _ = db.cypher_query(
            query,
            {"user_uuid": self.uuid, "skip": skip, "limit": page_size},
        )

        paginated_raw = results[0][0]
        total = results[0][1]

        from .post import Post

        posts = []
        for item in paginated_raw:
            post = Post.inflate(item["post"])
            post._comments_count = item["comments_count"]
            posts.append(post)

        return {
            "page": page,
            "page_size": page_size,
            "total": total,
            "results": posts,
        }

    @classmethod
    def get_user_posts(cls, user_uuid, page=1, page_size=10):
        skip = (page - 1) * page_size

        query = """
        MATCH (u:User {uuid: $user_uuid})-[:CREATED_POST]->(p:Post)
        OPTIONAL MATCH (p)<-[:ON]-(c:Comment)
        WITH p, count(c) AS comments_count
        ORDER BY p.created_at DESC
        WITH COLLECT({post: p, comments_count: comments_count}) AS all_posts, SIZE(COLLECT(p)) AS total
        RETURN all_posts[$skip..$skip+$limit] AS paginated_posts, total
        """

        results, _ = db.cypher_query(
            query,
            {
                "user_uuid": user_uuid,
                "skip": skip,
                "limit": page_size,
            },
        )

        paginated_raw = results[0][0]
        total = results[0][1]

        from .post import Post

        posts = []
        for item in paginated_raw:
            post = Post.inflate(item["post"])
            post._comments_count = item["comments_count"]
            posts.append(post)

        return {
            "page": page,
            "page_size": page_size,
            "total": total,
            "results": posts,
        }

    def get_posts_from_following(self, page=1, page_size=10):
        skip = (page - 1) * page_size

        query = """
        MATCH (me:User {uuid: $user_uuid})-[:FOLLOWS]->(friend:User)
        MATCH (post:Post)<-[:CREATED_POST]-(friend)
        OPTIONAL MATCH (post)<-[:ON]-(c:Comment)
        WITH post, count(c) AS comments_count
        ORDER BY post.created_at DESC
        WITH COLLECT({post: post, comments_count: comments_count}) AS all_posts, SIZE(COLLECT(post)) AS total
        RETURN all_posts[$skip..$skip+$limit] AS paginated_posts, total
        """

        results, meta = db.cypher_query(
            query,
            {
                "user_uuid": self.uuid,
                "skip": skip,
                "limit": page_size,
            },
        )

        paginated_raw = results[0][0]
        total = results[0][1]

        from .post import Post

        posts = []
        for item in paginated_raw:
            post = Post.inflate(item["post"])
            post._comments_count = item["comments_count"]
            posts.append(post)

        return {
            "page": page,
            "page_size": page_size,
            "total": total,
            "results": posts,
        }
