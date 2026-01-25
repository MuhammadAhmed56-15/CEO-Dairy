from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
from django.db.models import Count
from .models import Profile, Commitment, Task  # Saare models aik saath
from .forms import CommitmentForm


# =========================================================
# LOGIN VIEW
# =========================================================
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
            elif profile.role == "Manager":
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
        return {
            'id': c.id,
            'title': c.title,
            'description': c.description,
            'location': c.location,
            'category': c.category,
            'status': c.status,
            'date': c.commitment_date.strftime('%b %d, %Y'),
            'time': c.commitment_date.strftime('%I:%M %p'),
            'datetime': c.commitment_date.strftime('%Y-%m-%d %H:%M')
        }

    all_commitments_json = json.dumps([commitment_to_dict(c) for c in all_commitments])
    pending_list_json = json.dumps([commitment_to_dict(c) for c in pending_list])
    approved_list_json = json.dumps([commitment_to_dict(c) for c in approved_list])
    rejected_list_json = json.dumps([commitment_to_dict(c) for c in rejected_list])

    # Upcoming commitments (next 7 days)
    today = timezone.now()
    next_week = today + timedelta(days=7)
    upcoming = Commitment.objects.filter(
        created_by=profile, 
        commitment_date__range=(today, next_week)
    ).order_by('commitment_date')

    # --- GRAPHS DATA ---
    # 1. Category Chart
    category_counts = Commitment.objects.filter(created_by=profile).values('category').annotate(count=Count('id'))
    category_labels = [item['category'] for item in category_counts]
    category_data = [item['count'] for item in category_counts]

    # 2. Daily Chart (default next 7 days)
    daily_labels = []
    daily_data = []
    for i in range(7):
        day = today + timedelta(days=i)
        daily_labels.append(day.strftime("%Y-%m-%d"))
        count = Commitment.objects.filter(created_by=profile, commitment_date__date=day.date()).count()
        daily_data.append(count)

    context = {
        "total": total,
        "pending": pending,
        "approved": approved,
        "rejected": rejected,
        "all_commitments_json": all_commitments_json,
        "pending_list_json": pending_list_json,
        "approved_list_json": approved_list_json,
        "rejected_list_json": rejected_list_json,
        "approved_list": approved_list,  # For calendar
        "upcoming": upcoming,
        "category_labels": category_labels,
        "category_data": category_data,
        "daily_labels": daily_labels,
        "daily_data": daily_data,
    }
    return render(request, "ps_dashboard.html", context)


# =========================================================
# PS CHART DATA API - ENDPOINT FOR DYNAMIC CHART
# =========================================================
@login_required
def get_ps_chart_data(request):
    """
    API endpoint to get PS chart data for specific date ranges
    Usage: /api/ps-chart-data/?dates=2026-01-22,2026-01-23,2026-01-24
    """
    profile = Profile.objects.get(user=request.user)
    if profile.role != "PS":
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    dates_str = request.GET.get('dates', '')
    
    if not dates_str:
        return JsonResponse({'error': 'No dates provided'}, status=400)
    
    dates = dates_str.split(',')
    data = []
    
    for date_str in dates:
        try:
            # Parse the date string
            date = datetime.strptime(date_str.strip(), '%Y-%m-%d').date()
            
            # Count PS's commitments on this date
            count = Commitment.objects.filter(
                created_by=profile,
                commitment_date__date=date
            ).count()
            
            data.append(count)
        except ValueError:
            # If date parsing fails, append 0
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
    profile = Profile.objects.get(user=request.user)
    if profile.role != "CEO":
        return redirect("ps_dashboard")

    today = timezone.now()
    next_week = today + timedelta(days=7)

    # KPI counts - Poore system se data uthane ke liye user filter nahi lagana
    total_list = Commitment.objects.all()
    pending_list = Commitment.objects.filter(status__iexact="Pending")
    approved_list = Commitment.objects.filter(status__iexact="Approved")
    rejected_list = Commitment.objects.filter(status__iexact="Rejected")

    total = total_list.count()
    pending = pending_list.count()
    approved = approved_list.count()
    rejected = rejected_list.count()

    # Upcoming approved commitments (Next 7 days for Everyone)
    upcoming = Commitment.objects.filter(
        commitment_date__range=(today, next_week), 
        status__iexact="Approved"
    ).order_by('commitment_date')

    # Tasks assigned by CEO
    my_assigned_tasks = Task.objects.filter(assigned_by=request.user).order_by('-created_at')[:5]

    # CALENDAR DATA: Calendar par sab approved meetings show hon
    all_commitments = Commitment.objects.filter(status__iexact="Approved").order_by('commitment_date')

    # Charts data (Pure system ki base par)
    category_counts = Commitment.objects.values('category').annotate(count=Count('id'))
    category_labels = [item['category'] for item in category_counts]
    category_data = [item['count'] for item in category_counts]

    # Daily data for next 7 days (default view)
    daily_labels = []
    daily_data = []
    for i in range(7):
        day = today + timedelta(days=i)
        daily_labels.append(day.strftime("%Y-%m-%d"))
        count = Commitment.objects.filter(commitment_date__date=day.date(), status__iexact="Approved").count()
        daily_data.append(count)

    context = {
        "total": total,
        "pending": pending, 
        "approved": approved,
        "rejected": rejected,
        "total_list": total_list,
        "pending_list": pending_list,
        "approved_list": approved_list,
        "rejected_list": rejected_list,
        "upcoming": upcoming,
        "all_commitments": all_commitments, 
        "category_labels": category_labels,
        "category_data": category_data,
        "daily_labels": daily_labels,
        "daily_data": daily_data,
        "my_assigned_tasks": my_assigned_tasks,
    }

    return render(request, "ceo_dashboard.html", context)


# =========================================================
# CHART DATA API - FOR DYNAMIC CHART
# =========================================================
@login_required
def get_chart_data(request):
    """API endpoint to get chart data for specific date ranges"""
    profile = Profile.objects.get(user=request.user)
    if profile.role != "CEO":
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    dates_str = request.GET.get('dates', '')
    
    if not dates_str:
        return JsonResponse({'error': 'No dates provided'}, status=400)
    
    dates = dates_str.split(',')
    data = []
    
    for date_str in dates:
        try:
            date = datetime.strptime(date_str.strip(), '%Y-%m-%d').date()
            count = Commitment.objects.filter(
                commitment_date__date=date,
                status__iexact="Approved"
            ).count()
            data.append(count)
        except ValueError:
            data.append(0)
    
    return JsonResponse(data, safe=False)


# =========================================================
# ADD COMMITMENT
# =========================================================
@login_required
def add_commitment(request):
    profile = Profile.objects.get(user=request.user)

    managers = User.objects.filter(
        profile__role="Manager",
        profile__employee__isnull=False
    ).select_related("profile__employee")

    if request.method == "POST":
        form = CommitmentForm(request.POST, user=request.user)
        if form.is_valid():
            commitment = form.save(commit=False)
            commitment.created_by = profile

            if profile.role == "PS":
                commitment.status = "Pending"
            elif profile.role == "CEO":
                commitment.status = "Approved"

            commitment.save()

            invited_ids = request.POST.getlist("invited_managers")
            commitment.invited_managers.set(invited_ids)

            messages.success(request, "Commitment added successfully!")
            return redirect(
                "ceo_dashboard" if profile.role == "CEO" else "ps_dashboard"
            )
    else:
        form = CommitmentForm(user=request.user)

    return render(request, "add_commitment.html", {"form": form, "managers": managers})


@login_required
def edit_commitment(request, pk):
    profile = Profile.objects.get(user=request.user)
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


@login_required
def update_status(request, pk, status):
    """CEO approves or rejects a commitment"""
    profile = Profile.objects.get(user=request.user)
    if profile.role != "CEO":
        messages.error(request, "Not authorized")
        return redirect("ps_dashboard")

    commitment = get_object_or_404(Commitment, pk=pk)
    if status in ["Approved", "Rejected"]:
        commitment.status = status
        commitment.save()
        messages.success(request, f"Commitment {status.lower()} successfully!")
    return redirect("ceo_dashboard")


@login_required
def delete_commitment(request, pk):
    profile = Profile.objects.get(user=request.user)
    commitment = get_object_or_404(Commitment, pk=pk)

    if profile.role == "CEO" or commitment.created_by == profile:
        commitment.delete()
        messages.success(request, "Deleted successfully!")
    else:
        messages.error(request, "You cannot delete this!")
    
    return redirect("ceo_dashboard" if profile.role == "CEO" else "ps_dashboard")


@login_required
def commitment_list(request):
    profile = Profile.objects.get(user=request.user)
    today = timezone.now()
    status_filter = request.GET.get('status')

    # Approval Logic (Sirf CEO ke liye)
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
        except Commitment.DoesNotExist: 
            pass
        return redirect("commitment_list")

    # Role-based filtering
    if profile.role == "PS":
        commitments = Commitment.objects.filter(created_by=profile).order_by('-created_at')
    elif profile.role == "CEO":
        commitments = Commitment.objects.all().order_by('-created_at')
    else:
        commitments = Commitment.objects.none()

    # Status filter
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
        'category_choices': ['All', 'Meeting', 'Task', 'Visit', 'Event', 'Other'],
        'priority_choices': ['All', 'Low', 'Medium', 'High'],
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


@login_required
def assign_task_view(request):
    if request.user.profile.role != "CEO":
        return HttpResponseForbidden("You are not allowed to access this page")

    if request.method == "POST":
        form = TaskAssignForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.assigned_by = request.user
            task.save()
            return redirect('ceo_dashboard')
    else:
        form = TaskAssignForm()
    
    return render(request, 'ceo_assign_task.html', {'form': form})

import json
from django.db.models import Count
from django.utils import timezone
from datetime import timedelta
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from .forms import RemarkForm
from .models import Task, Remark, Commitment


@login_required
def manager_dashboard(request):
    # 1. Manager ke apne tasks
    my_tasks = Task.objects.filter(assigned_to=request.user)
    
    # --- UPCOMING TASKS LOGIC ---
    today = timezone.now().date()
    next_week = today + timedelta(days=7)
    upcoming_tasks = my_tasks.filter(
        due_date__range=[today, next_week]
    ).exclude(status='Completed').order_by('due_date')

    # --- INVITED COMMITMENTS/MEETINGS ---
    # Sirf wo meetings dikhani hain jin mein ye user invited hai aur PS ne send kar di hain
    invited_commitments = Commitment.objects.filter(
        invited_managers=request.user,
        is_sent_to_manager=True,
        status='Approved'
    ).order_by('-commitment_date')

    # 2. KPI Cards ka data
    total_tasks = my_tasks.count()
    pending_tasks = my_tasks.filter(status='Pending').count()
    in_progress_tasks = my_tasks.filter(status='In Progress').count()
    completed_tasks = my_tasks.filter(status='Completed').count()

    # Status Pie Chart
    status_data = list(my_tasks.values('status').annotate(count=Count('id')))
    cat_labels = [item['status'] for item in status_data] 
    cat_counts = [item['count'] for item in status_data]

    # Next 7 Days Bar Chart data
    days = [(today + timedelta(days=i)) for i in range(7)]
    day_labels = [d.strftime('%Y-%m-%d') for d in days]
    day_counts = [my_tasks.filter(due_date=d).count() for d in days]

    # 3. Context
    context = {
        'tasks': my_tasks,
        'upcoming_tasks': upcoming_tasks,
        'invited_commitments': invited_commitments,
        'total_tasks': total_tasks,
        'pending_tasks': pending_tasks,
        'in_progress_tasks': in_progress_tasks,
        'completed_tasks': completed_tasks,
        
        'cat_labels': json.dumps(cat_labels),
        'cat_counts': json.dumps(cat_counts),
        'day_labels': json.dumps(day_labels),
        'day_counts': json.dumps(day_counts),
    }
    
    return render(request, 'manager_dashboard.html', context)


@login_required
def manager_task_view(request):
    """
    Manager Tasks View with Status Filtering
    - Total Tasks card: Shows all tasks (no filter)
    - Pending card: Shows only Pending tasks
    - In Progress card: Shows only In Progress tasks
    - Completed card: Shows only Completed tasks
    """
    # URL se status filter pakrain
    status_filter = request.GET.get('status')
    
    # Manager ke apne tasks (Base List)
    tasks = Task.objects.filter(assigned_to=request.user).order_by('-created_at')

    # Filter apply karein agar specific card click hua hai
    if status_filter:
        tasks = tasks.filter(status=status_filter)

    # Context mein status filter bhi bhejain taake template mein active filter dikha sakain
    context = {
        'tasks': tasks,
        'selected_status': status_filter,
        'total_count': Task.objects.filter(assigned_to=request.user).count(),
        'pending_count': Task.objects.filter(assigned_to=request.user, status='Pending').count(),
        'in_progress_count': Task.objects.filter(assigned_to=request.user, status='In Progress').count(),
        'completed_count': Task.objects.filter(assigned_to=request.user, status='Completed').count(),
    }
    
    return render(request, 'manager_tasks.html', context)


@login_required
def add_remark_view(request):
    """
    Add Remark View - Only Manager can access
    """
    # Only Manager can access
    if request.user.profile.role != "Manager":
        return HttpResponseForbidden("You are not allowed to access this page")

    if request.method == "POST":
        form = RemarkForm(request.POST, manager=request.user)
        if form.is_valid():
            remark = form.save(commit=False)
            remark.manager = request.user
            remark.save()
            return redirect('manager_dashboard')  # redirect to dashboard
    else:
        # GET request - check if task_id is in query params
        task_id = request.GET.get('task_id')
        if task_id:
            # Pre-select the task if task_id is provided
            form = RemarkForm(manager=request.user, initial={'task': task_id})
        else:
            form = RemarkForm(manager=request.user)

    return render(request, 'add_remark.html', {'form': form})


# ==========================================================
# CEO TASK ASSIGNMENT LOGIC     
# ==========================================================
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.utils import timezone
from .models import Task  # Ensure Task model is imported

@login_required
def ceo_assign_task(request):
    # 1. Check ke sirf CEO hi access kar sake
    if request.user.profile.role != 'CEO':
        messages.error(request, "Access Denied! Only CEO can assign tasks.")
        return redirect('dashboard') 

    if request.method == 'POST':
        # Form se data uthana (priority wala variable yahan se hata diya hai)
        title = request.POST.get('title')
        description = request.POST.get('description')
        assigned_to_id = request.POST.get('assigned_to')
        due_date = request.POST.get('due_date')

        try:
            # Task create karna database mein
            user_to_assign = User.objects.get(id=assigned_to_id)
            
            # Yahan se priority=priority nikaal diya hai taake error na aaye
            Task.objects.create(
                title=title,
                description=description,
                assigned_to=user_to_assign,
                assigned_by=request.user,
                due_date=due_date,
                status='Pending'
            )
            messages.success(request, f"Task successfully assigned to {user_to_assign.username}!")
            return redirect('ceo_dashboard') 
            
        except User.DoesNotExist:
            messages.error(request, "Selected staff member not found.")
        except Exception as e:
            messages.error(request, f"Something went wrong: {e}")

    # Staff members filter karna
    staff_members = User.objects.filter(profile__role__in=['GM', 'HR', 'Manager'])
    
    context = {
        'staff_members': staff_members,
        'today_date': timezone.now().date()
    }
    
    return render(request, 'ceo_assign_task.html', context)
# ==========================================================



# ==========================================================
# VIEW FEEDBACKS LOGIC 
# ==========================================================
import pandas as pd
from django.db.models import Q
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from .models import Task

# PDF ke liye ReportLab imports
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet

@login_required
def ceo_view_feedbacks(request):
    if request.user.profile.role != 'CEO':
        return redirect('ceo_dashboard')

    # 1. Base query: Get tasks with feedback
    feedback_tasks = Task.objects.filter(
        assigned_by=request.user,
        remarks__feedback__isnull=False
    ).distinct().order_by('-created_at')

    # 2. Filtering Logic (Search & Status)
    query = request.GET.get('q', '')
    status_filter = request.GET.get('status', 'all')

    if query:
        feedback_tasks = feedback_tasks.filter(
            Q(title__icontains=query) | 
            Q(assigned_to__username__icontains=query)
        )

    if status_filter and status_filter.lower() != 'all' and status_filter != 'All Status':
        feedback_tasks = feedback_tasks.filter(status__iexact=status_filter)

    # 3. Export Logic
    export_format = request.GET.get('export')
    
    # --- EXCEL SECTION ---
    if export_format == 'excel':
        data = []
        for task in feedback_tasks:
            feedback_text = task.remarks.first().feedback if task.remarks.exists() else "No Feedback"
            staff_name = task.assigned_to.username if task.assigned_to else "N/A"
            data.append({
                'Task Name': task.title,
                'Staff Member': staff_name,
                'Feedback': feedback_text,
                'Due Date': task.due_date.strftime('%Y-%m-%d') if task.due_date else "N/A",
                'Status': task.status
            })
        
        df = pd.DataFrame(data)
        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename="Staff_Feedback_Report.xlsx"'
        with pd.ExcelWriter(response, engine='openpyxl') as writer:
            df.to_excel(writer, index=False)
        return response

    # --- PDF SECTION ---
    if export_format == 'pdf':
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="Staff_Feedback_Report.pdf"'
        
        # Landscape orientation for better feedback visibility
        doc = SimpleDocTemplate(response, pagesize=landscape(letter))
        elements = []
        styles = getSampleStyleSheet()
        
        # Report Title
        elements.append(Paragraph("Staff Feedback Detailed Report", styles['Title']))
        
        # Table Header
        data = [['Task Name', 'Staff Member', 'Feedback', 'Due Date', 'Status']]
        
        # Table Rows
        for task in feedback_tasks:
            fb = task.remarks.first().feedback if task.remarks.exists() else "No Feedback"
            staff = task.assigned_to.username if task.assigned_to else "N/A"
            date = task.due_date.strftime('%Y-%m-%d') if task.due_date else "N/A"
            data.append([task.title, staff, fb, date, task.status])
        
        # Table Styling (Purple/Dark Blue theme)
        feedback_table = Table(data, repeatRows=1)
        feedback_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#6f42c1')), # Purple Theme
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.whitesmoke),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        
        elements.append(feedback_table)
        doc.build(elements)
        return response

    # 4. Normal View
    return render(request, 'ceo_view_feedbacks.html', {
        'feedbacks': feedback_tasks,
        'query': query,
        'status_filter': status_filter
    })


from django.db.models import Q
from django.shortcuts import render
from .models import Task # Ya jo bhi aapka model name hai

def all_tasks_view(request):
    # 1. Base query: Saare tasks uthao (Global view jaisa aapne kaha tha)
    tasks = Task.objects.all().order_by('-created_at')

    # 2. Search Logic (id="customSearch" wala data)
    query = request.GET.get('q') # HTML mein name="q" hona chahiye
    if query:
        tasks = tasks.filter(
            Q(title__icontains=query) | 
            Q(location__icontains=query) |
            Q(description__icontains=query)
        )

    # 3. Status Filter (id="statusFilter" wala data)
    status_filter = request.GET.get('status') # HTML mein name="status" hona chahiye
    if status_filter:
        # Note: Aapke HTML mein values "Approved" aur "Pending" hain
        tasks = tasks.filter(status__iexact=status_filter)

    # 4. Context bhej dena
    return render(request, 'all_tasks_list.html', {'tasks': tasks})