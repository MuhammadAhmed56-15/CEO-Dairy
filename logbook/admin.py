from django.contrib import admin

from .models import (
    Vehicle,
    Driver,
    LogBook,
    LogBookPage,
    LogBookEntry
)


# =========================================================
# VEHICLE
# =========================================================

@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):

    list_display = (
        "vehicle_number",
        "registration_number",
        "zone",
        "vehicle_type",
        "current_meter_reading",
        "status",
    )

    list_filter = (
        "zone",
        "status",
        "vehicle_type",
    )

    search_fields = (
        "vehicle_number",
        "registration_number",
        "zone",
        "driver_name",
    )


# =========================================================
# DRIVER
# =========================================================

@admin.register(Driver)
class DriverAdmin(admin.ModelAdmin):

    list_display = (
        "name",
        "mobile",
        "cnic",
        "vehicle",
        "is_active",
    )

    list_filter = (
        "is_active",
    )

    search_fields = (
        "name",
        "mobile",
        "cnic",
        "vehicle__vehicle_number",
    )


# =========================================================
# LOG BOOK
# =========================================================

@admin.register(LogBook)
class LogBookAdmin(admin.ModelAdmin):

    list_display = (
        "vehicle_number",
        "serial_number",
        "average_to_litre",
        "opening_meter_reading",
        "is_active",
        "created_at",
    )

    list_filter = (
        "is_active",
    )

    search_fields = (
        "vehicle_number",
        "serial_number",
    )


# =========================================================
# LOG BOOK PAGE
# =========================================================

@admin.register(LogBookPage)
class LogBookPageAdmin(admin.ModelAdmin):

    list_display = (
        "logbook",
        "page_number",
        "created_at",
    )

    list_filter = (
        "logbook",
    )

    search_fields = (
        "logbook__vehicle_number",
        "page_number",
    )


# =========================================================
# LOG BOOK ENTRY
# =========================================================

@admin.register(LogBookEntry)
class LogBookEntryAdmin(admin.ModelAdmin):

    fields = (
        "logbook",
        "page",
        "signed_requisition",
        "date",
    )

    list_display = (
        "logbook",
        "page",
        "signed_requisition",
        "date",
    )

    list_filter = (
        "date",
        "logbook",
    )

    search_fields = (
        "logbook__vehicle_number",
    )





