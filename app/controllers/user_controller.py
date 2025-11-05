from flask import request, jsonify
from ..extensions import db
from ..models import User, Role
from flask_jwt_extended import jwt_required, get_jwt_identity


def can_create_role(current_user, target_roles):
    """Restrict role creation based on hierarchy."""
    current_roles = [r.name for r in current_user.roles]
    target_role_names = [r.name for r in target_roles]

    # Super admin can create anyone
    if "Super Admin" in current_roles:
        return True

    # State Admins cannot create Super Admins
    if "State Admin" in current_roles and any(r in ["Super Admin"] for r in target_role_names):
        return False

    # Region/District Admins cannot create higher-level roles
    if "Region Admin" in current_roles and any(r in ["Super Admin", "State Admin"] for r in target_role_names):
        return False

    return True

@jwt_required()
def create_user():
    """
    Create User
    ---
    tags:
      - Users
    description: Create a new user account (with hierarchical role checks).
    security:
      - Bearer: []
    consumes:
      - application/json
    parameters:
      - in: body
        name: body
        required: true
        schema:
          id: CreateUser
          required:
            - email
            - password
          properties:
            name:
              type: string
              example: John Doe
            email:
              type: string
              example: johndoe@example.com
            phone:
              type: string
              example: "+2348012345678"
            password:
              type: string
              example: mysecurepass
            roles:
              type: array
              items:
                type: integer
              example: [1, 2]
            state_id:
              type: integer
            region_id:
              type: integer
            district_id:
              type: integer
    responses:
      201:
        description: User created successfully
      400:
        description: Invalid or missing input
      403:
        description: Insufficient permissions
    """
    data = request.get_json()
    current_user = User.query.get(get_jwt_identity())

    # Required
    email = data.get("email")
    password = data.get("password")
    if not all([email, password]):
        return jsonify({"error": "Email and password are required"}), 400

    # Check duplicates
    if User.query.filter_by(email=email).first():
        return jsonify({"error": "User with this email already exists"}), 400

    # Create user
    user = User(
        name=data.get("name"),
        email=email,
        phone=data.get("phone"),  # ✅ new
        is_active=True,
    )
    user.set_password(password)

    # Hierarchy links
    user.state_id = data.get("state_id")
    user.region_id = data.get("region_id")
    user.district_id = data.get("district_id")

    # Assign roles
    role_ids = data.get("roles", [])
    roles = Role.query.filter(Role.id.in_(role_ids)).all()
    if not can_create_role(current_user, roles):
        return jsonify({"error": "Insufficient permissions to create this role"}), 403
    
    if role_ids:
        roles = Role.query.filter(Role.id.in_(role_ids)).all()
        if not roles:
            return jsonify({"error": "Invalid roles"}), 400
        user.roles = roles

    db.session.add(user)
    db.session.commit()

    return jsonify({
        "message": "User created successfully",
        "user": user.to_dict()
    }), 201


def update_user(user_id):
    """
    Update User
    ---
    tags:
      - Users
    description: Update user details and assigned roles.
    security:
      - Bearer: []
    parameters:
      - in: path
        name: user_id
        required: true
        type: integer
      - in: body
        name: body
        schema:
          id: UpdateUser
          properties:
            name:
              type: string
            email:
              type: string
            phone:
              type: string
            is_active:
              type: boolean
            roles:
              type: array
              items:
                type: integer
    responses:
      200:
        description: User updated successfully
      404:
        description: User not found
    """
    data = request.get_json()
    user = User.query.get_or_404(user_id)

    user.name = data.get("name", user.name)
    user.email = data.get("email", user.email)
    user.phone = data.get("phone", user.phone)
    user.is_active = data.get("is_active", user.is_active)

    # Update hierarchy
    user.state_id = data.get("state_id", user.state_id)
    user.region_id = data.get("region_id", user.region_id)
    user.district_id = data.get("district_id", user.district_id)

    # Reassign roles if provided
    if "roles" in data:
        role_ids = data["roles"]
        roles = Role.query.filter(Role.id.in_(role_ids)).all()
        user.roles = roles

    db.session.commit()
    return jsonify({"message": "User updated successfully", "user": user.to_dict()}), 200


def list_users():
    """
    List All Users
    ---
    tags:
      - Users
    description: Returns a list of all users in the system.
    security:
      - Bearer: []
    responses:
      200:
        description: A list of users
        schema:
          type: array
          items:
            type: object
    """
    users = User.query.all()
    return jsonify([u.to_dict() for u in users]), 200
