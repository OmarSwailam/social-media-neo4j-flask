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

    @classmethod
    def find_by_id(cls, post_uuid):
        post = cls.nodes.get_or_none(uuid=post_uuid)
        return post
