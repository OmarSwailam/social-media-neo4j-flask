from neomodel import (
    StructuredNode,
    StringProperty,
    UniqueIdProperty,
    RelationshipTo,
    RelationshipFrom,
)


class User(StructuredNode):
    uuid = UniqueIdProperty()
    first_name = StringProperty(required=True)
    last_name = StringProperty(required=True)
    email = StringProperty(required=True, unique_index=True)
    password = StringProperty(required=True)

    following = RelationshipTo("User", "FOLLOWS")
    followers = RelationshipFrom("User", "FOLLOWS")

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
        return [rel.start_node() for rel in self.followers.all()]

    def get_following(self):
        return [rel.end_node() for rel in self.follows.all()]

    def get_followers_count(self):
        return len(self.followers)

    def get_following_count(self):
        return len(self.following)
