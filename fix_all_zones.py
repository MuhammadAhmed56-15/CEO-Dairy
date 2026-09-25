import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dairy.settings")
django.setup()

from core.models import User, Zone

users = User.objects.all()
zones = {z.name: z for z in Zone.objects.all()}

for u in users:
    if hasattr(u, 'profile') and u.profile.role:
        role_code = u.profile.role.code
        
        # If the user's zone is not set, try to infer it from their role_code
        if u.profile.zone is None:
            inferred_zone = None
            if 'ZoneA' in role_code or 'Zone A' in role_code or role_code.endswith('A'):
                inferred_zone = 'A'
            elif 'ZoneB' in role_code or 'Zone B' in role_code or role_code.endswith('B'):
                inferred_zone = 'B'
            elif 'ZoneC' in role_code or 'Zone C' in role_code or role_code.endswith('C'):
                inferred_zone = 'C'
            elif 'ZoneD' in role_code or 'Zone D' in role_code or role_code.endswith('D'):
                inferred_zone = 'D'
            elif 'ZoneE' in role_code or 'Zone E' in role_code or role_code.endswith('E'):
                inferred_zone = 'E'

            if inferred_zone and inferred_zone in zones:
                print(f"Fixing User: {u.username}, Role: {role_code} -> assigning to Zone {inferred_zone}")
                u.profile.zone = zones[inferred_zone]
                u.profile.save()
