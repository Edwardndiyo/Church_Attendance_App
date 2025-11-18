# from app.utils.email_service import send_email
# from app.utils.attendance_monitor import get_last_attendance_week, get_attendance_status
# from app.models import User

# def send_manual_reminders(entity_type):
#     """
#     entity_type: state / region / district / group / old_group
#     """

#     failed_list = []

#     users = User.query.all()

#     for user in users:
#         last_week = get_last_attendance_week(entity_type, user.state_id)

#         if last_week == 0 or get_attendance_status(last_week) != "green":
#             send_email(
#                 to=user.email,
#                 subject="Attendance Reminder",
#                 body=f"Dear {user.first_name}, you have not submitted attendance for week {last_week}. Kindly update it."
#             )
#             failed_list.append(user.email)

#     return failed_list
