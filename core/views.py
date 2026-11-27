from datetime import timedelta, date as date_type
from decimal import Decimal
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Sum, Count
from django.db import transaction
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST
from customers.models import Customer, TrainingApplication
from operations.models import Admission, Course, Employee, TrainingSession, Vehicle, FuelRecord, MaintenanceRecord, VehicleCheck, Attendance, Salary
from finance.models import Payment
from services.models import ServiceRequest
from .models import AuditLog

def home(request):
    courses = Course.objects.filter(active=True)
    return render(request, "public/home.html", {"courses": courses, "request_settings_qr": settings.OWNER_QR_IMAGE, "owner_upi_id": settings.OWNER_UPI_ID, "owner_name": settings.OWNER_NAME})

def apply(request):
    if request.method == "POST":
        form = {
            "full_name": request.POST.get("full_name", "").strip(),
            "phone": request.POST.get("phone", "").strip(),
            "email": request.POST.get("email", "").strip(),
            "address": request.POST.get("address", "").strip(),
            "date_of_birth": request.POST.get("date_of_birth") or None,
            "course_id": request.POST.get("course"),
            "vehicle_id": request.POST.get("vehicle"),
            "preferred_start_date": request.POST.get("preferred_start_date") or None,
        }
        if not form["full_name"] or not form["phone"] or not form["course_id"]:
            messages.error(request, "Name, phone and course are required.")
        else:
            TrainingApplication.objects.create(
                full_name=form["full_name"], phone=form["phone"], email=form["email"],
                address=form["address"], date_of_birth=form["date_of_birth"],
                course_id=form["course_id"], preferred_vehicle_id=form["vehicle_id"] or None,
                preferred_start_date=form["preferred_start_date"],
            )
            messages.success(request, "Your application has been submitted for review.")
            return redirect("apply")
    return render(request, "public/apply.html", {
        "courses": Course.objects.filter(active=True), "vehicles": Vehicle.objects.filter(status="available")
    })

def admin_login(request):
    if request.user.is_authenticated and request.user.is_staff:
        return redirect("dashboard")
    if request.method == "POST":
        user = authenticate(request, username=request.POST.get("username"), password=request.POST.get("password"))
        if user and user.is_staff:
            login(request, user)
            return redirect("dashboard")
        messages.error(request, "Invalid admin credentials.")
    return render(request, "admin/login.html")

def admin_logout(request):
    if request.method == "POST":
        logout(request)
    return redirect("home")

def staff_required(view):
    return login_required(user_passes_test(lambda u: u.is_staff)(view))

@staff_required
def dashboard(request):
    today = timezone.localdate()
    context = {
        "active_admissions": Admission.objects.filter(status="active").count(),
        "today_sessions": TrainingSession.objects.filter(session_date=today).count(),
        "pending_applications": TrainingApplication.objects.filter(status="pending").count(),
        "pending_balance": Decimal("0.00"),
        "recent_sessions": TrainingSession.objects.select_related("admission__customer","trainer","vehicle").filter(session_date=today)[:8],
        "expiring_vehicles": Vehicle.objects.filter(status="available").order_by("insurance_expiry")[:5],
    }
    total_fees = Admission.objects.filter(status__in=["active", "completed"]).aggregate(total=Sum("custom_fee"))["total"] or Decimal("0.00")
    received = Payment.objects.filter(status="success").aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
    context["pending_balance"] = max(Decimal("0.00"), total_fees - received)
    return render(request, "admin/dashboard.html", context)

@staff_required
def customer_list(request):
    q=request.GET.get("q","").strip()
    items=Customer.objects.filter(full_name__icontains=q) if q else Customer.objects.all()
    return render(request,"admin/customers.html",{"customers":items.order_by("-created_at")[:200],"q":q})

@staff_required
def customer_create(request):
    if request.method=="POST":
        c=Customer.objects.create(full_name=request.POST.get("full_name","").strip(),
            phone=request.POST.get("phone","").strip(),email=request.POST.get("email","").strip(),
            address=request.POST.get("address","").strip(),date_of_birth=request.POST.get("date_of_birth") or None,
            photograph=request.FILES.get("photograph"))
        messages.success(request,"Customer created.")
        return redirect("admission_create")
    return render(request,"admin/customer_form.html")

@staff_required
def admission_list(request):
    return render(request,"admin/admissions.html",{"admissions":Admission.objects.select_related("customer","course","vehicle").order_by("-admission_date")[:200]})

@staff_required
def admission_create(request):
    if request.method=="POST":
        with transaction.atomic():
            customer_id=request.POST.get("customer")
            if customer_id:
                customer=get_object_or_404(Customer,pk=customer_id)
            else:
                customer=Customer.objects.create(full_name=request.POST.get("full_name","").strip(),
                    phone=request.POST.get("phone","").strip(),email=request.POST.get("email","").strip(),
                    address=request.POST.get("address","").strip(),date_of_birth=request.POST.get("date_of_birth") or None)
            course=get_object_or_404(Course,pk=request.POST.get("course"))
            vehicle=get_object_or_404(Vehicle,pk=request.POST.get("vehicle"))
            if vehicle.category != course.category:
                messages.error(request,"Selected vehicle does not match the course category.")
                return redirect("admission_create")
            start=timezone.localdate()
            days=int(request.POST.get("validity_days") or 30)
            admission=Admission.objects.create(customer=customer,course=course,vehicle=vehicle,
                admission_date=start,original_expiry_date=start+timedelta(days=days),
                current_expiry_date=start+timedelta(days=days),total_sessions=int(request.POST.get("total_sessions") or 21),
                custom_fee=Decimal(request.POST.get("custom_fee") or "0"),
                status="active")
            AuditLog.objects.create(actor=request.user,action="created",model_name="Admission",object_id=str(admission.pk))
        messages.success(request,"Admission created.")
        return redirect("admission_detail",pk=admission.pk)
    return render(request,"admin/admission_form.html",{
        "selected_customer": request.GET.get("customer", ""),
        "customers":Customer.objects.all().order_by("full_name"),"courses":Course.objects.filter(active=True),
        "vehicles":Vehicle.objects.filter(status="available"),"employees":Employee.objects.filter(active=True)
    })

@staff_required
def admission_detail(request,pk):
    admission=get_object_or_404(Admission.objects.select_related("customer","course","vehicle"),pk=pk)
    sessions=admission.sessions.select_related("trainer","vehicle").order_by("session_date")
    payments=admission.payments.all()
    completed=sessions.filter(status="completed").count()
    paid=payments.filter(status="success").aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
    balance=max(Decimal("0.00"),admission.custom_fee-paid)
    return render(request,"admin/admission_detail.html",{"admission":admission,"sessions":sessions,
        "completed":completed,"remaining":max(0,admission.total_sessions-completed),"paid":paid,"balance":balance,
        "whatsapp_phone": ("91" + "".join(ch for ch in admission.customer.phone if ch.isdigit())) if len("".join(ch for ch in admission.customer.phone if ch.isdigit())) == 10 else "".join(ch for ch in admission.customer.phone if ch.isdigit()),
        "whatsapp_message": f"Hello {admission.customer.full_name}, this is a reminder from Professional Motor Training School regarding your driving training. Please contact us for your next session.",
        "trainers":Employee.objects.filter(active=True),"vehicles":Vehicle.objects.all(),
        "extensions":admission.extensions.select_related("approved_by").all()})

@staff_required
def application_list(request):
    return render(request,"admin/applications.html",{"applications":TrainingApplication.objects.select_related("course","preferred_vehicle").order_by("-created_at")[:200]})

@staff_required
@require_POST
def application_decision(request,pk):
    app=get_object_or_404(TrainingApplication,pk=pk)
    decision=request.POST.get("decision")
    if decision=="reject":
        app.status="rejected"; app.admin_remarks=request.POST.get("remarks","")
        app.save()
    elif decision=="approve":
        with transaction.atomic():
            customer=Customer.objects.create(full_name=app.full_name,phone=app.phone,email=app.email,
                address=app.address,date_of_birth=app.date_of_birth)
            app.customer=customer; app.status="approved"
            app.admin_remarks=request.POST.get("remarks",""); app.save()
            messages.success(request,"Application approved. Create an admission and set the custom fee.")
    return redirect("application_list")

@staff_required
def training_list(request):
    date=request.GET.get("date") or timezone.localdate().isoformat()
    items=TrainingSession.objects.select_related("admission__customer","trainer","vehicle").filter(session_date=date).order_by("start_time")
    return render(request,"admin/training.html",{"sessions":items,"selected_date":date})

@staff_required
def training_create(request):
    if request.method=="POST":
        admission=get_object_or_404(Admission,pk=request.POST.get("admission"))
        session_date=request.POST.get("session_date")
        if admission.status!="active" or session_date>str(admission.current_expiry_date):
            messages.error(request,"Admission is not active for this date.")
        elif TrainingSession.objects.filter(admission=admission,session_date=session_date,status__in=["scheduled","completed"]).exists():
            messages.error(request,"This customer already has a training session scheduled for that day.")
        else:
            start_time = request.POST.get("start_time") or "22:00"
            end_time = request.POST.get("end_time") or ""
            if not end_time or end_time <= start_time:
                messages.error(request, "End time must be later than start time.")
                return redirect("training_create")
            TrainingSession.objects.create(admission=admission,session_date=session_date,
                start_time=start_time,end_time=end_time,trainer_id=request.POST.get("trainer"),
                vehicle_id=request.POST.get("vehicle") or admission.vehicle_id,status="scheduled")
            messages.success(request,"Training scheduled.")
        return redirect("training_list")
    return render(request,"admin/training_form.html",{
        "admissions":Admission.objects.filter(status="active").select_related("customer"),
        "employees":Employee.objects.filter(active=True),"vehicles":Vehicle.objects.all()})

@staff_required
@require_POST
def training_complete(request,pk):
    with transaction.atomic():
        session=get_object_or_404(TrainingSession.objects.select_for_update().select_related("admission"),pk=pk)
        admission=Admission.objects.select_for_update().get(pk=session.admission_id)
        completed=TrainingSession.objects.filter(admission=admission,status="completed")
        if session.status!="scheduled":
            messages.error(request,"Only scheduled sessions can be completed.")
        elif session.session_date>timezone.localdate() or session.session_date>admission.current_expiry_date:
            messages.error(request,"Cannot complete a future or expired session.")
        elif admission.status!="active" or completed.count()>=admission.total_sessions:
            messages.error(request,"Admission is inactive or all sessions are completed.")
        elif completed.filter(session_date=session.session_date).exclude(pk=session.pk).exists():
            messages.error(request,"Only one completed session per admission per day.")
        elif not session.trainer_id or not session.vehicle_id:
            messages.error(request,"Assign a trainer and vehicle before completion.")
        elif not request.POST.get("odometer_after"):
            messages.error(request,"Enter the vehicle odometer reading after training.")
        else:
            session.status="completed"; session.recorded_by=request.user
            session.odometer_after=Decimal(request.POST.get("odometer_after"))
            vehicle = Vehicle.objects.select_for_update().get(pk=session.vehicle_id)
            if session.odometer_after < vehicle.current_odometer:
                messages.error(request, "Odometer reading cannot be lower than the vehicle's last recorded reading.")
                return redirect("training_list")
            session.remarks=request.POST.get("remarks",""); session.save()
            vehicle.current_odometer = session.odometer_after
            if request.POST.get("vehicle_condition") == "unsafe":
                vehicle.status = "maintenance"
            vehicle.save(update_fields=["current_odometer", "status"])
            VehicleCheck.objects.create(vehicle=vehicle, session=session, odometer=session.odometer_after,
                fuel_level=request.POST.get("fuel_level",""),
                condition=request.POST.get("vehicle_condition","normal"),
                remarks=request.POST.get("vehicle_remarks",""))
            AuditLog.objects.create(actor=request.user,action="completed",model_name="TrainingSession",object_id=str(session.pk))
            if completed.count()+1>=admission.total_sessions:
                admission.status="completed"; admission.save(update_fields=["status"])
            messages.success(request,"Training session marked completed.")
    return redirect("training_list")

@staff_required
def vehicle_list(request):
    return render(request,"admin/vehicles.html",{"vehicles":Vehicle.objects.all().order_by("registration_number"),
        "fuel_records":FuelRecord.objects.select_related("vehicle").order_by("-refill_date")[:30],
        "maintenance":MaintenanceRecord.objects.select_related("vehicle").order_by("-maintenance_date")[:20]})

@staff_required
def employee_list(request):
    selected_date = request.GET.get("date") or timezone.localdate().isoformat()
    employees = Employee.objects.filter(active=True).order_by("employee_name")
    records = {str(a.employee_id): a.status for a in Attendance.objects.filter(date=selected_date)}
    return render(request, "admin/employees.html", {
        "employees": employees, "attendance_records": records, "selected_date": selected_date
    })

@staff_required
def payment_list(request):
    return render(request,"admin/payments.html",{"payments":Payment.objects.select_related("customer","admission").order_by("-created_at")[:200]})

@staff_required
def service_request_list(request):
    return render(request,"admin/service_requests.html",{"requests":ServiceRequest.objects.select_related("customer","service").order_by("-created_at")[:200]})

@staff_required
def reports(request):
    today = timezone.localdate()
    try:
        start = date_type.fromisoformat(request.GET.get("start") or today.replace(day=1).isoformat())
        end = date_type.fromisoformat(request.GET.get("end") or today.isoformat())
        if end < start:
            raise ValueError
    except ValueError:
        start, end = today.replace(day=1), today
        messages.error(request, "Choose a valid date range.")
    sessions = TrainingSession.objects.filter(session_date__range=(start, end))
    payments = Payment.objects.filter(status="success", payment_date__date__range=(start, end))
    fuel = FuelRecord.objects.filter(refill_date__date__range=(start, end))
    maintenance = MaintenanceRecord.objects.filter(maintenance_date__range=(start, end))
    return render(request, "admin/reports.html", {
        "start_date": start.isoformat(), "end_date": end.isoformat(),
        "total_customers": Customer.objects.count(), "total_admissions": Admission.objects.count(),
        "completed_sessions": sessions.filter(status="completed").count(),
        "scheduled_sessions": sessions.filter(status="scheduled").count(),
        "missed_sessions": sessions.filter(status="missed").count(),
        "total_revenue": payments.aggregate(total=Sum("amount"))["total"] or Decimal("0.00"),
        "fuel_expense": fuel.aggregate(total=Sum("amount"))["total"] or Decimal("0.00"),
        "maintenance_expense": maintenance.aggregate(total=Sum("amount"))["total"] or Decimal("0.00"),
    })
