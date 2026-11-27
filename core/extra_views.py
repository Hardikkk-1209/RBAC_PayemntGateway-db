from datetime import timedelta, datetime
from decimal import Decimal, InvalidOperation
from django.contrib import messages
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST
from .views import staff_required
from .models import AuditLog
from operations.models import Admission, AdmissionExtension, Vehicle, Employee, FuelRecord, MaintenanceRecord, TrainingSession, Attendance, Salary
from customers.models import Customer
from services.models import Service, ServiceRequest

@staff_required
@require_POST
def extend_admission(request, pk):
    admission=get_object_or_404(Admission,pk=pk)
    try:
        days=int(request.POST.get("extension_days","0"))
        if days<1 or days>90: raise ValueError
    except ValueError:
        messages.error(request,"Enter an extension between 1 and 90 days.")
        return redirect("admission_detail",pk=pk)
    if admission.sessions.filter(status="completed").count()>=admission.total_sessions:
        messages.error(request,"A completed course cannot be extended.")
        return redirect("admission_detail",pk=pk)
    previous=admission.current_expiry_date
    new_expiry=previous+timedelta(days=days)
    with transaction.atomic():
        AdmissionExtension.objects.create(admission=admission,previous_expiry=previous,
            extension_days=days,new_expiry=new_expiry,reason=request.POST.get("reason","").strip(),
            approved_by=request.user)
        admission.current_expiry_date=new_expiry
        if admission.status=="expired": admission.status="active"
        admission.save(update_fields=["current_expiry_date","status","updated_at"])
        AuditLog.objects.create(actor=request.user,action="extended",model_name="Admission",object_id=str(pk),
            details={"days":days,"old_expiry":str(previous),"new_expiry":str(new_expiry)})
    messages.success(request,f"Admission extended through {new_expiry:%d %b %Y}.")
    return redirect("admission_detail",pk=pk)

@staff_required
def vehicle_create(request):
    if request.method=="POST":
        try:
            Vehicle.objects.create(registration_number=request.POST["registration_number"].strip().upper(),
                vehicle_name=request.POST["vehicle_name"].strip(),category=request.POST["category"],
                fuel_type=request.POST["fuel_type"],current_odometer=Decimal(request.POST.get("current_odometer") or "0"))
            messages.success(request,"Vehicle added.")
            return redirect("vehicle_list")
        except (KeyError,ValueError,InvalidOperation):
            messages.error(request,"Check the vehicle details and try again.")
    return render(request,"admin/vehicle_form.html")

@staff_required
def fuel_create(request):
    if request.method=="POST":
        try:
            vehicle=get_object_or_404(Vehicle,pk=request.POST["vehicle"])
            FuelRecord.objects.create(vehicle=vehicle,fuel_type=vehicle.fuel_type,
                refill_date=timezone.make_aware(datetime.fromisoformat(request.POST["refill_date"])),
                quantity=Decimal(request.POST["quantity"]),unit=request.POST.get("unit","litres"),
                amount=Decimal(request.POST["amount"]),odometer=Decimal(request.POST["odometer"]),
                remarks=request.POST.get("remarks","").strip())
            messages.success(request,"Fuel refill recorded.")
            return redirect("vehicle_list")
        except (KeyError,ValueError,InvalidOperation):
            messages.error(request,"Check the refill details and try again.")
    return render(request,"admin/fuel_form.html",{"vehicles":Vehicle.objects.all()})

@staff_required
def maintenance_create(request):
    if request.method=="POST":
        try:
            MaintenanceRecord.objects.create(vehicle_id=request.POST["vehicle"],
                maintenance_date=request.POST["maintenance_date"],maintenance_type=request.POST["maintenance_type"].strip(),
                description=request.POST.get("description","").strip(),amount=Decimal(request.POST.get("amount") or "0"),
                odometer=Decimal(request.POST["odometer"]),next_service_date=request.POST.get("next_service_date") or None)
            messages.success(request,"Maintenance record saved.")
            return redirect("vehicle_list")
        except (KeyError,ValueError,InvalidOperation):
            messages.error(request,"Check the maintenance details and try again.")
    return render(request,"admin/maintenance_form.html",{"vehicles":Vehicle.objects.all()})

@staff_required
def employee_create(request):
    if request.method=="POST":
        Employee.objects.create(employee_name=request.POST["employee_name"].strip(),
            phone=request.POST["phone"].strip(),designation=request.POST.get("designation","trainer"),
            joining_date=request.POST.get("joining_date") or None,monthly_salary=Decimal(request.POST.get("monthly_salary") or "0"))
        messages.success(request,"Employee added.")
        return redirect("employee_list")
    return render(request,"admin/employee_form.html")

@staff_required
def service_request_create(request):
    if request.method=="POST":
        ServiceRequest.objects.create(customer_id=request.POST["customer"],service_id=request.POST["service"],
            application_date=request.POST.get("application_date") or timezone.localdate(),
            custom_fee=Decimal(request.POST.get("custom_fee") or "0"),
            assigned_employee_id=request.POST.get("assigned_employee") or None,
            remarks=request.POST.get("remarks","").strip())
        messages.success(request,"Service request created.")
        return redirect("service_request_list")
    return render(request,"admin/service_request_form.html",{
        "customers":Customer.objects.all().order_by("full_name"),"services":Service.objects.filter(active=True),
        "employees":Employee.objects.filter(active=True)})

@staff_required
def manual_payment(request):
    from finance.models import Payment
    import uuid
    from django.db.models import Sum
    if request.method == "POST":
        try:
            admission = get_object_or_404(Admission.objects.select_related("customer"), pk=request.POST["admission"])
            amount = Decimal(request.POST["amount"])
            if amount <= 0:
                raise ValueError
            received = admission.payments.filter(status="success").aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
            if amount > admission.custom_fee - received:
                messages.error(request, "Payment exceeds the outstanding balance.")
                return redirect("manual_payment")
            Payment.objects.create(admission=admission, customer=admission.customer,
                amount=amount, payment_method=request.POST.get("payment_method", "upi_manual"),
                status="success", payment_date=timezone.now(),
                receipt_number=f"PMTS-{timezone.now():%Y%m%d}-{uuid.uuid4().hex[:8].upper()}")
            AuditLog.objects.create(actor=request.user, action="payment_recorded",
                model_name="Payment", object_id=str(admission.pk),
                details={"amount": str(amount), "method": request.POST.get("payment_method", "upi_manual")})
            messages.success(request, "Payment recorded as received after manual verification.")
            return redirect("payment_list")
        except (KeyError, ValueError, InvalidOperation):
            messages.error(request, "Check the admission and payment amount.")
    return render(request, "admin/manual_payment.html", {
        "admissions": Admission.objects.filter(status__in=["active", "completed"]).select_related("customer", "course"),
    })

@staff_required
@require_POST
def attendance_save(request):
    employee = get_object_or_404(Employee, pk=request.POST.get("employee"))
    day = request.POST.get("date") or timezone.localdate().isoformat()
    status = request.POST.get("status")
    if status not in dict(Attendance.STATUS):
        messages.error(request, "Choose a valid attendance status.")
    else:
        Attendance.objects.update_or_create(employee=employee, date=day,
            defaults={"status": status, "remarks": request.POST.get("remarks", "").strip()})
        AuditLog.objects.create(actor=request.user, action="attendance_saved",
            model_name="Attendance", object_id=str(employee.pk),
            details={"date": day, "status": status})
        messages.success(request, "Attendance saved.")
    return redirect("/admin-panel/employees/?date=" + day)

@staff_required
def salary_list(request):
    month_raw = request.GET.get("month") or timezone.localdate().strftime("%Y-%m")
    try:
        month = datetime.strptime(month_raw, "%Y-%m").date().replace(day=1)
    except ValueError:
        month = timezone.localdate().replace(day=1)
        month_raw = month.strftime("%Y-%m")
        messages.error(request, "Choose a valid salary month.")
    return render(request, "admin/salaries.html", {
        "salaries": Salary.objects.filter(month=month).select_related("employee").order_by("employee__employee_name"),
        "month": month_raw, "employees": Employee.objects.filter(active=True).order_by("employee_name")
    })

@staff_required
@require_POST
def salary_generate(request):
    try:
        employee = get_object_or_404(Employee, pk=request.POST.get("employee"))
        month = datetime.strptime(request.POST.get("month"), "%Y-%m").date().replace(day=1)
        advance = Decimal(request.POST.get("advance") or "0")
        deductions = Decimal(request.POST.get("deductions") or "0")
        bonus = Decimal(request.POST.get("bonus") or "0")
        if min(advance, deductions, bonus) < 0:
            raise ValueError
        attendance = Attendance.objects.filter(employee=employee, date__year=month.year, date__month=month.month)
        present_days = attendance.filter(status="present").count()
        leave_days = attendance.filter(status="leave").count()
        base = employee.monthly_salary
        payable = base + bonus - advance - deductions
        if payable < 0:
            raise ValueError
        Salary.objects.update_or_create(employee=employee, month=month, defaults={
            "base_salary": base, "present_days": present_days, "leave_days": leave_days,
            "advance": advance, "deductions": deductions, "bonus": bonus,
            "final_payable": payable, "status": "pending", "paid_at": None
        })
        messages.success(request, "Salary prepared.")
    except (ValueError, InvalidOperation, TypeError):
        messages.error(request, "Check the salary month and non-negative amounts.")
    return redirect("/admin-panel/salaries/?month=" + request.POST.get("month", ""))

@staff_required
@require_POST
def salary_mark_paid(request, pk):
    salary = get_object_or_404(Salary, pk=pk)
    if salary.status != "paid":
        salary.status = "paid"
        salary.paid_at = timezone.now()
        salary.save(update_fields=["status", "paid_at"])
        AuditLog.objects.create(actor=request.user, action="salary_paid",
            model_name="Salary", object_id=str(salary.pk),
            details={"amount": str(salary.final_payable), "month": str(salary.month)})
        messages.success(request, "Salary marked as paid.")
    return redirect("/admin-panel/salaries/?month=" + salary.month.strftime("%Y-%m"))
