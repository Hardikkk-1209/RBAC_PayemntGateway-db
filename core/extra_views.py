from datetime import date
from decimal import Decimal, InvalidOperation
from django.contrib import messages
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST
from .views import staff_required
from .models import AuditLog
from operations.models import Admission, AdmissionExtension, Vehicle, Employee, FuelRecord, MaintenanceRecord, TrainingSession
from customers.models import Customer
from services.models import Service, ServiceRequest

@staff_required
@require_POST
def extend_admission(request, pk):
    admission=get_object_or_404(Admission.objects.select_for_update(),pk=pk)
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
    new_expiry=previous+timezone.timedelta(days=days)
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
                refill_date=timezone.make_aware(timezone.datetime.fromisoformat(request.POST["refill_date"])),
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
