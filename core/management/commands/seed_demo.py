from django.core.management.base import BaseCommand
from operations.models import Course,Vehicle
from services.models import Service
class Command(BaseCommand):
    help="Create initial course, vehicle and service catalogue entries."
    def handle(self,*args,**kwargs):
        for name,category in [("2 Wheeler Training","2w"),("4 Wheeler Training","4w")]:
            Course.objects.get_or_create(name=name,defaults={"category":category})
        for name,category,fuel in [("Activa","2w","petrol"),("Ertiga","4w","cng"),("WagonR","4w","cng"),("Swift Dzire","4w","diesel")]:
            Vehicle.objects.get_or_create(registration_number=f"ADD-REG-{name.upper().replace(' ','-')}",
                defaults={"vehicle_name":name,"category":category,"fuel_type":fuel})
        entries=[
            ("New Learner's Licence","licence"),("New Driving Licence","licence"),("Licence Renewal","licence"),
            ("Duplicate Licence","licence"),("Licence Name Change","licence"),("Licence DOB Change","licence"),
            ("Licence Address Change","licence"),("International Driving Permit","licence"),
            ("RC Ownership Transfer","rc"),("Duplicate RC","rc"),("Hypothecation Cancellation","rc"),
            ("RC Address Change","rc"),("Vehicle Re-registration","rc"),("Vehicle Alteration","rc"),
            ("Insurance Assistance","other"),("PUC Assistance","other")]
        for name,category in entries: Service.objects.get_or_create(name=name,defaults={"category":category})
        self.stdout.write(self.style.SUCCESS("Initial catalogue created. Replace placeholder vehicle registrations."))
