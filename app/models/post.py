from neomodel import (
    StructuredNode,
    UniqueIdProperty,
    StringProperty,
    ArrayProperty,
    DateTimeProperty,
    RelationshipFrom,
    StructuredRel,
)
from .user import User


class Post(StructuredNode):
    uuid = UniqueIdProperty()
    text = StringProperty(required=True)
    images = ArrayProperty(StringProperty())
    created_at = DateTimeProperty(default_now=True)
    updated_at = DateTimeProperty(default_now=True)

    created_by = RelationshipFrom(User, "CREATED_POST")

    @classmethod
    def find_by_id(cls, post_uuid):
        post = cls.nodes.get_or_none(uuid=post_uuid)
        return post

    @classmethod
    def get_all_posts(cls):
        return cls.nodes.all()
