from django.db import models
class Payment(models.Model):
    STATUS=[("created","Created"),("pending","Pending"),("success","Success"),("failed","Failed"),("refunded","Refunded")]
    admission=models.ForeignKey("operations.Admission",related_name="payments",null=True,blank=True,on_delete=models.PROTECT)
    customer=models.ForeignKey("customers.Customer",related_name="payments",on_delete=models.PROTECT)
    amount=models.DecimalField(max_digits=10,decimal_places=2)
    payment_method=models.CharField(max_length=20,choices=[("upi_manual","UPI (manual verification)"),("cash","Cash"),("bank_transfer","Bank transfer")],default="upi_manual")
    gateway_order_id=models.CharField(max_length=100,blank=True,db_index=True)
    gateway_payment_id=models.CharField(max_length=100,blank=True,unique=True,null=True)
    status=models.CharField(max_length=12,choices=STATUS,default="created",db_index=True)
    receipt_number=models.CharField(max_length=40,unique=True,blank=True)
    created_at=models.DateTimeField(auto_now_add=True)
    payment_date=models.DateTimeField(null=True,blank=True)
    def __str__(self): return f"{self.customer} · ₹{self.amount} · {self.status}"
class PaymentWebhookEvent(models.Model):
    event_id=models.CharField(max_length=120,unique=True)
    event_type=models.CharField(max_length=100)
    processed=models.BooleanField(default=False)
    payload=models.JSONField(default=dict)
    received_at=models.DateTimeField(auto_now_add=True)
    processed_at=models.DateTimeField(null=True,blank=True)
