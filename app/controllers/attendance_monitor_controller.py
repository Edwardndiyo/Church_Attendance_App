from app.models import State, Region, District, Group, OldGroup
from app.utils.attendance_monitor import get_last_attendance_week, get_attendance_status

def get_attendance_monitor_summary():
    summary = {
        "states": [],
        "regions": [],
        "districts": [],
        "groups": [],
        "old_groups": []
    }

    # STATES
    for state in State.query.all():
        last_week = get_last_attendance_week("state", state.id)
        summary["states"].append({
            "id": state.id,
            "name": state.name,
            "last_filled_week": last_week,
            "status": get_attendance_status(last_week)
        })

    # REGIONS
    for region in Region.query.all():
        last_week = get_last_attendance_week("region", region.id)
        summary["regions"].append({
            "id": region.id,
            "name": region.name,
            "last_filled_week": last_week,
            "status": get_attendance_status(last_week)
        })

    # DISTRICTS
    for district in District.query.all():
        last_week = get_last_attendance_week("district", district.id)
        summary["districts"].append({
            "id": district.id,
            "name": district.name,
            "last_filled_week": last_week,
            "status": get_attendance_status(last_week)
        })

    # GROUPS
    for group in Group.query.all():
        last_week = get_last_attendance_week("group", group.id)
        summary["groups"].append({
            "id": group.id,
            "name": group.name,
            "last_filled_week": last_week,
            "status": get_attendance_status(last_week)
        })

    # OLD GROUPS
    for old_group in OldGroup.query.all():
        last_week = get_last_attendance_week("old_group", old_group.id)
        summary["old_groups"].append({
            "id": old_group.id,
            "name": old_group.name,
            "last_filled_week": last_week,
            "status": get_attendance_status(last_week)
        })

    return summary
