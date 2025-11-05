from ..models import User, State, Region, District

def get_user_scope(user: User):
    """Return the scope of data a user has access to."""
    if user.district_id:
        return {"level": "district", "id": user.district_id}
    elif user.region_id:
        return {"level": "region", "id": user.region_id}
    elif user.state_id:
        return {"level": "state", "id": user.state_id}
    else:
        return {"level": "global"}

def filter_data_by_user_scope(query, user: User):
    """Filter database queries based on user's assigned scope."""
    scope = get_user_scope(user)

    if scope["level"] == "state":
        return query.filter_by(state_id=scope["id"])
    elif scope["level"] == "region":
        return query.filter_by(region_id=scope["id"])
    elif scope["level"] == "district":
        return query.filter_by(district_id=scope["id"])
    else:
        # Global access (super admin)
        return query


# Now, in any controller where you fetch data, you can apply:
# query = filter_data_by_user_scope(SomeModel.query, current_user)
