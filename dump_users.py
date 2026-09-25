import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dairy.settings")
django.setup()

from core.models import User

users = User.objects.all()
for u in users:
    if hasattr(u, 'profile'):
        role_cat = u.profile.role.category if u.profile.role else 'None'
        role_code = u.profile.role.code if u.profile.role else 'None'
        if 'WS' in role_code or 'ws' in u.username.lower():
            zone_name = u.profile.zone.name if u.profile.zone else 'None'
            print(f"User: {u.username}, Full Name: {u.get_full_name()}, Role: {role_code}, Cat: {role_cat}, Zone: {zone_name}")
