import uuid
from django.conf import settings
from django.db import models
from django.db.models import Q

class Course(models.Model):
    CATEGORY=[("2w","Two Wheeler"),("4w","Four Wheeler")]
    name=models.CharField(max_length=100)
    category=models.CharField(max_length=2,choices=CATEGORY)
    default_sessions=models.PositiveSmallIntegerField(default=21)
    default_validity_days=models.PositiveSmallIntegerField(default=30)
    active=models.BooleanField(default=True)
    def __str__(self): return self.name

class Employee(models.Model):
    ROLE=[("trainer","Trainer"),("office","Office Staff"),("other","Other")]
    id=models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False)
    employee_name=models.CharField(max_length=150)
    phone=models.CharField(max_length=20)
    designation=models.CharField(max_length=20,choices=ROLE,default="trainer")
    joining_date=models.DateField(null=True,blank=True)
    monthly_salary=models.DecimalField(max_digits=10,decimal_places=2,default=0)
    active=models.BooleanField(default=True)
    def __str__(self): return self.employee_name

class Vehicle(models.Model):
    CATEGORY=[("2w","Two Wheeler"),("4w","Four Wheeler")]
    FUEL=[("petrol","Petrol"),("cng","CNG"),("diesel","Diesel"),("electric","Electric")]
    STATUS=[("available","Available"),("in_use","In use"),("maintenance","Maintenance"),("inactive","Inactive")]
    id=models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False)
    registration_number=models.CharField(max_length=20,unique=True)
    vehicle_name=models.CharField(max_length=100)
    category=models.CharField(max_length=2,choices=CATEGORY)
    fuel_type=models.CharField(max_length=10,choices=FUEL)
    insurance_expiry=models.DateField(null=True,blank=True)
    puc_expiry=models.DateField(null=True,blank=True)
    current_odometer=models.DecimalField(max_digits=10,decimal_places=1,default=0)
    status=models.CharField(max_length=16,choices=STATUS,default="available")
    def __str__(self): return f"{self.vehicle_name} · {self.registration_number}"

class Admission(models.Model):
    STATUS=[("pending_payment","Pending payment"),("active","Active"),("completed","Completed"),("expired","Expired"),("cancelled","Cancelled")]
    id=models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False)
    customer=models.ForeignKey("customers.Customer",related_name="admissions",on_delete=models.PROTECT)
    course=models.ForeignKey(Course,on_delete=models.PROTECT)
    vehicle=models.ForeignKey(Vehicle,on_delete=models.PROTECT)
    admission_date=models.DateField()
    original_expiry_date=models.DateField()
    current_expiry_date=models.DateField()
    total_sessions=models.PositiveSmallIntegerField(default=21)
    preferred_training_time=models.TimeField(null=True,blank=True)
    custom_fee=models.DecimalField(max_digits=10,decimal_places=2)
    status=models.CharField(max_length=20,choices=STATUS,default="active",db_index=True)
    remarks=models.TextField(blank=True)
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now=True)
    def __str__(self): return f"{self.customer.full_name} · {self.course.name}"

class AdmissionExtension(models.Model):
    admission=models.ForeignKey(Admission,related_name="extensions",on_delete=models.CASCADE)
    previous_expiry=models.DateField()
    extension_days=models.PositiveSmallIntegerField()
    new_expiry=models.DateField()
    reason=models.TextField()
    approved_by=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.PROTECT)
    approved_at=models.DateTimeField(auto_now_add=True)
    def __str__(self): return f"{self.admission} +{self.extension_days} days"

class TrainingSession(models.Model):
    STATUS=[("scheduled","Scheduled"),("completed","Completed"),("cancelled","Cancelled"),("missed","Missed")]
    id=models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False)
    admission=models.ForeignKey(Admission,related_name="sessions",on_delete=models.PROTECT)
    session_date=models.DateField(db_index=True)
    start_time=models.TimeField()
    end_time=models.TimeField(null=True,blank=True)
    trainer=models.ForeignKey(Employee,null=True,blank=True,on_delete=models.PROTECT)
    vehicle=models.ForeignKey(Vehicle,null=True,blank=True,on_delete=models.PROTECT)
    status=models.CharField(max_length=12,choices=STATUS,default="scheduled")
    odometer_before=models.DecimalField(max_digits=10,decimal_places=1,null=True,blank=True)
    odometer_after=models.DecimalField(max_digits=10,decimal_places=1,null=True,blank=True)
    remarks=models.TextField(blank=True)
    recorded_by=models.ForeignKey(settings.AUTH_USER_MODEL,null=True,blank=True,on_delete=models.SET_NULL)
    created_at=models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering=["session_date","start_time"]
        constraints=[models.UniqueConstraint(fields=["admission","session_date"],condition=Q(status="completed"),name="one_completed_training_per_admission_day")]
    def __str__(self): return f"{self.admission} · {self.session_date}"

class FuelRecord(models.Model):
    vehicle=models.ForeignKey(Vehicle,related_name="fuel_records",on_delete=models.PROTECT)
    fuel_type=models.CharField(max_length=10,choices=Vehicle.FUEL)
    refill_date=models.DateTimeField()
    quantity=models.DecimalField(max_digits=10,decimal_places=2)
    unit=models.CharField(max_length=10,default="litres")
    amount=models.DecimalField(max_digits=10,decimal_places=2)
    odometer=models.DecimalField(max_digits=10,decimal_places=1)
    receipt=models.FileField(upload_to="private/fuel-receipts/",blank=True,null=True)
    remarks=models.TextField(blank=True)
    created_at=models.DateTimeField(auto_now_add=True)
    def __str__(self): return f"{self.vehicle} · {self.amount}"

class VehicleCheck(models.Model):
    vehicle=models.ForeignKey(Vehicle,on_delete=models.PROTECT)
    session=models.OneToOneField(TrainingSession,related_name="vehicle_check",on_delete=models.PROTECT)
    check_date=models.DateTimeField(auto_now_add=True)
    odometer=models.DecimalField(max_digits=10,decimal_places=1)
    fuel_level=models.CharField(max_length=40,blank=True)
    condition=models.CharField(max_length=20,choices=[("normal","Normal"),("attention","Needs attention"),("unsafe","Do not use")],default="normal")
    remarks=models.TextField(blank=True)

class MaintenanceRecord(models.Model):
    vehicle=models.ForeignKey(Vehicle,related_name="maintenance_records",on_delete=models.PROTECT)
    maintenance_date=models.DateField()
    maintenance_type=models.CharField(max_length=100)
    description=models.TextField(blank=True)
    amount=models.DecimalField(max_digits=10,decimal_places=2,default=0)
    odometer=models.DecimalField(max_digits=10,decimal_places=1)
    next_service_date=models.DateField(null=True,blank=True)
    invoice=models.FileField(upload_to="private/maintenance-invoices/",blank=True,null=True)
    def __str__(self): return f"{self.vehicle} · {self.maintenance_type}"

class Attendance(models.Model):
    STATUS=[("present","Present"),("absent","Absent"),("leave","Leave"),("holiday","Holiday")]
    employee=models.ForeignKey(Employee,on_delete=models.PROTECT)
    date=models.DateField()
    status=models.CharField(max_length=10,choices=STATUS)
    remarks=models.CharField(max_length=250,blank=True)
    class Meta:
        constraints=[models.UniqueConstraint(fields=["employee","date"],name="one_attendance_per_employee_day")]

class Salary(models.Model):
    employee=models.ForeignKey(Employee,on_delete=models.PROTECT)
    month=models.DateField(help_text="Use the first day of the salary month.")
    base_salary=models.DecimalField(max_digits=10,decimal_places=2)
    present_days=models.PositiveSmallIntegerField(default=0)
    leave_days=models.PositiveSmallIntegerField(default=0)
    advance=models.DecimalField(max_digits=10,decimal_places=2,default=0)
    deductions=models.DecimalField(max_digits=10,decimal_places=2,default=0)
    bonus=models.DecimalField(max_digits=10,decimal_places=2,default=0)
    final_payable=models.DecimalField(max_digits=10,decimal_places=2)
    status=models.CharField(max_length=12,choices=[("pending","Pending"),("paid","Paid")],default="pending")
    paid_at=models.DateTimeField(null=True,blank=True)
    class Meta:
        constraints=[models.UniqueConstraint(fields=["employee","month"],name="one_salary_per_employee_month")]
