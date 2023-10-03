from datetime import timedelta
from flask import Flask
from neomodel import config
from flask_jwt_extended import JWTManager
from flask_restx import Api

app = Flask(__name__)
app.config["SECRET_KEY"] = "d!-*k_6)0_xwm1x=j2r+^8f0rae8x8w-)k&=_+&_=*9hvzlcib"
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=24)
app.config["JWT_REFRESH_TOKEN_EXPIRES"] = timedelta(days=30)

jwt = JWTManager(app)
config.DATABASE_URL = "bolt://neo4j:password@localhost:7687"
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
