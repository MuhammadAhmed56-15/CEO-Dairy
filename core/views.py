from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
from django.db.models import Count
from django.views.decorators.csrf import ensure_csrf_cookie
from .models import Profile, Commitment, Task, NotesheetAttachment, UserHierarchy  # Saare models aik saath
from .forms import CommitmentForm, RemarkForm, TaskAssignForm
from .utils import create_notification
# =========================================================
# LOGIN VIEW (UPDATED FOR CFO)
# =========================================================
@ensure_csrf_cookie
def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            profile = Profile.objects.get(user=user)
            
            # Role-based redirect
            if profile.role == "CEO":
                return redirect("ceo_dashboard")
            elif profile.role == "PS":
                return redirect("ps_dashboard")
            elif profile.role == "GM":
                return redirect("gm_dashboard")
            elif profile.role in ["Manager", "ZM", "AM", "IT", "CFO", "HR"]:
                return redirect("manager_dashboard")
            else:
                messages.error(request, "Role not recognized")
                return redirect("login")
        else:
            messages.error(request, "Invalid username or password")
    return render(request, "login.html")

# =========================================================
# LOGOUT VIEW
# =========================================================
@login_required
def logout_view(request):
    logout(request)
    return redirect("login")

# =========================================================
# PS DASHBOARD
# =========================================================
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Count
from datetime import timedelta, datetime
from .models import Profile, Commitment
import json

@login_required
def ps_dashboard(request):
    profile = Profile.objects.get(user=request.user)
    if profile.role != "PS":
        return redirect("ceo_dashboard")

    # KPI counts
    total = Commitment.objects.filter(created_by=profile).count()
    pending = Commitment.objects.filter(created_by=profile, status="Pending").count()
    approved = Commitment.objects.filter(created_by=profile, status="Approved").count()
    rejected = Commitment.objects.filter(created_by=profile, status="Rejected").count()

    # Lists for modal display
    all_commitments = Commitment.objects.filter(created_by=profile).order_by('-commitment_date')
    pending_list = Commitment.objects.filter(created_by=profile, status="Pending").order_by('-commitment_date')
    approved_list = Commitment.objects.filter(created_by=profile, status="Approved").order_by('-commitment_date')
    rejected_list = Commitment.objects.filter(created_by=profile, status="Rejected").order_by('-commitment_date')

    # Convert querysets to JSON for JavaScript
    def commitment_to_dict(c):
        # handle date vs datetime comparisons safely
        is_overdue = False
        if c.commitment_date:
            try:
                if hasattr(c.commitment_date, 'hour'):
                    is_overdue = (c.commitment_date < timezone.now() and c.status != 'Completed')
                else:
                    is_overdue = (c.commitment_date < timezone.now().date() and c.status != 'Completed')
            except Exception:
                is_overdue = False

        return {
            'id': c.id,
            'title': c.title,
            'description': c.description,
            'location': c.location,
            'category': c.category,
            'status': c.status,
            'date': c.commitment_date.strftime('%b %d, %Y'),
            'time': c.commitment_date.strftime('%I:%M %p'),
            'datetime': c.commitment_date.strftime('%Y-%m-%d %H:%M'),
            'is_overdue': is_overdue
        }

    all_commitments_json = json.dumps([commitment_to_dict(c) for c in all_commitments])
    pending_list_json = json.dumps([commitment_to_dict(c) for c in pending_list])
    approved_list_json = json.dumps([commitment_to_dict(c) for c in approved_list])
    rejected_list_json = json.dumps([commitment_to_dict(c) for c in rejected_list])

    today = timezone.now()
    next_week = today + timedelta(days=7)

    upcoming = Commitment.objects.filter(
        created_by=profile,
        commitment_date__range=(today, next_week)
    ).order_by('commitment_date')

    # Commitment category / daily charts
    category_counts = Commitment.objects.filter(created_by=profile).values('category').annotate(count=Count('id'))
    category_labels = [item['category'] for item in category_counts]
    category_data = [item['count'] for item in category_counts]

    daily_labels = []
    daily_data = []
    for i in range(7):
        day = today + timedelta(days=i)
        daily_labels.append(day.strftime("%Y-%m-%d"))
        cnt = Commitment.objects.filter(created_by=profile, commitment_date__date=day.date()).count()
        daily_data.append(cnt)

    com_category_counts = Commitment.objects.filter(created_by=profile).values('category').annotate(count=Count('id'))
    com_category_labels = [item['category'] if item['category'] else 'Uncategorized' for item in com_category_counts]
    com_category_data = [item['count'] for item in com_category_counts]

    # ============================================================
    # NOTESHEET DATA
    # ============================================================
    from django.db.models import Q
    from .models import Notesheet, NotesheetForward, File, Letter, Task

    ns_files = File.objects.filter(created_by=request.user).order_by('-created_at')
    ns_inbox = Notesheet.objects.filter(current_holder=request.user).order_by('-updated_at')
    ns_forwarded_ids = NotesheetForward.objects.filter(forwarded_by=request.user).values_list('notesheet_id', flat=True)
    ns_outbox = Notesheet.objects.filter(
        Q(created_by=request.user) | Q(id__in=ns_forwarded_ids)
    ).exclude(current_holder=request.user).distinct().order_by('-updated_at')

    ns_total_count = Notesheet.objects.filter(
        Q(current_holder=request.user) | Q(created_by=request.user) | Q(id__in=ns_forwarded_ids)
    ).distinct().count()

    ns_status_counts = {'Files': ns_files.count(), 'Inbox': ns_inbox.count(), 'Outbox': ns_outbox.count()}
    ns_category_labels = list(ns_status_counts.keys())
    ns_category_data = list(ns_status_counts.values())

    # ============================================================
    # TASK DATA
    # ============================================================
    tasks_total = Task.objects.filter(
        Q(assigned_to=request.user) | Q(assigned_by=request.user)
    ).distinct().order_by('-created_at')
    tasks_pending = tasks_total.exclude(status='Completed').order_by('-created_at')
    tasks_completed = tasks_total.filter(status='Completed').order_by('-created_at')
    tasks_overdue = tasks_total.filter(due_date__lt=today.date()).exclude(status='Completed').order_by('-created_at')
    upcoming_tasks = tasks_total.filter(
        due_date__range=(today.date(), next_week.date())
    ).exclude(status='Completed').order_by('due_date')
    task_status_counts = tasks_total.values('status').annotate(count=Count('id'))
    task_category_labels = [item['status'] if item['status'] else 'Uncategorized' for item in task_status_counts]
    task_category_data = [item['count'] for item in task_status_counts]

    # ============================================================
    # LETTER DATA
    # ============================================================
    letters_total = Letter.objects.filter(
        Q(sender=request.user) | Q(receiver=request.user)
    ).distinct().order_by('-created_at')
    letters_inbox = Letter.objects.filter(receiver=request.user, is_draft=False).order_by('-created_at')
    letters_outbox = Letter.objects.filter(sender=request.user, is_draft=False).order_by('-created_at')
    letters_drafts = Letter.objects.filter(sender=request.user, is_draft=True).order_by('-created_at')

    letters_drafts_count = letters_drafts.count()
    letters_inbox_count = letters_inbox.count()
    letters_outbox_count = letters_outbox.count()
    letters_total_count = letters_total.count()
    letter_category_labels = ['Inbox', 'Outbox', 'Drafts']
    letter_category_data = [letters_inbox_count, letters_outbox_count, letters_drafts_count]

    context = {
        # Legacy commitment keys (keep for backward compat)
        "total": total, "pending": pending, "approved": approved, "rejected": rejected,
        "all_commitments_json": all_commitments_json,
        "pending_list_json": pending_list_json,
        "approved_list_json": approved_list_json,
        "rejected_list_json": rejected_list_json,
        "approved_list": approved_list,
        "upcoming": upcoming,
        "category_labels": category_labels,
        "category_data": category_data,
        "daily_labels": daily_labels,
        "daily_data": daily_data,

        # CEO-style commitment keys
        "com_total": total, "com_pending": pending, "com_approved": approved, "com_rejected": rejected,
        "com_total_list": all_commitments,
        "com_pending_list": pending_list,
        "com_approved_list": approved_list,
        "com_rejected_list": rejected_list,
        "com_category_labels": com_category_labels,
        "com_category_data": com_category_data,

        # Notesheets
        "ns_total_count": ns_total_count,
        "ns_files_count": ns_files.count(), "ns_inbox_count": ns_inbox.count(), "ns_outbox_count": ns_outbox.count(),
        "ns_files_list": ns_files, "ns_inbox_list": ns_inbox, "ns_outbox_list": ns_outbox,
        "ns_category_labels": ns_category_labels, "ns_category_data": ns_category_data,

        # Tasks
        "tasks_total_count": tasks_total.count(), "tasks_pending_count": tasks_pending.count(),
        "tasks_completed_count": tasks_completed.count(), "tasks_overdue_count": tasks_overdue.count(),
        "tasks_total_list": tasks_total, "tasks_pending_list": tasks_pending,
        "tasks_completed_list": tasks_completed, "tasks_overdue_list": tasks_overdue,
        "upcoming_tasks": upcoming_tasks,
        "task_category_labels": task_category_labels, "task_category_data": task_category_data,

        # Letters
        "letters_total_count": letters_total_count, "letters_drafts_count": letters_drafts_count,
        "letters_outbox_count": letters_outbox_count, "letters_inbox_count": letters_inbox_count,
        "letters_total_list": letters_total, "letters_drafts_list": letters_drafts,
        "letters_outbox_list": letters_outbox, "letters_inbox_list": letters_inbox,
        "letter_category_labels": letter_category_labels, "letter_category_data": letter_category_data,
    }
    return render(request, "ps_dashboard.html", context)

# =========================================================
# PS CHART DATA API - ENDPOINT FOR DYNAMIC CHART
# =========================================================
@login_required
def get_ps_chart_data(request):
    """
    API endpoint to get PS chart data for specific date ranges.
    Supports sections: notesheet, commitment, task, letter
    Usage: /api/ps-chart-data/?dates=2026-01-22,2026-01-23&section=notesheet
    """
    from .models import Notesheet, Task, Letter
    profile = Profile.objects.get(user=request.user)
    if profile.role != "PS":
        return JsonResponse({'error': 'Unauthorized'}, status=403)

    dates_str = request.GET.get('dates', '')
    section   = request.GET.get('section', 'commitment')

    if not dates_str:
        return JsonResponse({'error': 'No dates provided'}, status=400)

    dates = dates_str.split(',')
    data  = []

    for date_str in dates:
        try:
            date = datetime.strptime(date_str.strip(), '%Y-%m-%d').date()
            if section == 'notesheet':
                count = Notesheet.objects.filter(created_by=request.user, created_at__date=date).count()
            elif section == 'task':
                from django.db.models import Q as _Q
                count = Task.objects.filter(
                    _Q(assigned_to=request.user) | _Q(assigned_by=request.user),
                    created_at__date=date
                ).distinct().count()
            elif section == 'letter':
                count = Letter.objects.filter(sender=request.user, created_at__date=date).count()
            else:
                count = Commitment.objects.filter(created_by=profile, commitment_date__date=date).count()
            data.append(count)
        except ValueError:
            data.append(0)

    return JsonResponse(data, safe=False)

# =========================================================
# CEO DASHBOARD 
# =========================================================
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Count, Q
from datetime import timedelta, datetime
from .models import Profile, Commitment, Task, User
from .forms import CommitmentForm, TaskAssignForm

@login_required
def ceo_dashboard(request):
    from django.db.models import Q
    from django.db.models import Count
    from .models import Notesheet, NotesheetForward, File, Letter, LetterFile, Task, Commitment, Profile

    profile = Profile.objects.get(user=request.user)
    if profile.role != "CEO":
        return redirect("ps_dashboard")

    today = timezone.now()
    next_week = today + timedelta(days=7)

    # 1. Commitments Data (Whole system base)
    com_total_list = Commitment.objects.all()
    com_pending_list = Commitment.objects.filter(status__iexact="Pending")
    com_approved_list = Commitment.objects.filter(status__iexact="Approved")
    com_rejected_list = Commitment.objects.filter(status__iexact="Rejected")

    upcoming = Commitment.objects.filter(
        commitment_date__range=(today, next_week), 
        status__iexact="Approved"
    ).order_by('commitment_date')

    # Commitments Category breakdown for Pie Chart
    com_category_counts = Commitment.objects.values('category').annotate(count=Count('id'))
    com_category_labels = [item['category'] if item['category'] else 'Uncategorized' for item in com_category_counts]
    com_category_data = [item['count'] for item in com_category_counts]

    # 2. Notesheets Data (My files, My inbox, My outbox)
    ns_files = File.objects.filter(created_by=request.user).order_by('-created_at')
    ns_inbox = Notesheet.objects.filter(current_holder=request.user).order_by('-updated_at')
    
    ns_forwarded_ids = NotesheetForward.objects.filter(forwarded_by=request.user).values_list('notesheet_id', flat=True)
    ns_outbox = Notesheet.objects.filter(
        Q(created_by=request.user) | Q(id__in=ns_forwarded_ids)
    ).exclude(current_holder=request.user).distinct().order_by('-updated_at')

    # Notesheet total in hand or created
    ns_total_count = Notesheet.objects.filter(
        Q(current_holder=request.user) | Q(created_by=request.user) | Q(id__in=ns_forwarded_ids)
    ).distinct().count()

    # Notesheet status count for Pie chart
    ns_status_counts = {
        'Files': ns_files.count(),
        'Inbox': ns_inbox.count(),
        'Outbox': ns_outbox.count()
    }
    ns_category_labels = list(ns_status_counts.keys())
    ns_category_data = list(ns_status_counts.values())

    # 3. Tasks Data (Whole system)
    tasks_total = Task.objects.all().order_by('-created_at')
    tasks_pending = Task.objects.exclude(status='Completed').order_by('-created_at')
    tasks_completed = Task.objects.filter(status='Completed').order_by('-created_at')
    
    # Overdue Tasks (due_date < today and not completed)
    tasks_overdue = Task.objects.filter(
        due_date__lt=today.date()
    ).exclude(status='Completed').order_by('-created_at')

    # Upcoming Tasks (Next 7 days, pending/seen/in progress)
    upcoming_tasks = Task.objects.filter(
        due_date__range=(today.date(), next_week.date())
    ).exclude(status='Completed').order_by('due_date')

    # Task Status breakdown for Pie Chart
    task_status_counts = Task.objects.values('status').annotate(count=Count('id'))
    task_category_labels = [item['status'] if item['status'] else 'Uncategorized' for item in task_status_counts]
    task_category_data = [item['count'] for item in task_status_counts]

    # 4. Letters Data (Whole system)
    letters_total = Letter.objects.all().order_by('-created_at')
    letters_inbox = Letter.objects.filter(receiver=request.user, is_draft=False).order_by('-created_at')
    letters_outbox = Letter.objects.filter(sender=request.user, is_draft=False).order_by('-created_at')
    letters_drafts = Letter.objects.filter(sender=request.user, is_draft=True).order_by('-created_at')
    
    letters_drafts_count = letters_drafts.count()
    letters_inbox_count = letters_inbox.count()
    letters_outbox_count = letters_outbox.count()
    letters_total_count = letters_total.count()

    # Letter status breakdown (Inbox vs Outbox vs Drafts) for Pie Chart
    letter_category_labels = ['Inbox', 'Outbox', 'Drafts']
    letter_category_data = [letters_inbox_count, letters_outbox_count, letters_drafts_count]

    # Render context
    context = {
        # Commitments lists/counts
        "com_total": com_total_list.count(),
        "com_pending": com_pending_list.count(),
        "com_approved": com_approved_list.count(),
        "com_rejected": com_rejected_list.count(),
        "com_total_list": com_total_list,
        "com_pending_list": com_pending_list,
        "com_approved_list": com_approved_list,
        "com_rejected_list": com_rejected_list,
        "upcoming": upcoming,
        "com_category_labels": com_category_labels,
        "com_category_data": com_category_data,

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

    return render(request, "ceo_dashboard.html", context)

# =========================================================
# CHART DATA API - FOR DYNAMIC CHART
# =========================================================
@login_required
def get_chart_data(request):
    """API endpoint to get chart data for specific date ranges"""
    from datetime import datetime
    from .models import Commitment, Notesheet, Task, Letter, Profile
    
    profile = Profile.objects.get(user=request.user)
    if profile.role != "CEO":
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    dates_str = request.GET.get('dates', '')
    section = request.GET.get('section', 'commitment')
    
    if not dates_str:
        return JsonResponse({'error': 'No dates provided'}, status=400)
    
    dates = dates_str.split(',')
    data = []
    
    for date_str in dates:
        try:
            date = datetime.strptime(date_str.strip(), '%Y-%m-%d').date()
            if section == 'notesheet':
                initiated = Notesheet.objects.filter(created_by=request.user, created_at__date=date).count()
                data.append(initiated)
            elif section == 'task':
                created = Task.objects.filter(created_at__date=date).count()
                data.append(created)
            elif section == 'letter':
                sent = Letter.objects.filter(sender=request.user, created_at__date=date).count()
                data.append(sent)
            else:
                count = Commitment.objects.filter(
                    commitment_date__date=date,
                    status__iexact="Approved"
                ).count()
                data.append(count)
        except ValueError:
            data.append(0)
    
    return JsonResponse(data, safe=False)

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.contrib.auth.models import User
from .models import Profile, Commitment
from .forms import CommitmentForm


# =========================================================
# 1. ADD COMMITMENT
# =========================================================
@login_required
def add_commitment(request):
    profile = get_object_or_404(Profile, user=request.user)

    managers = User.objects.filter(
        profile__role="Manager",
        profile__employee__isnull=False
    ).select_related("profile__employee")

    if request.method == "POST":
        form = CommitmentForm(request.POST, user=request.user)
        if form.is_valid():
            commitment = form.save(commit=False)
            commitment.created_by = profile

            # PS add kare toh 'Pending', CEO add kare toh direkt 'Approved'
            if profile.role == "PS":
                commitment.status = "Pending"
            elif profile.role == "CEO":
                commitment.status = "Approved"

            commitment.save()

            invited_ids = request.POST.getlist("invited_managers")
            commitment.invited_managers.set(invited_ids)

            for user_id in invited_ids:
                try:
                    manager_user = User.objects.get(id=user_id)
                    create_notification(
                        recipient=manager_user,
                        sender=request.user,
                        title="New Commitment Assigned",
                        message=f"You have been assigned to a new commitment: '{commitment.title}' by {request.user.username}",
                        link=f"/commitment/list/",
                        notification_type='commitment'
                    )
                except User.DoesNotExist:
                    pass

            messages.success(request, "Commitment added successfully!")
            return redirect("ceo_dashboard" if profile.role == "CEO" else "ps_dashboard")
    else:
        form = CommitmentForm(user=request.user)

    return render(request, "add_commitment.html", {"form": form, "managers": managers})


# =========================================================
# 2. EDIT COMMITMENT
# =========================================================
@login_required
def edit_commitment(request, pk):
    profile = get_object_or_404(Profile, user=request.user)
    commitment = get_object_or_404(Commitment, pk=pk)

    if commitment.is_expired and profile.role != "CEO":
        messages.error(request, "Cannot edit expired commitments!")
        return redirect("ps_dashboard" if profile.role == "PS" else "commitment_list")

    if profile.role == "CEO" or commitment.created_by == profile:
        if request.method == "POST":
            form = CommitmentForm(request.POST, instance=commitment, user=request.user)
            if form.is_valid():
                updated_commitment = form.save(commit=False)
                if profile.role == "PS":
                    updated_commitment.status = "Pending"
                updated_commitment.save()
                form.save_m2m()

                messages.success(request, "Commitment updated successfully!")
                return redirect("ceo_dashboard" if profile.role == "CEO" else "ps_dashboard")
        else:
            form = CommitmentForm(instance=commitment, user=request.user)

        return render(request, "edit_commitment.html", {"form": form, "commitment": commitment})
    else:
        messages.error(request, "You are not authorized to edit this!")
        return redirect("ps_dashboard")


# =========================================================
# 3. UPDATE STATUS (CEO Approval Action)
# =========================================================
@login_required
def update_status(request, pk, status):
    """CEO approves or rejects a commitment"""
    profile = get_object_or_404(Profile, user=request.user)
    if profile.role != "CEO":
        messages.error(request, "Not authorized")
        return redirect("ps_dashboard")

    commitment = get_object_or_404(Commitment, pk=pk)
    if status in ["Approved", "Rejected"]:
        commitment.status = status
        commitment.save()


        messages.success(request, f"Commitment {status.lower()} successfully!")
    return redirect("ceo_dashboard")


# =========================================================
# 4. DELETE COMMITMENT
# =========================================================
@login_required
def delete_commitment(request, pk):
    profile = get_object_or_404(Profile, user=request.user)
    commitment = get_object_or_404(Commitment, pk=pk)

    if profile.role == "CEO" or commitment.created_by == profile:
        commitment.delete()
        messages.success(request, "Deleted successfully!")
    else:
        messages.error(request, "You cannot delete this!")

    return redirect("ceo_dashboard" if profile.role == "CEO" else "ps_dashboard")


# =========================================================
# 5. COMMITMENT LIST (ALL COMMITMENTS FOR CEO & PS)
# =========================================================
@login_required
def commitment_list(request):
    profile = get_object_or_404(Profile, user=request.user)
    today = timezone.now()
    status_filter = request.GET.get('status')

    # Quick Inline Approval Logic (CEO Modal / Table Actions)
    if profile.role == "CEO" and request.method == "POST":
        commitment_id = request.POST.get("commitment_id")
        action = request.POST.get("action")
        try:
            commitment = Commitment.objects.get(id=commitment_id)
            if action == "approve":
                commitment.status = "Approved"
            elif action == "reject":
                commitment.status = "Rejected"
            commitment.save()
            messages.success(request, f"Commitment {commitment.status.lower()} successfully!")
        except Commitment.DoesNotExist:
            pass
        return redirect("commitment_list")

    # ── FIXED QUERY LOGIC ──
    # CEO aur PS DONO ko TAMAM Commitments show hongi
    if profile.role in ["CEO", "PS"]:
        commitments = Commitment.objects.select_related('created_by__user').all().order_by('-created_at')
    else:
        commitments = Commitment.objects.none()

    # Status filter (Agar user dropdown filtering use kare)
    if status_filter and status_filter != 'All':
        commitments = commitments.filter(status=status_filter)

    return render(request, 'commitment_list.html', {
        'commitments': commitments,
        'today': today,
        'profile': profile,
    })

@login_required
def commitment_report(request):
    profile = Profile.objects.get(user=request.user)

    if profile.role == "CEO":
        commitments = Commitment.objects.all().order_by('-commitment_date')
    elif profile.role == "PS":
        commitments = Commitment.objects.filter(created_by=profile).order_by('-commitment_date')
    else:
        commitments = Commitment.objects.none()

    status_filter = request.GET.get('status')
    category_filter = request.GET.get('category')
    priority_filter = request.GET.get('priority')
    search_query = request.GET.get('search')

    if status_filter and status_filter != 'All':
        commitments = commitments.filter(status=status_filter)
    if category_filter and category_filter != 'All':
        commitments = commitments.filter(category=category_filter)
    if priority_filter and priority_filter != 'All':
        commitments = commitments.filter(priority=priority_filter)
    if search_query:
        commitments = commitments.filter(
            Q(title__icontains=search_query) | Q(description__icontains=search_query)
        )

    context = {
        'commitments': commitments,
        'status_choices': ['All'] + [choice[0] for choice in Commitment.STATUS_CHOICES],
        'category_choices': ['All', 'Meeting', 'Visit', 'Event'],
        'priority_choices': ['All', 'Normal', 'High'],
        'selected_status': status_filter or 'All',
        'selected_category': category_filter or 'All',
        'selected_priority': priority_filter or 'All',
        'search_query': search_query or ''
    }
    return render(request, 'report.html', context)

@login_required
def approve_commitment(request, id):
    commitment = get_object_or_404(Commitment, id=id)
    commitment.status = "Approved"
    commitment.save()
    return redirect("manager_dashboard")

@login_required
def reject_commitment(request, id):
    commitment = get_object_or_404(Commitment, id=id)
    commitment.status = "Rejected"
    commitment.save()
    return redirect("manager_dashboard")

# =========================================================
# TASK MODULE (Line 547 se Aage Fully Fixed Code)
# =========================================================

# 1. ASSIGN / ADD TASK VIEW
@login_required
def assign_task_view(request):
    role = getattr(request.user.profile, 'role', '')
    
    # Removed ZM Users restriction to allow access


    # Dynamic Dropdown Filters
    username_upper = request.user.username.upper()
    if role == 'CFO':
        filtered_users = User.objects.filter(username__in=['FINANCE_MANAGER', 'BILLING_MANAGER'])
    elif role == 'CEO':
        filtered_users = User.objects.exclude(id=request.user.id)
    elif role == 'GM_HR' or username_upper == 'GM_HR':
        filtered_users = User.objects.filter(username__iexact='Asis_Manager_Hr')
    elif username_upper == 'PROJECT_MANAGER':
        filtered_users = User.objects.filter(username__iexact='Asis_Manager_Pro')
    elif username_upper == 'FINANCE_MANAGER':
        filtered_users = User.objects.filter(username__iexact='Asis_Manager_Finance')
    elif username_upper == 'MANAGER_MEDIA':
        filtered_users = User.objects.filter(username__iexact='Asis_Manager_Media')
    elif username_upper == 'BILLING_MANAGER':
        filtered_users = User.objects.filter(username__iexact='Asis_Manager_Billing')
    elif username_upper == 'AUDIT_MANAGER':
        filtered_users = User.objects.filter(username__iexact='Asis_Manager_Audit')
    elif username_upper == 'MANAGER_PMER':
        filtered_users = User.objects.filter(username__iexact='Asis_Manager_PMER')
    elif username_upper == 'FLEET_MANAGER':
        filtered_users = User.objects.filter(username__in=['Fleet_Officer_A', 'Fleet_Officer_B', 'Fleet_Officer_C', 'Fleet_Officer_D', 'Fleet_Officer_E'])
    else:
        hierarchy = UserHierarchy.objects.filter(boss=request.user).first()
        if hierarchy:
            filtered_users = hierarchy.subordinates.all()
        else:
            filtered_users = User.objects.exclude(id=request.user.id)
            
        if role in ['CEO', 'GM'] and username_upper != 'GM_HR':
            cfo_user = User.objects.filter(username='CFO')
            filtered_users = (filtered_users | cfo_user).distinct()

    if request.method == "POST":
        form = TaskAssignForm(request.POST)
        form.fields['assigned_to'].queryset = filtered_users
        
        if form.is_valid():
            task = form.save(commit=False)
            task.assigned_by = request.user 
            task.save()
            task.save()
            
            create_notification(
                recipient=task.assigned_to,
                sender=request.user,
                title="New Task Assigned",
                message=f"You have been assigned a new task: '{task.title}' by {request.user.username}",
                link="/manager/tasks/",
                notification_type='task'
            )
            
            messages.success(request, f"Task '{task.title}' has been successfully assigned to {task.assigned_to.username}!")
            return redirect('all_tasks')
    else:
        form = TaskAssignForm()
        form.fields['assigned_to'].queryset = filtered_users
    
    return render(request, 'ceo_assign_task.html', {
        'form': form,
        'user_role': role
    })

# Aliases for Assign Task
add_task_view = assign_task_view


# 2. MY TASKS (INBOX)
@login_required
def manager_task_view(request):
    status_filter = request.GET.get('status')
    
    # Jo tasks CURRENT LOGIN USER ko assign hue hain
    base_tasks = Task.objects.filter(assigned_to=request.user)

    # Mark as Seen automatically
    unseen_tasks = base_tasks.filter(is_seen=False)
    if unseen_tasks.exists():
        unseen_tasks.update(is_seen=True, seen_at=timezone.now())

    tasks = base_tasks.order_by('-created_at')

    if status_filter and status_filter.lower() != 'all':
        tasks = tasks.filter(status__iexact=status_filter)

    context = {
        'tasks': tasks,
        'selected_status': status_filter,
        'total_count': base_tasks.count(),
        'pending_count': base_tasks.filter(status='Pending').count(),
        'in_progress_count': base_tasks.filter(status='In Progress').count(),
        'completed_count': base_tasks.filter(status='Completed').count(),
        'page_title': 'My Tasks (Inbox)'
    }
    
    return render(request, 'manager_tasks.html', context)

# Aliases for Manager Tasks
my_tasks_view = manager_task_view


# 3. SENT TASKS / ALL TASKS (OUTBOX)
@login_required
def sent_tasks_view(request):
    tasks = Task.objects.filter(assigned_by=request.user).order_by('-created_at')

    query = request.GET.get('q')
    if query:
        tasks = tasks.filter(
            Q(title__icontains=query) | 
            Q(description__icontains=query) |
            Q(assigned_to__username__icontains=query)
        )

    status_filter = request.GET.get('status')
    if status_filter and status_filter.lower() != 'all':
        tasks = tasks.filter(status__iexact=status_filter)

    return render(request, 'all_tasks_list.html', {
        'tasks': tasks,
        'user_role': request.user.profile.role,
        'page_title': 'Sent Tasks (Assigned by Me)'
    })

# Aliases for All Tasks / Sent Tasks
all_tasks_view = sent_tasks_view


# 4. TASK FEEDBACKS VIEW
@login_required
def task_feedbacks_view(request):
    user_role = request.user.profile.role
    
    if user_role == 'CEO':
        feedback_tasks = Task.objects.filter(assigned_by=request.user, remarks__isnull=False)
    else:
        feedback_tasks = Task.objects.filter(
            Q(assigned_by=request.user) | Q(assigned_to=request.user),
            remarks__isnull=False
        )

    feedback_tasks = feedback_tasks.distinct().order_by('-created_at')

    query = request.GET.get('q', '')
    status_filter = request.GET.get('status', 'all')

    if query:
        feedback_tasks = feedback_tasks.filter(
            Q(title__icontains=query) | 
            Q(assigned_to__username__icontains=query) |
            Q(assigned_by__username__icontains=query)
        )

    if status_filter and status_filter.lower() != 'all':
        feedback_tasks = feedback_tasks.filter(status__iexact=status_filter)

    export_format = request.GET.get('export')
    if export_format == 'excel':
        data = []
        for task in feedback_tasks:
            last_remark = task.remarks.last()
            feedback_text = last_remark.feedback if last_remark else "No Feedback"
            attachment_urls = []
            if last_remark:
                for n in (1, 2, 3):
                    f = getattr(last_remark, f'attachment_{n}', None)
                    if f:
                        attachment_urls.append(request.build_absolute_uri(f.url))
            file_url = ', '.join(attachment_urls) if attachment_urls else "No Attachment"

            data.append({
                'Task Name': task.title,
                'Assigned By': task.assigned_by.username,
                'Assigned To': task.assigned_to.username if task.assigned_to else "N/A",
                'Feedback': feedback_text,
                'Attachment Link': file_url,
                'Due Date': task.due_date.strftime('%Y-%m-%d') if task.due_date else "N/A",
                'Status': task.status
            })
        df = pd.DataFrame(data)
        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = f'attachment; filename="{user_role}_Task_Feedbacks.xlsx"'
        with pd.ExcelWriter(response, engine='openpyxl') as writer:
            df.to_excel(writer, index=False)
        return response

    if export_format == 'pdf':
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{user_role}_Task_Feedbacks.pdf"'
        doc = SimpleDocTemplate(response, pagesize=landscape(letter))
        elements = []
        styles = getSampleStyleSheet()
        elements.append(Paragraph(f"{user_role} Task Feedback Report", styles['Title']))
        
        data = [['Task Name', 'Assigned To', 'Feedback', 'Attachment Link', 'Status']]
        for task in feedback_tasks:
            last_remark = task.remarks.last()
            fb = last_remark.feedback if last_remark else "No Feedback"
            staff = task.assigned_to.username if task.assigned_to else "N/A"
            attachment_urls = []
            if last_remark:
                for n in (1, 2, 3):
                    f = getattr(last_remark, f'attachment_{n}', None)
                    if f:
                        attachment_urls.append(request.build_absolute_uri(f.url))
            file_url = ', '.join(attachment_urls) if attachment_urls else "No Attachment"
            data.append([task.title, staff, fb, file_url, task.status])
        
        feedback_table = Table(data, repeatRows=1)
        feedback_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#6f42c1')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        elements.append(feedback_table)
        doc.build(elements)
        return response

    return render(request, 'ceo_view_feedbacks.html', {
        'feedbacks': feedback_tasks,
        'query': query,
        'status_filter': status_filter,
        'user_role': user_role
    })

# Aliases for Feedbacks
view_feedbacks = task_feedbacks_view


# 5. ADD REMARK / FEEDBACK VIEW
@login_required
def add_remark_view(request):
    role = request.user.profile.role
    username_upper = request.user.username.upper()

    from .forms import RemarkForm
    from .models import Remark, RemarkAttachment
    
    if request.method == "POST":
        form = RemarkForm(request.POST, request.FILES, manager=request.user) 
        
        if form.is_valid():
            task_obj = form.cleaned_data.get('task')
            # Prevent double submission
            if Remark.objects.filter(task=task_obj, manager=request.user).exists():
                messages.info(request, "Feedback already submitted for this task.")
                return redirect('manager_tasks')
            cd = form.cleaned_data
            remark = Remark(
                task=cd.get('task'),
                manager=request.user,
                feedback=cd.get('feedback'),
                action_taken=cd.get('action_taken')
            )

            uploaded_files = request.FILES.getlist('attachments') if request.FILES else []
            max_file_size = 50 * 1024 * 1024
            allowed_ext = ('.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.png', '.jpg', '.jpeg')
            
            for f in uploaded_files:
                if f.size > max_file_size:
                    messages.error(request, f"File '{f.name}' exceeds the 50MB limit.")
                    return render(request, 'add_remark.html', {'form': form})
                if not f.name.lower().endswith(allowed_ext):
                    messages.error(request, f"Unsupported file type: {f.name}")
                    return render(request, 'add_remark.html', {'form': form})

            # For backward compatibility: populate attachment_1, attachment_2, attachment_3
            for idx, field_name in enumerate(('attachment_1', 'attachment_2', 'attachment_3')):
                if idx < len(uploaded_files):
                    setattr(remark, field_name, uploaded_files[idx])
            
            remark.save()

            # Save all files to RemarkAttachment
            for f in uploaded_files:
                RemarkAttachment.objects.create(remark=remark, file=f)
            
            task = cd.get('task')
            if remark.action_taken == 'approve':
                task.status = 'Completed'
            else:
                task.status = 'In Progress'
            task.save()

            messages.success(request, "Feedback submitted successfully!")
            return redirect('manager_tasks')
    else:
        task_id = request.GET.get('task_id')
        if task_id:
            from .models import Remark
            if Remark.objects.filter(task_id=task_id, manager=request.user).exists():
                messages.info(request, "Feedback already submitted for this task.")
                return redirect('manager_tasks')
        initial_data = {'task': task_id} if task_id else {}
        form = RemarkForm(manager=request.user, initial=initial_data)

    return render(request, 'add_remark.html', {'form': form})


@login_required
def task_feedback_detail_view(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    role = getattr(request.user.profile, 'role', '')
    
    if not (task.assigned_to == request.user or task.assigned_by == request.user or role in ['CEO', 'PS']):
        return HttpResponseForbidden("You are not authorized to view feedbacks for this task.")

    remarks = task.remarks.all().order_by('created_at')

    return render(request, 'task_feedback_detail.html', {
        'task': task,
        'remarks': remarks,
        'user_role': role
    })


# 6. MANAGER DASHBOARD VIEW
@login_required
def manager_dashboard(request):
    from django.db.models import Q, Count
    from .models import Notesheet, NotesheetForward, File, Letter, Task, Commitment, Profile

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

    # 2. Tasks Data (Only tasks assigned to manager)
    my_tasks = Task.objects.filter(assigned_to=request.user)
    
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
    
    return render(request, 'manager_dashboard.html', context)

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse
import json
from datetime import datetime, timedelta

import json
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.utils import timezone
from .models import Task, User # Jo bhi aapke models hain

@login_required
def gm_dashboard(request):
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



from django.http import JsonResponse
from datetime import datetime
from .models import Task # Ensure Task model is imported

@login_required
def gm_chart_data(request):
    """
    Ye function frontend (JavaScript) ko asli data supply karega.
    """
    # JavaScript se dates ki list aayegi: ?dates=2026-01-29,2026-01-30...
    dates_str = request.GET.get('dates', '')
    if not dates_str:
        return JsonResponse([], safe=False)

    dates_list = dates_str.split(',')
    data = []
    
    # Which field to use for counting: 'created_at' (assigned date) or 'due_date'
    by_field = request.GET.get('by', 'created_at')

    for d_str in dates_list:
        try:
            # String ko date object mein convert karna
            date_obj = datetime.strptime(d_str, '%Y-%m-%d').date()
            
            # Asli Data: Check karein ke is din kitne tasks assign kiye is GM ne
            if by_field == 'due_date':
                # Count tasks whose due_date falls on this date
                count = Task.objects.filter(
                    due_date__date=date_obj,
                    assigned_by=request.user
                ).count()
            else:
                # Default: count by creation/assignment date
                count = Task.objects.filter(
                    created_at__date=date_obj,
                    assigned_by=request.user
                ).count()
            
            data.append(count)
        except (ValueError, TypeError):
            data.append(0)
    
    return JsonResponse(data, safe=False)


from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from .models import Task, Remark, TaskTracking, Profile, Notesheet, NotesheetForward, NotesheetAgenda, File
from .forms import InitiateNotesheetForm

# =========================================================
# 1. FILE MANAGEMENT VIEWS (STAGES 2 & 3)
# =========================================================

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import File  # Aapka File model

@login_required
def notesheet_files(request):
    files = File.objects.filter(created_by=request.user).order_by('-created_at')
    return render(request, 'notesheet_files.html', {'files': files})

@login_required
def create_file(request):
    """Nayi File/Folder banane ke liye"""
    if request.method == "POST":
        name = request.POST.get('file_name')
        number = request.POST.get('file_number')
        desc = request.POST.get('description')
        
        if name and number:
            # Check if file_number already exists to avoid UNIQUE constraint error
            if File.objects.filter(file_number=number).exists():
                messages.error(request, f"File number '{number}' already exists. Please use a different file number.")
            else:
                File.objects.create(
                    file_name=name,
                    file_number=number,
                    description=desc,
                    created_by=request.user
                )
                messages.success(request, f"File '{name}' created successfully!")
                return redirect('notesheet_files')
        else:
            messages.error(request, "Please fill name and file number.")
            
    return render(request, 'create_file.html')

@login_required
def file_detail(request, file_id):
    file_obj = get_object_or_404(File, id=file_id)
    
    task_records = list(file_obj.tasks.all())
    notesheet_records = list(file_obj.notesheets.all())
    combined_records = sorted(
        task_records + notesheet_records,
        key=lambda item: item.created_at,
        reverse=True
    )

    return render(request, 'file_detail.html', {
        'file': file_obj,
        'tasks': combined_records
    })
# =========================================================
# 2. TASK / NOTESHEET SYSTEM 1 (Manager Logic)
# =========================================================

@login_required
def initiate_notesheet(request):
    from .models import NotesheetAttachment, NotesheetAgenda

    file_id = request.GET.get('file_id')
    from django.db.models import Case, When, Value, IntegerField
    all_users = User.objects.exclude(id=request.user.id).annotate(
        role_order=Case(
            When(profile__role='CEO', then=Value(1)),
            When(profile__role='PS', then=Value(2)),
            When(profile__role='GM', then=Value(3)),
            When(profile__role='Manager', then=Value(4)),
            When(profile__role='ZM', then=Value(5)),
            When(profile__role='Field Manager', then=Value(6)),
            When(profile__role='IT', then=Value(7)),
            default=Value(99),
            output_field=IntegerField(),
        )
    ).order_by('role_order', 'username')

    if request.method == "POST":
        form = InitiateNotesheetForm(request.POST, request.FILES)
        agenda_titles = request.POST.getlist('agenda_title[]')
        post_file_id = request.POST.get('file_id')

        valid_file_id = None
        if post_file_id and post_file_id.isdigit():
            valid_file_id = int(post_file_id)
        elif file_id and str(file_id).isdigit():
            valid_file_id = int(file_id)

        if form.is_valid():
            notesheet = form.save(commit=False)
            target_user = form.cleaned_data.get('forward_to_user')

            if not target_user:
                form.add_error('forward_to_user', 'Please select a user.')
            else:
                notesheet.current_holder = target_user
                notesheet.created_by = request.user

                if valid_file_id is not None:
                    notesheet.file_id = valid_file_id

                notesheet.status = 'Pending'
                notesheet.save()

                for content in agenda_titles:
                    if content.strip():
                        NotesheetAgenda.objects.create(
                            notesheet=notesheet,
                            agenda_title=content.strip()
                        )

                uploaded_files = request.FILES.getlist('attachments') if request.FILES else []
                attachment_labels = request.POST.getlist('attachment_labels[]')

                for i, f in enumerate(uploaded_files):
                    label = attachment_labels[i] if i < len(attachment_labels) else None
                    NotesheetAttachment.objects.create(
                        notesheet=notesheet,
                        file=f,
                        flag_name=label
                    )

                messages.success(request, f"Notesheet '{notesheet.title}' created successfully!")
                return redirect('my_notesheets')
        else:
            messages.error(request, "Please fix the errors below and resubmit.")

    else:
        form = InitiateNotesheetForm()

    return render(request, 'initiate_notesheet.html', {
        'form': form,
        'file_id': file_id,
        'users': all_users
    })

# =========================================================
# 3. OTHER VIEWS (VIEWING & FORWARDING)
# =========================================================

@login_required
def view_notesheet(request, task_id):
    from .models import NotesheetAttachment, NotesheetReturn  # ✅ NotesheetReturn ko bhi import kiya
    
    # First try Notesheet and then fall back to Task for backward compatibility
    notesheet = None
    is_task = False

    try:
        notesheet = Notesheet.objects.get(id=task_id)
    except Notesheet.DoesNotExist:
        try:
            notesheet = Task.objects.get(id=task_id)
            is_task = True
        except Task.DoesNotExist:
            messages.error(request, f"Notesheet with ID {task_id} not found.")
            return redirect('notesheet_files')

    if is_task:
        if notesheet.assigned_to == request.user and not notesheet.is_seen:
            notesheet.is_seen = True
            notesheet.seen_at = timezone.now()
            notesheet.save(update_fields=['is_seen', 'seen_at'])
        remarks = notesheet.remarks.all().order_by('created_at')
        agendas = []
        forwards = []
        attachments = []  # Tasks ke liye khali rkhlein
        returns = []      # Tasks ke liye returns bhi khali rhega
    else:
        if notesheet.current_holder == request.user and not notesheet.is_seen:
            notesheet.is_seen = True
            notesheet.seen_at = timezone.now()
            notesheet.save(update_fields=['is_seen', 'seen_at'])
        remarks = []
        agendas = notesheet.agendas.all()
        forwards = notesheet.forwards.all()
        
        # ✅ IMPORTANT: Is notesheet ki saari initial attachments fetch karli hain
        attachments = NotesheetAttachment.objects.filter(notesheet=notesheet)
        
        # ✅ NEW: Is notesheet ki saari return history aur manager ke remarks nikaal liye
        returns = NotesheetReturn.objects.filter(notesheet=notesheet).order_by('-returned_at')

    context = {
        'notesheet': notesheet,
        'remarks': remarks,
        'agendas': agendas,
        'forwards': forwards,
        'attachments': attachments,  # ✅ Context mein pass kardiya
        'return_history': returns,    # ✅ Return history ko template ke liye pass kardiya
    }
    return render(request, 'view_notesheet.html', context)

@login_required
def notesheet_detail(request, task_id):
    notesheet = get_object_or_404(Task, id=task_id)
    officers = User.objects.filter(profile__isnull=False).exclude(id=request.user.id).select_related('profile').order_by('username')

    if request.method == 'POST':
        feedback_text = request.POST.get('remarks')
        forward_to_id = request.POST.get('forward_to')

        if feedback_text:
            Remark.objects.create(task=notesheet, manager=request.user, feedback=feedback_text)
            if forward_to_id:
                new_officer = User.objects.get(id=forward_to_id)
                notesheet.assigned_to = new_officer
                notesheet.status = 'In Progress'
                notesheet.save()
            return redirect('view_notesheets')

    return render(request, 'notesheet_detail.html', {'notesheet': notesheet, 'officers': officers})

@login_required
def my_notesheets(request):
    task_notesheets = Task.objects.filter(assigned_to=request.user)
    notesheet_items = Notesheet.objects.filter(
        Q(current_holder=request.user) | Q(created_by=request.user)
    ).distinct()
    combined_notesheets = sorted(
        list(task_notesheets) + list(notesheet_items),
        key=lambda item: item.created_at,
        reverse=True
    )
    return render(request, "my_notesheets.html", {"notesheets": combined_notesheets}) 


@login_required
def forward_notesheet(request, pk):
    notesheet = None
    is_task = False

    try:
        notesheet = Notesheet.objects.get(pk=pk)
    except Notesheet.DoesNotExist:
        try:
            notesheet = Task.objects.get(pk=pk)
            is_task = True
        except Task.DoesNotExist:
            return HttpResponseNotFound("No notesheet found with that ID.")

    if is_task:
        if notesheet.assigned_to != request.user and notesheet.assigned_by != request.user:
            messages.error(request, "You are not allowed to forward this.")
            return redirect("my_notesheets")
    else:
        if notesheet.current_holder != request.user and notesheet.created_by != request.user:
            messages.error(request, "You are not allowed to forward this.")
            return redirect("my_notesheets")
# 2. TASK / NOTESHEET SYSTEM 1 (Manager Logic)
# =========================================================

@login_required
def initiate_notesheet(request):
    from .models import NotesheetAttachment, NotesheetAgenda

    file_id = request.GET.get('file_id')
    from django.db.models import Case, When, Value, IntegerField
    all_users = User.objects.exclude(id=request.user.id).annotate(
        role_order=Case(
            When(profile__role='CEO', then=Value(1)),
            When(profile__role='PS', then=Value(2)),
            When(profile__role='GM', then=Value(3)),
            When(profile__role='Manager', then=Value(4)),
            When(profile__role='ZM', then=Value(5)),
            When(profile__role='Field Manager', then=Value(6)),
            When(profile__role='IT', then=Value(7)),
            default=Value(99),
            output_field=IntegerField(),
        )
    ).order_by('role_order', 'username')

    if request.method == "POST":
        form = InitiateNotesheetForm(request.POST, request.FILES)
        agenda_titles = request.POST.getlist('agenda_title[]')
        post_file_id = request.POST.get('file_id')

        valid_file_id = None
        if post_file_id and post_file_id.isdigit():
            valid_file_id = int(post_file_id)
        elif file_id and str(file_id).isdigit():
            valid_file_id = int(file_id)

        if form.is_valid():
            notesheet = form.save(commit=False)
            target_user = form.cleaned_data.get('forward_to_user')

            if not target_user:
                form.add_error('forward_to_user', 'Please select a user.')
            else:
                notesheet.current_holder = target_user
                notesheet.created_by = request.user

                if valid_file_id is not None:
                    notesheet.file_id = valid_file_id

                notesheet.status = 'Pending'
                notesheet.save()

                for content in agenda_titles:
                    if content.strip():
                        NotesheetAgenda.objects.create(
                            notesheet=notesheet,
                            agenda_title=content.strip()
                        )

                uploaded_files = request.FILES.getlist('attachments') if request.FILES else []
                attachment_labels = request.POST.getlist('attachment_labels[]')

                for i, f in enumerate(uploaded_files):
                    label = attachment_labels[i] if i < len(attachment_labels) else None
                    NotesheetAttachment.objects.create(
                        notesheet=notesheet,
                        file=f,
                        flag_name=label
                    )

                create_notification(
                    recipient=target_user,
                    sender=request.user,
                    title=f"New Notesheet Initiated",
                    message=f"Notesheet '{notesheet.title}' has been initiated by {request.user.username}.",
                    link=f"/notesheet/view/{notesheet.id}/",
                    notification_type='notesheet'
                )

                messages.success(request, f"Notesheet '{notesheet.title}' created successfully!")
                return redirect('my_notesheets')
        else:
            messages.error(request, "Please fix the errors below and resubmit.")

    else:
        form = InitiateNotesheetForm()

    files = File.objects.filter(created_by=request.user).order_by('-created_at')

    return render(request, 'initiate_notesheet.html', {
        'form': form,
        'file_id': file_id,
        'users': all_users,
        'files': files
    })

# =========================================================
# 3. OTHER VIEWS (VIEWING & FORWARDING)
# =========================================================

@login_required
def view_notesheet(request, task_id):
    from .models import NotesheetAttachment, NotesheetReturn  # ✅ NotesheetReturn ko bhi import kiya
    
    # First try Notesheet and then fall back to Task for backward compatibility
    notesheet = None
    is_task = False

    try:
        notesheet = Notesheet.objects.get(id=task_id)
    except Notesheet.DoesNotExist:
        try:
            notesheet = Task.objects.get(id=task_id)
            is_task = True
        except Task.DoesNotExist:
            messages.error(request, f"Notesheet with ID {task_id} not found.")
            return redirect('notesheet_files')

    if is_task:
        if notesheet.assigned_to == request.user and not notesheet.is_seen:
            notesheet.is_seen = True
            notesheet.seen_at = timezone.now()
            notesheet.save(update_fields=['is_seen', 'seen_at'])
        remarks = notesheet.remarks.all().order_by('created_at')
        agendas = []
        forwards = []
        attachments = []  # Tasks ke liye khali rkhlein
        returns = []      # Tasks ke liye returns bhi khali rhega
    else:
        if notesheet.current_holder == request.user and not notesheet.is_seen:
            notesheet.is_seen = True
            notesheet.seen_at = timezone.now()
            notesheet.save(update_fields=['is_seen', 'seen_at'])
        remarks = []
        agendas = notesheet.agendas.all()
        forwards = notesheet.forwards.all()
        
        # ✅ IMPORTANT: Is notesheet ki saari initial attachments fetch karli hain
        attachments = NotesheetAttachment.objects.filter(notesheet=notesheet)
        
        # ✅ NEW: Is notesheet ki saari return history aur manager ke remarks nikaal liye
        returns = NotesheetReturn.objects.filter(notesheet=notesheet).order_by('-returned_at')

    context = {
        'notesheet': notesheet,
        'remarks': remarks,
        'agendas': agendas,
        'forwards': forwards,
        'attachments': attachments,  # ✅ Context mein pass kardiya
        'return_history': returns,    # ✅ Return history ko template ke liye pass kardiya
    }
    return render(request, 'view_notesheet.html', context)

@login_required
def notesheet_detail(request, task_id):
    notesheet = get_object_or_404(Task, id=task_id)
    officers = User.objects.filter(profile__isnull=False).exclude(id=request.user.id).select_related('profile').order_by('username')

    if request.method == 'POST':
        feedback_text = request.POST.get('remarks')
        forward_to_id = request.POST.get('forward_to')

        if feedback_text:
            Remark.objects.create(task=notesheet, manager=request.user, feedback=feedback_text)
            if forward_to_id:
                new_officer = User.objects.get(id=forward_to_id)
                notesheet.assigned_to = new_officer
                notesheet.status = 'In Progress'
                notesheet.save()
            return redirect('view_notesheets')

    return render(request, 'notesheet_detail.html', {'notesheet': notesheet, 'officers': officers})

@login_required
def my_notesheets(request):
    task_notesheets = Task.objects.filter(assigned_to=request.user)
    notesheet_items = Notesheet.objects.filter(
        Q(current_holder=request.user) | Q(created_by=request.user)
    ).distinct()
    combined_notesheets = sorted(
        list(task_notesheets) + list(notesheet_items),
        key=lambda item: item.created_at,
        reverse=True
    )
    return render(request, "my_notesheets.html", {"notesheets": combined_notesheets}) 

import re
def get_next_para_num(notesheet, is_task=False):
    count = 0
    if not is_task:
        for agenda in notesheet.agendas.all():
            content = agenda.agenda_title or ''
            lis = re.findall(r'<li[^>]*>', content, re.IGNORECASE)
            if lis: count += len(lis)
            else:
                ps = re.findall(r'<p[^>]*>', content, re.IGNORECASE)
                count += len(ps) if ps else 1
        for forward in notesheet.forwards.all():
            content = forward.remark or ''
            lis = re.findall(r'<li[^>]*>', content, re.IGNORECASE)
            if lis: count += len(lis)
            else:
                ps = re.findall(r'<p[^>]*>', content, re.IGNORECASE)
                count += len(ps) if ps else 1
        for ret in notesheet.returns.all():
            content = ret.remark or ''
            lis = re.findall(r'<li[^>]*>', content, re.IGNORECASE)
            if lis: count += len(lis)
            else:
                ps = re.findall(r'<p[^>]*>', content, re.IGNORECASE)
                count += len(ps) if ps else 1
    else:
        for remark in notesheet.remarks.all():
            content = remark.feedback or ''
            lis = re.findall(r'<li[^>]*>', content, re.IGNORECASE)
            if lis: count += len(lis)
            else:
                ps = re.findall(r'<p[^>]*>', content, re.IGNORECASE)
                count += len(ps) if ps else 1
    return count + 1


@login_required
def forward_notesheet(request, pk):
    notesheet = None
    is_task = False

    try:
        notesheet = Notesheet.objects.get(pk=pk)
    except Notesheet.DoesNotExist:
        try:
            notesheet = Task.objects.get(pk=pk)
            is_task = True
        except Task.DoesNotExist:
            return HttpResponseNotFound("No notesheet found with that ID.")

    if is_task:
        if notesheet.assigned_to != request.user and notesheet.assigned_by != request.user:
            messages.error(request, "You are not allowed to forward this.")
            return redirect("my_notesheets")
    else:
        if notesheet.current_holder != request.user and notesheet.created_by != request.user:
            messages.error(request, "You are not allowed to forward this.")
            return redirect("my_notesheets")

    if request.method == "POST":
        forwarded_to_id = request.POST.get("forwarded_to")
        remark_text = request.POST.get("remark")

        try:
            forwarded_user = User.objects.get(id=forwarded_to_id)
            if not is_task:
                forward_obj = NotesheetForward.objects.create(
                    notesheet=notesheet,
                    forwarded_by=request.user,
                    forwarded_to=forwarded_user,
                    remark=remark_text,
                )

                # Attachments with labels save karo
                uploaded_files = request.FILES.getlist('attachments')
                
                # Assign up to 3 attachments directly to the forward object
                for i, f in enumerate(uploaded_files[:3]):
                    if f:
                        if i == 0:
                            forward_obj.attachment_1 = f
                        elif i == 1:
                            forward_obj.attachment_2 = f
                        elif i == 2:
                            forward_obj.attachment_3 = f
                forward_obj.save()

                attachment_labels = request.POST.getlist('attachment_labels[]')
                for i, f in enumerate(uploaded_files):
                    if f:
                        label = attachment_labels[i] if i < len(attachment_labels) else None
                        NotesheetAttachment.objects.create(
                            notesheet=notesheet,
                            file=f,
                            flag_name=label,
                        )
            else:
                TaskTracking.objects.create(
                    task=notesheet,
                    from_user=request.user,
                    to_user=forwarded_user,
                    message=f"Forwarded notesheet with remark: {remark_text or 'No remark'}"
                )

            if is_task:
                notesheet.assigned_to = forwarded_user
            else:
                notesheet.current_holder = forwarded_user

            notesheet.is_seen = False
            notesheet.seen_at = None
            notesheet.status = "In Progress"
            notesheet.save()

            create_notification(
                recipient=forwarded_user,
                sender=request.user,
                title=f"{'Task' if is_task else 'Notesheet'} Forwarded",
                message=f"'{notesheet.title}' has been forwarded to you by {request.user.username}.",
                link=f"/notesheet/view/{notesheet.id}/" if not is_task else "/manager/tasks/",
                notification_type='task' if is_task else 'notesheet'
            )

            messages.success(request, f"Forwarded to {forwarded_user.username}.")
            return redirect("my_notesheets")
        except User.DoesNotExist:
            messages.error(request, "Officer not found.")

    # ── GET: existing flags/annexure/puc count SEPARATELY calculate karo ──
    existing_flag_count = 0
    existing_annexure_count = 0
    existing_puc_count = 0

    if not is_task:
        all_attachments = NotesheetAttachment.objects.filter(notesheet=notesheet)
        for att in all_attachments:
            name = (att.flag_name or '').strip()
            if name.startswith('Flag'):
                existing_flag_count += 1
            elif name.startswith('Annexure'):
                existing_annexure_count += 1
            elif name.startswith('PUC'):
                existing_puc_count += 1
            else:
                existing_flag_count += 1

    from django.db.models import Case, When, Value, IntegerField
    users = User.objects.exclude(id=request.user.id).annotate(
        role_order=Case(
            When(profile__role='CEO', then=Value(1)),
            When(profile__role='PS', then=Value(2)),
            When(profile__role='GM', then=Value(3)),
            When(profile__role='Manager', then=Value(4)),
            When(profile__role='ZM', then=Value(5)),
            When(profile__role='Field Manager', then=Value(6)),
            When(profile__role='IT', then=Value(7)),
            default=Value(99),
            output_field=IntegerField(),
        )
    ).order_by('role_order', 'username')
    
    next_para_num = get_next_para_num(notesheet, is_task)

    return render(request, "forward_notesheet.html", {
        "notesheet": notesheet,
        "users": users,
        "existing_flag_count": existing_flag_count,
        "existing_annexure_count": existing_annexure_count,
        "existing_puc_count": existing_puc_count,
        "next_para_num": next_para_num,
    })


# =========================================================
# 3. OTHER VIEWS (VIEWING & FORWARDING)
# =========================================================

@login_required
def view_notesheet(request, task_id):
    from .models import NotesheetAttachment, NotesheetReturn
    import re
    
    def extract_letterhead(text):
        """Extracts letterhead from text and returns (letterhead, clean_text)"""
        if not text:
            return '', ''
            
        letterhead = ''
        clean_text = text
        
        # Check for new letterhead div format (mceNonEditable)
        match = re.search(r'(<div class="mceNonEditable"[^>]*>.*?</div>\s*(?:<hr[^>]*>|<div[^>]*border-top[^>]*></div>))', text, re.IGNORECASE | re.DOTALL)
        if match:
            letterhead = match.group(1)
            clean_text = text[match.end():]
        else:
            # Fallback for old letterhead format
            if 'CHIEF EXECUTIVE OFFICER' in text and ('091-9219018' in text or '091-9219074' in text):
                match = re.search(r'(<table.*?</table>\s*(?:<div[^>]*></div>|<hr[^>]*>)?)', text, re.IGNORECASE | re.DOTALL)
                if match:
                    letterhead = match.group(1)
                    clean_text = text[match.end():]
                    
        # Clean up any leading empty p tags or brs
        clean_text = re.sub(r'^\s*(<p>&nbsp;</p>|<p>\s*</p>|<br\s*/?>)\s*', '', clean_text, count=1, flags=re.IGNORECASE).strip()
        
        return letterhead, clean_text
    
    # First try Notesheet and then fall back to Task for backward compatibility
    notesheet = None
    is_task = False

    try:
        notesheet = Notesheet.objects.get(id=task_id)
    except Notesheet.DoesNotExist:
        try:
            notesheet = Task.objects.get(id=task_id)
            is_task = True
        except Task.DoesNotExist:
            messages.error(request, f"Notesheet with ID {task_id} not found.")
            return redirect('notesheet_files')

    if is_task:
        if notesheet.assigned_to == request.user and not notesheet.is_seen:
            notesheet.is_seen = True
            notesheet.seen_at = timezone.now()
            notesheet.save(update_fields=['is_seen', 'seen_at'])
        remarks = notesheet.remarks.all().order_by('created_at')
        agendas = []
        forwards = []
        attachments = []
        returns = []
    else:
        if notesheet.current_holder == request.user and not notesheet.is_seen:
            notesheet.is_seen = True
            notesheet.seen_at = timezone.now()
            notesheet.save(update_fields=['is_seen', 'seen_at'])
        remarks = []
        
        clean_agendas = []
        for agenda in notesheet.agendas.all():
            lh, content = extract_letterhead(agenda.agenda_title)
            clean_agendas.append({
                'obj': agenda,
                'letterhead': lh,
                'content': content
            })
        forwards = notesheet.forwards.all().order_by('forwarded_at')
        
        attachments = NotesheetAttachment.objects.filter(notesheet=notesheet)
        returns = NotesheetReturn.objects.filter(notesheet=notesheet).order_by('returned_at')

    all_attachments = list(attachments) if not is_task else []
    used_att_ids = set()

    # Build clean_forwards with HTML-stripped remarks and matched attachments for template
    clean_forwards = []
    for fwd in forwards:
        fwd_atts = []
        # Match attachments uploaded within 15 seconds of this forward
        matched = [a for a in all_attachments if abs((a.uploaded_at - fwd.forwarded_at).total_seconds()) < 15 and a.id not in used_att_ids]
        matched.sort(key=lambda x: x.id)
        for a in matched:
            used_att_ids.add(a.id)
            fwd_atts.append(a)
            
        lh, content = extract_letterhead(fwd.remark)
        clean_forwards.append({
            'type': 'forward',
            'action_date': fwd.forwarded_at,
            'actor': fwd.forwarded_by,
            'receiver': fwd.forwarded_to,
            'obj': fwd,
            'letterhead': lh,
            'clean_remark': content,
            'rich_attachments': fwd_atts,
        })
    
    # Build clean_returns with HTML-stripped remarks and matched attachments for template
    clean_returns = []
    for ret in returns:
        ret_atts = []
        # Match attachments uploaded within 15 seconds of this return
        matched = [a for a in all_attachments if abs((a.uploaded_at - ret.returned_at).total_seconds()) < 15 and a.id not in used_att_ids]
        matched.sort(key=lambda x: x.id)
        for a in matched:
            used_att_ids.add(a.id)
            ret_atts.append(a)
            
        lh, content = extract_letterhead(ret.remark)
        clean_returns.append({
            'type': 'return',
            'action_date': ret.returned_at,
            'actor': ret.returned_by,
            'receiver': ret.returned_to,
            'obj': ret,
            'letterhead': lh,
            'clean_remark': content,
            'rich_attachments': ret_atts,
        })
        
    initial_attachments = [a for a in all_attachments if a.id not in used_att_ids]

    # Combine forwards and returns into a single unified timeline
    timeline = clean_forwards + clean_returns
    timeline.sort(key=lambda x: x['action_date'])

    initial_receiver = timeline[0]['actor'] if timeline else notesheet.current_holder

    context = {
        'notesheet': notesheet,
        'initial_receiver': initial_receiver,
        'remarks': remarks,
        'agendas': clean_agendas,
        'forwards': forwards,
        'clean_forwards': clean_forwards,
        'attachments': attachments,
        'initial_attachments': initial_attachments,
        'all_attachments': all_attachments,
        'return_history': returns,
        'clean_returns': clean_returns,
        'timeline': timeline,
    }
    return render(request, 'view_notesheet.html', context)


from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Notesheet, NotesheetForward, NotesheetReturn, NotesheetAttachment

@login_required
def return_notesheet(request, pk):
    # 1. Database se notesheet get karein
    notesheet = get_object_or_404(Notesheet, pk=pk)
    
    if request.method == 'POST':
        remark = request.POST.get('remark')
        current_user = request.user

        # ── Attachments + Flags dynamic handle ──
        attachments = request.FILES.getlist('attachments')

        # 2. History check karein (Forward aur Return dono tables mein)
        last_forward = NotesheetForward.objects.filter(notesheet=notesheet).order_by('-forwarded_at').first()
        last_return  = NotesheetReturn.objects.filter(notesheet=notesheet).order_by('-returned_at').first()
        
        target_user = None

        # 3. Agar dono history majood hain, toh check karo latest kaunsi hai
        if last_forward and last_return:
            if last_forward.forwarded_at > last_return.returned_at:
                if last_forward.forwarded_by != current_user:
                    target_user = last_forward.forwarded_by
            else:
                if last_return.returned_by != current_user:
                    target_user = last_return.returned_by
                    
        elif last_forward and last_forward.forwarded_by != current_user:
            target_user = last_forward.forwarded_by
            
        elif last_return and last_return.returned_by != current_user:
            target_user = last_return.returned_by

        # 4. CRITICAL FALLBACK
        if not target_user:
            if notesheet.created_by and notesheet.created_by != current_user:
                target_user = notesheet.created_by

        # 5. Data update aur save karein
        if target_user:
            notesheet.current_holder = target_user
            notesheet.status = 'Returned'
            notesheet.is_seen = False
            notesheet.save()
            
            # Return history save karein
            return_obj = NotesheetReturn.objects.create(
                notesheet=notesheet,
                returned_by=current_user,
                returned_to=target_user,
                remark=remark if remark else "Notesheet returned for corrections.",
            )

            # Assign up to 3 attachments directly to the return object
            for i, f in enumerate(attachments[:3]):
                if f:
                    if i == 0:
                        return_obj.attachment_1 = f
                    elif i == 1:
                        return_obj.attachment_2 = f
                    elif i == 2:
                        return_obj.attachment_3 = f
            return_obj.save()

            # ── Dynamic label attachments save karein ──
            attachment_labels = request.POST.getlist('attachment_labels[]')
            for i, file in enumerate(attachments):
                if file:
                    label = attachment_labels[i] if i < len(attachment_labels) else None
                    NotesheetAttachment.objects.create(
                        notesheet=notesheet,
                        file=file,
                        flag_name=label,
                    )

            create_notification(
                recipient=target_user,
                sender=current_user,
                title=f"Notesheet Returned",
                message=f"'{notesheet.title}' has been returned to you by {current_user.username}.",
                link=f"/notesheet/view/{notesheet.id}/",
                notification_type='notesheet'
            )

            messages.success(request, f"Notesheet returned successfully to {target_user.username}.")
        else:
            messages.error(request, "Cannot return this notesheet. No previous owner or creator found to return to.")

        # Role ke mutabiq sahi dashboard par redirect karein
        if request.user.profile.role == 'CEO':
            return redirect('ceo_dashboard')
        elif request.user.profile.role == 'GM':
            return redirect('gm_dashboard')
        elif request.user.profile.role in ['Manager', 'ZM', 'IT', 'IT Officer']:
            return redirect('manager_dashboard')
        elif request.user.profile.role == 'PS':
            return redirect('ps_dashboard')
        else:
            return redirect('my_notesheets')

    # ── GET: existing flags/annexure/puc count SEPARATELY calculate karo ──
    all_attachments = NotesheetAttachment.objects.filter(notesheet=notesheet)
    existing_flag_count = 0
    existing_annexure_count = 0
    existing_puc_count = 0
    for att in all_attachments:
        name = (att.flag_name or '').strip()
        if name.startswith('Flag'):
            existing_flag_count += 1
        elif name.startswith('Annexure'):
            existing_annexure_count += 1
        elif name.startswith('PUC'):
            existing_puc_count += 1
        else:
            # Unknown type — count as flag for safety
            existing_flag_count += 1

    next_para_num = get_next_para_num(notesheet)

    return render(request, 'return_notesheet.html', {
        'notesheet': notesheet,
        'existing_flag_count': existing_flag_count,
        'existing_annexure_count': existing_annexure_count,
        'existing_puc_count': existing_puc_count,
        'next_para_num': next_para_num,
    })





from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import LetterFile, Letter
from django.contrib.auth.models import User

# 1. Letter Files List Page View
@login_required
def letter_files_list(request):
    files = LetterFile.objects.filter(created_by=request.user)
    return render(request, 'letter_files.html', {'files': files})

# 2. Create New Letter File
@login_required
def create_letter_file(request):
    if request.method == 'POST':
        title = request.POST.get('file_title')
        ref_num = request.POST.get('reference_number')
        desc = request.POST.get('description')
        
        LetterFile.objects.create(
            file_title=title,
            reference_number=ref_num,
            description=desc,
            created_by=request.user
        )
        messages.success(request, "Letter File successfuly create ho gayi hai!")
        return redirect('letter_files_list')
        
    return render(request, 'create_letter_file.html')

# 3. New Letter Send View
@login_required
def create_letter(request):
    files = LetterFile.objects.filter(created_by=request.user)
    users = User.objects.exclude(id=request.user.id)

    if request.method == 'POST':
        file_id = request.POST.get('letter_file', '').strip()
        receiver_id = request.POST.get('receiver', '').strip()
        subject = request.POST.get('subject', '').strip()
        body = request.POST.get('body', '')
        attachment = request.FILES.get('attachment')
        save_as_draft = request.POST.get('save_as_draft') == '1'

        # Validate letter file
        if not file_id:
            messages.error(request, "Please select a Letter File before continuing.")
            return render(request, 'create_letter.html', {'files': files, 'users': users})

        letter_file = get_object_or_404(LetterFile, id=file_id)

        if save_as_draft:
            # Receiver is optional for drafts
            if receiver_id:
                receiver = get_object_or_404(User, id=receiver_id)
            else:
                receiver = request.user  # placeholder for draft

            Letter.objects.create(
                letter_file=letter_file,
                sender=request.user,
                receiver=receiver,
                ref_no=request.POST.get('ref_no', ''),
                recipient_address=request.POST.get('recipient_address', ''),
                subject=subject or '(Draft)',
                body=body or '',
                signer_name=request.POST.get('signer_name', ''),
                signer_designation=request.POST.get('signer_designation', ''),
                cc_list=request.POST.get('cc_list', ''),
                attachment=attachment,
                is_draft=True
            )
            messages.success(request, "Letter draft save ho gai hai!")
            return redirect('letter_drafts')
        else:
            # Sending requires a recipient
            if not receiver_id:
                messages.error(request, "Letter issue karne ke liye recipient (Send To) select karna zaroori hai.")
                return render(request, 'create_letter.html', {'files': files, 'users': users})

            receiver = get_object_or_404(User, id=receiver_id)
            Letter.objects.create(
                letter_file=letter_file,
                sender=request.user,
                receiver=receiver,
                ref_no=request.POST.get('ref_no', ''),
                recipient_address=request.POST.get('recipient_address', ''),
                subject=subject,
                body=body,
                signer_name=request.POST.get('signer_name', ''),
                signer_designation=request.POST.get('signer_designation', ''),
                cc_list=request.POST.get('cc_list', ''),
                attachment=attachment,
                is_draft=False
            )
            
            create_notification(
                recipient=receiver,
                sender=request.user,
                title="New Letter Received",
                message=f"You have received a new letter: '{subject}'",
                link=f"/letters/detail/{Letter.objects.last().id}/",
                notification_type='letter'
            )
            
            messages.success(request, "Letter kamyabi se bhej diya gaya hai!")
            return redirect('letter_outbox')

    return render(request, 'create_letter.html', {'files': files, 'users': users})


# Draft Letters View
@login_required
def letter_drafts(request):
    search_query = request.GET.get('search', '')
    drafts = Letter.objects.filter(sender=request.user, is_draft=True)
    if search_query:
        from django.db.models import Q
        drafts = drafts.filter(
            Q(subject__icontains=search_query) |
            Q(ref_no__icontains=search_query) |
            Q(body__icontains=search_query)
        )
    return render(request, 'letter_drafts.html', {'drafts': drafts, 'search_query': search_query})

@login_required
def send_draft_letter(request, letter_id):
    letter = get_object_or_404(Letter, id=letter_id, sender=request.user, is_draft=True)
    if request.method == "POST":
        receiver_id = request.POST.get('receiver')
        if not receiver_id:
            messages.error(request, "Please select a system recipient before issuing the letter.")
            return redirect('letter_detail', letter_id=letter.id)
            
        receiver = get_object_or_404(User, id=receiver_id)
        letter.receiver = receiver
        letter.is_draft = False
        letter.save()

        create_notification(
            recipient=receiver,
            sender=request.user,
            title="New Letter Received",
            message=f"You have received a new letter: '{letter.subject}' by {request.user.username}",
            link=f"/letters/detail/{letter.id}/",
            notification_type='letter'
        )

        messages.success(request, f"Letter '{letter.subject}' issued successfully to {receiver.username}!")
        return redirect('letter_outbox')

    return redirect('letter_detail', letter_id=letter.id)


# 4. Inbox View (Mili hui Letters)
@login_required
def letter_inbox(request):
    search_query = request.GET.get('search', '')
    letters = Letter.objects.filter(receiver=request.user, is_draft=False)
    if search_query:
        from django.db.models import Q
        letters = letters.filter(
            Q(subject__icontains=search_query) |
            Q(ref_no__icontains=search_query) |
            Q(body__icontains=search_query) |
            Q(sender__username__icontains=search_query)
        )
    return render(request, 'letter_inbox.html', {'letters': letters, 'search_query': search_query})

# 5. Outbox View (Bheji hui Letters)
@login_required
def letter_outbox(request):
    search_query = request.GET.get('search', '')
    letters = Letter.objects.filter(sender=request.user, is_draft=False)
    if search_query:
        from django.db.models import Q
        letters = letters.filter(
            Q(subject__icontains=search_query) |
            Q(ref_no__icontains=search_query) |
            Q(body__icontains=search_query) |
            Q(receiver__username__icontains=search_query)
        )
    return render(request, 'letter_outbox.html', {'letters': letters, 'search_query': search_query})

# 6. Letter Detail Page View
@login_required
def letter_detail(request, letter_id):
    letter = get_object_or_404(Letter, id=letter_id)
    if letter.sender != request.user and letter.receiver != request.user:
        messages.error(request, "Aapko yeh letter dekhne ki ijazat nahi hai!")
        return redirect('letter_inbox')
    
    if letter.receiver == request.user and not letter.is_read:
        letter.is_read = True
        letter.save()
        
    users = User.objects.exclude(id=request.user.id) if letter.is_draft else None

    return render(request, 'letter_detail.html', {'letter': letter, 'users': users})


import base64
from django.core.files.base import ContentFile
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Profile  # Apne Profile model ko import karein

@login_required
def edit_profile_signature(request):
    # Safely profile instance get ya create karein
    profile, created = Profile.objects.get_or_create(user=request.user)

    # Where to go after saving — read from GET or POST
    next_param = request.GET.get('next') or request.POST.get('next', '')
    # Build the redirect URL safely
    if next_param.startswith('/'):
        next_url = next_param
        next_name = next_param.strip('/').replace('/', ' › ').title() or 'Back'
    else:
        try:
            from django.urls import reverse, NoReverseMatch
            next_url = reverse(next_param) if next_param else None
            next_name = next_param.replace('_', ' ').title() if next_param else 'Dashboard'
        except Exception:
            next_url = None
            next_name = 'Dashboard'

    if request.method == 'POST':
        signature_data = request.POST.get('signature_data', '').strip()
        signature_file = request.FILES.get('signature_file')

        # ── PRIORITY 1: Uploaded Image File ──
        if signature_file:
            profile.signature = signature_file
            profile.save()
            messages.success(request, "Signature image successfully uploaded and saved!")
            return redirect(next_url or 'edit_profile_signature')

        # ── PRIORITY 2: Drawn Base64 Signature ──
        elif signature_data and signature_data.startswith('data:image'):
            try:
                fmt, imgstr = signature_data.split(';base64,')
                ext = 'png' if 'png' in fmt else 'jpg'
                
                # Base64 string ko decode karke ContentFile banana
                file_obj = ContentFile(
                    base64.b64decode(imgstr),
                    name=f"signature_user_{request.user.id}.{ext}"
                )
                
                # ImageField par directly save karein taake storage override ho sake
                profile.signature.save(f"sig_user_{request.user.id}.{ext}", file_obj, save=True)
                
                messages.success(request, "Digital signature successfully saved!")
                return redirect(next_url or 'edit_profile_signature')
            except Exception as e:
                messages.error(request, f"Error processing signature: {str(e)}")

        else:
            messages.warning(request, "Please draw your signature or upload an image before saving.")

    return render(request, 'edit_profile.html', {
        'profile': profile,
        'next_url': next_url,
        'next_name': next_name,
    })


# 📥 INBOX VIEW
@login_required
def notesheet_inbox(request):
    notesheets = Notesheet.objects.filter(
        current_holder=request.user
    ).order_by('-updated_at')
    return render(request, 'notesheet_inbox.html', {'notesheets': notesheets})


# 📤 OUTBOX VIEW
@login_required
def notesheet_outbox(request):
    from django.db.models import Q
    forwarded_ids = NotesheetForward.objects.filter(
        forwarded_by=request.user
    ).values_list('notesheet_id', flat=True)
    notesheets = Notesheet.objects.filter(
        Q(created_by=request.user) | Q(id__in=forwarded_ids)
    ).exclude(current_holder=request.user).distinct().order_by('-updated_at')
    return render(request, 'notesheet_outbox.html', {'notesheets': notesheets})

# =========================================================
# LETTER REPLY VIEWS
# =========================================================
@login_required
def reply_letter(request, letter_id):
    from .models import LetterReplyAttachment
    letter = get_object_or_404(Letter, id=letter_id)
    
    # Only receiver can reply, and only if not already replied
    if request.user != letter.receiver:
        messages.error(request, "You are not authorized to reply to this letter.")
        return redirect('letter_inbox')
        
    if letter.reply_text:
        messages.info(request, "You have already replied to this letter.")
        return redirect('view_letter_reply', letter_id=letter.id)
        
    if request.method == 'POST':
        reply_text = request.POST.get('reply_text')
        reply_files = request.FILES.getlist('reply_attachments')
        
        if reply_text:
            from django.utils import timezone
            letter.reply_text = reply_text
            # Backward compatibility: save first file to old field
            if reply_files:
                letter.reply_attachment = reply_files[0]
            letter.reply_date = timezone.now()
            letter.save()
            
            # Save all files to LetterReplyAttachment
            for f in reply_files:
                LetterReplyAttachment.objects.create(letter=letter, file=f)
            
            messages.success(request, "Reply submitted successfully!")
            return redirect('letter_inbox')
        else:
            messages.error(request, "Reply text cannot be empty.")
            
    return render(request, 'reply_letter.html', {'letter': letter})

@login_required
def view_letter_reply(request, letter_id):
    letter = get_object_or_404(Letter, id=letter_id)
    
    # Only sender and receiver can view the reply
    if request.user != letter.sender and request.user != letter.receiver:
        messages.error(request, "You are not authorized to view this reply.")
        return redirect('letter_inbox')
        
    if not letter.reply_text:
        messages.info(request, "No reply has been sent for this letter yet.")
        return redirect('letter_detail', letter_id=letter.id)
        
    return render(request, 'view_letter_reply.html', {'letter': letter})

@login_required
def mark_notification_as_read(request, notification_id):
    from django.http import JsonResponse
    from .models import Notification
    
    notification = get_object_or_404(Notification, id=notification_id, recipient=request.user)
    notification.is_read = True
    notification.save()
    
    # If the request is AJAX, return JsonResponse with the link
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'status': 'success', 'link': notification.link})
        
    # Otherwise redirect to the link if it exists
    if notification.link:
        return redirect(notification.link)
    
    return redirect(request.META.get('HTTP_REFERER', '/'))