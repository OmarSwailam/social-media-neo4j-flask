from functools import wraps

from flask_jwt_extended import verify_jwt_in_request
from flask_jwt_extended.exceptions import (
    FreshTokenRequired,
    InvalidHeaderError,
    NoAuthorizationError,
    RevokedTokenError,
    UserLookupError,
)
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError


def jwt_guard(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            verify_jwt_in_request()
        except (
            NoAuthorizationError,
            InvalidHeaderError,
            RevokedTokenError,
            FreshTokenRequired,
            UserLookupError,
            InvalidTokenError,
            ExpiredSignatureError,
        ) as e:
            return {"error": str(e)}, 401
        return fn(*args, **kwargs)

    return wrapper


def jwt_refresh_guard(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            verify_jwt_in_request(refresh=True)
        except Exception as e:
            return {"error": str(e)}, 401

        return fn(*args, **kwargs)

    return wrapper
