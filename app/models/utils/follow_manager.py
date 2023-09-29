from py2neo import Relationship, Node
from app import graph


class FollowManager:
    @classmethod
    def follow_user(cls, follower_id, followed_id):
        follower_node = graph.nodes.match("User", uuid=follower_id).first()
        followed_node = graph.nodes.match("User", uuid=followed_id).first()

        if not follower_node or not followed_node:
            return False

        if not graph.match((follower_node, followed_node), r_type="FOLLOWS").first():
            follows_relation = Relationship(follower_node, "FOLLOWS", followed_node)
            graph.create(follows_relation)

        return True

    @classmethod
    def unfollow_user(cls, follower_id, followed_id):
        follower_node = graph.nodes.match("User", uuid=follower_id).first()
        followed_node = graph.nodes.match("User", uuid=followed_id).first()

        if not follower_node or not followed_node:
            return False

        follows_relation = graph.match(
            (follower_node, followed_node), r_type="FOLLOWS"
        ).first()
        if follows_relation:
            graph.delete(follows_relation)

        return True

    @classmethod
    def get_followers(cls, user_id):
        user_node = graph.nodes.match("User", uuid=user_id).first()

        if not user_node:
            return []

        followers = graph.match((None, user_node), r_type="FOLLOWS")
        return [follower.start_node() for follower in followers]

    @classmethod
    def get_following(cls, user_id):
        user_node = graph.nodes.match("User", uuid=user_id).first()

        if not user_node:
            return []

        following = graph.match((user_node, None), r_type="FOLLOWS")
        return [followed.end_node() for followed in following]
