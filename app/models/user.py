from neomodel import (
    RelationshipFrom,
    RelationshipTo,
    StringProperty,
    StructuredNode,
    UniqueIdProperty,
    db,
)


class Skill(StructuredNode):
    uuid = UniqueIdProperty()
    name = StringProperty(required=True)


class User(StructuredNode):
    uuid = UniqueIdProperty()
    first_name = StringProperty(required=True)
    last_name = StringProperty(required=True)
    email = StringProperty(required=True, unique_index=True)
    password = StringProperty(required=True)
    title = StringProperty()
    profile_image = StringProperty()

    follows = RelationshipTo("User", "FOLLOWS")
    followed_by = RelationshipFrom("User", "FOLLOWS")

    likes = RelationshipTo("app.models.post.Post", "LIKES")
    likes_comment = RelationshipTo("app.models.comment.Comment", "LIKES")

    skills = RelationshipTo("Skill", "HAS_SKILL")

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

    def get_users_list(self, page=1, page_size=10, title=None, skills=None):
        skip = (page - 1) * page_size

        match_clause = """
        MATCH (u:User)
        WHERE u.uuid <> $current_uuid
        """

        params = {
            "current_uuid": self.uuid,
            "skip": skip,
            "limit": page_size,
        }

        where_clauses = []

        if title:
            where_clauses.append("u.title = $title")
            params["title"] = title

        if skills:
            match_clause += "\nOPTIONAL MATCH (u)-[:HAS_SKILL]->(s:Skill)"
            where_clauses.append("s.name IN $skills")
            params["skills"] = skills

        if where_clauses:
            match_clause += "\nAND " + " AND ".join(where_clauses)

        query = f"""
        {match_clause}
        OPTIONAL MATCH (me:User {{uuid: $current_uuid}})
        OPTIONAL MATCH (me)-[f:FOLLOWS]->(u)
        OPTIONAL MATCH (u)-[f2:FOLLOWS]->(me)
        OPTIONAL MATCH (u)-[:HAS_SKILL]->(skill:Skill)
        WITH u, collect(DISTINCT skill.name) AS skill_names, count(f) > 0 AS is_following, count(f2) > 0 AS follows_me
        ORDER BY u.first_name
        WITH collect({{
            user: u,
            is_following: is_following,
            follows_me: follows_me,
            skills: skill_names
        }}) AS all_users
        RETURN all_users[$skip..$skip+$limit] AS paginated, size(all_users) AS total
        """

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
                    "title": user.title,
                    "profile_image": user.profile_image,
                    "is_following": item["is_following"],
                    "follows_me": item["follows_me"],
                    "skills": item["skills"],
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

        // Check if the suggested user follows me
        OPTIONAL MATCH (user)-[:FOLLOWS]->(me)
        WITH user, degree, COUNT(*) > 0 AS follows_me

        RETURN suggestion.user as user, suggestion.degree as degree
        ORDER BY degree ASC, user.first_name ASC
        """

        results, meta = db.cypher_query(query, {"user_uuid": self.uuid})

        suggested_users = []
        for record in results:
            user_data = record[0]
            degree = record[1]
            follows_me = record[2]

            user = User.inflate(user_data)
            suggested_users.append(
                {"user": user, "degree": degree, "follows_me": follows_me}
            )

        return suggested_users

    @classmethod
    def get_user_posts(cls, user_uuid, page=1, page_size=10):
        skip = (page - 1) * page_size

        query = """
        MATCH (u:User {uuid: $user_uuid})-[:CREATED_POST]->(p:Post)
        OPTIONAL MATCH (p)<-[:ON]-(c:Comment)
        OPTIONAL MATCH (p)<-[:LIKES]-(l:User)
        WITH p, u, COUNT(DISTINCT c) AS comments_count, COUNT(DISTINCT l) AS likes_count
        ORDER BY p.created_at DESC
        WITH COLLECT({
            post: p, 
            comments_count: comments_count, 
            likes_count: likes_count,
            creator: {
                uuid: u.uuid,
                first_name: u.first_name,
                last_name: u.last_name,
                profile_image: u.profile_image,
                title: u.title
            }
        }) AS all_posts, SIZE(COLLECT(p)) AS total
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
            post._likes_count = item["likes_count"]
            post._creator = item["creator"]
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
        OPTIONAL MATCH (post)<-[:LIKES]-(l:User)
        WITH post, u, COUNT(DISTINCT c) AS comments_count, COUNT(DISTINCT l) AS likes_count
        ORDER BY post.created_at DESC
        WITH COLLECT({
            post: post, 
            comments_count: comments_count, 
            likes_count: likes_count,
            creator: {
                uuid: friend.uuid,
                first_name: friend.first_name,
                last_name: friend.last_name,
                profile_image: friend.profile_image,
                title: friend.title
            }
        }) AS all_posts, SIZE(COLLECT(post)) AS total
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
            post._likes_count = item["likes_count"]
            post._creator = item["creator"]
            posts.append(post)

        return {
            "page": page,
            "page_size": page_size,
            "total": total,
            "results": posts,
        }

    def get_posts_from_second_degree_connections(self, page=1, page_size=10):
        skip = (page - 1) * page_size
        query = """
        MATCH (me:User {uuid: $user_uuid})
        MATCH (me)-[:FOLLOWS]->(friend:User)-[:FOLLOWS]->(friend_of_friend:User)
        WHERE NOT (me)-[:FOLLOWS]->(friend_of_friend) AND me <> friend_of_friend
        MATCH (post:Post)<-[:CREATED_POST]-(friend_of_friend)
        OPTIONAL MATCH (post)<-[:ON]-(c:Comment)
        OPTIONAL MATCH (post)<-[:LIKES]-(l:User)
        WITH post, friend_of_friend, COUNT(DISTINCT c) AS comments_count, COUNT(DISTINCT l) AS likes_count
        ORDER BY post.created_at DESC
        WITH COLLECT({
            post: post, 
            comments_count: comments_count, 
            likes_count: likes_count,
            creator: {
                uuid: friend_of_friend.uuid,
                first_name: friend_of_friend.first_name,
                last_name: friend_of_friend.last_name,
                profile_image: friend_of_friend.profile_image,
                title: friend_of_friend.title
            }
        }) AS all_posts, SIZE(COLLECT(post)) AS total
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
            post._likes_count = item["likes_count"]
            post._creator = item["creator"]
            posts.append(post)

        return {
            "page": page,
            "page_size": page_size,
            "total": total,
            "results": posts,
        }


def user_to_dict(user) -> dict:
    return {
        "uuid": user.uuid,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "title": user.title,
        "email": user.email,
        "followers_count": user.get_followers_count(),
        "following_count": user.get_following_count(),
        "profile_image": user.profile_image,
        "skills": [skill.name for skill in user.skills.all()],
    }
