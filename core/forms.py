from django import forms
from django.contrib.auth.models import User
from django.db.models import Q
from .models import Commitment, Task, Notesheet, Remark, Profile, VehicleRequisition

# =========================================================
# 1. COMMITMENT FORM
# =========================================================
class CommitmentForm(forms.ModelForm):
    invited_managers = forms.ModelMultipleChoiceField(
        queryset=User.objects.none(),
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        required=False,
        label="Select Staff to Invite (HR, GM, Manager, etc.)"
    )

    class Meta:
        model = Commitment
        fields = ['title', 'description', 'location', 'commitment_date', 'priority', 'category', 'invited_managers']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Title'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'commitment_date': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}, format='%Y-%m-%dT%H:%M'),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('manager', kwargs.pop('user', None))
        super().__init__(*args, **kwargs)
        self.fields['invited_managers'].queryset = User.objects.filter(
            Q(profile__role__category__in=['HR', 'GM', 'Manager']) | Q(profile__role__code__in=['HR', 'GM', 'Manager'])
        ).order_by('username')
        if self.instance and self.instance.commitment_date:
            self.initial['commitment_date'] = self.instance.commitment_date.strftime('%Y-%m-%dT%H:%M')

# =========================================================
# 2. INITIATE NOTESHEET FORM
# =========================================================
class InitiateNotesheetForm(forms.ModelForm):
    para_1 = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Para 1: Background/Reference...'}),
        label="Paragraph 1 (Background)",
        required=False 
    )
    para_2 = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Para 2: Proposal/Request...'}),
        label="Paragraph 2 (Current Status)",
        required=False
    )
    
    forward_to_user = forms.ModelChoiceField(
        queryset=User.objects.all().order_by('username'),
        widget=forms.Select(attrs={'class': 'form-control select2'}),
        label="Forward To (Select Officer)"
    )

    class Meta:
        model = Notesheet
        fields = ['title'] 
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Subject of Notesheet'}),
        }

    def __init__(self, *args, **kwargs):
        self.manager = kwargs.pop('manager', None)
        super().__init__(*args, **kwargs)
        qs = User.objects.exclude(Q(profile__role__category='HR') | Q(profile__role__code='HR'))
        if self.manager:
            qs = qs.exclude(id=self.manager.id)
        self.fields['forward_to_user'].queryset = qs

# =========================================================
# 3. REMARK FORM (FIXED - Dropdowns will now show)
# =========================================================
class RemarkForm(forms.ModelForm):
    # 1. Task Dropdown
    task = forms.ModelChoiceField(
        queryset=Task.objects.none(),
        widget=forms.Select(attrs={'class': 'form-control select2'}), # CSS match karne ke liye
        label="Select Task",
        required=True
    )

    # 2. Update Status (Wahi purane 2 options jo aapko chahiye thay)
    action_taken = forms.ChoiceField(
        choices=[
            ('save', 'In Progress'),
            ('approve', 'Completed'),
        ],
        widget=forms.Select(attrs={'class': 'form-control'}), # Aapki styling ke liye
        label="Update Status",
        required=True
    )

    class Meta:
        model = Remark
        fields = ['task', 'feedback', 'action_taken'] 
        widgets = {
            'feedback': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 4, 
                'placeholder': 'Enter your feedback...',
                'id': 'feedbackTextarea' # Counter ke liye
            }),
        }

    def __init__(self, *args, **kwargs):
        manager = kwargs.pop('manager', None)
        super().__init__(*args, **kwargs)
        if manager:
            # Only show tasks that are assigned to the manager, not completed, and do not have remarks yet
            self.fields['task'].queryset = Task.objects.filter(
                assigned_to=manager
            ).exclude(status='Completed').exclude(remarks__isnull=False).distinct().order_by('-created_at')

# =========================================================
# 4. TASK ASSIGN FORM
# =========================================================
class TaskAssignForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['title', 'description', 'assigned_to', 'due_date']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'assigned_to': forms.Select(attrs={'class': 'form-select'}),
            'due_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
        }

    def __init__(self, *args, **kwargs):
        kwargs.pop('manager', None)
        super().__init__(*args, **kwargs)

# =========================================================
# 5. VEHICLE REQUISITION FORM
# =========================================================
class VehicleRequisitionForm(forms.ModelForm):
    class Meta:
        model = VehicleRequisition
        fields = [
            'zone', 'uc_route', 'vehicle_number', 'issue_description', 
            'previous_issue_date', 'estimated_cost', 'driver_name', 
            'driver_mobile', 'driver_cnic', 'is_first_time'
        ]
        widgets = {
            'zone': forms.TextInput(attrs={'class': 'form-input form-input-line', 'placeholder': 'Zone'}),
            'uc_route': forms.TextInput(attrs={'class': 'form-input form-input-line', 'placeholder': 'U.C / Route'}),
            'vehicle_number': forms.TextInput(attrs={'class': 'form-input form-input-line', 'placeholder': 'Vehicle Number'}),
            'issue_description': forms.Textarea(attrs={'class': 'form-input form-input-line-textarea', 'rows': 4, 'placeholder': '(1) \n(2) \n(3) \n(4)'}),
            'previous_issue_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-input form-input-line'}),
            'estimated_cost': forms.TextInput(attrs={'class': 'form-input form-input-line', 'placeholder': 'Rs. 10000'}),
            'driver_name': forms.TextInput(attrs={'class': 'form-input form-input-line', 'placeholder': 'Driver Name'}),
            'driver_mobile': forms.TextInput(attrs={'class': 'form-input form-input-line', 'placeholder': '03XX-XXXXXXX'}),
            'driver_cnic': forms.TextInput(attrs={'class': 'form-input form-input-line', 'placeholder': 'XXXXX-XXXXXXX-X'}),
        }