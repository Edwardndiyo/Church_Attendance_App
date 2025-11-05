# from flask import Blueprint, request, jsonify
# from ..models.state import State
# from ..extensions import db
# from ..utils.csv_import import import_states_from_file
# from flask_jwt_extended import jwt_required, get_jwt
# from functools import wraps

# state_bp = Blueprint("state", __name__)

# def roles_required(*allowed_roles):
#     """
#     Decorator to ensure JWT contains one of allowed_roles in 'roles' claim.
#     """
#     def decorator(fn):
#         @wraps(fn)
#         @jwt_required()
#         def wrapper(*a, **kw):
#             claims = get_jwt()
#             roles = claims.get("roles", [])
#             if not any(r in roles for r in allowed_roles):
#                 return jsonify({"error": "insufficient role"}), 403
#             return fn(*a, **kw)
#         return wrapper
#     return decorator

# @state_bp.route("/", methods=["GET"])
# @roles_required("admin", "state_manager")
# def list_states():
#     states = State.query.order_by(State.name).all()
#     return jsonify([s.to_dict() for s in states]), 200

# @state_bp.route("/", methods=["POST"])
# @roles_required("admin", "state_manager")
# def create_state():
#     data = request.get_json() or {}
#     name = data.get("name")
#     code = data.get("code")
#     leader = data.get("leader")
#     if not name:
#         return jsonify({"error": "name required"}), 400

#     existing = State.query.filter_by(name=name).first()
#     if existing:
#         return jsonify({"error": "state with that name exists"}), 400

#     state = State(name=name, code=code, leader=leader)
#     db.session.add(state)
#     db.session.commit()
#     return jsonify(state.to_dict()), 201

# @state_bp.route("/<int:state_id>", methods=["PUT"])
# @roles_required("admin", "state_manager")
# def update_state(state_id):
#     state = State.query.get_or_404(state_id)
#     data = request.get_json() or {}
#     state.name = data.get("name", state.name)
#     state.code = data.get("code", state.code)
#     state.leader = data.get("leader", state.leader)
#     db.session.commit()
#     return jsonify(state.to_dict()), 200

# @state_bp.route("/<int:state_id>", methods=["DELETE"])
# @roles_required("admin")
# def delete_state(state_id):
#     state = State.query.get_or_404(state_id)
#     db.session.delete(state)
#     db.session.commit()
#     return jsonify({"message": "deleted"}), 200

# @state_bp.route("/upload", methods=["POST"])
# @roles_required("admin", "state_manager")
# def upload_states_csv():
#     if "file" not in request.files:
#         return jsonify({"error": "file part missing"}), 400

#     file = request.files["file"]
#     if file.filename == "":
#         return jsonify({"error": "no selected file"}), 400

#     result = import_states_from_file(file)
#     return jsonify(result), 200
