from django.urls import path
from . import views
urlpatterns = [
    path("login/", views.admin_login, name="admin_login"),
    path("logout/", views.admin_logout, name="admin_logout"),
    path("", views.dashboard, name="dashboard"),
    path("customers/", views.customer_list, name="customer_list"),
    path("customers/new/", views.customer_create, name="customer_create"),
    path("admissions/", views.admission_list, name="admission_list"),
    path("admissions/new/", views.admission_create, name="admission_create"),
    path("admissions/<int:pk>/", views.admission_detail, name="admission_detail"),
    path("applications/", views.application_list, name="application_list"),
    path("applications/<int:pk>/decision/", views.application_decision, name="application_decision"),
    path("training/", views.training_list, name="training_list"),
    path("training/new/", views.training_create, name="training_create"),
    path("training/<int:pk>/complete/", views.training_complete, name="training_complete"),
    path("vehicles/", views.vehicle_list, name="vehicle_list"),
    path("employees/", views.employee_list, name="employee_list"),
    path("payments/", views.payment_list, name="payment_list"),
    path("services/", views.service_request_list, name="service_request_list"),
    path("reports/", views.reports, name="reports"),
]
