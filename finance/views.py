import hashlib,hmac,json,uuid
from decimal import Decimal
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import JsonResponse,HttpResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from customers.models import Customer
from operations.models import Admission
from .models import Payment,PaymentWebhookEvent

def _client():
    if not settings.RAZORPAY_KEY_ID or not settings.RAZORPAY_KEY_SECRET: return None
    import razorpay
    return razorpay.Client(auth=(settings.RAZORPAY_KEY_ID,settings.RAZORPAY_KEY_SECRET))

@login_required
@require_POST
def create_order(request):
    if not request.user.is_staff: return JsonResponse({"error":"Forbidden"},status=403)
    try:
        data=json.loads(request.body or "{}")
        admission=Admission.objects.select_related("customer").get(pk=data["admission_id"])
        amount=Decimal(str(data["amount"]))
        paid=admission.payments.filter(status="success").aggregate(total=__import__("django.db.models",fromlist=["Sum"]).Sum("amount"))["total"] or Decimal("0")
        if amount<=0 or amount>admission.custom_fee-paid: return JsonResponse({"error":"Amount exceeds outstanding balance"},status=400)
        client=_client()
        if not client: return JsonResponse({"error":"Payment gateway is not configured"},status=503)
        order=client.order.create({"amount":int(amount*100),"currency":"INR","receipt":f"adm-{admission.pk}-{uuid.uuid4().hex[:8]}"})
        payment=Payment.objects.create(admission=admission,customer=admission.customer,amount=amount,gateway_order_id=order["id"],status="pending")
        return JsonResponse({"order_id":order["id"],"amount":int(amount*100),"currency":"INR","key":settings.RAZORPAY_KEY_ID,"payment_id":payment.pk})
    except (KeyError,ValueError,Admission.DoesNotExist):
        return JsonResponse({"error":"Invalid payment request"},status=400)

@login_required
@require_POST
def verify_payment(request):
    if not request.user.is_staff: return JsonResponse({"error":"Forbidden"},status=403)
    try:
        data=json.loads(request.body)
        client=_client()
        if not client: return JsonResponse({"error":"Gateway not configured"},status=503)
        client.utility.verify_payment_signature({"razorpay_order_id":data["razorpay_order_id"],"razorpay_payment_id":data["razorpay_payment_id"],"razorpay_signature":data["razorpay_signature"]})
        with transaction.atomic():
            payment=Payment.objects.select_for_update().get(gateway_order_id=data["razorpay_order_id"])
            payment.gateway_payment_id=data["razorpay_payment_id"]; payment.status="success"
            payment.payment_date=timezone.now(); payment.save()
        return JsonResponse({"status":"success"})
    except Exception:
        return JsonResponse({"error":"Payment verification failed"},status=400)

@csrf_exempt
@require_POST
def payment_webhook(request):
    secret=settings.RAZORPAY_WEBHOOK_SECRET
    signature=request.headers.get("X-Razorpay-Signature","")
    expected=hmac.new(secret.encode(),request.body,hashlib.sha256).hexdigest() if secret else ""
    if not secret or not hmac.compare_digest(expected,signature): return HttpResponse(status=400)
    payload=json.loads(request.body); event_id=request.headers.get("X-Razorpay-Event-Id","")
    if not event_id: return HttpResponse(status=400)
    with transaction.atomic():
        event,created=PaymentWebhookEvent.objects.get_or_create(event_id=event_id,defaults={"event_type":payload.get("event",""),"payload":payload})
        if created and payload.get("event") in ("payment.captured","order.paid"):
            entity=payload.get("payload",{}).get("payment",{}).get("entity",{})
            order_id=entity.get("order_id")
            payment=Payment.objects.select_for_update().filter(gateway_order_id=order_id).first()
            if payment:
                payment.status="success"; payment.gateway_payment_id=entity.get("id")
                payment.payment_date=timezone.now(); payment.save()
            event.processed=True; event.processed_at=timezone.now(); event.save()
    return HttpResponse(status=200)
