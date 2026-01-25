from django import forms
from .models import Commitment
from django.contrib.auth.models import User

from django import forms
from django.contrib.auth.models import User
from .models import Commitment

class CommitmentForm(forms.ModelForm):
    invited_managers = forms.ModelMultipleChoiceField(
        queryset=User.objects.none(),
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        required=False,
        label="Select Staff to Invite (HR, GM, Manager, etc.)"
    )

    class Meta:
        model = Commitment
        fields = [
            'title',
            'description',
            'location',
            'commitment_date',
            'priority',
            'category',
            'invited_managers',
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Title'}),
            'description': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 4, 
                'placeholder': 'Enter Description (Optional)'
            }),
            'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Location (Optional)'}),
            'commitment_date': forms.DateTimeInput(
                attrs={'type': 'datetime-local', 'class': 'form-control'},
                format='%Y-%m-%dT%H:%M'
            ),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # --- YAHAN FIELDS KI SETTINGS HAI ---
        self.fields['description'].required = False 
        self.fields['location'].required = False
        self.fields['title'].required = True  # Title lazmi hai
        self.fields['commitment_date'].required = False
        self.fields['priority'].required = False
        self.fields['category'].required = False

        # Populate invited_managers with HR, GM, and Managers only
        self.fields['invited_managers'].queryset = User.objects.filter(
            profile__role__in=['HR', 'GM', 'Manager']
        ).order_by('profile__role', 'username')

        # Format commitment_date field for datetime-local input
        if self.instance and self.instance.commitment_date:
            self.initial['commitment_date'] = self.instance.commitment_date.strftime('%Y-%m-%dT%H:%M')

        # Role-based field control
        if user:
            profile = getattr(user, 'profile', None)
            if profile and profile.role == 'PS' and 'status' in self.fields:
                self.fields.pop('status')

    # --- YE FUNCTION __init__ KE BAHAR HONA CHAHIYE (Lekin Class ke andar) ---
    def clean_title(self):
        title = self.cleaned_data.get('title')
        if not title or len(title.strip()) == 0:
            raise forms.ValidationError("Title likhna lazmi hai!")
        return title

from django import forms
from django.contrib.auth.models import User
from .models import Task, Profile

class TaskAssignForm(forms.ModelForm):
    assigned_to = forms.ModelChoiceField(
        queryset=User.objects.filter(profile__role="Manager"),
        label="Assign To (Manager)",
        widget=forms.Select(attrs={'class': 'form-select'}) # Styling ke liye
    )

    class Meta:
        model = Task
        fields = ['title', 'description', 'assigned_to', 'due_date']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Task Title'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Optional'}),
            'due_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
        }

    def __init__(self, *args, **kwargs):
        super(TaskAssignForm, self).__init__(*args, **kwargs)
        
        # --- TITLE PAR STERIC LAZMI HAI (REQUIRED) ---
        self.fields['title'].required = True
        
        # --- BAQI FIELDS OPTIONAL HAIN ---
        self.fields['description'].required = False
        self.fields['due_date'].required = False
        



from django import forms
from .models import Remark, Task

class RemarkForm(forms.ModelForm):
    class Meta:
        model = Remark
        fields = ['task', 'feedback', 'status_update']
        widgets = {
            'task': forms.Select(attrs={'class': 'form-control'}),
            'feedback': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Enter your feedback...'}),
            'status_update': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        manager = kwargs.pop('manager', None)
        super().__init__(*args, **kwargs)
        if manager:
            # Show only tasks assigned to this manager AND NOT completed
            self.fields['task'].queryset = Task.objects.filter(
                assigned_to=manager,
            ).exclude(status='Completed')
