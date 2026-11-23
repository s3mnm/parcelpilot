# ParcelPilot
Apartment Parcel Management and Tracking System

A responsive academic MVP for apartment parcel intake, resident tracking, and secure collection verification.

## Features
- Admin, guard, and resident demo roles
- Guard parcel registration and unique parcel IDs
- Resident-specific parcel dashboard
- Six-digit OTP with 10-minute expiry and single-use verification
- Parcel event history, overdue highlighting, disputes, dashboard metrics
- FastAPI + SQLAlchemy + SQLite; responsive HTML/CSS/JavaScript frontend

## Run
Python 3.10+ required.

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```
Open http://127.0.0.1:8000. API docs: http://127.0.0.1:8000/docs

## Demo accounts
Password for all: `parcel123`
- Admin: admin@parcelpilot.local
- Guard: guard@parcelpilot.local
- Resident: resident@parcelpilot.local (flat A-204)

## Demo flow
Sign in as Guard, register a parcel for A-204, sign in as Resident and generate its OTP, then sign in as Guard and verify the OTP.

## Academic MVP limitations
Demo authentication is intentionally lightweight and intended only for localhost. Production requires secure server-side sessions/OAuth, HTTPS, rate limiting, managed secrets, email/SMS delivery, PostgreSQL migrations, and security review. QR scanning, image uploads, third-party pickup authorization, and multi-community tenancy are future enhancements.
