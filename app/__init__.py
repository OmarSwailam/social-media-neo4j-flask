from flask import Flask
from neomodel import config
from flask_jwt_extended import JWTManager
from flask_restx import Api
import os

app = Flask(__name__)
jwt = JWTManager(app)
config.DATABASE_URL = "bolt://neo4j:neo4j@localhost:7687"
config.NEO4J_USERNAME = os.environ["NEO4J_USERNAME"]
config.NEO4J_PASSWORD = os.environ["NEO4J_PASSWORD"]

api = Api(
    app,
    title="Neo4j Social Media RESTFUL-API",
    version="1.0",
    description="Social Media RESTFUL-API using Neo4j, A powerful Graph db",
)

from .routes.post_routes import post_nc
from .routes.user_routes import user_nc

api.add_namespace(post_nc)
api.add_namespace(user_nc)
