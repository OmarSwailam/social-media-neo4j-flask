from flask import Flask
from py2neo import Graph
from flask_jwt_extended import JWTManager
from flask_restx import Api


app = Flask(__name__)
jwt = JWTManager(app)
graph = Graph("neo4j://localhost:7687", auth=("neo4j", "password"))

api = Api(
    title="Neo4j Social Media RESTFUL-API",
    version="1.0",
    description="Social Media RESTFUL-API using Neo4j, A powerful Graph db",
)

from .routes.post_routes import post_nc
from .routes.user_routes import user_nc

api.add_namespace(post_nc)
api.add_namespace(user_nc)
