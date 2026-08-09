from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Profile, Commitment, Employee, Task, Remark, 
    File, Notesheet, NotesheetForward, NotesheetAgenda,
    UserHierarchy, NotesheetReturn, NotesheetAttachment,
    LetterFile, Letter, DraftLetter, Notification
)

# =========================================================
# 📂 FILE / FOLDER ADMIN
# =========================================================

@admin.register(NotesheetAttachment)
class NotesheetAttachmentAdmin(admin.ModelAdmin):
    list_display = ('notesheet', 'uploaded_at')


@admin.register(File)
class FileAdmin(admin.ModelAdmin):
    list_display = ('file_name', 'file_number', 'created_at')
    search_fields = ('file_name', 'file_number')
    list_filter = ('created_at',)
    ordering = ('-created_at',)

# =========================================================
# 👤 PROFILE ADMIN
# =========================================================
from django.contrib import admin
from django.utils.html import format_html
from .models import Profile


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    # Table View Columns
    list_display = ('user', 'role', 'department', 'employee', 'signature_preview')
    list_filter = ('role', 'department')
    search_fields = ('user__username', 'department', 'user__first_name', 'user__last_name')
    ordering = ('role', 'user__username')
    
    # Specific Profile Edit Page Par Preview Layout
    readonly_fields = ('signature_detail_preview',)
    fields = ('user', 'role', 'employee', 'department', 'signature', 'signature_detail_preview')

    # 1. Table View Thumbnail (Chota Preview Table Mein)
    def signature_preview(self, obj):
        if obj.signature:
            return format_html(
                '<img src="{}" style="height: 35px; width: auto; border: 1px solid #ccc; padding: 2px; background: white; border-radius: 4px;" />',
                obj.signature.url
            )
        return "No Signature"
    signature_preview.short_description = 'Signature'

    # 2. Detail View Large Preview (Bada Preview Profile Form Mein)
    def signature_detail_preview(self, obj):
        if obj.signature:
            return format_html(
                '<div style="margin-top: 5px;">'
                '<img src="{}" style="max-height: 120px; width: auto; border: 1px solid #0f392b; padding: 6px; background: #ffffff; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);" />'
                '</div>',
                obj.signature.url
            )
        return "No Digital Signature Saved Yet"
    signature_detail_preview.short_description = 'Current Saved Signature'

# =========================================================
# 🤝 COMMITMENT ADMIN
# =========================================================
@admin.register(Commitment)
class CommitmentAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_by', 'commitment_date', 'status', 'priority', 'category')
    list_filter = ('status', 'priority', 'category', 'commitment_date')
    search_fields = ('title', 'description', 'location', 'created_by__user__username')
    date_hierarchy = 'commitment_date'
    ordering = ('-commitment_date',)
    readonly_fields = ('created_at', 'updated_at')

# =========================================================
# 👷 EMPLOYEE ADMIN
# =========================================================
@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('emp_id', 'name', 'department', 'designation')
    search_fields = ('emp_id', 'name', 'department', 'designation')
    list_filter = ('department', 'designation')
    ordering = ('emp_id',)

# =========================================================
# 📝 TASK ADMIN (NOTESHEET)
# =========================================================
@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'file', 'assigned_by', 'current_handler_role', 'status', 'created_at')
    list_filter = ('status', 'current_handler_role', 'assigned_by', 'file')
    search_fields = ('title', 'description', 'assigned_by__username')
    ordering = ('-created_at',)
    readonly_fields = ('created_at',)

# =========================================================
# 💬 REMARK ADMIN (NOTESHEET PARAS)
# =========================================================
@admin.register(Remark)
class RemarkAdmin(admin.ModelAdmin):
    list_display = ('task', 'manager', 'action_taken', 'created_at')
    list_filter = ('action_taken', 'created_at')
    search_fields = ('task__title', 'manager__username', 'feedback')

# =========================================================
# 🔹 NOTESHEET INLINES
# =========================================================
class NotesheetAgendaInline(admin.TabularInline):
    model = NotesheetAgenda
    extra = 1
    fields = ('agenda_title', 'created_at')
    readonly_fields = ('created_at',)
    show_change_link = True

class NotesheetForwardInline(admin.TabularInline):
    model = NotesheetForward
    extra = 0
    fields = ('forwarded_by', 'forwarded_to', 'remark', 'forwarded_at')
    readonly_fields = ('forwarded_by', 'forwarded_to', 'remark', 'forwarded_at')
    can_delete = False
    show_change_link = True

class NotesheetReturnInline(admin.TabularInline):
    model = NotesheetReturn
    extra = 0
    fields = ('returned_by', 'returned_to', 'remark', 'returned_at')
    readonly_fields = ('returned_by', 'returned_to', 'remark', 'returned_at')
    can_delete = False
    show_change_link = True

# =========================================================
# 📄 MAIN NOTESHEET ADMIN
# =========================================================
@admin.register(Notesheet)
class NotesheetAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_by', 'current_holder', 'status',  'created_at')
    list_filter = ('status', 'due_date', 'created_at')
    search_fields = ('title',)
    autocomplete_fields = ('created_by', 'current_holder')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [NotesheetAgendaInline, NotesheetForwardInline, NotesheetReturnInline]
    ordering = ('-created_at',)

@admin.register(NotesheetForward)
class NotesheetForwardAdmin(admin.ModelAdmin):
    list_display = ('notesheet', 'forwarded_by', 'forwarded_to', 'forwarded_at')
    list_filter = ('forwarded_at',)
    search_fields = ('notesheet__title',)

@admin.register(NotesheetReturn)
class NotesheetReturnAdmin(admin.ModelAdmin):
    list_display = ('notesheet', 'returned_by', 'returned_to', 'returned_at')
    list_filter = ('returned_at',)
    search_fields = ('notesheet__title', 'remark')

@admin.register(NotesheetAgenda)
class NotesheetAgendaAdmin(admin.ModelAdmin):
    list_display = ('notesheet', 'agenda_preview', 'created_at')
    search_fields = ('notesheet__title',)
    readonly_fields = ('agenda_rendered', 'created_at')

    def agenda_preview(self, obj):
        import re
        plain = re.sub(r'<[^>]+>', '', obj.agenda_title or '')
        plain = plain.strip()
        return plain[:80] + '…' if len(plain) > 80 else plain
    agenda_preview.short_description = 'Agenda (Preview)'

    def agenda_rendered(self, obj):
        return format_html(obj.agenda_title or '')
    agenda_rendered.short_description = 'Agenda (Rendered)'

# =========================================================
# 👑 USER HIERARCHY ADMIN
# =========================================================
@admin.register(UserHierarchy)
class UserHierarchyAdmin(admin.ModelAdmin):
    list_display = ('boss', 'get_subordinates_count')
    search_fields = ('boss__username',)
    filter_horizontal = ('subordinates',)

    def get_subordinates_count(self, obj):
        return obj.subordinates.count()
    get_subordinates_count.short_description = 'Number of Subordinates'

# =========================================================
# 📩 LETTER SYSTEM ADMINS (UPDATED & ENHANCED)
# =========================================================
@admin.register(LetterFile)
class LetterFileAdmin(admin.ModelAdmin):
    list_display = ('reference_number', 'file_title', 'created_by', 'created_at')
    search_fields = ('reference_number', 'file_title', 'created_by__username')
    list_filter = ('created_at',)
    ordering = ('-created_at',)


@admin.register(Letter)
class LetterAdmin(admin.ModelAdmin):
    list_display = ('subject_preview', 'sender', 'receiver', 'letter_file', 'read_status', 'created_at')
    list_filter = ('is_read', 'created_at', 'letter_file')
    search_fields = ('subject', 'sender__username', 'receiver__username', 'letter_file__reference_number')
    ordering = ('-created_at',)
    readonly_fields = ('created_at',)

    def subject_preview(self, obj):
        """Shortens subject for clean table rendering."""
        return obj.subject[:60] + '...' if len(obj.subject) > 60 else obj.subject
    subject_preview.short_description = 'Subject'

    def read_status(self, obj):
        """Displays Read/Unread badge cleanly in admin."""
        if obj.is_read:
            return format_html('<span style="color: green; font-weight: bold;">✔ Read</span>')
        return format_html('<span style="color: red; font-weight: bold;">✖ Unread</span>')
    read_status.short_description = 'Status'


@admin.register(DraftLetter)
class DraftLetterAdmin(admin.ModelAdmin):
    list_display = ('subject_preview', 'sender', 'receiver', 'letter_file', 'created_at')
    list_filter = ('created_at', 'letter_file')
    search_fields = ('subject', 'sender__username', 'receiver__username', 'letter_file__reference_number')
    ordering = ('-created_at',)
    readonly_fields = ('created_at',)

    def get_queryset(self, request):
        return super().get_queryset(request).filter(is_draft=True)

    def subject_preview(self, obj):
        return obj.subject[:60] + '...' if len(obj.subject) > 60 else obj.subject
    subject_preview.short_description = 'Subject'


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('title', 'recipient', 'sender', 'notification_type', 'is_read', 'created_at')
    list_filter = ('notification_type', 'is_read', 'created_at')
    search_fields = ('title', 'message', 'recipient__username', 'sender__username')
    ordering = ('-created_at',)