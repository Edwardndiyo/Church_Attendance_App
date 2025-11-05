from functools import wraps
from flask import request, jsonify
from ..models import User
from ..extensions import db

def require_permission(permission_code):
    """Decorator to check if a user has a given permission code."""

    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            # Assuming user_id is extracted from JWT or session
            user_id = getattr(request, "user_id", None)
            if not user_id:
                return jsonify({"error": "Unauthorized"}), 401

            user = db.session.get(User, user_id)
            if not user or not user.is_active:
                return jsonify({"error": "User not found or inactive"}), 403

            # Collect permissions
            user_permissions = set()
            for role in user.roles:
                for perm in role.permissions:
                    user_permissions.add(perm.code)

            # Check if permission is allowed
            if permission_code not in user_permissions:
                return jsonify({"error": "Forbidden"}), 403

            return f(*args, **kwargs)
        return wrapper
    return decorator
