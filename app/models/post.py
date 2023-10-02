import datetime
from py2neo import Node, Relationship, NodeMatcher
from app import graph
import uuid


class Post:
    def __init__(self, user_uuid, text, images=None):
        self.uuid = str(uuid.uuid4())
        self.user_uuid = user_uuid
        self.text = text
        self.images = images or []
        self.created_at = None
        self.updated_at = None

    def create(self):
        user_node = graph.nodes.match("User", uuid=self.user_uuid).first()
        if user_node:
            post = Node("Post", uuid=self.uuid, text=self.text, images=self.images)
            post["created_at"] = datetime.utcnow()
            post["updated_at"] = datetime.utcnow()
            graph.create(post)
            relationship = Relationship(user_node, "POSTED", post)
            graph.create(relationship)

    def edit(self, new_text, new_images):
        if new_text:
            self.text = new_text
        if new_images:
            self.images = new_images

        self.updated_at = datetime.utcnow()

        post_node = graph.nodes.match("Post", uuid=self.uuid).first()
        if post_node:
            post_node["text"] = self.text
            post_node["images"] = self.images
            post_node["updated_at"] = self.updated_at
            post_node.push()

    def delete(self):
        post_node = graph.nodes.match("Post", uuid=self.uuid).first()

        if post_node:
            graph.delete(post_node, detach=True)

    @classmethod
    def find_by_id(cls, post_uuid):
        matcher = NodeMatcher(graph)
        post_node = matcher.match("Post").where(uuid=post_uuid).first()

        if post_node:
            user_relationship = graph.match((None, post_node), r_type="POSTED").first()

            if user_relationship:
                user_node = user_relationship.nodes()[0]
                return {
                    "uuid": post_node["uuid"],
                    "user_uuid": user_node["uuid"],
                    "text": post_node["text"],
                    "images": post_node["images"],
                }

        return None

    @classmethod
    def get_all_posts(cls):
        matcher = NodeMatcher(graph)
        posts = matcher.match("Post")
        return [cls(**post) for post in posts]
