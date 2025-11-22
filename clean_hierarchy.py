# scripts/clean_hierarchy_complete_fixed.py
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.extensions import db
from app.models import State, Region, OldGroup, Group, District, User, Role, Attendance, YouthAttendance

def clean_hierarchy_complete_fixed():
    """Completely wipe ALL hierarchy data in correct order to handle foreign key constraints"""
    app = create_app()
    
    with app.app_context():
        try:
            print("🧹 Starting COMPLETE hierarchy cleanup with proper deletion order...")
            
            # Count records before deletion
            states_count = State.query.count()
            regions_count = Region.query.count()
            old_groups_count = OldGroup.query.count()
            groups_count = Group.query.count()
            districts_count = District.query.count()
            attendance_count = Attendance.query.count()
            youth_attendance_count = YouthAttendance.query.count()
            total_users_before = User.query.count()
            
            print(f"📊 Current counts:")
            print(f"   States: {states_count}")
            print(f"   Regions: {regions_count}")
            print(f"   Old Groups: {old_groups_count}")
            print(f"   Groups: {groups_count}")
            print(f"   Districts: {districts_count}")
            print(f"   Attendance Records: {attendance_count}")
            print(f"   Youth Attendance Records: {youth_attendance_count}")
            print(f"   Total Users: {total_users_before}")
            
            # 🎯 DELETE IN CORRECT ORDER TO HANDLE FOREIGN KEY CONSTRAINTS
            
            # 1. First delete attendance records (they reference districts, groups, etc.)
            print("\n🗑️  Step 1: Deleting youth attendance records...")
            youth_deleted = YouthAttendance.query.delete()
            print(f"   ✅ Deleted {youth_deleted} youth attendance records")
            
            print("🗑️  Step 2: Deleting regular attendance records...")
            attendance_deleted = Attendance.query.delete()
            print(f"   ✅ Deleted {attendance_deleted} regular attendance records")
            
            # 2. Delete or update users that reference hierarchy
            print("\n🗑️  Step 3: Handling users with hierarchy references...")
            
            # Option A: Delete auto-created users
            auto_users = User.query.filter(
                (User.email.like('%@thedcmp.org')) |
                (User.email.notlike('%@%')) |
                (User.name.contains('Admin'))
            ).all()
            
            auto_user_count = len(auto_users)
            print(f"   🔍 Found {auto_user_count} automatically created users to delete")
            
            for user in auto_users:
                print(f"      Deleting user: {user.email} (ID: {user.id})")
                db.session.delete(user)
            
            # Option B: Clear hierarchy references for remaining users
            users_with_hierarchy = User.query.filter(
                (User.state_id.isnot(None)) | 
                (User.region_id.isnot(None)) |
                (User.district_id.isnot(None)) |
                (User.group_id.isnot(None)) |
                (User.old_group_id.isnot(None))
            ).all()
            
            for user in users_with_hierarchy:
                user.state_id = None
                user.region_id = None
                user.district_id = None
                user.group_id = None
                user.old_group_id = None
                print(f"      Cleared hierarchy for user: {user.email}")
            
            db.session.commit()  # Commit user changes before deleting hierarchy
            
            # 3. Now delete hierarchy data in correct order
            print("\n🗑️  Step 4: Deleting hierarchy data...")
            
            # Delete in reverse order of dependencies:
            # Districts → Groups → OldGroups → Regions → States
            
            print("   🗑️  Deleting districts...")
            districts_deleted = District.query.delete()
            print(f"      ✅ Deleted {districts_deleted} districts")
            
            print("   🗑️  Deleting groups...")
            groups_deleted = Group.query.delete()
            print(f"      ✅ Deleted {groups_deleted} groups")
            
            print("   🗑️  Deleting old groups...")
            old_groups_deleted = OldGroup.query.delete()
            print(f"      ✅ Deleted {old_groups_deleted} old groups")
            
            print("   🗑️  Deleting regions...")
            regions_deleted = Region.query.delete()
            print(f"      ✅ Deleted {regions_deleted} regions")
            
            print("   🗑️  Deleting states...")
            states_deleted = State.query.delete()
            print(f"      ✅ Deleted {states_deleted} states")
            
            db.session.commit()
            
            # Final counts
            total_users_after = User.query.count()
            
            print(f"\n✅ COMPLETE cleanup completed successfully!")
            print(f"📊 Final counts:")
            print(f"   States: {State.query.count()}")
            print(f"   Regions: {Region.query.count()}")
            print(f"   Old Groups: {OldGroup.query.count()}")
            print(f"   Groups: {Group.query.count()}")
            print(f"   Districts: {District.query.count()}")
            print(f"   Attendance Records: {Attendance.query.count()}")
            print(f"   Youth Attendance Records: {YouthAttendance.query.count()}")
            print(f"   Auto-users deleted: {auto_user_count}")
            print(f"   Remaining users: {total_users_after}")
            
            # Final verification
            remaining_hierarchy_users = User.query.filter(
                (User.state_id.isnot(None)) | 
                (User.region_id.isnot(None)) |
                (User.district_id.isnot(None)) |
                (User.group_id.isnot(None)) |
                (User.old_group_id.isnot(None))
            ).count()
            
            if remaining_hierarchy_users == 0:
                print("🎉 SUCCESS: All hierarchy data and references removed!")
            else:
                print(f"⚠️  Warning: {remaining_hierarchy_users} users still have hierarchy links")
                
        except Exception as e:
            db.session.rollback()
            print(f"❌ Cleanup failed: {e}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    print("🚨 COMPLETE HIERARCHY CLEANUP (FIXED VERSION)")
    print("This will DELETE in proper order:")
    print("   1. Attendance records (youth & regular)")
    print("   2. Automatically created group users")
    print("   3. Clear hierarchy links from remaining users")
    print("   4. All hierarchy data (districts → groups → old groups → regions → states)")
    print("\n⚠️  This action cannot be undone!")
    
    confirm = input("\nType 'DELETE EVERYTHING' to confirm: ")
    if confirm == "DELETE EVERYTHING":
        clean_hierarchy_complete_fixed()
    else:
        print("❌ Cleanup cancelled.")













# # scripts/clean_hierarchy_complete.py
# import sys
# import os
# sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# from app import create_app
# from app.extensions import db
# from app.models import State, Region, OldGroup, Group, District, User, Role

# def clean_hierarchy_complete():
#     """Completely wipe ALL hierarchy data and ALL automatically created users"""
#     app = create_app()
    
#     with app.app_context():
#         try:
#             print("🧹 Starting COMPLETE hierarchy cleanup...")
            
#             # Count records before deletion
#             states_count = State.query.count()
#             regions_count = Region.query.count()
#             old_groups_count = OldGroup.query.count()
#             groups_count = Group.query.count()
#             districts_count = District.query.count()
#             total_users_before = User.query.count()
            
#             print(f"📊 Current counts:")
#             print(f"   States: {states_count}")
#             print(f"   Regions: {regions_count}")
#             print(f"   Old Groups: {old_groups_count}")
#             print(f"   Groups: {groups_count}")
#             print(f"   Districts: {districts_count}")
#             print(f"   Total Users: {total_users_before}")
            
#             # 🎯 IDENTIFY AND DELETE AUTOMATICALLY CREATED USERS
#             print("\n🗑️  Deleting automatically created group users...")
            
#             # Find users created by the old importer (emails without @domain or with group patterns)
#             auto_users = User.query.filter(
#                 (User.email.like('%@thedcmp.org')) |
#                 (User.email.notlike('%@%')) |  # Emails without @ (old format)
#                 (User.name.contains('Admin'))  # Users with "Admin" in name
#             ).all()
            
#             auto_user_count = len(auto_users)
#             print(f"🔍 Found {auto_user_count} automatically created users to delete")
            
#             for user in auto_users:
#                 print(f"   Deleting user: {user.email} (ID: {user.id})")
#                 db.session.delete(user)
            
#             # Delete all hierarchy data in correct order to handle foreign key constraints
#             print("\n🗑️  Deleting districts...")
#             District.query.delete()
            
#             print("🗑️  Deleting groups...")
#             Group.query.delete()
            
#             print("🗑️  Deleting old groups...")
#             OldGroup.query.delete()
            
#             print("🗑️  Deleting regions...")
#             Region.query.delete()
            
#             print("🗑️  Deleting states...")
#             State.query.delete()
            
#             db.session.commit()
            
#             # Count records after deletion
#             total_users_after = User.query.count()
            
#             print(f"\n✅ COMPLETE cleanup completed successfully!")
#             print(f"📊 Final counts:")
#             print(f"   States: {State.query.count()}")
#             print(f"   Regions: {Region.query.count()}")
#             print(f"   Old Groups: {OldGroup.query.count()}")
#             print(f"   Groups: {Group.query.count()}")
#             print(f"   Districts: {District.query.count()}")
#             print(f"   Users deleted: {auto_user_count}")
#             print(f"   Remaining users: {total_users_after}")
            
#             # 🎯 VERIFY CLEANUP
#             remaining_hierarchy_users = User.query.filter(
#                 (User.state_id.isnot(None)) | 
#                 (User.region_id.isnot(None)) |
#                 (User.district_id.isnot(None)) |
#                 (User.group_id.isnot(None)) |
#                 (User.old_group_id.isnot(None))
#             ).count()
            
#             if remaining_hierarchy_users == 0:
#                 print("🎉 SUCCESS: All hierarchy-linked users removed!")
#             else:
#                 print(f"⚠️  Warning: {remaining_hierarchy_users} users still have hierarchy links")
                
#         except Exception as e:
#             db.session.rollback()
#             print(f"❌ Cleanup failed: {e}")
#             import traceback
#             print(f"Traceback: {traceback.format_exc()}")

# if __name__ == "__main__":
#     print("🚨 COMPLETE HIERARCHY CLEANUP")
#     print("This will DELETE:")
#     print("   - All states, regions, old groups, groups, districts")
#     print("   - All automatically created group users")
#     print("   - All hierarchy relationships")
#     print("\n⚠️  This action cannot be undone!")
    
#     confirm = input("\nType 'DELETE EVERYTHING' to confirm: ")
#     if confirm == "DELETE EVERYTHING":
#         clean_hierarchy_complete()
#     else:
#         print("❌ Cleanup cancelled.")












# # scripts/clean_hierarchy.py
# import sys
# import os
# sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# from app import create_app
# from app.extensions import db
# from app.models import State, Region, OldGroup, Group, District, User

# def clean_hierarchy():
#     """Completely wipe all hierarchy data and associated users"""
#     app = create_app()
    
#     with app.app_context():
#         try:
#             print("🧹 Starting hierarchy cleanup...")
            
#             # Count records before deletion
#             states_count = State.query.count()
#             old_groups_count = OldGroup.query.count()
#             groups_count = Group.query.count()
#             districts_count = District.query.count()
            
#             print(f"📊 Current counts - States: {states_count}, OldGroups: {old_groups_count}, Groups: {groups_count}, Districts: {districts_count}")
            
#             # Delete in correct order to handle foreign key constraints
#             print("🗑️  Deleting districts...")
#             District.query.delete()
            
#             print("🗑️  Deleting groups...")
#             Group.query.delete()
            
#             print("🗑️  Deleting old groups...")
#             OldGroup.query.delete()
            
#             print("🗑️  Deleting regions...")
#             Region.query.delete()
            
#             print("🗑️  Deleting states...")
#             State.query.delete()
            
#             # Delete group users (users with email containing @thedcmp.org)
#             print("🗑️  Deleting group users...")
#             group_users = User.query.filter(User.email.like('%@thedcmp.org')).all()
#             for user in group_users:
#                 db.session.delete(user)
#                 print(f"   Deleted user: {user.email}")
            
#             db.session.commit()
            
#             print("✅ Hierarchy cleanup completed successfully!")
#             print("📊 Final counts:")
#             print(f"   States: {State.query.count()}")
#             print(f"   OldGroups: {OldGroup.query.count()}")
#             print(f"   Groups: {Group.query.count()}")
#             print(f"   Districts: {District.query.count()}")
#             print(f"   Group users: {User.query.filter(User.email.like('%@thedcmp.org')).count()}")
            
#         except Exception as e:
#             db.session.rollback()
#             print(f"❌ Cleanup failed: {e}")
#             import traceback
#             print(f"Traceback: {traceback.format_exc()}")

# if __name__ == "__main__":
#     confirm = input("⚠️  This will DELETE ALL hierarchy data and group users. Type 'YES' to confirm: ")
#     if confirm == "YES":
#         clean_hierarchy()
#     else:
#         print("❌ Cleanup cancelled.")