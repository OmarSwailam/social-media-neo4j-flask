from neomodel import (
    StructuredNode,
    StringProperty,
    UniqueIdProperty,
)


class User(StructuredNode):
    uuid = UniqueIdProperty()
    first_name = StringProperty(required=True)
    last_name = StringProperty(required=True)
    email = StringProperty(required=True, unique_index=True)
    password = StringProperty(required=True)

    @classmethod
    def find_by_email(cls, email):
        user = cls.nodes.get_or_none(email=email)
        return user

    @classmethod
    def find_by_id(cls, uuid):
        user = cls.nodes.get_or_none(uuid=uuid)
        return user
