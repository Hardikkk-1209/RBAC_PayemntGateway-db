# Professional Motor Training School

A clean, admin-first management system for a local motor training school.

## Stack
- Django 5.2, Django templates, Bootstrap 5 and vanilla JavaScript
- PostgreSQL in production (SQLite works locally)
- Razorpay integration is scaffolded and requires test/live credentials
- English public website and private admin dashboard

## Current implementation
- Public home, course/service listing and training application
- Admin login, dashboard, customer, employee, course, vehicle and admission management
- Training session scheduling/completion with 21-session and one-completed-session-per-day enforcement
- Admin-approved admission expiry extensions
- Fuel, vehicle-check and maintenance records
- Payment records, balance calculation and Razorpay order/webhook scaffolding
- Licence/RC service catalogue and service requests
- Employee attendance and salary records

## Run locally
```bash
python -m venv .venv
source .venv/bin/activate # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Open http://127.0.0.1:8000/ for the public site and /admin-panel/ for the owner dashboard.

## Environment
See `.env.example`. Keep secrets out of Git. Set `DEBUG=False`, `SECRET_KEY`, `ALLOWED_HOSTS`, `DATABASE_URL`, Razorpay credentials and email settings before production deployment.

## Production notes
- Configure PostgreSQL and persistent private media storage.
- Set HTTPS and secure cookies.
- Configure the Razorpay webhook URL as `/api/payments/webhook/`, using the same webhook secret in the provider dashboard.
- Run `python manage.py check --deploy` before deployment.
- Configure a scheduled job/worker for reminders before enabling customer messaging.
- Obtain customer consent and approved templates before WhatsApp notifications.

This is a starter production-oriented implementation, not a substitute for sandbox payment testing, deployment configuration, or operational acceptance testing.
