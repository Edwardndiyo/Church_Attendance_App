from functools import wraps
from flask_jwt_extended import get_jwt_identity
from flask import jsonify
from ..models import User

def role_required(roles):
    """Restrict access based on user role."""
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            user_id = get_jwt_identity()
            user = User.query.get(user_id)
            if not user or user.role.name not in roles:
                return jsonify({"error": "Unauthorized access"}), 403
            return fn(*args, **kwargs)
        return wrapper
    return decorator
