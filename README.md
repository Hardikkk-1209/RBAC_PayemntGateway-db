# Professional Motor Training School

A clean, admin-first management system for a local motor training school.

## Zero-cost operating target

The first release is designed around free tiers: Render Free for the Django app, Supabase Free for PostgreSQL and private file storage, direct UPI QR with manual admin verification, and admin-triggered WhatsApp/email links. It does not require a paid gateway, paid messaging API, custom domain or paid hosting subscription.

Free tiers have limits and may change. Render Free web services sleep after 15 minutes without traffic, can restart and have an ephemeral local filesystem. Supabase Free currently includes 500 MB database and 1 GB file storage, and a project may pause after a week of low activity. This is suitable for a low-volume pilot, not an always-on service with an SLA. Keep independent backups.

## Stack

- Django 5.2, Django templates, Bootstrap 5 and vanilla JavaScript
- PostgreSQL via Supabase; SQLite for local development
- Supabase S3-compatible private storage for uploaded documents
- English public website and private admin dashboard

## Current modules

- Public home, course/service listing and training application
- Admin login, dashboard, customer, employee, course, vehicle and admission management
- Training scheduling with actual start/end time capture, instructor and vehicle assignment, completion records and one-session-per-customer-per-day enforcement
- Admin-approved admission extensions
- Fuel, vehicle checks and maintenance records
- Payment ledger with manual UPI/cash reconciliation
- Licence/RC service catalogue and requests
- Employee daily attendance, monthly salary preparation and paid-status tracking
- Date-range reports with CSV export

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate --run-syncdb
python manage.py seed_demo
python manage.py createsuperuser
python manage.py runserver
```

Open http://127.0.0.1:8000/ for the public site and /admin-panel/ for the owner dashboard.

## Free deployment

1. Create a Supabase Free project and set its PostgreSQL connection string as `DATABASE_URL`.
2. Create a **private** Storage bucket named `school-private`; enable its S3 protocol and create S3 credentials. Fill in the five `SUPABASE_S3_*` variables.
3. Connect this GitHub repository to Render and create a Free Web Service. Build command: `pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate --run-syncdb`. Start command: `gunicorn config.wsgi:application`.
4. Set `SECRET_KEY`, `DEBUG=False`, `ALLOWED_HOSTS` to the assigned `.onrender.com` host, `CSRF_TRUSTED_ORIGINS` to its HTTPS origin, and the Supabase variables in Render.
5. Run `python manage.py seed_demo` once. Replace placeholder vehicle registration numbers, add real school details and add the owner's QR image.
6. Create the first admin account securely. Do not enable public staff registration.

## Zero-fee payments and notifications

The customer scans the owner's UPI QR and pays directly. The admin verifies the payment in the bank/UPI app, then records it against the correct admission. Automatic payment confirmation is deliberately disabled because payment gateways may charge a platform or transaction fee.

For reminders, the admin can open a pre-filled WhatsApp chat or an email draft and send it manually. WhatsApp Business Platform API notifications and automated email delivery are excluded from the strict ₹0 release because messaging providers have usage limits or charges.

## Free-tier limitations

- Render Free sleeps after 15 idle minutes; the first request after sleep may take about a minute. Its local filesystem is temporary.
- Supabase Free currently includes 500 MB database and 1 GB file storage, and can pause projects after one week of low activity.
- A provider subdomain is free; a custom domain name is not included.
- Free quotas, eligibility and terms can change. Monitor usage and keep independent backups.
- Do not store Aadhaar or other sensitive identity documents until private storage, access controls, retention and backup procedures are reviewed.
- Run `python manage.py check --deploy` and complete acceptance tests before handling real customer data.

This is an initial implementation, not an audited production service. Test payment reconciliation, document access, backup restoration and deployment before go-live.
