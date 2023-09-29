from flask import Flask
from py2neo import Graph
from flask_jwt_extended import JWTManager

app = Flask(__name__)
jwt = JWTManager(app)

graph = Graph("neo4j://localhost:7687", auth=("neo4j", "password"))

from app.routes import user_routes

app.register_blueprint(user_routes.user_bp)
