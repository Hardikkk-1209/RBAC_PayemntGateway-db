from datetime import date
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from customers.models import Customer
from operations.models import Course,Vehicle,Admission,Employee,TrainingSession,Attendance,Salary
class TrainingRulesTests(TestCase):
    def setUp(self):
        self.user=get_user_model().objects.create_user(username="owner",password="test-pass-123",is_staff=True)
        self.client.force_login(self.user)
        self.customer=Customer.objects.create(full_name="Test Customer",phone="9999999999")
        self.course=Course.objects.create(name="4 Wheeler",category="4w")
        self.vehicle=Vehicle.objects.create(registration_number="TEST-001",vehicle_name="Ertiga",category="4w",fuel_type="cng")
        self.trainer=Employee.objects.create(employee_name="Trainer",phone="9999999998",monthly_salary=15000)
        self.admission=Admission.objects.create(customer=self.customer,course=self.course,vehicle=self.vehicle,
            admission_date=date.today(),original_expiry_date=date.today(),current_expiry_date=date.today(),
            total_sessions=21,custom_fee=6000,status="active")
    def test_admin_dashboard_requires_staff(self):
        self.client.logout()
        self.assertEqual(self.client.get(reverse("dashboard")).status_code,302)
    def test_second_completed_session_same_day_is_rejected(self):
        first=TrainingSession.objects.create(admission=self.admission,session_date=date.today(),start_time="09:00",trainer=self.trainer,vehicle=self.vehicle,status="scheduled")
        self.client.post(reverse("training_complete",args=[first.pk]), {"odometer_after": "0", "start_time": "09:00", "end_time": "09:30"})
        second=TrainingSession.objects.create(admission=self.admission,session_date=date.today(),start_time="11:00",trainer=self.trainer,vehicle=self.vehicle,status="scheduled")
        self.client.post(reverse("training_complete",args=[second.pk]), {"odometer_after": "0", "start_time": "11:00", "end_time": "11:30"})
        self.assertEqual(TrainingSession.objects.filter(admission=self.admission,status="completed").count(),1)
    def test_public_application_page_loads(self):
        self.client.logout()
        self.assertEqual(self.client.get(reverse("apply")).status_code,200)


    def test_actual_training_hours_are_saved_when_completed(self):
        session = TrainingSession.objects.create(
            admission=self.admission, session_date=date.today(),
            start_time="09:00", end_time="09:30",
            trainer=self.trainer, vehicle=self.vehicle, status="scheduled"
        )
        self.client.post(reverse("training_complete", args=[session.pk]), {
            "odometer_after": "1", "start_time": "22:00", "end_time": "22:45"
        })
        session.refresh_from_db()
        self.assertEqual(str(session.start_time), "22:00:00")
        self.assertEqual(str(session.end_time), "22:45:00")
        self.assertEqual(session.recorded_by, self.user)

    def test_employee_attendance_can_be_recorded(self):
        response = self.client.post(reverse("attendance_save"), {
            "employee": str(self.trainer.pk), "date": date.today().isoformat(), "status": "present"
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Attendance.objects.filter(employee=self.trainer, status="present").exists())

    def test_monthly_salary_can_be_prepared(self):
        response = self.client.post(reverse("salary_generate"), {
            "employee": str(self.trainer.pk), "month": date.today().strftime("%Y-%m"),
            "advance": "1000", "deductions": "500", "bonus": "250"
        })
        self.assertEqual(response.status_code, 302)
        salary = Salary.objects.get(employee=self.trainer)
        self.assertEqual(salary.final_payable, 13750)

    def test_missed_session_extends_admission_by_one_day(self):
        session = TrainingSession.objects.create(
            admission=self.admission, session_date=date.today(),
            start_time="09:00", end_time="09:30",
            trainer=self.trainer, vehicle=self.vehicle, status="scheduled"
        )
        old_expiry = self.admission.current_expiry_date
        response = self.client.post(reverse("training_missed", args=[session.pk]))
        self.assertEqual(response.status_code, 302)
        session.refresh_from_db()
        self.admission.refresh_from_db()
        self.assertEqual(session.status, "missed")
        self.assertEqual(self.admission.current_expiry_date, old_expiry + __import__("datetime").timedelta(days=1))
