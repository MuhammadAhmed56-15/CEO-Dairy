from django.contrib import admin
from .models import Profile, Commitment, Employee

# =========================================================
# PROFILE ADMIN
# =========================================================
@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'department', 'employee')
    list_filter = ('role', 'department')
    search_fields = ('user__username', 'department')
    ordering = ('role', 'user__username')


# =========================================================
# COMMITMENT ADMIN
# =========================================================


@admin.register(Commitment)
class CommitmentAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_by', 'commitment_date', 'status', 'priority', 'category')
    list_filter = ('status', 'priority', 'category', 'commitment_date')
    search_fields = ('title', 'description', 'location', 'created_by__user__username')
    date_hierarchy = 'commitment_date'
    ordering = ('-commitment_date',)
    readonly_fields = ('created_at', 'updated_at')



@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('emp_id', 'name', 'department', 'designation')
    search_fields = ('emp_id', 'name', 'department', 'designation')
    list_filter = ('department', 'designation')
    ordering = ('emp_id',)


from django.contrib import admin
from .models import Task

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'assigned_by', 'assigned_to', 'status', 'due_date', 'created_at')
    list_filter = ('status', 'due_date', 'assigned_by', 'assigned_to')
    search_fields = ('title', 'description', 'assigned_by__username', 'assigned_to__username')
    ordering = ('-created_at',)
    readonly_fields = ('created_at',)



from django.contrib import admin
from .models import Remark

@admin.register(Remark)
class RemarkAdmin(admin.ModelAdmin):
    list_display = ('task', 'manager', 'status_update', 'created_at')
    list_filter = ('status_update', 'created_at')
    search_fields = ('task__title', 'manager__username', 'feedback')
