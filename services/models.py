from django.db import models
class Service(models.Model):
    CATEGORY=[("licence","Licence"),("rc","Registration Certificate"),("other","Other")]
    name=models.CharField(max_length=150)
    category=models.CharField(max_length=12,choices=CATEGORY)
    description=models.TextField(blank=True)
    default_fee=models.DecimalField(max_digits=10,decimal_places=2,null=True,blank=True)
    active=models.BooleanField(default=True)
    def __str__(self): return self.name
class ServiceRequest(models.Model):
    STATUS=[("pending","Pending"),("in_progress","In progress"),("completed","Completed"),("rejected","Rejected")]
    customer=models.ForeignKey("customers.Customer",on_delete=models.PROTECT)
    service=models.ForeignKey(Service,on_delete=models.PROTECT)
    application_date=models.DateField()
    assigned_employee=models.ForeignKey("operations.Employee",null=True,blank=True,on_delete=models.SET_NULL)
    custom_fee=models.DecimalField(max_digits=10,decimal_places=2,default=0)
    amount_paid=models.DecimalField(max_digits=10,decimal_places=2,default=0)
    status=models.CharField(max_length=12,choices=STATUS,default="pending")
    documents=models.FileField(upload_to="private/service-documents/",blank=True,null=True)
    remarks=models.TextField(blank=True)
    completed_at=models.DateTimeField(null=True,blank=True)
    created_at=models.DateTimeField(auto_now_add=True)
    def __str__(self): return f"{self.customer} · {self.service}"
