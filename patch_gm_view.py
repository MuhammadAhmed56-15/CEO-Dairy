import re

with open('core/views.py', 'r', encoding='utf-8') as f:
    content = f.read()

new_func = """def gm_dashboard(request):
    from django.db.models import Q, Count
    from .models import Notesheet, NotesheetForward, File, Letter, Task, Commitment, Profile
    from django.utils import timezone
    from datetime import timedelta

    today = timezone.now()
    next_week = today + timedelta(days=7)

    # 1. Notesheets Data (My files, My inbox, My outbox)
    ns_files = File.objects.filter(created_by=request.user).order_by('-created_at')
    ns_inbox = Notesheet.objects.filter(current_holder=request.user).order_by('-updated_at')
    
    ns_forwarded_ids = NotesheetForward.objects.filter(forwarded_by=request.user).values_list('notesheet_id', flat=True)
    ns_outbox = Notesheet.objects.filter(
        Q(created_by=request.user) | Q(id__in=ns_forwarded_ids)
    ).exclude(current_holder=request.user).distinct().order_by('-updated_at')

    ns_total_count = Notesheet.objects.filter(
        Q(current_holder=request.user) | Q(created_by=request.user) | Q(id__in=ns_forwarded_ids)
    ).distinct().count()

    ns_status_counts = {
        'Files': ns_files.count(),
        'Inbox': ns_inbox.count(),
        'Outbox': ns_outbox.count()
    }
    ns_category_labels = list(ns_status_counts.keys())
    ns_category_data = list(ns_status_counts.values())

    # 2. Tasks Data (Tasks assigned TO or BY the GM)
    my_tasks = Task.objects.filter(Q(assigned_to=request.user) | Q(assigned_by=request.user)).distinct()
    
    tasks_total = my_tasks.order_by('-created_at')
    tasks_pending = my_tasks.exclude(status='Completed').order_by('-created_at')
    tasks_completed = my_tasks.filter(status='Completed').order_by('-created_at')
    tasks_overdue = my_tasks.filter(due_date__lt=today.date()).exclude(status='Completed').order_by('-created_at')
    
    upcoming_tasks = my_tasks.filter(
        due_date__range=(today.date(), next_week.date())
    ).exclude(status='Completed').order_by('due_date')

    task_status_counts = my_tasks.values('status').annotate(count=Count('id'))
    task_category_labels = [item['status'] if item['status'] else 'Uncategorized' for item in task_status_counts]
    task_category_data = [item['count'] for item in task_status_counts]

    # 3. Letters Data (My letters)
    letters_inbox = Letter.objects.filter(receiver=request.user, is_draft=False).order_by('-created_at')
    letters_outbox = Letter.objects.filter(sender=request.user, is_draft=False).order_by('-created_at')
    letters_drafts = Letter.objects.filter(sender=request.user, is_draft=True).order_by('-created_at')
    
    letters_total = list(letters_inbox) + list(letters_outbox) + list(letters_drafts)
    
    letters_drafts_count = letters_drafts.count()
    letters_inbox_count = letters_inbox.count()
    letters_outbox_count = letters_outbox.count()
    letters_total_count = len(letters_total)

    letter_category_labels = ['Inbox', 'Outbox', 'Drafts']
    letter_category_data = [letters_inbox_count, letters_outbox_count, letters_drafts_count]

    context = {
        # Notesheets lists/counts
        "ns_total_count": ns_total_count,
        "ns_files_count": ns_files.count(),
        "ns_inbox_count": ns_inbox.count(),
        "ns_outbox_count": ns_outbox.count(),
        "ns_files_list": ns_files,
        "ns_inbox_list": ns_inbox,
        "ns_outbox_list": ns_outbox,
        "ns_category_labels": ns_category_labels,
        "ns_category_data": ns_category_data,

        # Tasks lists/counts
        "tasks_total_count": tasks_total.count(),
        "tasks_pending_count": tasks_pending.count(),
        "tasks_completed_count": tasks_completed.count(),
        "tasks_overdue_count": tasks_overdue.count(),
        "tasks_total_list": tasks_total,
        "tasks_pending_list": tasks_pending,
        "tasks_completed_list": tasks_completed,
        "tasks_overdue_list": tasks_overdue,
        "upcoming_tasks": upcoming_tasks,
        "task_category_labels": task_category_labels,
        "task_category_data": task_category_data,

        # Letters lists/counts
        "letters_total_count": letters_total_count,
        "letters_drafts_count": letters_drafts_count,
        "letters_outbox_count": letters_outbox_count,
        "letters_inbox_count": letters_inbox_count,
        "letters_total_list": letters_total,
        "letters_drafts_list": letters_drafts,
        "letters_outbox_list": letters_outbox,
        "letters_inbox_list": letters_inbox,
        "letter_category_labels": letter_category_labels,
        "letter_category_data": letter_category_data,
    }
    
    return render(request, 'gm_dashboard.html', context)
"""

# Find def gm_dashboard and replace it up to return render(request, 'gm_dashboard.html', context)
pattern = re.compile(r"def gm_dashboard\(request\):.*?return render\(request, 'gm_dashboard\.html', context\)", re.DOTALL)
new_content = pattern.sub(new_func, content)

with open('core/views.py', 'w', encoding='utf-8') as f:
    f.write(new_content)
print("Updated gm_dashboard view in views.py")
