from datetime import timedelta

from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_jwt_extended.exceptions import (
    InvalidHeaderError,
    NoAuthorizationError,
)
from flask_restx import Api
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError
from neomodel import config

authorizations = {
    "Bearer Auth": {"type": "apiKey", "in": "header", "name": "Authorization"}
}

api = Api(
    ordered=True,
    title="Neo4j Social Media RESTFUL-API",
    description="Social Media RESTFUL-API using Neo4j, A powerful Graph db",
    version="1.0",
    security="Bearer Auth",
    authorizations=authorizations,
)

jwt = JWTManager()
cors = CORS(
    supports_credentials=True,
    resources={r"/*": {"origins": ["http://localhost:5173"]}},
)


def create_app(config_object):
    app = Flask(__name__)
    app.config.from_object(config_object)

    with app.app_context():
        api.init_app(app)
        jwt.init_app(app)
        if app.config.get("ENABLE_CORS", True):
            cors.init_app(app)

    from .routes.comment_routes import comment_nc
    from .routes.post_routes import post_nc
    from .routes.user_routes import user_nc

    api.add_namespace(post_nc)
    api.add_namespace(user_nc)
    api.add_namespace(comment_nc)

    return app
