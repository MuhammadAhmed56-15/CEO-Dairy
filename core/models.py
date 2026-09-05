from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from tinymce.models import HTMLField  # TinyMCE Rich Text Editor

# =========================================================
# EMPLOYEE MODEL
# =========================================================
class Employee(models.Model):
    emp_id = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)
    department = models.CharField(max_length=100)
    designation = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.emp_id} - {self.name}"

# =========================================================
# PROFILE MODEL
# =========================================================
class Profile(models.Model):
    ROLE_CHOICES = (
        ('CEO', 'CEO'),
        ('PS', 'Personal Secretary'),
        ('GM', 'General Manager'),
        ('Manager', 'Manager'),
        ('ZM', 'Zonal Manager'),
        ('AM', 'Assistant Manager'),          
        ('HR', 'HR'),
        ('IT', 'Officer'),
        ('CFO', 'Chief Financial Officer'),
        ('Auditor', 'Auditor'),
    )
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=30, choices=ROLE_CHOICES, default="HR")
    employee = models.OneToOneField(
        Employee,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="profile"
    )
    department = models.CharField(max_length=100, blank=True, null=True)
    signature = models.ImageField(upload_to='signatures/', blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} ({self.role})"

# =========================================================
# COMMITMENT MODEL
# =========================================================
class Commitment(models.Model):
    STATUS_CHOICES = (
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
    )

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    location = models.CharField(max_length=200, blank=True, null=True)
    priority = models.CharField(
        max_length=20,
        choices=(('Normal', 'Normal'), ('High', 'High')),
        default='Normal'
    )
    category = models.CharField(
        max_length=50,
        choices=(
            ('Meeting', 'Meeting'),
            ('Visit', 'Visit'),
            ('Event', 'Event'),
        ),
        default='Meeting'
    )
    commitment_date = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    created_by = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='commitments_created')
    
    invited_managers = models.ManyToManyField(
        User,
        related_name="invited_commitments",
        blank=True,
        limit_choices_to={'profile__role': 'Manager'}
    )
    
    is_sent_to_manager = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def is_expired(self):
        if self.commitment_date:
            return self.commitment_date < timezone.now()
        return False

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} — {self.created_by.user.username}"

    def save(self, *args, **kwargs):
        if self.status == 'Approved':
            self.is_sent_to_manager = True
        super().save(*args, **kwargs)

# =========================================================
# FILE / FOLDER MODEL
# =========================================================
class File(models.Model):
    file_name = models.CharField(max_length=255)
    file_number = models.CharField(max_length=100, unique=True)
    description = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.file_name

# =========================================================
# TASK MODEL (Cleaned & Updated)
# =========================================================
class Task(models.Model):
    STATUS_CHOICES = (
        ('Pending', 'Pending'),
        ('In Progress', 'In Progress'),
        ('Seen', 'Seen'),
        ('Completed', 'Completed'),
    )
    
    file = models.ForeignKey(File, on_delete=models.CASCADE, related_name='tasks', null=True, blank=True)
    title = models.CharField(max_length=200) 
    description = models.TextField(blank=True, null=True) 
    assigned_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="tasks_assigned")
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="tasks_received")
    current_handler_role = models.CharField(max_length=50, default="Manager") 
    due_date = models.DateField(blank=True, null=True) 
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    is_seen = models.BooleanField(default=False)
    seen_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} (From: {self.assigned_by.username} -> To: {self.assigned_to.username if self.assigned_to else 'Unassigned'})"

    @property
    def current_holder(self):
        return self.assigned_to

    @property
    def created_by(self):
        return self.assigned_by

    @property
    def updated_at(self):
        return self.created_at

# =========================================================
# REMARK / TASK FEEDBACK MODEL
# =========================================================
class Remark(models.Model):
    ACTION_CHOICES = (
        ('save', 'Submitted'),
        ('forward', 'Forwarded'),
        ('reverse', 'Reversed'),
        ('approve', 'Final Approved'),
    )

    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='remarks')
    manager = models.ForeignKey(User, on_delete=models.CASCADE, related_name='remarks_given')
    feedback = models.TextField()
    addressed_to = models.CharField(max_length=255, blank=True, null=True) 
    action_taken = models.CharField(max_length=20, choices=ACTION_CHOICES, default='save')
    attachment_1 = models.FileField(upload_to='remark_attachments/', null=True, blank=True)
    attachment_2 = models.FileField(upload_to='remark_attachments/', null=True, blank=True)
    attachment_3 = models.FileField(upload_to='remark_attachments/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Remark by {self.manager.username} on Task '{self.task.title}'"

    def get_formatted_time(self):
        return self.created_at.strftime("%d %b %Y | %I:%M %p") 


class RemarkAttachment(models.Model):
    remark = models.ForeignKey(Remark, on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to='remark_attachments/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Attachment for Remark {self.remark.id} ({self.file.name})"

# =========================================================
# TASK TRACKING / MOVEMENT LOG
# =========================================================
class TaskTracking(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='tracking_history')
    from_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_history')
    to_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_history')
    message = models.CharField(max_length=255) 
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp'] 

    def __str__(self):
        return f"{self.task.title} moved to {self.to_user.username}"

# =========================================================
# NOTESHEET MODEL
# =========================================================
class Notesheet(models.Model):
    STATUS_CHOICES = (
        ('Pending', 'Pending'),
        ('In Progress', 'Seen'),
        ('Returned', 'Returned'),
        ('Completed', 'Completed'),
    )

    file = models.ForeignKey(File, on_delete=models.CASCADE, related_name='notesheets', null=True, blank=True)
    title = models.CharField(max_length=200, db_index=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="created_notesheets")
    current_holder = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="notesheets_in_hand")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="Pending", db_index=True)
    due_date = models.DateField(null=True, blank=True, db_index=True)
    is_seen = models.BooleanField(default=False)
    seen_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        holder = self.current_holder.username if self.current_holder else "Unassigned"
        return f"{self.title} - Currently with {holder}"

# =========================================================
# NOTESHEET FORWARD MODEL
# =========================================================
class NotesheetForward(models.Model):
    notesheet = models.ForeignKey(Notesheet, on_delete=models.CASCADE, related_name="forwards")
    forwarded_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notesheets_forwarded")
    forwarded_to = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notesheets_received")  
    remark = models.TextField(blank=True)
    attachment_1 = models.FileField(upload_to='notesheet_forwards/', null=True, blank=True)
    attachment_2 = models.FileField(upload_to='notesheet_forwards/', null=True, blank=True)
    attachment_3 = models.FileField(upload_to='notesheet_forwards/', null=True, blank=True)
    forwarded_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-forwarded_at']

    def __str__(self):
        return f"{self.notesheet.title} → {self.forwarded_by} to {self.forwarded_to}"

# =========================================================
# NOTESHEET AGENDA MODEL
# =========================================================
class NotesheetAgenda(models.Model):
    notesheet = models.ForeignKey(Notesheet, on_delete=models.CASCADE, related_name="agendas")
    agenda_title = HTMLField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']
        verbose_name = "Notesheet Agenda"
        verbose_name_plural = "Notesheet Agendas"

    def __str__(self):
        return f"Agenda #{self.id} - {self.notesheet.title}"

# =========================================================
# USER HIERARCHY MODEL
# =========================================================
class UserHierarchy(models.Model):
    boss = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        related_name='hierarchy_boss',
        help_text="Wo user jo boss hai (e.g., GM_Operation, CEO, AM)"
    )
    subordinates = models.ManyToManyField(
        User, 
        blank=True, 
        related_name='hierarchy_subordinates',
        help_text="Is boss ke under jitne bhi log aate hain (e.g., Saare ZMs jo isko report karte hain)"
    )

    def __str__(self):
        return f"Boss: {self.boss.username} ({self.subordinates.count()} subordinates)"

    class Meta:
        verbose_name = "User Hierarchy"
        verbose_name_plural = "User Hierarchies"

# =====================================================================
# NOTESHEET ATTACHMENTS MODEL
# =====================================================================
class NotesheetAttachment(models.Model):
    notesheet = models.ForeignKey(
        'Notesheet', 
        on_delete=models.CASCADE, 
        related_name='attachments'
    )
    file = models.FileField(upload_to="notesheet_attachments/")
    flag_name = models.CharField(max_length=10, blank=True, null=True, help_text="e.g., 'A', 'B', 'C'")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        flag_label = self.flag_name if self.flag_name else "No Flag"
        return f"[{flag_label}] Attachment for Notesheet #{self.notesheet.id} - {self.file.name}"

# =====================================================================
# NOTESHEET RETURN TRACKING
# =====================================================================
class NotesheetReturn(models.Model):
    notesheet = models.ForeignKey(
        Notesheet, 
        on_delete=models.CASCADE, 
        related_name="returns"
    )
    returned_by = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name="notesheets_returned_by_me"
    )
    returned_to = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name="notesheets_returned_to_me"
    )  
    remark = models.TextField(blank=True)
    attachment_1 = models.FileField(upload_to='notesheet_returns/', null=True, blank=True)
    attachment_2 = models.FileField(upload_to='notesheet_returns/', null=True, blank=True)
    attachment_3 = models.FileField(upload_to='notesheet_returns/', null=True, blank=True)
    returned_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-returned_at']
        verbose_name = "Notesheet Return"
        verbose_name_plural = "Notesheet Returns"

    def __str__(self):
        return f"Return: {self.notesheet.title} ← From {self.returned_by.username} to {self.returned_to.username}"



# =========================================================
# LETTER SYSTEM MODELS
# =========================================================
class LetterFile(models.Model):
    file_title = models.CharField(max_length=255)
    reference_number = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='letter_files')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Letter File"
        verbose_name_plural = "Letter Files"

    def __str__(self):
        return f"{self.reference_number} - {self.file_title}"


class Letter(models.Model):
    letter_file = models.ForeignKey(LetterFile, on_delete=models.CASCADE, related_name='letters')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_letters')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_letters')
    
    ref_no = models.CharField(max_length=100, blank=True, null=True)
    recipient_address = models.TextField(blank=True, null=True)
    subject = models.CharField(max_length=255)
    body = models.TextField()
    signer_name = models.CharField(max_length=100, blank=True, null=True)
    signer_designation = models.CharField(max_length=100, blank=True, null=True)
    cc_list = models.TextField(blank=True, null=True)
    
    attachment = models.FileField(upload_to='letter_attachments/', blank=True, null=True)
    is_read = models.BooleanField(default=False)
    is_draft = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Reply Fields
    reply_text = models.TextField(blank=True, null=True)
    reply_attachment = models.FileField(upload_to='letter_replies/', blank=True, null=True)
    reply_date = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.subject} (From: {self.sender.username} -> To: {self.receiver.username})"


class DraftLetter(Letter):
    class Meta:
        proxy = True
        verbose_name = "Draft Letter"
        verbose_name_plural = "Draft Letters"



class LetterReplyAttachment(models.Model):
    letter = models.ForeignKey(Letter, on_delete=models.CASCADE, related_name='reply_attachments')
    file = models.FileField(upload_to='letter_reply_attachments/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Reply Attachment for Letter {self.letter.id} ({self.file.name})"

class Notification(models.Model):
    NOTIFICATION_TYPES = (
        ('notesheet', 'Notesheet'),
        ('task', 'Task'),
        ('commitment', 'Commitment'),
        ('letter', 'Letter'),
    )
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    sender = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='sent_notifications')
    title = models.CharField(max_length=255)
    message = models.TextField()
    link = models.CharField(max_length=500, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES, default='notesheet')

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.recipient.username} - {self.title}"

# =====================================================================
# VEHICLE REQUISITION
# =====================================================================
class VehicleRequisition(models.Model):
    STATUS_CHOICES = (
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
        ('Completed', 'Completed'),
    )
    fleet_officer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='requisitions_created')
    zone = models.CharField(max_length=100, blank=True, null=True)
    uc_route = models.CharField(max_length=100, blank=True, null=True)
    vehicle_number = models.CharField(max_length=50)
    issue_description = models.TextField()
    previous_issue_date = models.DateField(blank=True, null=True)
    estimated_cost = models.CharField(max_length=50, blank=True, null=True)
    driver_name = models.CharField(max_length=100)
    driver_mobile = models.CharField(max_length=20, blank=True, null=True)
    driver_cnic = models.CharField(max_length=20, blank=True, null=True)
    driver_signature = models.ImageField(upload_to='requisition_signatures/', blank=True, null=True)
    fleet_officer_signature = models.ImageField(upload_to='requisition_signatures/', blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    manager_admin = models.ForeignKey(User, on_delete=models.CASCADE, related_name='requisitions_received')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.vehicle_number} - {self.driver_name}"