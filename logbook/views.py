from django.db import models
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import (
    get_object_or_404,
    redirect,
    render,
)
from .forms import (
    LogBookForm,
    LogBookEntryForm,
    VehicleForm,
    DriverForm,
)

from .models import (
    LogBook,
    LogBookPage,
    LogBookEntry,
    Vehicle,
    Driver,
)


def is_manager(user):
    return (
        (hasattr(user, 'profile') and user.profile.role == 'Manager')
        or user.username in ['Fleet_Manager', 'Manager_Admin']
    )


def is_admin_or_ceo(user):
    """Returns True if user has global access (CEO, Manager, GM, PS, etc.)"""
    if user.username in ['CEO', 'Fleet_Manager', 'Manager_Admin']:
        return True
    if hasattr(user, 'profile') and user.profile.role in ['CEO', 'Manager', 'GM', 'PS']:
        return True
    return False


def get_user_zone(user):
    """Returns the Zone object for this user, or None."""
    if hasattr(user, 'profile') and user.profile.zone:
        return user.profile.zone
    return None


# =========================================================
# LOG BOOK LIST
# =========================================================

@login_required
def logbook_list(request):

    logbooks = (
        LogBook.objects
        .select_related("vehicle", "vehicle__zone")
        .prefetch_related("entries")
        .order_by("vehicle_name")
    )

    # Zone-based filtering: only show logbooks for vehicles in user's zone
    user_zone = get_user_zone(request.user)
    if not is_admin_or_ceo(request.user) and user_zone:
        logbooks = logbooks.filter(vehicle__zone=user_zone)

    return render(
        request,
        "logbook/logbook_list.html",
        {
            "logbooks": logbooks,
            "is_manager": is_manager(request.user),
        }
    )


# =========================================================
# CREATE LOG BOOK
# =========================================================

@login_required
def create_logbook(request):

    if is_manager(request.user):
        messages.error(
            request,
            "Manager Admin cannot create a Log Book."
        )

        return redirect("logbook_list")

    if request.method == "POST":

        form = LogBookForm(
            request.POST
        )

        if form.is_valid():

            logbook = form.save()

            messages.success(
                request,
                "Log Book created successfully."
            )

            return redirect(
                "logbook_detail",
                logbook_id=logbook.id
            )

    else:

        form = LogBookForm()

    return render(
        request,
        "logbook/create_logbook.html",
        {
            "form": form
        }
    )


# =========================================================
# LOG BOOK DETAIL
# =========================================================

@login_required
def logbook_detail(request, logbook_id):

    logbook = get_object_or_404(
        LogBook.objects.select_related("vehicle"),
        id=logbook_id
    )

    entries = (
        logbook.entries
        .all()
        .order_by(
            "-date",
            "-time_from"
        )
    )

    return render(
        request,
        "logbook/logbook_detail.html",
        {
            "logbook": logbook,
            "entries": entries,
            "is_manager": is_manager(request.user),
        }
    )


# =========================================================
# VEHICLE-SPECIFIC LOG BOOK & PAGES
# =========================================================

import io
import os
import shutil
import time
from PIL import Image, ImageOps
import pypdf
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader


def convert_image_to_a4_pdf(image_file_obj):
    """
    Converts an uploaded image (JPG, PNG, WEBP, etc.) into a PDF page matching standard A4 width (595.27 pt).
    Zero empty margin so the image fills 100% of its page bounds cleanly without white boxes.
    """
    image_file_obj.seek(0)
    img = Image.open(image_file_obj)

    try:
        img = ImageOps.exif_transpose(img)
    except Exception:
        pass

    if img.mode != 'RGB':
        img = img.convert('RGB')

    img_w, img_h = img.size
    target_w = 595.27  # Standard A4 width in points

    # Calculate proportional height matching image aspect ratio
    target_h = target_w * (float(img_h) / float(img_w))

    pdf_buffer = io.BytesIO()
    c = canvas.Canvas(pdf_buffer, pagesize=(target_w, target_h))

    temp_img_buf = io.BytesIO()
    img.save(temp_img_buf, format='JPEG', quality=95)
    temp_img_buf.seek(0)

    img_reader = ImageReader(temp_img_buf)
    c.drawImage(img_reader, 0, 0, width=target_w, height=target_h)
    c.showPage()
    c.save()

    pdf_buffer.seek(0)
    return pdf_buffer


def normalize_entire_pdf_to_a4(target_pdf_path):
    """
    Ensures every page in target_pdf_path has width <= 595.27pt.
    Scales page width proportionally so documents fit standard A4 width cleanly.
    """
    if not target_pdf_path or not os.path.exists(target_pdf_path):
        return False
    try:
        with open(target_pdf_path, "rb") as f:
            pdf_bytes = f.read()

        reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
        writer = pypdf.PdfWriter()

        modified = False
        target_w = 595.27

        for page in reader.pages:
            w = float(page.mediabox.width)
            if w > target_w + 5:
                scale = target_w / w
                page.scale_by(scale)
                modified = True
            writer.add_page(page)

        if modified:
            temp_path = target_pdf_path + ".tmp"
            with open(temp_path, "wb") as f_out:
                writer.write(f_out)

            try:
                os.replace(temp_path, target_pdf_path)
            except Exception:
                shutil.copyfile(temp_path, target_pdf_path)
                if os.path.exists(temp_path):
                    try:
                        os.remove(temp_path)
                    except Exception:
                        pass
        return True
    except Exception as err:
        print(f"Error normalizing PDF: {err}")
        return False


def append_file_to_existing_pdf(target_pdf_path, new_file_obj):
    """
    Prepends new uploaded PDF or Image file pages to target_pdf_path so newest page is on top.
    Normalizes all pages to standard A4 size so PDF viewer maintains 67% optimal zoom.
    """
    if not target_pdf_path or not os.path.exists(target_pdf_path):
        return False

    try:
        writer = pypdf.PdfWriter()
        target_w, target_h = 595.27, 841.89

        # 1. Add new uploaded file pages (newest upload on top)
        file_name = getattr(new_file_obj, 'name', '').lower()

        if file_name.endswith('.pdf'):
            new_file_obj.seek(0)
            new_bytes = io.BytesIO(new_file_obj.read())
            new_reader = pypdf.PdfReader(new_bytes)
            for page in new_reader.pages:
                w = float(page.mediabox.width)
                if w > target_w + 5:
                    scale = target_w / w
                    page.scale_by(scale)
                writer.add_page(page)
        else:
            # Image file (.jpg, .jpeg, .png, .webp) -> convert to standard A4 PDF page
            pdf_bytes_io = convert_image_to_a4_pdf(new_file_obj)
            img_reader = pypdf.PdfReader(pdf_bytes_io)
            for page in img_reader.pages:
                writer.add_page(page)

        # 2. Read existing PDF bytes entirely into memory so disk handle is closed immediately
        with open(target_pdf_path, "rb") as f:
            existing_bytes = f.read()

        existing_reader = pypdf.PdfReader(io.BytesIO(existing_bytes))
        for page in existing_reader.pages:
            w = float(page.mediabox.width)
            if w > target_w + 5:
                scale = target_w / w
                page.scale_by(scale)
            writer.add_page(page)

        # Write to temporary file and replace/copy atomically
        temp_path = target_pdf_path + ".tmp"
        with open(temp_path, "wb") as f_out:
            writer.write(f_out)

        # On Windows, os.replace can fail if target file is locked by a process.
        # Fallback to copyfile + remove to guarantee target update.
        try:
            os.replace(temp_path, target_pdf_path)
        except Exception:
            shutil.copyfile(temp_path, target_pdf_path)
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except Exception:
                    pass

        return True
    except Exception as err:
        print(f"Error prepending to PDF: {err}")
        return False


def remove_pages_from_pdf(target_pdf_path, start_page_1based, end_page_1based):
    """
    Removes pages from start_page_1based to end_page_1based (inclusive, 1-indexed) from target_pdf_path.
    """
    if not target_pdf_path or not os.path.exists(target_pdf_path):
        return False
    try:
        with open(target_pdf_path, "rb") as f:
            existing_bytes = f.read()

        reader = pypdf.PdfReader(io.BytesIO(existing_bytes))
        writer = pypdf.PdfWriter()

        remove_start = start_page_1based - 1
        remove_end = end_page_1based - 1

        for idx, page in enumerate(reader.pages):
            if not (remove_start <= idx <= remove_end):
                writer.add_page(page)

        if len(writer.pages) == 0:
            try:
                os.remove(target_pdf_path)
            except Exception:
                pass
            return True

        temp_path = target_pdf_path + ".tmp"
        with open(temp_path, "wb") as f_out:
            writer.write(f_out)

        try:
            os.replace(temp_path, target_pdf_path)
        except Exception:
            shutil.copyfile(temp_path, target_pdf_path)
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except Exception:
                    pass
        return True
    except Exception as err:
        print(f"Error removing pages from PDF: {err}")
        return False


def get_entry_pdf_page_count(entry):
    if entry and entry.signed_requisition and entry.signed_requisition.name.lower().endswith('.pdf'):
        try:
            reader = pypdf.PdfReader(entry.signed_requisition.path)
            return len(reader.pages)
        except Exception:
            pass
    return 1


def resequence_logbook(logbook):
    """
    Ensures logbook pages are numbered strictly 1, 2, 3... N without missing page numbers.
    """
    pages = list(logbook.pages.all().order_by("page_number", "id"))
    if not pages:
        pages = [LogBookPage.objects.create(logbook=logbook, page_number=i) for i in range(1, 3)]

    for index, p in enumerate(pages, start=1):
        if p.page_number != index:
            p.page_number = index
            p.save(update_fields=["page_number"])


@login_required
def vehicle_logbook(request, vehicle_id):
    if is_admin_or_ceo(request.user):
        vehicle = get_object_or_404(Vehicle, id=vehicle_id)
    else:
        user_zone = get_user_zone(request.user)
        if user_zone:
            vehicle = get_object_or_404(Vehicle, id=vehicle_id, zone=user_zone)
        else:
            from django.http import Http404
            raise Http404("No Vehicle matches the given query.")
    logbook, _ = LogBook.objects.get_or_create(
        vehicle=vehicle,
        defaults={
            'vehicle_name': vehicle.vehicle_name,
        }
    )

    # Automatically create 1 initial page if no pages exist yet
    if logbook.pages.count() == 0:
        LogBookPage.objects.create(logbook=logbook, page_number=1)

    # Clean up any empty pages with 0 entries (excluding Page 1)
    empty_pages = logbook.pages.filter(entries__isnull=True).exclude(page_number=1)
    if empty_pages.exists():
        empty_pages.delete()

    # Attach any unassigned entries to Page 1
    first_page = logbook.pages.filter(page_number=1).first()
    if not first_page:
        first_page = LogBookPage.objects.create(logbook=logbook, page_number=1)

    logbook.entries.filter(page__isnull=True).update(page=first_page)

    # Resequence page numbers to 1, 2, 3... N without gaps
    resequence_logbook(logbook)

    pages = list(logbook.pages.all().prefetch_related("entries").order_by("page_number"))
    
    current_page_counter = 1
    total_entries_in_logbook = sum(p.entries.count() for p in pages)

    main_pdf_entry = logbook.entries.filter(signed_requisition__isnull=False).exclude(signed_requisition='').first()
    if main_pdf_entry and main_pdf_entry.signed_requisition and os.path.exists(main_pdf_entry.signed_requisition.path):
        normalize_entire_pdf_to_a4(main_pdf_entry.signed_requisition.path)

    total_pdf_pages = get_entry_pdf_page_count(main_pdf_entry) if main_pdf_entry else 0

    # Auto-adjust initial page 1 pdf_page_count if initial upload had multiple pages
    if len(pages) == 1 and total_pdf_pages > 1 and pages[0].pdf_page_count <= 1:
        pages[0].pdf_page_count = total_pdf_pages
        LogBookPage.objects.filter(id=pages[0].id).update(pdf_page_count=total_pdf_pages)

    for p in pages:
        p.start_pdf_page = current_page_counter
        pdf_pages = p.pdf_page_count if p.pdf_page_count and p.pdf_page_count > 0 else 1
        p.pdf_pages_count = pdf_pages
        p.end_pdf_page = current_page_counter + pdf_pages - 1
        current_page_counter = p.end_pdf_page + 1

    if total_entries_in_logbook == 0:
        total_pages_count = 1
        next_page_num = 1
        has_entries = False
    else:
        total_pages_count = current_page_counter - 1
        next_page_num = current_page_counter
        has_entries = True

    target_page = request.GET.get('page')

    # Calculate PDF timestamp for cache busting
    pdf_timestamp = int(time.time())
    if main_pdf_entry and main_pdf_entry.signed_requisition and os.path.exists(main_pdf_entry.signed_requisition.path):
        try:
            pdf_timestamp = int(os.path.getmtime(main_pdf_entry.signed_requisition.path))
        except Exception:
            pdf_timestamp = int(time.time())

    # Display newest page at the top, oldest (Page 1) at the bottom
    pages.reverse()

    return render(
        request,
        "logbook/vehicle_logbook.html",
        {
            "vehicle": vehicle,
            "logbook": logbook,
            "pages": pages,
            "total_pages_count": total_pages_count,
            "next_page_num": next_page_num,
            "has_entries": has_entries,
            "total_entries_in_logbook": total_entries_in_logbook,
            "target_page": target_page,
            "main_pdf_entry": main_pdf_entry,
            "total_pdf_pages": total_pdf_pages,
            "pdf_timestamp": pdf_timestamp,
            "is_manager": is_manager(request.user),
        }
    )


@login_required
def add_logbook_page(request, vehicle_id):
    if is_manager(request.user):
        messages.error(request, "Manager Admin cannot add Log Book pages.")
        return redirect("vehicle_logbook", vehicle_id=vehicle_id)

    vehicle = get_object_or_404(Vehicle, id=vehicle_id)
    logbook, _ = LogBook.objects.get_or_create(
        vehicle=vehicle,
        defaults={
            'vehicle_number': vehicle.vehicle_number,
            'opening_meter_reading': vehicle.current_meter_reading
        }
    )
    empty_page = logbook.pages.filter(entries__isnull=True).first()
    if empty_page:
        target_page = empty_page
    else:
        next_num = (logbook.pages.aggregate(models.Max('page_number'))['page_number__max'] or 0) + 1
        target_page = LogBookPage.objects.create(logbook=logbook, page_number=next_num)

    return redirect("add_page_entry", page_id=target_page.id)


@login_required
def delete_logbook_page(request, page_id):
    if is_manager(request.user):
        messages.error(request, "Manager Admin cannot delete Log Book pages.")
        return redirect("vehicle_list")

    page = get_object_or_404(
        LogBookPage.objects.select_related("logbook__vehicle"),
        id=page_id
    )
    logbook = page.logbook
    vehicle_id = logbook.vehicle.id
    page_num = page.page_number

    # Remove corresponding PDF pages from physical PDF document on disk
    main_pdf_entry = logbook.entries.filter(signed_requisition__isnull=False).exclude(signed_requisition='').first()
    if main_pdf_entry and main_pdf_entry.signed_requisition and os.path.exists(main_pdf_entry.signed_requisition.path):
        pdf_path = main_pdf_entry.signed_requisition.path
        pages_desc = list(logbook.pages.all().order_by("-page_number"))
        curr_pdf_page = 1
        target_start = None
        target_end = None

        for p in pages_desc:
            cnt = p.pdf_page_count if p.pdf_page_count and p.pdf_page_count > 0 else 1
            if p.id == page.id:
                target_start = curr_pdf_page
                target_end = curr_pdf_page + cnt - 1
                break
            curr_pdf_page += cnt

        if target_start and target_end:
            remove_pages_from_pdf(pdf_path, target_start, target_end)

    page.delete()
    resequence_logbook(logbook)

    messages.success(request, f"Page {page_num} deleted successfully.")
    return redirect("vehicle_logbook", vehicle_id=vehicle_id)


@login_required
def logbook_page_detail(request, page_id):
    page = get_object_or_404(
        LogBookPage.objects.select_related("logbook__vehicle"),
        id=page_id
    )
    return redirect(f"/logbook/vehicles/{page.logbook.vehicle.id}/logbook/?page={page.page_number}")


@login_required
def add_page_entry(request, page_id):
    page = get_object_or_404(
        LogBookPage.objects.select_related("logbook__vehicle"),
        id=page_id
    )
    logbook = page.logbook
    vehicle = logbook.vehicle

    if is_manager(request.user):
        messages.error(request, "Manager Admin can only view Log Book records.")
        return redirect(f"/logbook/vehicles/{vehicle.id}/logbook/?page={page.page_number}")

    # Calculate target starting document page number for this page
    pages_before = logbook.pages.filter(page_number__lt=page.page_number).order_by("page_number")
    start_doc_page = 1 + sum((p.pdf_page_count if p.pdf_page_count > 0 else 1) for p in pages_before)
    total_entries_in_logbook = logbook.entries.count()

    if total_entries_in_logbook == 0 and page.page_number == 1:
        is_first_entry = True
        target_page_title = "Add Entry"
        target_page_num = 1
    else:
        is_first_entry = False
        target_page_num = start_doc_page
        target_page_title = f"Add Page {target_page_num}"

    if request.method == "POST":
        form = LogBookEntryForm(request.POST, request.FILES)
        if form.is_valid():
            entry = form.save(commit=False)
            entry.logbook = logbook
            entry.page = page
            entry.created_by = request.user

            existing_pdf_entry = logbook.entries.filter(signed_requisition__isnull=False).exclude(signed_requisition='').first()

            uploaded_file = request.FILES.get('signed_requisition')
            if uploaded_file:
                # Count uploaded pages
                new_file_pages = 1
                fname = getattr(uploaded_file, 'name', '').lower()
                if fname.endswith('.pdf'):
                    try:
                        uploaded_file.seek(0)
                        pdf_bytes = io.BytesIO(uploaded_file.read())
                        uploaded_file.seek(0)
                        rdr = pypdf.PdfReader(pdf_bytes)
                        new_file_pages = len(rdr.pages)
                    except Exception:
                        new_file_pages = 1

                page.pdf_page_count = new_file_pages
                page.save(update_fields=['pdf_page_count'])

                if existing_pdf_entry and existing_pdf_entry.signed_requisition and os.path.exists(existing_pdf_entry.signed_requisition.path):
                    target_path = existing_pdf_entry.signed_requisition.path
                    success = append_file_to_existing_pdf(target_path, uploaded_file)
                    if success:
                        entry.signed_requisition = existing_pdf_entry.signed_requisition
                    else:
                        entry.signed_requisition = uploaded_file
                else:
                    fname = getattr(uploaded_file, 'name', '').lower()
                    if not fname.endswith('.pdf'):
                        pdf_io = convert_image_to_a4_pdf(uploaded_file)
                        base_name = os.path.splitext(os.path.basename(getattr(uploaded_file, 'name', 'logbook_page.jpg')))[0]
                        from django.core.files.base import ContentFile
                        entry.signed_requisition.save(f"{base_name}_a4.pdf", ContentFile(pdf_io.read()), save=False)
                    else:
                        entry.signed_requisition = uploaded_file
            else:
                if existing_pdf_entry:
                    entry.signed_requisition = existing_pdf_entry.signed_requisition

            entry.save()

            if entry.signed_requisition:
                logbook.entries.all().update(signed_requisition=entry.signed_requisition)

            if entry.meter_reading_to and entry.meter_reading_to > vehicle.meter_reading:
                vehicle.meter_reading = entry.meter_reading_to
                vehicle.save(update_fields=['meter_reading'])

            msg_txt = "Entry added" if is_first_entry else f"Page {target_page_num} added"
            messages.success(request, f"{msg_txt} for Vehicle {vehicle.vehicle_name}!")
            return redirect(f"/logbook/vehicles/{vehicle.id}/logbook/?page={page.page_number}")
    else:
        last_entry = page.entries.order_by("-id").first() or logbook.entries.order_by("-id").first()
        initial = {}
        if last_entry:
            initial["meter_reading_from"] = last_entry.meter_reading_to
            initial["driver_name"] = last_entry.driver_name
        else:
            initial["meter_reading_from"] = logbook.opening_meter_reading
            driver = vehicle.drivers.filter(is_active=True).first()
            if driver:
                initial["driver_name"] = driver.name

        initial["officer_name"] = request.user.get_full_name() or request.user.username
        form = LogBookEntryForm(initial=initial)

    return render(
        request,
        "logbook/entry_form.html",
        {
            "form": form,
            "page": page,
            "logbook": logbook,
            "vehicle": vehicle,
            "target_page_num": target_page_num,
            "target_page_title": target_page_title,
            "is_first_entry": is_first_entry,
        }
    )


@login_required
def print_all_logbook_pages(request, vehicle_id):
    vehicle = get_object_or_404(Vehicle, id=vehicle_id)
    logbook = get_object_or_404(LogBook, vehicle=vehicle)
    pages = logbook.pages.all().prefetch_related("entries").order_by("page_number")

    return render(
        request,
        "logbook/print_all_pages.html",
        {
            "vehicle": vehicle,
            "logbook": logbook,
            "pages": pages,
        }
    )


# =========================================================
# ADD LOG BOOK ENTRY
# =========================================================

@login_required
def add_logbook_entry(request, logbook_id):

    if is_manager(request.user):

        messages.error(
            request,
            "Manager Admin can only view Log Book records."
        )

        return redirect(
            "logbook_detail",
            logbook_id=logbook_id
        )

    logbook = get_object_or_404(
        LogBook,
        id=logbook_id
    )

    if request.method == "POST":

        form = LogBookEntryForm(
            request.POST,
            request.FILES
        )

        if form.is_valid():

            entry = form.save(
                commit=False
            )

            entry.logbook = logbook
            entry.created_by = request.user

            entry.save()

            messages.success(
                request,
                "Log Book entry saved successfully."
            )

            return redirect(
                "logbook_detail",
                logbook_id=logbook.id
            )

    else:

        last_entry = (
            logbook.entries
            .order_by("-id")
            .first()
        )

        initial = {}

        # Previous meter reading
        if last_entry:

            initial[
                "meter_reading_from"
            ] = last_entry.meter_reading_to

            initial[
                "driver_name"
            ] = last_entry.driver_name

        # First entry
        else:

            initial[
                "meter_reading_from"
            ] = logbook.opening_meter_reading

            if logbook.vehicle:

                initial[
                    "meter_reading_from"
                ] = (
                    logbook
                    .vehicle
                    .current_meter_reading
                )

                driver = (
                    logbook
                    .vehicle
                    .drivers
                    .filter(
                        is_active=True
                    )
                    .first()
                )

                if driver:

                    initial[
                        "driver_name"
                    ] = driver.name

        # Logged-in user as officer
        initial[
            "officer_name"
        ] = (
            request.user.get_full_name()
            or request.user.username
        )

        form = LogBookEntryForm(
            initial=initial
        )

    return render(
        request,
        "logbook/entry_form.html",
        {
            "form": form,
            "logbook": logbook,
        }
    )


# =========================================================
# GENERIC CRUD HELPER FOR MANAGER CHECK
# =========================================================

def manager_error_redirect(request, redirect_name):
    if is_manager(request.user):
        messages.error(request, "Managers are not allowed to modify these records.")
        return redirect(redirect_name)
    return None


# =========================================================
# VEHICLES
# =========================================================

@login_required
def vehicle_list(request):
    from django.db.models import Exists, OuterRef
    has_pdf_subquery = LogBookEntry.objects.filter(
        logbook__vehicle=OuterRef('pk'),
        signed_requisition__isnull=False
    ).exclude(signed_requisition='')

    base_qs = Vehicle.objects.select_related('driver', 'zone').annotate(
        has_logbook_pdf=Exists(has_pdf_subquery)
    ).order_by('vehicle_name')

    if is_admin_or_ceo(request.user):
        vehicles = base_qs
    else:
        user_zone = get_user_zone(request.user)
        if user_zone:
            vehicles = base_qs.filter(zone=user_zone)
        else:
            vehicles = Vehicle.objects.none()

    return render(request, "logbook/vehicle_list.html", {
        "vehicles": vehicles,
        "is_manager": is_manager(request.user),
    })

@login_required
def vehicle_create(request):
    if error := manager_error_redirect(request, 'vehicle_list'): return error
    if request.method == "POST":
        form = VehicleForm(request.POST, user=request.user)
        if form.is_valid():
            vehicle = form.save(commit=False)
            vehicle.save()
            form.save_m2m()
            if vehicle.driver:
                vehicle.driver.vehicle = vehicle
                vehicle.driver.save(update_fields=['vehicle'])
            messages.success(request, "Vehicle created successfully.")
            return redirect('vehicle_list')
    else:
        form = VehicleForm(user=request.user)
    return render(request, "logbook/generic_form.html", {"form": form, "title": "Create Vehicle", "back_url": "vehicle_list"})

@login_required
def vehicle_edit(request, pk):
    if error := manager_error_redirect(request, 'vehicle_list'): return error
    if is_admin_or_ceo(request.user):
        vehicle = get_object_or_404(Vehicle, pk=pk)
    else:
        user_zone = get_user_zone(request.user)
        if user_zone:
            vehicle = get_object_or_404(Vehicle, pk=pk, zone=user_zone)
        else:
            return redirect('vehicle_list')

    if request.method == "POST":
        form = VehicleForm(request.POST, instance=vehicle, user=request.user)
        if form.is_valid():
            vehicle = form.save()
            if vehicle.driver:
                vehicle.driver.vehicle = vehicle
                vehicle.driver.save(update_fields=['vehicle'])
            messages.success(request, "Vehicle updated successfully.")
            return redirect('vehicle_list')
    else:
        form = VehicleForm(instance=vehicle, user=request.user)
    return render(request, "logbook/generic_form.html", {"form": form, "title": f"Edit Vehicle {vehicle.vehicle_name}", "back_url": "vehicle_list"})

@login_required
def vehicle_delete(request, pk):
    if error := manager_error_redirect(request, 'vehicle_list'): return error
    if is_admin_or_ceo(request.user):
        vehicle = get_object_or_404(Vehicle, pk=pk)
    else:
        user_zone = get_user_zone(request.user)
        if user_zone:
            vehicle = get_object_or_404(Vehicle, pk=pk, zone=user_zone)
        else:
            return redirect('vehicle_list')

    if request.method == "POST":
        vehicle.delete()
        messages.success(request, "Vehicle deleted successfully.")
        return redirect('vehicle_list')
    return render(request, "logbook/generic_confirm_delete.html", {"object": vehicle, "back_url": "vehicle_list"})


# =========================================================
# DRIVERS
# =========================================================

@login_required
def driver_list(request):
    if is_admin_or_ceo(request.user):
        drivers = Driver.objects.select_related('vehicle', 'vehicle__zone').all().order_by('name')
    else:
        user_zone = get_user_zone(request.user)
        if user_zone:
            drivers = Driver.objects.select_related('vehicle', 'vehicle__zone').filter(
                vehicle__zone=user_zone
            ).distinct().order_by('name')
        else:
            drivers = Driver.objects.none()

    return render(request, "logbook/driver_list.html", {
        "drivers": drivers,
        "is_manager": is_manager(request.user),
    })

@login_required
def driver_create(request):
    if error := manager_error_redirect(request, 'driver_list'): return error
    if request.method == "POST":
        form = DriverForm(request.POST, user=request.user)
        if form.is_valid():
            driver = form.save(commit=False)
            driver.save()
            messages.success(request, "Driver created successfully.")
            return redirect('driver_list')
    else:
        form = DriverForm(user=request.user)
    return render(request, "logbook/generic_form.html", {"form": form, "title": "Create Driver", "back_url": "driver_list"})

@login_required
def driver_edit(request, pk):
    if error := manager_error_redirect(request, 'driver_list'): return error
    if is_admin_or_ceo(request.user):
        driver = get_object_or_404(Driver, pk=pk)
    else:
        user_zone = get_user_zone(request.user)
        if user_zone:
            driver = get_object_or_404(Driver, pk=pk, vehicle__zone=user_zone)
        else:
            return redirect('driver_list')

    if request.method == "POST":
        form = DriverForm(request.POST, instance=driver, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Driver updated successfully.")
            return redirect('driver_list')
    else:
        form = DriverForm(instance=driver, user=request.user)
    return render(request, "logbook/generic_form.html", {"form": form, "title": f"Edit Driver {driver.name}", "back_url": "driver_list"})

@login_required
def driver_delete(request, pk):
    if error := manager_error_redirect(request, 'driver_list'): return error
    if is_admin_or_ceo(request.user):
        driver = get_object_or_404(Driver, pk=pk)
    else:
        user_zone = get_user_zone(request.user)
        if user_zone:
            driver = get_object_or_404(Driver, pk=pk, vehicle__zone=user_zone)
        else:
            return redirect('driver_list')

    if request.method == "POST":
        driver.delete()
        messages.success(request, "Driver deleted successfully.")
        return redirect('driver_list')
    return render(request, "logbook/generic_confirm_delete.html", {"object": driver, "back_url": "driver_list"})


