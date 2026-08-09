import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dairy.settings')
django.setup()

from core.models import Remark
from django.db.models import Count

# Find duplicates
duplicates = Remark.objects.values('task', 'manager', 'feedback').annotate(Count('id')).filter(id__count__gt=1)

for dup in duplicates:
    remarks = Remark.objects.filter(
        task=dup['task'],
        manager=dup['manager'],
        feedback=dup['feedback']
    ).order_by('created_at')
    
    # Keep the first one, delete the rest
    for remark in remarks[1:]:
        print(f"Deleting duplicate remark: {remark.id}")
        remark.delete()

print("Duplicate remarks removed successfully.")
