from django.contrib import admin
from .models import Customer, TrainingApplication
@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display=("full_name","phone","email","created_at")
    search_fields=("full_name","phone","email")
@admin.register(TrainingApplication)
class ApplicationAdmin(admin.ModelAdmin):
    list_display=("full_name","phone","course","status","created_at")
    list_filter=("status","course")
    search_fields=("full_name","phone")
