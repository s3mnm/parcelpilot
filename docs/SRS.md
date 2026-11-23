# Software Requirements Specification — ParcelPilot
Version 1.0 · Academic MVP

## 1. Purpose
ParcelPilot digitizes apartment parcel intake at the security desk, resident visibility, and verified handover.

## 2. Problem
Paper registers are hard to search and do not provide timely resident updates or reliable evidence of handover. A centralized system can track each parcel from receipt to collection.

## 3. Actors
- Administrator: sees dashboard, parcel register, and disputes.
- Security guard: registers deliveries and verifies collection OTPs.
- Resident: sees parcels for their assigned flat, requests OTP, and raises disputes.
- Courier: no account; hands parcel to security.

## 4. Functional requirements
FR-01 Users sign in with demo credentials and receive role-specific access.
FR-02 Guard/admin registers resident name, flat, courier, tracking reference, and notes.
FR-03 Every parcel receives a unique parcel code.
FR-04 Residents can view only parcels assigned to their flat.
FR-05 Parcel status is PENDING or COLLECTED.
FR-06 Assigned resident can request a six-digit OTP for a pending parcel.
FR-07 OTP expires after ten minutes and is stored as a hash.
FR-08 Only guard/admin can verify OTP and complete collection.
FR-09 Successful collection invalidates OTP and cannot be repeated.
FR-10 Dashboard displays total, pending, collected, and open dispute counts.
FR-11 Pending parcels older than three days are highlighted.
FR-12 Residents can raise disputes for parcels assigned to their flat.
FR-13 Intake, OTP issue, and collection are written to parcel event history.

## 5. Non-functional requirements
- Responsive desktop and mobile interface.
- Local API response target below two seconds for a small demo dataset.
- Passwords stored as salted PBKDF2-HMAC-SHA256 hashes.
- Server-side role and flat authorization checks.
- Unique parcel codes and single-use collection state transition.
- SQLite for zero-configuration demo; SQLAlchemy persistence layer.
- Demo data only; no real resident information.

## 6. Business rules
1. Only guard/admin can register incoming parcels.
2. Resident access is restricted to the assigned flat.
3. Only the assigned resident can request an OTP.
4. OTP validity is ten minutes.
5. A parcel can be collected only once.
6. Collection requires a valid, unexpired OTP.
7. A parcel pending for more than three days is overdue.

## 7. Architecture
Presentation: HTML/CSS/JavaScript. Application: FastAPI REST API. Persistence: SQLAlchemy ORM with SQLite. The browser calls JSON endpoints; the API authenticates the demo user, applies role/flat checks, and manages parcel status and OTP lifecycle.

## 8. Main data entities
User(id, name, email, password_hash, role, flat_number)
Parcel(id, code, resident_name, flat, courier, tracking, notes, status, received_at, collected_at, received_by, otp_hash, otp_expires)
Event(id, parcel_id, kind, details, created_at)
Dispute(id, parcel_code, raised_by, issue, description, status, created_at)

## 9. API
GET /api/health · POST /api/login · GET /api/dashboard · GET /api/parcels?email=
POST /api/parcels?email= · POST /api/parcels/{code}/otp?email=
POST /api/parcels/{code}/collect?email= · POST /api/disputes?email= · GET /api/disputes

## 10. Future enhancements
Production OAuth/session management, PostgreSQL migrations, email/SMS notifications, QR scanning, parcel images, authorized pickup, multi-community tenancy, analytics, and deployment automation. The current build is a localhost academic MVP, not a production security system.
