from app.utils.notification_service import notification_service
from app.utils.attendance_monitor import get_last_attendance_week, get_attendance_status
from app.models import User
from app.models.hierarchy import State, Region, District, Group, OldGroup

def send_manual_reminders(entity_type, methods=['email', 'whatsapp']):
    """
    entity_type: state / region / district / group / old_group
    methods: list of notification methods ['email', 'whatsapp']
    """
    
    failed_list = []
    notification_results = []

    users = User.query.all()

    for user in users:
        last_week = get_last_attendance_week(entity_type, user.state_id)

        if last_week == 0 or get_attendance_status(last_week) != "green":
            results = notification_service.send_attendance_reminder(
                user=user,
                week=last_week,
                methods=methods
            )
            
            notification_results.append({
                'user': user.email,
                'results': results
            })
            
            # If both methods failed, add to failed list
            if not results['email_sent'] and not results['whatsapp_sent']:
                failed_list.append(user.email)

    return {
        'failed_list': failed_list,
        'notification_results': notification_results
    }

def send_targeted_reminders(entity_type, entity_id, methods=['email', 'whatsapp']):
    model_map = {
        "state": State,
        "region": Region,
        "district": District,
        "group": Group,
        "old_group": OldGroup,
    }

    Model = model_map[entity_type]
    entity = Model.query.get(entity_id)

    if not entity:
        return []

    admin_users = entity.admins  # Get user objects instead of just emails
    notification_results = []
    
    for user in admin_users:
        results = notification_service.send_attendance_reminder(
            user=user,
            week=get_last_attendance_week(entity_type, user.state_id),
            methods=methods
        )
        
        notification_results.append({
            'user': user.email,
            'results': results
        })

    return notification_results










# from app.utils.email_service import send_email
# from app.utils.attendance_monitor import get_last_attendance_week, get_attendance_status
# from app.models import User
# from app.models.hierarchy import State, Region, District, Group, OldGroup
# from app.utils.email_service import EmailService

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
#                 to_email=user.email,
#                 subject="Attendance Reminder",
#                 template_name="attendance_reminder",
#                 context={
#                     "name": user.name or user.email,
#                     "week": last_week
#                 }
#             )

#             failed_list.append(user.email)

#     return failed_list

# def send_targeted_reminders(entity_type, entity_id):
#     model_map = {
#         "state": State,
#         "region": Region,
#         "district": District,
#         "group": Group,
#         "old_group": OldGroup,
#     }

#     Model = model_map[entity_type]
#     entity = Model.query.get(entity_id)

#     if not entity:
#         return []

#     admin_emails = [user.email for user in entity.admins]  # depends on your relationship
    
#     email_service = EmailService()
#     for email in admin_emails:
#         email_service.send_email(
#             to_email=email,
#             subject="Attendance Reminder",
#             template_name="attendance_reminder",
#             context={"name": email}  
#         )

#     return admin_emails
