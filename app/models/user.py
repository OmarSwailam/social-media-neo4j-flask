from py2neo import Node, NodeMatcher
from passlib.hash import pbkdf2_sha256
from app import graph
import uuid


class User:
    def __init__(self, first_name, last_name, email, password):
        self.uuid = str(uuid.uuid4())
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.password = password

    def create(self):
        hashed_password = pbkdf2_sha256.hash(self.password)
        user = Node(
            "User",
            first_name=self.first_name,
            last_name=self.last_name,
            email=self.email,
            password=hashed_password,
        )
        graph.create(user)

    @classmethod
    def find_by_email(cls, email):
        matcher = NodeMatcher(graph)
        user = matcher.match("User").where(email=email).first()
        return user

    @classmethod
    def find_by_id(cls, uuid):
        matcher = NodeMatcher(graph)
        user = matcher.match("User").where(uuid=uuid).first()
        return user

    @classmethod
    def get_all_users(cls):
        matcher = NodeMatcher(graph)
        users = matcher.match("User")
        return users
