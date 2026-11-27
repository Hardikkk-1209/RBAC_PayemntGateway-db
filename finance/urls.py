from django.urls import path
from . import views
urlpatterns=[
    path("payments/create-order/",views.create_order,name="create_payment_order"),
    path("payments/verify/",views.verify_payment,name="verify_payment"),
    path("payments/webhook/",views.payment_webhook,name="payment_webhook"),
]
