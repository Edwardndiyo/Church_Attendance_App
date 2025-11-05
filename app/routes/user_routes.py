from flask import Blueprint
from ..controllers import user_controller
from flask_jwt_extended import jwt_required, get_jwt_identity

user_bp = Blueprint("users", __name__)

user_bp.route("/", methods=["GET"])(jwt_required()(user_controller.list_users))
user_bp.route("/", methods=["POST"])(jwt_required()(user_controller.create_user))
user_bp.route("/<int:user_id>", methods=["PUT"])(jwt_required()(user_controller.update_user))
