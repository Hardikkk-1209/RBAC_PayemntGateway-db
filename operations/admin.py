from django.contrib import admin
from .models import Course,Employee,Vehicle,Admission,AdmissionExtension,TrainingSession,FuelRecord,VehicleCheck,MaintenanceRecord,Attendance,Salary
for model in [Course,Employee,Vehicle,Admission,AdmissionExtension,TrainingSession,FuelRecord,VehicleCheck,MaintenanceRecord,Attendance,Salary]:
    admin.site.register(model)
