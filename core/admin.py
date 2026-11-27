from django.contrib import admin
from .models import AuditLog, SiteSetting
admin.site.register(AuditLog)
admin.site.register(SiteSetting)
