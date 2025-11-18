from flask import Blueprint, jsonify
from app.controllers.attendance_monitor_controller import get_attendance_monitor_summary
from app.controllers.reminder_controller import send_manual_reminders
from app.utils.access_control import require_role

monitor_bp = Blueprint("monitor_bp", __name__)

@monitor_bp.get("/monitor/attendance")
@require_role(["super admin", "state admin"])
def attendance_monitor():
    return jsonify(get_attendance_monitor_summary()), 200


@monitor_bp.post("/monitor/remind/<entity_type>")
@require_role(["super admin"])
def manual_remind(entity_type):
    valid = ["state", "region", "district", "group", "old_group"]
    if entity_type not in valid:
        return jsonify({"error": "Invalid entity type"}), 400

    emails = send_manual_reminders(entity_type)
    return jsonify({"sent_to": emails}), 200
