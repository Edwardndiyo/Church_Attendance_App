# Super admin user role must be expliccitly called "Super Admin"

from functools import wraps
from flask_jwt_extended import get_jwt_identity
from flask import jsonify
from app.models import User, State, Region, District, Group

def get_current_user():
    user_id = get_jwt_identity()
    return User.query.get(user_id)

def apply_scope_filters(model, user):
    """Automatically restrict query based on user access level."""
    if any(role.name == "Super Admin" for role in user.roles):
        return model.query  # FULL ACCESS

    query = model.query

    # Apply hierarchical restriction
    if user.district_id:
        if hasattr(model, "district_id"):
            query = query.filter(model.district_id == user.district_id)

    elif user.region_id:
        if hasattr(model, "region_id"):
            query = query.filter(model.region_id == user.region_id)

    elif user.state_id:
        if hasattr(model, "state_id"):
            query = query.filter(model.state_id == user.state_id)

    return query


def scoped_query(model):
    """
    Decorator to apply access filtering automatically to GET, POST, PUT, DELETE.
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            user = get_current_user()
            scoped_q = apply_scope_filters(model, user)
            return fn(scoped_q, *args, **kwargs)
        return wrapper
    return decorator










# from ..models import User, State, Region, District

# def get_user_scope(user: User):
#     """Return the scope of data a user has access to."""
#     if user.district_id:
#         return {"level": "district", "id": user.district_id}
#     elif user.region_id:
#         return {"level": "region", "id": user.region_id}
#     elif user.state_id:
#         return {"level": "state", "id": user.state_id}
#     else:
#         return {"level": "global"}

# def filter_data_by_user_scope(query, user: User):
#     """Filter database queries based on user's assigned scope."""
#     scope = get_user_scope(user)

#     if scope["level"] == "state":
#         return query.filter_by(state_id=scope["id"])
#     elif scope["level"] == "region":
#         return query.filter_by(region_id=scope["id"])
#     elif scope["level"] == "district":
#         return query.filter_by(district_id=scope["id"])
#     else:
#         # Global access (super admin)
#         return query


# # Now, in any controller where you fetch data, you can apply:
# # query = filter_data_by_user_scope(SomeModel.query, current_user)
