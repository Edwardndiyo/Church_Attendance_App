# app/utils/excel_importer_enhanced.py
import pandas as pd
from app.extensions import db
from app.models import State, Region, OldGroup, Group, District, User, Role

def safe_strip(value):
    """Safely strip any value - converts to string first"""
    if value is None or pd.isna(value):
        return ""
    return str(value).strip()

def create_group_user(group_name, group, district=None):
    """
    Create a user for a group with COMPLETE hierarchy links
    Username/email format: groupname (lowercase, no spaces) - NO SUFFIX
    """
    # Clean group name for email - NO SUFFIX
    clean_name = group_name.lower().replace(' ', '_').replace("'", "").replace("-", "_")
    email = f"{clean_name}"  # 🎯 REMOVED SUFFIX COMPLETELY
    
    print(f"🔄 Creating user with email: '{email}' for group '{group_name}'")
    
    # Check if user already exists
    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        print(f"📧 User already exists, updating: {email}")
        user = existing_user
    else:
        print(f"👤 CREATING NEW User: {email} for group '{group_name}'")
        user = User(
            email=email,
            name=f"{group_name} Admin",
            phone=None
        )
        user.set_password("12345678")  # Default password
    
    # 🎯 SET COMPLETE HIERARCHY LINKS - CRITICAL FOR ACCESS CONTROL
    user.state_id = group.state_id
    user.region_id = group.region_id
    user.old_group_id = group.old_group_id  # 🎯 Link to old group
    user.group_id = group.id  # 🎯 Link to the group
    
    # For group admin, district_id should be NULL to access ALL districts in the group
    user.district_id = None  # 🎯 This gives access to all districts in the group
    
    print(f"🔗 Setting hierarchy for {email}: State={group.state_id}, Region={group.region_id}, OldGroup={group.old_group_id}, Group={group.id}")
    
    # Assign Group Admin role
    group_admin_role = Role.query.filter_by(name="Group Admin").first()
    if group_admin_role:
        if group_admin_role not in user.roles:
            user.roles.append(group_admin_role)
            print(f"✅ Assigned Group Admin role to {email}")
    else:
        print(f"⚠️  Warning: Group Admin role not found!")
        # Create the role if it doesn't exist
        group_admin_role = Role(name="Group Admin", description="Administrator for a specific group")
        db.session.add(group_admin_role)
        db.session.commit()
        user.roles.append(group_admin_role)
        print(f"✅ Created and assigned Group Admin role to {email}")
    
    if not existing_user:
        db.session.add(user)
    
    # Commit immediately to ensure user is saved with proper hierarchy
    db.session.commit()
    
    print(f"🔗 FINAL User {email} linked to - State: {user.state_id}, Region: {user.region_id}, " 
          f"District: {user.district_id}, Group: {user.group_id}, OldGroup: {user.old_group_id}")
    return user

def import_hierarchy_from_excel(file_path, state_name="Rivers Central", state_code="RIV-CEN", region_name="Port Harcourt"):
    """
    Enhanced version that properly links users to COMPLETE hierarchy
    All data will be under Rivers Central state and Port Harcourt region
    """
    print("=== Starting ENHANCED hierarchy import ===")
    print(f"🎯 Importing under State: {state_name}, Region: {region_name}")
    
    try:
        # Read Excel file
        df = pd.read_excel(file_path, sheet_name=0, header=None)
        print(f"Loaded Excel with {len(df)} rows, {len(df.columns)} columns")
        
        # 🎯 CREATE OR GET STATE - Rivers Central
        state = State.query.filter_by(name=state_name).first()
        if not state:
            state = State(name=state_name, code=state_code, leader="State Leader")
            db.session.add(state)
            db.session.commit()
            print(f"✅ Created state: {state_name} (ID: {state.id})")
        else:
            print(f"📁 Using existing state: {state_name} (ID: {state.id})")
        
        # 🎯 CREATE OR GET REGION - Port Harcourt Region
        region = Region.query.filter_by(name=region_name, state_id=state.id).first()
        if not region:
            region = Region(
                name=region_name,
                code="PH-RGN",  # Port Harcourt Region code
                leader="Region Leader",
                state_id=state.id
            )
            db.session.add(region)
            db.session.commit()
            print(f"✅ Created region: {region_name} (ID: {region.id})")
        else:
            print(f"📁 Using existing region: {region_name} (ID: {region.id})")
        
        current_old_group = None
        old_groups_created = 0
        groups_created = 0
        districts_created = 0
        users_created = 0
        
        # Track groups we process to avoid duplicates
        processed_groups = set()
        
        for index, row in df.iterrows():
            # Convert all cells to strings for safe processing
            row_str = [safe_strip(cell) for cell in row]
            
            # Skip completely empty rows
            if all(cell == '' for cell in row_str):
                continue
            
            # DETECT OLD GROUP - Check ALL columns for "OLD GROUP"
            for col_idx, cell_value in enumerate(row_str):
                if cell_value and "OLD GROUP" in cell_value.upper():
                    old_group_name = cell_value
                    print(f"\n🎯 FOUND OLD GROUP: '{old_group_name}'")
                    
                    # Create the Old Group under Rivers Central state and Port Harcourt region
                    current_old_group = OldGroup(
                        name=old_group_name,
                        code=old_group_name.replace("OLD GROUP", "").strip()[:4].upper(),
                        state_id=state.id,      # 🎯 Rivers Central
                        region_id=region.id     # 🎯 Port Harcourt Region
                    )
                    db.session.add(current_old_group)
                    db.session.commit()
                    old_groups_created += 1
                    print(f"✅ CREATED OldGroup: {old_group_name} (ID: {current_old_group.id}) under {state_name}/{region_name}")
                    break
            
            # Process groups and districts if we have a current Old Group
            if current_old_group:
                for col_idx in range(len(row_str)):
                    group_name = row_str[col_idx]
                    
                    # Skip empty cells, numbers, and Old Group indicators
                    if (not group_name or
                        group_name.isdigit() or
                        "OLD GROUP" in group_name.upper()):
                        continue
                    
                    # Check if this looks like a group name
                    if (len(group_name.split()) >= 2 or
                        any(word in group_name.upper() for word in ['GROUP', 'DISTRICT', 'UNIPORT', 'CORPER', 'FELLOWSHIP'])):
                        
                        group_key = f"{group_name}_{current_old_group.id}"
                        if group_key in processed_groups:
                            continue
                        processed_groups.add(group_key)
                        
                        print(f"\n🎯 PROCESSING GROUP: '{group_name}' under '{current_old_group.name}'")
                        
                        # Create the Group with COMPLETE hierarchy links
                        group = Group(
                            name=group_name,
                            code=group_name[:4].upper(),
                            state_id=state.id,          # 🎯 Rivers Central
                            region_id=region.id,        # 🎯 Port Harcourt Region
                            old_group_id=current_old_group.id,  # 🎯 Link to old group
                            leader=f"{group_name} Leader"
                        )
                        db.session.add(group)
                        db.session.commit()
                        groups_created += 1
                        print(f"✅ CREATED Group: {group_name} (ID: {group.id}) under {state_name}/{region_name}")
                        print(f"📋 Group hierarchy: State={state.id}, Region={region.id}, OldGroup={current_old_group.id}")
                        
                        # 🎯 CREATE USER FOR THIS GROUP with COMPLETE hierarchy links
                        group_user = create_group_user(group_name, group)
                        if group_user:
                            users_created += 1
                            print(f"✅ Created user {group_user.email} with Group ID: {group_user.group_id}, OldGroup ID: {group_user.old_group_id}")
                        
                        # Process districts under this group
                        district_start_row = index + 1
                        district_count = 0
        
                        for dist_row_idx in range(district_start_row, min(district_start_row + 30, len(df))):
                            district_name = safe_strip(df.iloc[dist_row_idx, col_idx])
                            
                            # Stop when we hit another group, Old Group, or empty row
                            if (not district_name or
                                district_name.isdigit() or
                                any(word in district_name.upper() for word in ['GROUP', 'OLD GROUP']) or
                                dist_row_idx >= len(df)):
                                if district_count > 0:  # Only break if we found at least one district
                                    break
                                else:
                                    continue
                            
                            # Get district code from column 0 of the same row
                            district_code = safe_strip(df.iloc[dist_row_idx, 0])
                            if not district_code or district_code.isdigit():
                                district_code = district_name[:4].upper()
                            
                            # Only create district if it's a valid name
                            if (district_name and
                                not district_name.isdigit() and
                                "GROUP" not in district_name.upper()):
                                
                                print(f"  🎯 FOUND DISTRICT: {district_name}")
                                
                                district = District(
                                    name=district_name,
                                    code=district_code,
                                    state_id=state.id,          # 🎯 Rivers Central
                                    region_id=region.id,        # 🎯 Port Harcourt Region
                                    old_group_id=current_old_group.id,  # 🎯 Link to old group
                                    group_id=group.id,          # 🎯 Link to parent group
                                    leader=f"{district_name} Leader"
                                )
                                db.session.add(district)
                                db.session.commit()
                                districts_created += 1
                                district_count += 1
                                print(f"  ✅ CREATED District: {district_name} (ID: {district.id}) under {group.name}")
        
        db.session.commit()
        
        print(f"\n=== IMPORT SUMMARY ===")
        print(f"✅ State: {state_name} (ID: {state.id})")
        print(f"✅ Region: {region_name} (ID: {region.id})") 
        print(f"✅ Old Groups: {old_groups_created}")
        print(f"✅ Groups: {groups_created}")
        print(f"✅ Districts: {districts_created}")
        print(f"✅ Users: {users_created}")
        print("🎉 Enhanced import completed successfully!")
        
        # 🎯 VERIFY HIERARCHY LINKS - Check ALL users
        print(f"\n=== HIERARCHY VERIFICATION ===")
        all_users = User.query.all()
        for user in all_users:
            print(f"🔍 User {user.email}: State={user.state_id}, Region={user.region_id}, "
                  f"District={user.district_id}, Group={user.group_id}, OldGroup={user.old_group_id}")
        
        # Count users with proper group links
        users_with_groups = User.query.filter(User.group_id.isnot(None)).count()
        users_with_old_groups = User.query.filter(User.old_group_id.isnot(None)).count()
        
        print(f"\n📊 USER HIERARCHY SUMMARY:")
        print(f"Users with Group ID: {users_with_groups}/{len(all_users)}")
        print(f"Users with OldGroup ID: {users_with_old_groups}/{len(all_users)}")
        
        return {
            "message": f"Enhanced hierarchy imported successfully under {state_name}/{region_name}!",
            "summary": {
                "state": state_name,
                "region": region_name,
                "old_groups": old_groups_created,
                "groups": groups_created,
                "districts": districts_created,
                "users": users_created
            },
            "hierarchy_ids": {
                "state_id": state.id,
                "region_id": region.id
            }
        }
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ IMPORT FAILED: {str(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        raise e










# # app/utils/excel_importer_enhanced.py
# import pandas as pd
# from app.extensions import db
# from app.models import State, Region, OldGroup, Group, District, User, Role

# def safe_strip(value):
#     """Safely strip any value - converts to string first"""
#     if value is None or pd.isna(value):
#         return ""
#     return str(value).strip()

# def create_group_user(group_name, group, district=None):
#     """
#     Create a user for a group with COMPLETE hierarchy links
#     Username/email format: groupname@thedcmp.org (lowercase, no spaces)
#     """
#     # Clean group name for email
#     clean_name = group_name.lower().replace(' ', '_').replace("'", "").replace("-", "_")
#     email = f"{clean_name}"
    
#     # Check if user already exists
#     existing_user = User.query.filter_by(email=email).first()
#     if existing_user:
#         print(f"📧 User already exists, updating: {email}")
#         user = existing_user
#     else:
#         print(f"👤 CREATING User: {email} for group '{group_name}'")
#         user = User(
#             email=email,
#             name=f"{group_name} Admin",
#             phone=None
#         )
#         user.set_password("12345678")  # Default password
    
#     # 🎯 SET COMPLETE HIERARCHY LINKS - CRITICAL FOR ACCESS CONTROL
#     user.state_id = group.state_id
#     user.region_id = group.region_id
#     user.district_id = district.id if district else None
#     user.group_id = group.id  # 🆕 ADDED - Link to the group
#     user.old_group_id = group.old_group_id  # 🆕 ADDED - Link to the old group
    
#     # Assign Group Admin role
#     group_admin_role = Role.query.filter_by(name="Group Admin").first()
#     if group_admin_role and group_admin_role not in user.roles:
#         user.roles.append(group_admin_role)
#         print(f"✅ Assigned Group Admin role to {email}")
#     elif not group_admin_role:
#         print(f"⚠️  Warning: Group Admin role not found!")
#         # Create the role if it doesn't exist
#         group_admin_role = Role(name="Group Admin", description="Administrator for a specific group")
#         db.session.add(group_admin_role)
#         db.session.commit()
#         user.roles.append(group_admin_role)
#         print(f"✅ Created and assigned Group Admin role to {email}")
    
#     if not existing_user:
#         db.session.add(user)
    
#     print(f"🔗 User {email} linked to - State: {user.state_id}, Region: {user.region_id}, " 
#           f"District: {user.district_id}, Group: {user.group_id}, OldGroup: {user.old_group_id}")
#     return user

# def import_hierarchy_from_excel(file_path, state_name="Rivers Central", state_code="RIV-CEN", region_name="Port Harcourt"):
#     """
#     Enhanced version that properly links users to COMPLETE hierarchy
#     All data will be under Rivers Central state and Port Harcourt region
#     """
#     print("=== Starting ENHANCED hierarchy import ===")
#     print(f"🎯 Importing under State: {state_name}, Region: {region_name}")
    
#     try:
#         # Read Excel file
#         df = pd.read_excel(file_path, sheet_name=0, header=None)
#         print(f"Loaded Excel with {len(df)} rows, {len(df.columns)} columns")
        
#         # 🎯 CREATE OR GET STATE - Rivers Central
#         state = State.query.filter_by(name=state_name).first()
#         if not state:
#             state = State(name=state_name, code=state_code, leader="State Leader")
#             db.session.add(state)
#             db.session.commit()
#             print(f"✅ Created state: {state_name} (ID: {state.id})")
#         else:
#             print(f"📁 Using existing state: {state_name} (ID: {state.id})")
        
#         # 🎯 CREATE OR GET REGION - Port Harcourt Region
#         region = Region.query.filter_by(name=region_name, state_id=state.id).first()
#         if not region:
#             region = Region(
#                 name=region_name,
#                 code="PH-RGN",  # Port Harcourt Region code
#                 leader="Region Leader",
#                 state_id=state.id
#             )
#             db.session.add(region)
#             db.session.commit()
#             print(f"✅ Created region: {region_name} (ID: {region.id})")
#         else:
#             print(f"📁 Using existing region: {region_name} (ID: {region.id})")
        
#         current_old_group = None
#         old_groups_created = 0
#         groups_created = 0
#         districts_created = 0
#         users_created = 0
        
#         # Track groups we process to avoid duplicates
#         processed_groups = set()
        
#         for index, row in df.iterrows():
#             # Convert all cells to strings for safe processing
#             row_str = [safe_strip(cell) for cell in row]
            
#             # Skip completely empty rows
#             if all(cell == '' for cell in row_str):
#                 continue
            
#             # DETECT OLD GROUP - Check ALL columns for "OLD GROUP"
#             for col_idx, cell_value in enumerate(row_str):
#                 if cell_value and "OLD GROUP" in cell_value.upper():
#                     old_group_name = cell_value
#                     print(f"\n🎯 FOUND OLD GROUP: '{old_group_name}'")
                    
#                     # Create the Old Group under Rivers Central state and Port Harcourt region
#                     current_old_group = OldGroup(
#                         name=old_group_name,
#                         code=old_group_name.replace("OLD GROUP", "").strip()[:4].upper(),
#                         state_id=state.id,      # 🎯 Rivers Central
#                         region_id=region.id     # 🎯 Port Harcourt Region
#                     )
#                     db.session.add(current_old_group)
#                     db.session.commit()
#                     old_groups_created += 1
#                     print(f"✅ CREATED OldGroup: {old_group_name} (ID: {current_old_group.id}) under {state_name}/{region_name}")
#                     break
            
#             # Process groups and districts if we have a current Old Group
#             if current_old_group:
#                 for col_idx in range(len(row_str)):
#                     group_name = row_str[col_idx]
                    
#                     # Skip empty cells, numbers, and Old Group indicators
#                     if (not group_name or
#                         group_name.isdigit() or
#                         "OLD GROUP" in group_name.upper()):
#                         continue
                    
#                     # Check if this looks like a group name
#                     if (len(group_name.split()) >= 2 or
#                         any(word in group_name.upper() for word in ['GROUP', 'DISTRICT', 'UNIPORT', 'CORPER', 'FELLOWSHIP'])):
                        
#                         group_key = f"{group_name}_{current_old_group.id}"
#                         if group_key in processed_groups:
#                             continue
#                         processed_groups.add(group_key)
                        
#                         print(f"\n🎯 PROCESSING GROUP: '{group_name}' under '{current_old_group.name}'")
                        
#                         # Create the Group with COMPLETE hierarchy links
#                         group = Group(
#                             name=group_name,
#                             code=group_name[:4].upper(),
#                             state_id=state.id,          # 🎯 Rivers Central
#                             region_id=region.id,        # 🎯 Port Harcourt Region
#                             old_group_id=current_old_group.id,
#                             leader=f"{group_name} Leader"
#                         )
#                         db.session.add(group)
#                         db.session.commit()
#                         groups_created += 1
#                         print(f"✅ CREATED Group: {group_name} (ID: {group.id}) under {state_name}/{region_name}")
                        
#                         # 🎯 CREATE USER FOR THIS GROUP with COMPLETE hierarchy links
#                         group_user = create_group_user(group_name, group)
#                         if group_user:
#                             users_created += 1
#                             db.session.commit()  # Ensure user is saved
                        
#                         # Process districts under this group
#                         district_start_row = index + 1
#                         district_count = 0
                        
#                         for dist_row_idx in range(district_start_row, min(district_start_row + 30, len(df))):
#                             district_name = safe_strip(df.iloc[dist_row_idx, col_idx])
                            
#                             # Stop when we hit another group, Old Group, or empty row
#                             if (not district_name or
#                                 district_name.isdigit() or
#                                 any(word in district_name.upper() for word in ['GROUP', 'OLD GROUP']) or
#                                 dist_row_idx >= len(df)):
#                                 if district_count > 0:  # Only break if we found at least one district
#                                     break
#                                 else:
#                                     continue
                            
#                             # Get district code from column 0 of the same row
#                             district_code = safe_strip(df.iloc[dist_row_idx, 0])
#                             if not district_code or district_code.isdigit():
#                                 district_code = district_name[:4].upper()
                            
#                             # Only create district if it's a valid name
#                             if (district_name and
#                                 not district_name.isdigit() and
#                                 "GROUP" not in district_name.upper()):
                                
#                                 print(f"  🎯 FOUND DISTRICT: {district_name}")
                                
#                                 district = District(
#                                     name=district_name,
#                                     code=district_code,
#                                     state_id=state.id,          # 🎯 Rivers Central
#                                     region_id=region.id,        # 🎯 Port Harcourt Region
#                                     old_group_id=current_old_group.id,
#                                     group_id=group.id,
#                                     leader=f"{district_name} Leader"
#                                 )
#                                 db.session.add(district)
#                                 db.session.commit()
#                                 districts_created += 1
#                                 district_count += 1
#                                 print(f"  ✅ CREATED District: {district_name} (ID: {district.id}) under {group.name}")
                                
#                                 # 🎯 CREATE USER FOR THIS DISTRICT (Optional - uncomment if needed)
#                                 # district_user = create_group_user(
#                                 #     f"{district_name} District", 
#                                 #     group, 
#                                 #     district
#                                 # )
#                                 # if district_user:
#                                 #     users_created += 1
#                                 #     db.session.commit()
        
#         db.session.commit()
        
#         print(f"\n=== IMPORT SUMMARY ===")
#         print(f"✅ State: {state_name} (ID: {state.id})")
#         print(f"✅ Region: {region_name} (ID: {region.id})") 
#         print(f"✅ Old Groups: {old_groups_created}")
#         print(f"✅ Groups: {groups_created}")
#         print(f"✅ Districts: {districts_created}")
#         print(f"✅ Users: {users_created}")
#         print("🎉 Enhanced import completed successfully!")
        
#         # 🎯 VERIFY HIERARCHY LINKS
#         print(f"\n=== HIERARCHY VERIFICATION ===")
#         group_users = User.query.filter(User.group_id.isnot(None)).all()
#         for user in group_users:
#             print(f"🔍 User {user.email}: State={user.state_id}, Region={user.region_id}, "
#                   f"District={user.district_id}, Group={user.group_id}, OldGroup={user.old_group_id}")
        
#         return {
#             "message": f"Enhanced hierarchy imported successfully under {state_name}/{region_name}!",
#             "summary": {
#                 "state": state_name,
#                 "region": region_name,
#                 "old_groups": old_groups_created,
#                 "groups": groups_created,
#                 "districts": districts_created,
#                 "users": users_created
#             },
#             "hierarchy_ids": {
#                 "state_id": state.id,
#                 "region_id": region.id
#             }
#         }
        
#     except Exception as e:
#         db.session.rollback()
#         print(f"❌ IMPORT FAILED: {str(e)}")
#         import traceback
#         print(f"Traceback: {traceback.format_exc()}")
#         raise e














# # app/utils/excel_importer_enhanced.py
# import pandas as pd
# from app.extensions import db
# from app.models import State, Region, OldGroup, Group, District, User, Role

# def safe_strip(value):
#     """Safely strip any value - converts to string first"""
#     if value is None or pd.isna(value):
#         return ""
#     return str(value).strip()

# def create_group_user(group_name, group, district=None):
#     """
#     Create a user for a group with proper hierarchy links
#     Username/email format: groupname (lowercase, no spaces)
#     """
#     # Clean group name for email
#     clean_name = group_name.lower().replace(' ', '_').replace("'", "").replace("-", "_")
#     email = f"{clean_name}"
    
#     # Check if user already exists
#     existing_user = User.query.filter_by(email=email).first()
#     if existing_user:
#         print(f"📧 User already exists, updating: {email}")
#         user = existing_user
#     else:
#         print(f"👤 CREATING User: {email} for group '{group_name}'")
#         user = User(
#             email=email,
#             name=f"{group_name} Admin",
#             phone=None
#         )
#         user.set_password("12345678")  # Default password
    
#     # Set hierarchy links - CRITICAL FOR ACCESS CONTROL
#     user.state_id = group.state_id
#     user.region_id = group.region_id
#     user.district_id = district.id if district else None
    
#     # Assign Group Admin role
#     group_admin_role = Role.query.filter_by(name="Group Admin").first()
#     if group_admin_role and group_admin_role not in user.roles:
#         user.roles.append(group_admin_role)
#         print(f"✅ Assigned Group Admin role to {email}")
#     elif not group_admin_role:
#         print(f"⚠️  Warning: Group Admin role not found!")
    
#     if not existing_user:
#         db.session.add(user)
    
#     print(f"🔗 User {email} linked to - State: {user.state_id}, Region: {user.region_id}, District: {user.district_id}")
#     return user

# def import_hierarchy_from_excel(file_path, state_name, state_code="RIV-CEN", region_name="Rivers Central Region"):
#     """
#     Enhanced version that properly links users to hierarchy
#     """
#     print("=== Starting ENHANCED hierarchy import ===")
    
#     try:
#         # Read Excel file
#         df = pd.read_excel(file_path, sheet_name=0, header=None)
#         print(f"Loaded Excel with {len(df)} rows, {len(df.columns)} columns")
        
#         # Create state
#         state = State.query.filter_by(name=state_name).first()
#         if not state:
#             state = State(name=state_name, code=state_code)
#             db.session.add(state)
#             db.session.commit()
#             print(f"✅ Created state: {state_name} (ID: {state.id})")
#         else:
#             print(f"📁 Using existing state: {state_name} (ID: {state.id})")
        
#         # Create region
#         region = Region.query.filter_by(name=region_name, state_id=state.id).first()
#         if not region:
#             region = Region(
#                 name=region_name,
#                 code=region_name[:4].upper(),
#                 state_id=state.id
#             )
#             db.session.add(region)
#             db.session.commit()
#             print(f"✅ Created region: {region_name} (ID: {region.id})")
#         else:
#             print(f"📁 Using existing region: {region_name} (ID: {region.id})")
        
#         current_old_group = None
#         old_groups_created = 0
#         groups_created = 0
#         districts_created = 0
#         users_created = 0
        
#         # Track groups we process to avoid duplicates
#         processed_groups = set()
        
#         for index, row in df.iterrows():
#             # Convert all cells to strings for safe processing
#             row_str = [safe_strip(cell) for cell in row]
            
#             # Skip completely empty rows
#             if all(cell == '' for cell in row_str):
#                 continue
            
#             # DETECT OLD GROUP - Check ALL columns for "OLD GROUP"
#             for col_idx, cell_value in enumerate(row_str):
#                 if cell_value and "OLD GROUP" in cell_value.upper():
#                     old_group_name = cell_value
#                     print(f"\n🎯 FOUND OLD GROUP: '{old_group_name}'")
                    
#                     # Create the Old Group
#                     current_old_group = OldGroup(
#                         name=old_group_name,
#                         code=old_group_name.replace("OLD GROUP", "").strip()[:4].upper(),
#                         state_id=state.id,
#                         region_id=region.id
#                     )
#                     db.session.add(current_old_group)
#                     db.session.commit()
#                     old_groups_created += 1
#                     print(f"✅ CREATED OldGroup: {old_group_name} (ID: {current_old_group.id})")
#                     break
            
#             # Process groups and districts if we have a current Old Group
#             if current_old_group:
#                 for col_idx in range(len(row_str)):
#                     group_name = row_str[col_idx]
                    
#                     # Skip empty cells, numbers, and Old Group indicators
#                     if (not group_name or
#                         group_name.isdigit() or
#                         "OLD GROUP" in group_name.upper()):
#                         continue
                    
#                     # Check if this looks like a group name
#                     if (len(group_name.split()) >= 2 or
#                         any(word in group_name.upper() for word in ['GROUP', 'DISTRICT', 'UNIPORT', 'CORPER', 'FELLOWSHIP'])):
                        
#                         group_key = f"{group_name}_{current_old_group.id}"
#                         if group_key in processed_groups:
#                             continue
#                         processed_groups.add(group_key)
                        
#                         print(f"\n🎯 PROCESSING GROUP: '{group_name}' under '{current_old_group.name}'")
                        
#                         # Create the Group with proper hierarchy links
#                         group = Group(
#                             name=group_name,
#                             code=group_name[:4].upper(),
#                             state_id=state.id,
#                             region_id=region.id,
#                             old_group_id=current_old_group.id
#                         )
#                         db.session.add(group)
#                         db.session.commit()
#                         groups_created += 1
#                         print(f"✅ CREATED Group: {group_name} (ID: {group.id})")
                        
#                         # 🆕 CREATE USER FOR THIS GROUP with proper hierarchy links
#                         group_user = create_group_user(group_name, group)
#                         if group_user:
#                             users_created += 1
                        
#                         # Process districts under this group
#                         district_start_row = index + 1
#                         district_count = 0
                        
#                         for dist_row_idx in range(district_start_row, min(district_start_row + 30, len(df))):
#                             district_name = safe_strip(df.iloc[dist_row_idx, col_idx])
                            
#                             # Stop when we hit another group, Old Group, or empty row
#                             if (not district_name or
#                                 district_name.isdigit() or
#                                 any(word in district_name.upper() for word in ['GROUP', 'OLD GROUP']) or
#                                 dist_row_idx >= len(df)):
#                                 if district_count > 0:  # Only break if we found at least one district
#                                     break
#                                 else:
#                                     continue
                            
#                             # Get district code from column 0 of the same row
#                             district_code = safe_strip(df.iloc[dist_row_idx, 0])
#                             if not district_code or district_code.isdigit():
#                                 district_code = district_name[:4].upper()
                            
#                             # Only create district if it's a valid name
#                             if (district_name and
#                                 not district_name.isdigit() and
#                                 "GROUP" not in district_name.upper()):
                                
#                                 print(f"  🎯 FOUND DISTRICT: {district_name}")
                                
#                                 district = District(
#                                     name=district_name,
#                                     code=district_code,
#                                     state_id=state.id,
#                                     region_id=region.id,
#                                     old_group_id=current_old_group.id,
#                                     group_id=group.id
#                                 )
#                                 db.session.add(district)
#                                 db.session.commit()
#                                 districts_created += 1
#                                 district_count += 1
#                                 print(f"  ✅ CREATED District: {district_name} (ID: {district.id})")
                                
#                                 # 🆕 CREATE USER FOR THIS DISTRICT (Optional - uncomment if needed)
#                                 # district_user = create_group_user(
#                                 #     f"{district_name} District", 
#                                 #     group, 
#                                 #     district
#                                 # )
#                                 # if district_user:
#                                 #     users_created += 1
        
#         db.session.commit()
        
#         print(f"\n=== IMPORT SUMMARY ===")
#         print(f"✅ States: 1")
#         print(f"✅ Regions: 1") 
#         print(f"✅ Old Groups: {old_groups_created}")
#         print(f"✅ Groups: {groups_created}")
#         print(f"✅ Districts: {districts_created}")
#         print(f"✅ Users: {users_created}")
#         print("🎉 Enhanced import completed successfully!")
        
#         return {
#             "message": "Enhanced hierarchy imported successfully with proper user links!",
#             "summary": {
#                 "states": 1,
#                 "regions": 1,
#                 "old_groups": old_groups_created,
#                 "groups": groups_created,
#                 "districts": districts_created,
#                 "users": users_created
#             }
#         }
        
#     except Exception as e:
#         db.session.rollback()
#         print(f"❌ IMPORT FAILED: {str(e)}")
#         import traceback
#         print(f"Traceback: {traceback.format_exc()}")
#         raise e

