import uuid
from django.db import models

class Customer(models.Model):
    id=models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False)
    full_name=models.CharField(max_length=160)
    date_of_birth=models.DateField(null=True,blank=True)
    phone=models.CharField(max_length=20,db_index=True)
    email=models.EmailField(blank=True)
    address=models.TextField(blank=True)
    photograph=models.ImageField(upload_to="customers/photos/",blank=True,null=True)
    identity_document=models.FileField(upload_to="private/customer-documents/",blank=True,null=True)
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now=True)
    class Meta: ordering=["full_name"]
    def __str__(self): return f"{self.full_name} ({self.phone})"

class TrainingApplication(models.Model):
    STATUS=[("pending","Pending"),("approved","Approved"),("rejected","Rejected"),("converted","Converted")]
    full_name=models.CharField(max_length=160)
    date_of_birth=models.DateField(null=True,blank=True)
    phone=models.CharField(max_length=20)
    email=models.EmailField(blank=True)
    address=models.TextField(blank=True)
    course=models.ForeignKey("operations.Course",on_delete=models.PROTECT)
    preferred_vehicle=models.ForeignKey("operations.Vehicle",null=True,blank=True,on_delete=models.SET_NULL)
    preferred_start_date=models.DateField(null=True,blank=True)
    status=models.CharField(max_length=16,choices=STATUS,default="pending",db_index=True)
    admin_remarks=models.TextField(blank=True)
    customer=models.ForeignKey(Customer,null=True,blank=True,on_delete=models.SET_NULL)
    created_at=models.DateTimeField(auto_now_add=True)
    def __str__(self): return f"{self.full_name} - {self.course}"
