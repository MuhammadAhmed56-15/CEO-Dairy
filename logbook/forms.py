from django import forms
from django.db.models import Q
from core.models import Zone
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
            "vehicle_id_number",
            "vehicle_name",
            "zone",
            "vehicle_type",
            "category",
            "driver",
            "status",
        ]

        widgets = {

            "vehicle_id_number": forms.TextInput(
                attrs={
                    "class": "form-control"
                }
            ),

            "vehicle_name": forms.TextInput(
                attrs={
                    "class": "form-control"
                }
            ),

            "zone": forms.Select(
                attrs={
                    "class": "form-control"
                }
            ),

            "vehicle_type": forms.TextInput(
                attrs={
                    "class": "form-control"
                }
            ),

            "category": forms.TextInput(
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

        # Auto-set zone from user's profile if creating new vehicle
        if user and not self.instance.pk:
            if hasattr(user, 'profile') and user.profile.zone:
                self.initial['zone'] = user.profile.zone.pk

        if 'driver' in self.fields:
            self.fields['driver'].label = "Assigned Driver"
            self.fields['driver'].empty_label = "-- Select Driver --"
            if user and not (user.username in ['CEO', 'Fleet_Manager', 'Manager_Admin'] or (hasattr(user, 'profile') and user.profile.role in ['CEO', 'Manager', 'GM', 'PS'])):
                if hasattr(user, 'profile') and user.profile.zone:
                    self.fields['driver'].queryset = Driver.objects.filter(Q(vehicle__zone=user.profile.zone) | Q(vehicle__isnull=True))
                else:
                    self.fields['driver'].queryset = Driver.objects.none()

        if 'zone' in self.fields:
            self.fields['zone'].empty_label = "-- Select Zone --"
            if user and not (user.username in ['CEO', 'Fleet_Manager', 'Manager_Admin'] or (hasattr(user, 'profile') and user.profile.role in ['CEO', 'Manager', 'GM', 'PS'])):
                if hasattr(user, 'profile') and user.profile.zone:
                    self.fields['zone'].queryset = Zone.objects.filter(id=user.profile.zone.id)
                    self.initial['zone'] = user.profile.zone.id
                else:
                    self.fields['zone'].queryset = Zone.objects.none()


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
                    "class": "form-control driver-mobile-input",
                    "maxlength": "11",
                    "inputmode": "numeric",
                    "placeholder": "e.g. 03001234567"
                }
            ),

            "cnic": forms.TextInput(
                attrs={
                    "class": "form-control driver-cnic-input",
                    "maxlength": "15",
                    "inputmode": "numeric",
                    "placeholder": "e.g. 17301-1234567-1"
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
        self.fields['vehicle'].label_from_instance = lambda obj: f"{obj.vehicle_name} ({obj.vehicle_id_number})" if obj.vehicle_id_number else obj.vehicle_name
        self.fields['cnic'].label = "CNIC"
        
        if user and not (user.username in ['CEO', 'Fleet_Manager', 'Manager_Admin'] or (hasattr(user, 'profile') and user.profile.role in ['CEO', 'Manager', 'GM', 'PS'])):
            if hasattr(user, 'profile') and user.profile.zone:
                self.fields['vehicle'].queryset = Vehicle.objects.filter(zone=user.profile.zone)
            else:
                self.fields['vehicle'].queryset = Vehicle.objects.none()


# =========================================================
# LOG BOOK FORM
# =========================================================

class LogBookForm(forms.ModelForm):

    class Meta:
        model = LogBook

        fields = [
            "vehicle",
            "vehicle_name",
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

            "vehicle_name": forms.TextInput(
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
