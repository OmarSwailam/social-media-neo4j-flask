import datetime
from neomodel import (
    StructuredNode,
    UniqueIdProperty,
    StringProperty,
    ArrayProperty,
    DateTimeProperty,
    RelationshipTo,
)
from .user import User


class Post(StructuredNode):
    uuid = UniqueIdProperty()
    text = StringProperty(required=True)
    images = ArrayProperty(StringProperty())
    created_at = DateTimeProperty(default_now=True)
    updated_at = DateTimeProperty(default_now=True)

    user = RelationshipTo(User, "POSTED_BY")

    def create(self, user_uuid):
        user = User.nodes.get(uuid=user_uuid)
        self.posted_by.connect(user)
        self.save()

    def edit(self, new_text, new_images):
        if new_text:
            self.text = new_text
        if new_images:
            self.images = new_images
        self.updated_at = datetime.datetime.utcnow()
        self.save()

    @classmethod
    def find_by_id(cls, post_uuid):
        post = cls.nodes.get_or_none(uuid=post_uuid)
        return post

    @classmethod
    def get_all_posts(cls):
        return [post for post in cls.nodes.all()]
