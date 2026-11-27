from datetime import date
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from customers.models import Customer
from operations.models import Course,Vehicle,Admission,Employee,TrainingSession
class TrainingRulesTests(TestCase):
    def setUp(self):
        self.user=get_user_model().objects.create_user(username="owner",password="test-pass-123",is_staff=True)
        self.client.force_login(self.user)
        self.customer=Customer.objects.create(full_name="Test Customer",phone="9999999999")
        self.course=Course.objects.create(name="4 Wheeler",category="4w")
        self.vehicle=Vehicle.objects.create(registration_number="TEST-001",vehicle_name="Ertiga",category="4w",fuel_type="cng")
        self.trainer=Employee.objects.create(employee_name="Trainer",phone="9999999998")
        self.admission=Admission.objects.create(customer=self.customer,course=self.course,vehicle=self.vehicle,
            admission_date=date.today(),original_expiry_date=date.today(),current_expiry_date=date.today(),
            total_sessions=21,custom_fee=6000,status="active")
    def test_admin_dashboard_requires_staff(self):
        self.client.logout()
        self.assertEqual(self.client.get(reverse("dashboard")).status_code,302)
    def test_second_completed_session_same_day_is_rejected(self):
        first=TrainingSession.objects.create(admission=self.admission,session_date=date.today(),start_time="09:00",trainer=self.trainer,vehicle=self.vehicle,status="scheduled")
        self.client.post(reverse("training_complete",args=[first.pk]))
        second=TrainingSession.objects.create(admission=self.admission,session_date=date.today(),start_time="11:00",trainer=self.trainer,vehicle=self.vehicle,status="scheduled")
        self.client.post(reverse("training_complete",args=[second.pk]))
        self.assertEqual(TrainingSession.objects.filter(admission=self.admission,status="completed").count(),1)
    def test_public_application_page_loads(self):
        self.client.logout()
        self.assertEqual(self.client.get(reverse("apply")).status_code,200)
