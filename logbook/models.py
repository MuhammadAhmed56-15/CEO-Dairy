from django.db import models
from django.contrib.auth.models import User
from core.models import VehicleRequisition


# =========================================================
# VEHICLE
# =========================================================

class Vehicle(models.Model):
    STATUS_CHOICES = (
        ("Active", "Active"),
        ("Maintenance", "Maintenance"),
        ("Inactive", "Inactive"),
    )

    vehicle_number = models.CharField(
        max_length=50,
        unique=True
    )

    registration_number = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    zone = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    vehicle_type = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    current_meter_reading = models.PositiveIntegerField(
        default=0
    )

    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default="Active"
    )

    driver = models.ForeignKey(
        'Driver',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_vehicles"
    )

    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_vehicles"
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        ordering = ["vehicle_number"]
        verbose_name = "Vehicle"
        verbose_name_plural = "Vehicles"

    def __str__(self):
        return self.vehicle_number


# =========================================================
# DRIVER
# =========================================================

class Driver(models.Model):

    name = models.CharField(
        max_length=150
    )

    mobile = models.CharField(
        max_length=30,
        blank=True,
        null=True
    )

    cnic = models.CharField(
        max_length=30,
        blank=True,
        null=True
    )

    vehicle = models.ForeignKey(
        Vehicle,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="drivers"
    )

    is_active = models.BooleanField(
        default=True
    )

    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_drivers"
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return self.name


# =========================================================
# LOG BOOK
# =========================================================

class LogBook(models.Model):

    vehicle = models.OneToOneField(
        Vehicle,
        on_delete=models.CASCADE,
        related_name="logbook",
        null=True,
        blank=True
    )

    vehicle_number = models.CharField(
        max_length=50
    )

    serial_number = models.CharField(
        max_length=50,
        blank=True,
        null=True
    )

    average_to_litre = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        help_text="Average KM per litre"
    )

    opening_meter_reading = models.PositiveIntegerField(
        default=0
    )

    from django.utils import timezone
    opened_on = models.DateField(
        default=timezone.now
    )

    is_active = models.BooleanField(
        default=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        ordering = ["vehicle_number"]
        verbose_name = "Log Book"
        verbose_name_plural = "Log Books"

    def __str__(self):
        return f"{self.vehicle_number} - Log Book"


# =========================================================
# LOG BOOK PAGE
# =========================================================

class LogBookPage(models.Model):
    logbook = models.ForeignKey(
        LogBook,
        on_delete=models.CASCADE,
        related_name="pages"
    )

    page_number = models.PositiveIntegerField()

    pdf_page_count = models.PositiveIntegerField(
        default=1
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        ordering = ["page_number"]
        unique_together = ("logbook", "page_number")
        verbose_name = "Log Book Page"
        verbose_name_plural = "Log Book Pages"

    def __str__(self):
        return f"Page {self.page_number}"


# =========================================================
# LOG BOOK ENTRY
# =========================================================

class LogBookEntry(models.Model):

    logbook = models.ForeignKey(
        LogBook,
        on_delete=models.CASCADE,
        related_name="entries"
    )

    page = models.ForeignKey(
        LogBookPage,
        on_delete=models.CASCADE,
        related_name="entries",
        null=True,
        blank=True
    )

    requisition = models.ForeignKey(
        VehicleRequisition,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="logbook_entries"
    )

    signed_requisition = models.FileField(
        upload_to="signed_requisitions/",
        null=True,
        blank=True,
        verbose_name="Upload Document / File (PDF / Image)"
    )

    RECORD_TYPE_CHOICES = (
        ("Journey", "Journey"),
        ("Maintenance", "Maintenance"),
        ("Other", "Other"),
    )

    SERVICE_TYPE_CHOICES = (
        ("Tyre Replacement", "Tyre Replacement"),
        ("Oil Change", "Oil Change"),
        ("Battery Replacement", "Battery Replacement"),
        ("General Service", "General Service"),
        ("Repair", "Repair"),
        ("Inspection", "Inspection"),
        ("Other", "Other"),
    )

    record_type = models.CharField(
        max_length=50,
        choices=RECORD_TYPE_CHOICES,
        default="Journey",
        blank=True,
        null=True
    )

    service_type = models.CharField(
        max_length=100,
        choices=SERVICE_TYPE_CHOICES,
        blank=True,
        null=True
    )

    # -----------------------------
    # JOURNEY INFORMATION
    # -----------------------------

    date = models.DateField(
        null=True,
        blank=True
    )

    time_from = models.TimeField(
        null=True,
        blank=True
    )

    time_to = models.TimeField(
        null=True,
        blank=True
    )

    details_of_journey = models.TextField(
        null=True,
        blank=True
    )

    purpose_of_journey = models.CharField(
        max_length=255,
        null=True,
        blank=True
    )

    # -----------------------------
    # OFFICER / DRIVER
    # -----------------------------

    officer_name = models.CharField(
        max_length=150,
        null=True,
        blank=True
    )

    driver_name = models.CharField(
        max_length=150,
        blank=True,
        null=True
    )

    # -----------------------------
    # METER
    # -----------------------------

    meter_reading_from = models.PositiveIntegerField(
        null=True,
        blank=True
    )

    meter_reading_to = models.PositiveIntegerField(
        null=True,
        blank=True
    )

    km_covered = models.PositiveIntegerField(
        default=0
    )

    # -----------------------------
    # SIGNATURES
    # -----------------------------

    driver_signature = models.TextField(
        blank=True,
        null=True
    )

    fleet_officer_signature = models.TextField(
        blank=True,
        null=True
    )

    # -----------------------------
    # P.O.L
    # -----------------------------

    fuel_type = models.CharField(
        max_length=50,
        blank=True,
        null=True
    )

    pol_drawn = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    # -----------------------------
    # REMARKS
    # -----------------------------

    remarks = models.TextField(
        blank=True,
        null=True
    )

    # -----------------------------
    # CREATED BY
    # -----------------------------

    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="logbook_entries_created"
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        ordering = ["-date", "-time_from"]
        verbose_name = "Log Book Entry"
        verbose_name_plural = "Log Book Entries"

    def save(self, *args, **kwargs):

        # Automatic KM calculation with None safeguards
        if self.meter_reading_to is not None and self.meter_reading_from is not None:
            if self.meter_reading_to >= self.meter_reading_from:
                self.km_covered = (
                    self.meter_reading_to
                    - self.meter_reading_from
                )
            else:
                self.km_covered = 0
        else:
            self.km_covered = 0

        super().save(*args, **kwargs)

        # Update vehicle's current meter if meter_reading_to is provided
        if self.logbook and self.logbook.vehicle and self.meter_reading_to is not None:
            vehicle = self.logbook.vehicle
            if self.meter_reading_to > (vehicle.current_meter_reading or 0):
                vehicle.current_meter_reading = (
                    self.meter_reading_to
                )
                vehicle.save(
                    update_fields=[
                        "current_meter_reading",
                        "updated_at"
                    ]
                )

    def __str__(self):

        return (
            f"{self.logbook.vehicle_number} - "
            f"{self.date}"
        )


