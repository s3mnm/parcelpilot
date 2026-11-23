# ParcelPilot Test Cases

## Test setup
Run `cd backend && python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt && uvicorn main:app --reload`. Open http://127.0.0.1:8000.

Demo password: `parcel123`
- admin@parcelpilot.local
- guard@parcelpilot.local
- resident@parcelpilot.local (flat A-204)

| ID | Test | Expected result |
|---|---|---|
| TC-01 | Login with valid guard credentials | Guard dashboard opens |
| TC-02 | Login with incorrect password | API rejects credentials |
| TC-03 | Guard registers parcel | Unique PP code and PENDING status |
| TC-04 | Resident calls parcel registration | API returns 403 |
| TC-05 | Resident views parcel list | Only A-204 parcels are returned |
| TC-06 | Resident requests OTP for own parcel | Six-digit OTP returned, expires in 10 min |
| TC-07 | Guard enters wrong OTP | API rejects; parcel remains pending |
| TC-08 | Guard enters correct OTP | Parcel becomes COLLECTED |
| TC-09 | Reuse OTP after collection | API rejects second collection |
| TC-10 | Submit expired OTP | API returns expired-code error |
| TC-11 | Resident raises dispute for own parcel | Dispute is recorded |
| TC-12 | Resident disputes another flat's parcel | API returns 403 |
| TC-13 | Dashboard after parcel transitions | Counts reflect latest state |
| TC-14 | Open app on narrow viewport | Layout stacks and remains usable |

## Demonstration acceptance
Register a parcel as Guard for A-204, request its OTP as Resident, verify it as Guard, then confirm status and dashboard counts. Test both incorrect and correct OTP paths.
