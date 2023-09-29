from py2neo import Node, Relationship
from app import graph


class Post:
    def __init__(self, user_uuid, text, images=None):
        self.user_uuid = user_uuid
        self.text = text
        self.images = images or []

    def create(self):
        user_node = graph.nodes.match("User", uuid=self.user_uuid).first()
        if user_node:
            post = Node("Post", text=self.text, images=self.images)
            graph.create(post)
            relationship = Relationship(user_node, "POSTED", post)
            graph.create(relationship)
