import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dairy.settings')
django.setup()

from django.template import Template, Context
from django.contrib.auth.models import User

u = User.objects.get(username='AuditManager')

template_content = """
{% if user.profile.role == 'CEO' %}
CEO
{% elif user.profile.role == 'GM' or user.profile.role == 'GM_HR' %}
GM
{% elif user.profile.role == 'Manager' or user.profile.role == 'ZM' or user.profile.role == 'AM' or user.profile.role == 'IT' or user.profile.role == 'CFO' or 'Asis' in user.username or 'PMER' in user.username or 'Audit' in user.username %}
Manager
{% elif user.profile.role == 'PS' %}
PS
{% else %}
ELSE
{% endif %}
"""

t = Template(template_content)
print("Rendered:", t.render(Context({'user': u})).strip())
