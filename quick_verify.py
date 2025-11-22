# quick_verify.py
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.extensions import db
from app.models import State, Region, OldGroup, Group, District, User

app = create_app()
with app.app_context():
    print("🔍 Verifying cleanup...")
    print(f"States: {State.query.count()}")
    print(f"Regions: {Region.query.count()}")
    print(f"Old Groups: {OldGroup.query.count()}")
    print(f"Groups: {Group.query.count()}")
    print(f"Districts: {District.query.count()}")
    
    # Check for remaining auto-users
    auto_users = User.query.filter(
        (User.email.like('%@thedcmp.org')) |
        (User.email.notlike('%@%'))
    ).count()
    print(f"Remaining auto-users: {auto_users}")
    
    if all([State.query.count() == 0, Region.query.count() == 0, 
            OldGroup.query.count() == 0, Group.query.count() == 0,
            District.query.count() == 0, auto_users == 0]):
        print("🎉 Database is clean and ready for new import!")
    else:
        print("❌ Database still has data - run cleanup again")