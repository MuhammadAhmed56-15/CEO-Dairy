from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

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
        ('Manager', 'Manager'),
        ('HR', 'HR'),
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
        choices=(('Low', 'Low'), ('Medium', 'Medium'), ('High', 'High')),
        default='Medium'
    )
    category = models.CharField(
        max_length=50,
        choices=(
            ('Meeting', 'Meeting'),
            ('Task', 'Task'),
            ('Visit', 'Visit'),
            ('Event', 'Event'),
            ('Urgent', 'Urgent'),
            ('Other', 'Other'),
        ),
        default='Other'
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

    # ===== NAYA PROPERTY METHOD - CHECK IF EXPIRED =====
    @property
    def is_expired(self):
        """Check if commitment date has passed"""
        if self.commitment_date:
            return self.commitment_date < timezone.now()
        return False

    class Meta:
        ordering = ['-created_at']  # Newest first by default

    def __str__(self):
        return f"{self.title} — {self.created_by.user.username}"

    # --------------------------
    # Override save method
    # --------------------------
    def save(self, *args, **kwargs):
        # If status is Approved, auto-set is_sent_to_manager to True
        if self.status == 'Approved':
            self.is_sent_to_manager = True
        super().save(*args, **kwargs)

# =========================================================
# TASK MODEL
# =========================================================
class Task(models.Model):
    STATUS_CHOICES = (
        ('Pending', 'Pending'),
        ('In Progress', 'In Progress'),
        ('Completed', 'Completed'),
    )
    
    title = models.CharField(max_length=200, blank=False, null=False)
    description = models.TextField(blank=True, null=True)
    assigned_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="tasks_assigned")
    assigned_to = models.ForeignKey(User, on_delete=models.CASCADE, related_name="tasks_received")
    due_date = models.DateField(blank=True, null=True) 
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} → {self.assigned_to.username}"

# =========================================================
# REMARK MODEL
# =========================================================
class Remark(models.Model):
    STATUS_CHOICES = (
        ('In Progress', 'In Progress'),
        ('Completed', 'Completed'),
    )
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='remarks')
    manager = models.ForeignKey(User, on_delete=models.CASCADE, related_name='remarks_given')
    feedback = models.TextField()
    status_update = models.CharField(max_length=20, choices=STATUS_CHOICES, default='In Progress')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        self.task.status = self.status_update
        self.task.save()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Remark by {self.manager.username} on {self.task.title}"