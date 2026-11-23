from datetime import datetime, timedelta
from pathlib import Path
import hashlib, hmac, secrets

from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, String, DateTime, ForeignKey, Text, select, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker, Session

ROOT = Path(__file__).resolve().parent.parent
DB = create_engine(f"sqlite:///{Path(__file__).with_name('parcelpilot.db')}", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=DB, autoflush=False)
class Base(DeclarativeBase): pass
class User(Base):
    __tablename__="users"
    id: Mapped[int]=mapped_column(primary_key=True)
    name: Mapped[str]=mapped_column(String(100))
    email: Mapped[str]=mapped_column(String(160),unique=True,index=True)
    password_hash: Mapped[str]=mapped_column(String(256))
    role: Mapped[str]=mapped_column(String(20))
    flat_number: Mapped[str|None]=mapped_column(String(30),nullable=True)
class Parcel(Base):
    __tablename__="parcels"
    id: Mapped[int]=mapped_column(primary_key=True)
    code: Mapped[str]=mapped_column(String(20),unique=True,index=True)
    resident_name: Mapped[str]=mapped_column(String(100))
    flat: Mapped[str]=mapped_column(String(30),index=True)
    courier: Mapped[str]=mapped_column(String(80))
    tracking: Mapped[str]=mapped_column(String(100),default="")
    notes: Mapped[str]=mapped_column(String(200),default="")
    status: Mapped[str]=mapped_column(String(20),default="PENDING")
    received_at: Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow)
    collected_at: Mapped[datetime|None]=mapped_column(DateTime,nullable=True)
    received_by: Mapped[str]=mapped_column(String(100))
    otp_hash: Mapped[str|None]=mapped_column(String(64),nullable=True)
    otp_expires: Mapped[datetime|None]=mapped_column(DateTime,nullable=True)
    events: Mapped[list["Event"]]=relationship(back_populates="parcel",cascade="all, delete-orphan")
class Event(Base):
    __tablename__="parcel_events"
    id: Mapped[int]=mapped_column(primary_key=True)
    parcel_id: Mapped[int]=mapped_column(ForeignKey("parcels.id"))
    kind: Mapped[str]=mapped_column(String(40))
    details: Mapped[str]=mapped_column(Text,default="")
    created_at: Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow)
    parcel: Mapped[Parcel]=relationship(back_populates="events")
class Dispute(Base):
    __tablename__="disputes"
    id: Mapped[int]=mapped_column(primary_key=True)
    parcel_code: Mapped[str]=mapped_column(String(20))
    raised_by: Mapped[str]=mapped_column(String(160))
    issue: Mapped[str]=mapped_column(String(50))
    description: Mapped[str]=mapped_column(Text)
    status: Mapped[str]=mapped_column(String(20),default="OPEN")
    created_at: Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow)

def pw_hash(p):
    salt=secrets.token_bytes(16); d=hashlib.pbkdf2_hmac("sha256",p.encode(),salt,240000)
    return salt.hex()+":"+d.hex()
def pw_ok(p,s):
    try:
        salt,d=s.split(":"); return hmac.compare_digest(hashlib.pbkdf2_hmac("sha256",p.encode(),bytes.fromhex(salt),240000).hex(),d)
    except Exception: return False
def db_session():
    db=SessionLocal()
    try: yield db
    finally: db.close()
def get_user(db,email): return db.scalar(select(User).where(User.email==email.lower().strip()))
def parcel_json(p):
    return {"id":p.id,"parcel_code":p.code,"resident_name":p.resident_name,"resident_flat":p.flat,"courier":p.courier,"tracking_reference":p.tracking,"description":p.notes,"status":p.status,"received_at":p.received_at.isoformat()+"Z","collected_at":p.collected_at.isoformat()+"Z" if p.collected_at else None,"received_by":p.received_by,"overdue":p.status=="PENDING" and p.received_at<datetime.utcnow()-timedelta(days=3)}
app=FastAPI(title="ParcelPilot API",version="1.0.0")
app.mount("/static",StaticFiles(directory=ROOT/"frontend"),name="static")
class Login(BaseModel): email:str; password:str
class ParcelIn(BaseModel):
    resident_name:str=Field(min_length=2,max_length=100)
    resident_flat:str=Field(min_length=1,max_length=30)
    courier:str=Field(min_length=2,max_length=80)
    tracking_reference:str=""
    description:str=""
class OTPIn(BaseModel): otp:str=Field(min_length=6,max_length=6)
class DisputeIn(BaseModel): parcel_code:str; issue:str; description:str=Field(min_length=5,max_length=1000)
@app.on_event("startup")
def startup():
    Base.metadata.create_all(DB)
    with SessionLocal() as db:
        if not db.scalar(select(User).limit(1)):
            db.add_all([User(name="Aarav Mehta",email="admin@parcelpilot.local",password_hash=pw_hash("parcel123"),role="ADMIN"),User(name="Security Desk",email="guard@parcelpilot.local",password_hash=pw_hash("parcel123"),role="GUARD"),User(name="Priya Sharma",email="resident@parcelpilot.local",password_hash=pw_hash("parcel123"),role="RESIDENT",flat_number="A-204")]); db.commit()
@app.get("/")
def home(): return FileResponse(ROOT/"frontend"/"index.html")
@app.get("/api/health")
def health(): return {"status":"ok","service":"ParcelPilot"}
@app.post("/api/login")
def login(x:Login,db:Session=Depends(db_session)):
    u=get_user(db,x.email)
    if not u or not pw_ok(x.password,u.password_hash): raise HTTPException(401,"Invalid email or password")
    return {"user":{"id":u.id,"name":u.name,"email":u.email,"role":u.role,"flat_number":u.flat_number}}
@app.get("/api/dashboard")
def dashboard(db:Session=Depends(db_session)):
    return {"total":db.scalar(select(func.count(Parcel.id))) or 0,"pending":db.scalar(select(func.count(Parcel.id)).where(Parcel.status=="PENDING")) or 0,"collected":db.scalar(select(func.count(Parcel.id)).where(Parcel.status=="COLLECTED")) or 0,"open_disputes":db.scalar(select(func.count(Dispute.id)).where(Dispute.status=="OPEN")) or 0}
@app.get("/api/parcels")
def list_parcels(email:str,db:Session=Depends(db_session)):
    u=get_user(db,email)
    if not u: raise HTTPException(401,"Please sign in again")
    q=select(Parcel).order_by(Parcel.received_at.desc())
    if u.role=="RESIDENT": q=q.where(Parcel.flat==u.flat_number)
    return [parcel_json(p) for p in db.scalars(q).all()]
@app.post("/api/parcels",status_code=201)
def add_parcel(x:ParcelIn,email:str,db:Session=Depends(db_session)):
    u=get_user(db,email)
    if not u or u.role not in ("GUARD","ADMIN"): raise HTTPException(403,"Only security staff can register parcels")
    p=Parcel(code="PP-"+secrets.token_hex(3).upper(),resident_name=x.resident_name.strip(),flat=x.resident_flat.strip().upper(),courier=x.courier.strip(),tracking=x.tracking_reference,notes=x.description,received_by=u.name)
    p.events.append(Event(kind="RECEIVED",details="Parcel registered by "+u.name)); db.add(p); db.commit(); db.refresh(p)
    return parcel_json(p)
@app.post("/api/parcels/{code}/otp")
def issue_otp(code:str,email:str,db:Session=Depends(db_session)):
    u=get_user(db,email); p=db.scalar(select(Parcel).where(Parcel.code==code))
    if not u or not p: raise HTTPException(404,"Parcel not found")
    if u.role!="RESIDENT" or u.flat_number!=p.flat: raise HTTPException(403,"Only the assigned resident can request an OTP")
    if p.status!="PENDING": raise HTTPException(409,"Parcel already collected")
    otp=f"{secrets.randbelow(1000000):06d}"; p.otp_hash=hashlib.sha256(otp.encode()).hexdigest(); p.otp_expires=datetime.utcnow()+timedelta(minutes=10); p.events.append(Event(kind="OTP_ISSUED",details="Collection OTP issued")); db.commit()
    return {"otp":otp,"expires_in_minutes":10}
@app.post("/api/parcels/{code}/collect")
def collect(code:str,x:OTPIn,email:str,db:Session=Depends(db_session)):
    u=get_user(db,email); p=db.scalar(select(Parcel).where(Parcel.code==code))
    if not u or u.role not in ("GUARD","ADMIN"): raise HTTPException(403,"Only security staff can verify collection")
    if not p: raise HTTPException(404,"Parcel not found")
    if p.status!="PENDING" or not p.otp_hash: raise HTTPException(409,"No active OTP for this parcel")
    if not p.otp_expires or p.otp_expires<datetime.utcnow(): raise HTTPException(410,"OTP expired; ask resident to generate another")
    if not hmac.compare_digest(hashlib.sha256(x.otp.encode()).hexdigest(),p.otp_hash): raise HTTPException(400,"Incorrect OTP")
    p.status="COLLECTED"; p.collected_at=datetime.utcnow(); p.otp_hash=None; p.otp_expires=None; p.events.append(Event(kind="COLLECTED",details="Verified by "+u.name)); db.commit()
    return {"message":"Collection verified","parcel":parcel_json(p)}
@app.post("/api/disputes",status_code=201)
def add_dispute(x:DisputeIn,email:str,db:Session=Depends(db_session)):
    u=get_user(db,email); p=db.scalar(select(Parcel).where(Parcel.code==x.parcel_code))
    if not u or not p: raise HTTPException(404,"User or parcel not found")
    if u.role=="RESIDENT" and u.flat_number!=p.flat: raise HTTPException(403,"You can only dispute a parcel for your flat")
    d=Dispute(parcel_code=p.code,raised_by=u.email,issue=x.issue,description=x.description); db.add(d); db.commit()
    return {"message":"Dispute submitted","id":d.id}
@app.get("/api/disputes")
def disputes(db:Session=Depends(db_session)):
    return [{"id":d.id,"parcel_code":d.parcel_code,"raised_by":d.raised_by,"issue":d.issue,"description":d.description,"status":d.status,"created_at":d.created_at.isoformat()+"Z"} for d in db.scalars(select(Dispute).order_by(Dispute.created_at.desc())).all()]
