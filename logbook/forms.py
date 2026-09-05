from django import forms
from django.db.models import Q

from .models import (
    Vehicle,
    Driver,
    LogBook,
    LogBookEntry,
)


# =========================================================
# VEHICLE FORM
# =========================================================

class VehicleForm(forms.ModelForm):

    class Meta:
        model = Vehicle

        fields = [
            "vehicle_number",
            "registration_number",
            "zone",
            "vehicle_type",
            "driver",
            "status",
        ]

        widgets = {

            "vehicle_number": forms.TextInput(
                attrs={
                    "class": "form-control"
                }
            ),

            "registration_number": forms.TextInput(
                attrs={
                    "class": "form-control"
                }
            ),

            "zone": forms.TextInput(
                attrs={
                    "class": "form-control"
                }
            ),

            "vehicle_type": forms.TextInput(
                attrs={
                    "class": "form-control"
                }
            ),

            "driver": forms.Select(
                attrs={
                    "class": "form-control"
                }
            ),

            "status": forms.Select(
                attrs={
                    "class": "form-control"
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if 'driver' in self.fields:
            self.fields['driver'].label = "Assigned Driver"
            self.fields['driver'].empty_label = "-- Select Driver --"
            if user and not (user.username in ['CEO', 'Fleet_Manager', 'Manager_Admin'] or (hasattr(user, 'profile') and user.profile.role in ['CEO', 'Manager', 'GM', 'PS'])):
                self.fields['driver'].queryset = Driver.objects.filter(Q(created_by=user) | Q(created_by__isnull=True))


# =========================================================
# DRIVER FORM
# =========================================================

class DriverForm(forms.ModelForm):

    class Meta:
        model = Driver

        fields = [
            "name",
            "mobile",
            "cnic",
            "vehicle",
            "is_active",
        ]

        widgets = {

            "name": forms.TextInput(
                attrs={
                    "class": "form-control"
                }
            ),

            "mobile": forms.TextInput(
                attrs={
                    "class": "form-control"
                }
            ),

            "cnic": forms.TextInput(
                attrs={
                    "class": "form-control"
                }
            ),

            "vehicle": forms.Select(
                attrs={
                    "class": "form-control"
                }
            ),

            "is_active": forms.CheckboxInput(
                attrs={
                    "class": "form-check-input"
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user and not (user.username in ['CEO', 'Fleet_Manager', 'Manager_Admin'] or (hasattr(user, 'profile') and user.profile.role in ['CEO', 'Manager', 'GM', 'PS'])):
            self.fields['vehicle'].queryset = Vehicle.objects.filter(created_by=user)


# =========================================================
# LOG BOOK FORM
# =========================================================

class LogBookForm(forms.ModelForm):

    class Meta:
        model = LogBook

        fields = [
            "vehicle",
            "vehicle_number",
            "serial_number",
            "average_to_litre",
            "opening_meter_reading",
        ]

        widgets = {

            "vehicle": forms.Select(
                attrs={
                    "class": "form-control"
                }
            ),

            "vehicle_number": forms.TextInput(
                attrs={
                    "class": "form-control"
                }
            ),

            "serial_number": forms.TextInput(
                attrs={
                    "class": "form-control"
                }
            ),

            "average_to_litre": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "step": "0.01",
                    "min": 0,
                    "placeholder": "e.g. 10.50"
                }
            ),

            "opening_meter_reading": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": 0
                }
            ),
        }


# =========================================================
# LOG BOOK ENTRY FORM
# =========================================================

class LogBookEntryForm(forms.ModelForm):

    class Meta:
        model = LogBookEntry

        fields = [
            "signed_requisition",
            "date",
        ]

        widgets = {
            "signed_requisition": forms.ClearableFileInput(
                attrs={
                    "class": "form-control",
                    "accept": ".pdf,.jpg,.jpeg,.png,.webp,.doc,.docx"
                }
            ),

            "date": forms.DateInput(
                attrs={
                    "type": "date",
                    "class": "form-control"
                }
            ),
        }
