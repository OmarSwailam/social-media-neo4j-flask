from datetime import datetime

from neomodel import (
    DateTimeProperty,
    RelationshipFrom,
    RelationshipTo,
    StringProperty,
    StructuredNode,
    StructuredRel,
    UniqueIdProperty,
    db,
)


class Skill(StructuredNode):
    uuid = UniqueIdProperty()
    name = StringProperty(required=True)


class HasSkillRel(StructuredRel):
    created_at = DateTimeProperty(default_now=True)


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

    skills = RelationshipTo("Skill", "HAS_SKILL", model=HasSkillRel)

    def get_skills(self) -> list[str]:
        skill_nodes = self.skills.all()
        skill_pairs = []

        for skill in skill_nodes:
            rel = self.skills.relationship(skill)
            skill_pairs.append(
                (
                    skill.name,
                    rel.created_at if rel.created_at else datetime.min,
                )
            )

        sorted_skills = sorted(skill_pairs, key=lambda x: x[1], reverse=True)
        return [name for name, _ in sorted_skills]

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
        MATCH (target:User {uuid: $uuid})
        MATCH (follower:User)-[:FOLLOWS]->(target)
        OPTIONAL MATCH (follower)<-[:FOLLOWS]-(x)  // followers of follower
        WITH follower, COUNT(DISTINCT x) AS followers_count

        OPTIONAL MATCH (follower)-[:FOLLOWS]->(y)  // who follower is following
        WITH follower, followers_count, COUNT(DISTINCT y) AS following_count

        OPTIONAL MATCH (me:User {uuid: $current_user_uuid})
        OPTIONAL MATCH (me)-[:FOLLOWS]->(follower)
        WITH follower, followers_count, following_count, COUNT(*) > 0 AS is_following

        OPTIONAL MATCH (follower)-[:FOLLOWS]->(me)
        WITH follower, followers_count, following_count, is_following, COUNT(*) > 0 AS follows_me

        RETURN collect({
            user: follower,
            followers_count: followers_count,
            following_count: following_count,
            is_following: is_following,
            follows_me: follows_me
        })[$skip..$skip+$limit] AS paginated, COUNT(*) AS total
        """

        params = {
            "uuid": user_uuid,
            "current_user_uuid": self.uuid,
            "skip": skip,
            "limit": page_size,
        }
        results, _ = db.cypher_query(query, params)

        paginated_raw = results[0][0]
        total = results[0][1]

        followers = []
        for item in paginated_raw:
            user = User.inflate(item["user"])
            user._followers_count = item["followers_count"]
            user._following_count = item["following_count"]
            user._is_following = item["is_following"]
            user._follows_me = item["follows_me"]
            followers.append(user)

        return {
            "page": page,
            "page_size": page_size,
            "total": total,
            "results": followers,
        }

    def get_following(self, user_uuid, page=1, page_size=10):
        skip = (page - 1) * page_size

        query = """
        MATCH (source:User {uuid: $uuid})
        MATCH (source)-[:FOLLOWS]->(following:User)
        OPTIONAL MATCH (following)<-[:FOLLOWS]-(x)
        WITH following, COUNT(DISTINCT x) AS followers_count

        OPTIONAL MATCH (following)-[:FOLLOWS]->(y)
        WITH following, followers_count, COUNT(DISTINCT y) AS following_count

        OPTIONAL MATCH (me:User {uuid: $current_user_uuid})
        OPTIONAL MATCH (me)-[:FOLLOWS]->(following)
        WITH following, followers_count, following_count, COUNT(*) > 0 AS is_following

        OPTIONAL MATCH (following)-[:FOLLOWS]->(me)
        WITH following, followers_count, following_count, is_following, COUNT(*) > 0 AS follows_me

        RETURN collect({
            user: following,
            followers_count: followers_count,
            following_count: following_count,
            is_following: is_following,
            follows_me: follows_me
        })[$skip..$skip+$limit] AS paginated, COUNT(*) AS total
        """

        params = {
            "uuid": user_uuid,
            "current_user_uuid": self.uuid,
            "skip": skip,
            "limit": page_size,
        }
        results, _ = db.cypher_query(query, params)

        paginated_raw = results[0][0]
        total = results[0][1]

        following = []
        for item in paginated_raw:
            user = User.inflate(item["user"])
            user._followers_count = item["followers_count"]
            user._following_count = item["following_count"]
            user._is_following = item["is_following"]
            user._follows_me = item["follows_me"]
            following.append(user)

        return {
            "page": page,
            "page_size": page_size,
            "total": total,
            "results": following,
        }

    def get_followers_count(self):
        return len(self.followed_by)

    def get_following_count(self):
        return len(self.follows)

    def get_suggested_friends(self, page=1, page_size=10):
        skip = (page - 1) * page_size

        query = """
        MATCH (me:User {uuid: $user_uuid})

        OPTIONAL MATCH (me)-[:FOLLOWS]->(friend)-[:FOLLOWS]->(friend_of_friend)
        WHERE NOT (me)-[:FOLLOWS]->(friend_of_friend) 
        AND me <> friend_of_friend
        WITH me, COLLECT(DISTINCT {user: friend_of_friend, degree: 2}) AS second_degree

        OPTIONAL MATCH (me)-[:FOLLOWS]->()-[:FOLLOWS]->()-[:FOLLOWS]->(third_degree)
        WHERE NOT (me)-[:FOLLOWS]->(third_degree)
        AND me <> third_degree
        AND NOT third_degree IN [item IN second_degree | item.user]
        WITH me, second_degree, COLLECT(DISTINCT {user: third_degree, degree: 3}) AS third_degree

        WITH second_degree + third_degree AS all_suggestions
        UNWIND all_suggestions AS suggestion
        WITH suggestion
        WHERE suggestion.user IS NOT NULL

        WITH suggestion.user AS user, suggestion.degree AS degree
        OPTIONAL MATCH (user)-[:FOLLOWS]->(me)
        WITH user, degree, COUNT(*) > 0 AS follows_me

        ORDER BY degree ASC, user.first_name ASC
        WITH COLLECT({user: user, degree: degree, follows_me: follows_me}) AS all_suggestions
        RETURN all_suggestions[$skip..$skip+$limit] AS paginated_suggestions, SIZE(all_suggestions) AS total
        """

        results, _ = db.cypher_query(
            query, {"user_uuid": self.uuid, "skip": skip, "limit": page_size}
        )

        paginated_raw = results[0][0]
        total = results[0][1]

        suggested_users = []
        for item in paginated_raw:
            user = User.inflate(item["user"])
            suggested_users.append(
                {
                    "user": user,
                    "degree": item["degree"],
                    "follows_me": item["follows_me"],
                }
            )

        return {
            "page": page,
            "page_size": page_size,
            "total": total,
            "results": suggested_users,
        }

    @classmethod
    def get_user_posts(
        cls, user_uuid, current_user_uuid, page=1, page_size=10
    ):
        skip = (page - 1) * page_size

        query = """
        MATCH (u:User {uuid: $user_uuid})-[:CREATED_POST]->(p:Post)
        OPTIONAL MATCH (p)<-[:ON]-(c:Comment)
        OPTIONAL MATCH (p)<-[:LIKES]-(l:User)
        OPTIONAL MATCH (cu:User {uuid: $current_user_uuid}), (cu)-[cl:LIKES]->(p)
        WITH p, u, COUNT(DISTINCT c) AS comments_count, COUNT(DISTINCT l) AS likes_count, COUNT(cl) > 0 AS liked
        ORDER BY p.created_at DESC
        WITH COLLECT({
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
        }) AS all_posts, SIZE(COLLECT(p)) AS total
        RETURN all_posts[$skip..$skip+$limit] AS paginated_posts, total
        """

        results, _ = db.cypher_query(
            query,
            {
                "user_uuid": user_uuid,
                "current_user_uuid": current_user_uuid,
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
            post._liked = item["liked"]
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
        MATCH (me:User {uuid: $user_uuid})
        MATCH (creator:User)
        WHERE (me)-[:FOLLOWS]->(creator) OR creator.uuid = $user_uuid
        MATCH (post:Post)<-[:CREATED_POST]-(creator)
        OPTIONAL MATCH (post)<-[:ON]-(c:Comment)
        OPTIONAL MATCH (post)<-[:LIKES]-(l:User)
        OPTIONAL MATCH (me)-[ml:LIKES]->(post)
        WITH post, creator, COUNT(DISTINCT c) AS comments_count, COUNT(DISTINCT l) AS likes_count, COUNT(ml) > 0 AS liked
        ORDER BY post.created_at DESC
        WITH COLLECT({
            post: post, 
            comments_count: comments_count, 
            likes_count: likes_count,
            liked: liked,
            creator: {
                uuid: creator.uuid,
                first_name: creator.first_name,
                last_name: creator.last_name,
                profile_image: creator.profile_image,
                title: creator.title
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
            post._liked = item["liked"]
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
        OPTIONAL MATCH (me)-[ml:LIKES]->(post)
        WITH post, friend_of_friend, COUNT(DISTINCT c) AS comments_count, COUNT(DISTINCT l) AS likes_count, COUNT(ml) > 0 AS liked
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
            post._liked = item["liked"]
            posts.append(post)

        return {
            "page": page,
            "page_size": page_size,
            "total": total,
            "results": posts,
        }

    def get_feed(self, page=1, page_size=10):
        skip = (page - 1) * page_size

        query = """
        MATCH (me:User {uuid: $user_uuid})

        CALL {
            WITH me
            MATCH (creator:User)
            OPTIONAL MATCH (me)-[:FOLLOWS]->(f1:User)-[:FOLLOWS]->(creator)
            OPTIONAL MATCH (me)-[:FOLLOWS]->(creator)
            WITH creator, me,
                CASE
                    WHEN creator.uuid = me.uuid THEN 99
                    WHEN (me)-[:FOLLOWS]->(creator) THEN 100
                    WHEN (me)-[:FOLLOWS]->(:User)-[:FOLLOWS]->(creator)
                        AND NOT (me)-[:FOLLOWS]->(creator)
                        AND creator <> me THEN 98
                    WHEN f1 IS NOT NULL AND creator <> me
                        AND NOT (me)-[:FOLLOWS]->(creator)
                        AND NOT (me)-[:FOLLOWS]->(:User)-[:FOLLOWS]->(creator) THEN 90
                    ELSE NULL
                END AS relationship_score
            WHERE relationship_score IS NOT NULL
            RETURN creator.uuid AS creator_uuid, relationship_score
        }

        MATCH (creator:User {uuid: creator_uuid})
        MATCH (post:Post)<-[:CREATED_POST]-(creator)
        OPTIONAL MATCH (post)<-[:ON]-(c:Comment)
        OPTIONAL MATCH (post)<-[:LIKES]-(l:User)
        OPTIONAL MATCH (me)-[ml:LIKES]->(post)

        WITH
            post,
            creator,
            relationship_score,
            COUNT(DISTINCT c) AS comments_count,
            COUNT(DISTINCT l) AS likes_count,
            COUNT(ml) > 0 AS liked,
            datetime().epochSeconds - post.created_at AS age_seconds

        WITH
            post,
            creator,
            relationship_score,
            comments_count,
            likes_count,
            liked,
            age_seconds,
            toFloat(relationship_score) - (toFloat(age_seconds) / 120.0) AS priority

        ORDER BY priority DESC
        SKIP $skip
        LIMIT $page_size

        RETURN post, creator, comments_count, likes_count, liked, priority
        """

        results, _ = db.cypher_query(
            query,
            {"user_uuid": self.uuid, "skip": skip, "page_size": page_size},
        )

        from .post import Post

        posts = []
        for row in results:
            (
                post_data,
                creator_data,
                comments_count,
                likes_count,
                liked,
                priority,
            ) = row

            post = Post.inflate(post_data)
            post._comments_count = comments_count
            post._likes_count = likes_count
            post._creator = {
                "uuid": creator_data.get("uuid"),
                "first_name": creator_data.get("first_name"),
                "last_name": creator_data.get("last_name"),
                "profile_image": creator_data.get("profile_image"),
                "title": creator_data.get("title"),
            }
            post._liked = liked
            post._priority = priority
            posts.append(post)

        count_query = """
        MATCH (me:User {uuid: $user_uuid})

        CALL {
            WITH me
            MATCH (creator:User)
            OPTIONAL MATCH (me)-[:FOLLOWS]->(f1:User)-[:FOLLOWS]->(creator)
            OPTIONAL MATCH (me)-[:FOLLOWS]->(creator)
            WITH creator, me,
                CASE
                    WHEN creator.uuid = me.uuid THEN 99
                    WHEN (me)-[:FOLLOWS]->(creator) THEN 100
                    WHEN (me)-[:FOLLOWS]->(:User)-[:FOLLOWS]->(creator)
                        AND NOT (me)-[:FOLLOWS]->(creator)
                        AND creator <> me THEN 98
                    WHEN f1 IS NOT NULL AND creator <> me
                        AND NOT (me)-[:FOLLOWS]->(creator)
                        AND NOT (me)-[:FOLLOWS]->(:User)-[:FOLLOWS]->(creator) THEN 90
                    ELSE NULL
                END AS relationship_score
            WHERE relationship_score IS NOT NULL
            RETURN creator.uuid AS creator_uuid
        }

        MATCH (creator:User {uuid: creator_uuid})
        MATCH (post:Post)<-[:CREATED_POST]-(creator)
        RETURN COUNT(post) AS total
        """

        count_result, _ = db.cypher_query(
            count_query,
            {"user_uuid": self.uuid},
        )
        total = count_result[0][0]

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
