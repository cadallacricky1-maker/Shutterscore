from fastapi import FastAPI, APIRouter, HTTPException, Query, Depends, Header
from fastapi.responses import StreamingResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
import re
import io
import csv
import secrets
import asyncio
import resend
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import List, Optional
import uuid
from datetime import datetime, timezone, timedelta


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Resend setup
resend.api_key = os.environ.get('RESEND_API_KEY', '')
SENDER_EMAIL = os.environ.get('SENDER_EMAIL', 'onboarding@resend.dev')

# Admin password
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'admin123')

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Security
security = HTTPBasic()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Admin authentication
def verify_admin(credentials: HTTPBasicCredentials = Depends(security)):
    correct_password = secrets.compare_digest(credentials.password, ADMIN_PASSWORD)
    if not correct_password:
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username


# Define Models
class StatusCheck(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class StatusCheckCreate(BaseModel):
    client_name: str


# Waitlist Models with Referral
class WaitlistEntry(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: str
    referral_code: str = Field(default_factory=lambda: str(uuid.uuid4())[:8].upper())
    referred_by: Optional[str] = None
    referral_count: int = 0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class WaitlistCreate(BaseModel):
    email: str
    ref: Optional[str] = None  # Referral code from URL
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, v):
            raise ValueError('Invalid email format')
        return v.lower().strip()

class WaitlistResponse(BaseModel):
    success: bool
    message: str
    entry: Optional[WaitlistEntry] = None
    referral_link: Optional[str] = None


class WaitlistListResponse(BaseModel):
    entries: List[WaitlistEntry]
    total: int
    page: int
    page_size: int
    total_pages: int


class WaitlistStats(BaseModel):
    total_signups: int
    today_signups: int
    this_week_signups: int
    total_referrals: int


class AdminLoginRequest(BaseModel):
    password: str


class AdminLoginResponse(BaseModel):
    success: bool
    message: str


# Email sending function
async def send_welcome_email(email: str, referral_code: str, referral_link: str):
    """Send welcome email to new waitlist signup"""
    try:
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
        </head>
        <body style="font-family: Arial, sans-serif; background-color: #050505; color: #ffffff; padding: 40px; margin: 0;">
            <div style="max-width: 600px; margin: 0 auto; background-color: #0A0A0A; border-radius: 16px; padding: 40px; border: 1px solid #27272A;">
                <div style="text-align: center; margin-bottom: 32px;">
                    <h1 style="font-size: 36px; margin: 0; color: #ffffff;">
                        Shutter<span style="color: #7C3AED;">score</span>
                    </h1>
                </div>
                
                <h2 style="color: #ffffff; font-size: 24px; margin-bottom: 16px;">Welcome to the Waitlist! 🎉</h2>
                
                <p style="color: #A1A1AA; font-size: 16px; line-height: 1.6;">
                    Thanks for joining Shutterscore! You're now on the list for early access to our photo contest platform.
                </p>
                
                <p style="color: #A1A1AA; font-size: 16px; line-height: 1.6;">
                    Want to move up the waitlist? Share your unique referral link with friends:
                </p>
                
                <div style="background-color: #121212; border-radius: 8px; padding: 16px; margin: 24px 0; text-align: center;">
                    <p style="color: #7C3AED; font-size: 14px; margin: 0 0 8px 0;">Your Referral Link</p>
                    <a href="{referral_link}" style="color: #ffffff; font-size: 16px; word-break: break-all;">{referral_link}</a>
                </div>
                
                <p style="color: #A1A1AA; font-size: 14px; line-height: 1.6;">
                    Your referral code: <strong style="color: #10B981;">{referral_code}</strong>
                </p>
                
                <p style="color: #A1A1AA; font-size: 16px; line-height: 1.6;">
                    Every friend who joins using your link moves you up the list!
                </p>
                
                <div style="margin-top: 32px; padding-top: 24px; border-top: 1px solid #27272A; text-align: center;">
                    <p style="color: #52525B; font-size: 12px; margin: 0;">
                        © 2026 Shutterscore. Photo contests with purpose.
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        
        params = {
            "from": SENDER_EMAIL,
            "to": [email],
            "subject": "Welcome to Shutterscore! 📷 Your Early Access Awaits",
            "html": html_content
        }
        
        # Run sync SDK in thread to keep FastAPI non-blocking
        result = await asyncio.to_thread(resend.Emails.send, params)
        logger.info(f"Welcome email sent to {email}, ID: {result.get('id', 'unknown')}")
        return True
    except Exception as e:
        logger.error(f"Failed to send welcome email to {email}: {str(e)}")
        return False


# Status Routes
@api_router.get("/")
async def root():
    return {"message": "Hello World"}

@api_router.post("/status", response_model=StatusCheck)
async def create_status_check(input: StatusCheckCreate):
    status_dict = input.model_dump()
    status_obj = StatusCheck(**status_dict)
    
    doc = status_obj.model_dump()
    doc['timestamp'] = doc['timestamp'].isoformat()
    
    _ = await db.status_checks.insert_one(doc)
    return status_obj

@api_router.get("/status", response_model=List[StatusCheck])
async def get_status_checks():
    status_checks = await db.status_checks.find({}, {"_id": 0}).to_list(1000)
    
    for check in status_checks:
        if isinstance(check['timestamp'], str):
            check['timestamp'] = datetime.fromisoformat(check['timestamp'])
    
    return status_checks


# Waitlist Routes
@api_router.post("/waitlist", response_model=WaitlistResponse)
async def join_waitlist(input: WaitlistCreate):
    # Check if email already exists
    existing = await db.waitlist.find_one({"email": input.email}, {"_id": 0})
    if existing:
        referral_link = f"https://shutterscore.com/?ref={existing.get('referral_code', '')}"
        return WaitlistResponse(
            success=True,
            message="You're already on the waitlist! We'll notify you soon.",
            entry=WaitlistEntry(
                id=existing['id'],
                email=existing['email'],
                referral_code=existing.get('referral_code', ''),
                referred_by=existing.get('referred_by'),
                referral_count=existing.get('referral_count', 0),
                created_at=datetime.fromisoformat(existing['created_at']) if isinstance(existing['created_at'], str) else existing['created_at']
            ),
            referral_link=referral_link
        )
    
    # Check if referral code exists and update referrer's count
    referred_by = None
    if input.ref:
        referrer = await db.waitlist.find_one({"referral_code": input.ref.upper()}, {"_id": 0})
        if referrer:
            referred_by = input.ref.upper()
            # Increment referrer's count
            await db.waitlist.update_one(
                {"referral_code": input.ref.upper()},
                {"$inc": {"referral_count": 1}}
            )
            logger.info(f"Referral credited to {referrer['email']}")
    
    # Create new entry
    entry = WaitlistEntry(email=input.email, referred_by=referred_by)
    doc = entry.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    
    await db.waitlist.insert_one(doc)
    
    # Generate referral link
    referral_link = f"https://shutterscore.com/?ref={entry.referral_code}"
    
    # Send welcome email (non-blocking)
    asyncio.create_task(send_welcome_email(input.email, entry.referral_code, referral_link))
    
    return WaitlistResponse(
        success=True,
        message="Welcome to the waitlist! Check your email for your referral link.",
        entry=entry,
        referral_link=referral_link
    )

@api_router.get("/waitlist/count")
async def get_waitlist_count():
    count = await db.waitlist.count_documents({})
    return {"count": count}


# Admin Auth Routes
@api_router.post("/admin/login", response_model=AdminLoginResponse)
async def admin_login(request: AdminLoginRequest):
    if secrets.compare_digest(request.password, ADMIN_PASSWORD):
        return AdminLoginResponse(success=True, message="Login successful")
    raise HTTPException(status_code=401, detail="Invalid password")


@api_router.get("/admin/verify")
async def verify_admin_session(admin: str = Depends(verify_admin)):
    return {"authenticated": True, "user": admin}


# Admin Routes (Protected)
@api_router.get("/admin/waitlist", response_model=WaitlistListResponse)
async def get_waitlist_entries(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    admin: str = Depends(verify_admin)
):
    # Build query
    query = {}
    if search:
        query["email"] = {"$regex": search, "$options": "i"}
    
    # Get total count
    total = await db.waitlist.count_documents(query)
    total_pages = (total + page_size - 1) // page_size
    
    # Get paginated entries
    skip = (page - 1) * page_size
    cursor = db.waitlist.find(query, {"_id": 0}).sort("created_at", -1).skip(skip).limit(page_size)
    entries_raw = await cursor.to_list(page_size)
    
    # Convert to WaitlistEntry objects
    entries = []
    for entry in entries_raw:
        if isinstance(entry.get('created_at'), str):
            entry['created_at'] = datetime.fromisoformat(entry['created_at'])
        entries.append(WaitlistEntry(**entry))
    
    return WaitlistListResponse(
        entries=entries,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@api_router.get("/admin/waitlist/stats", response_model=WaitlistStats)
async def get_waitlist_stats(admin: str = Depends(verify_admin)):
    # Total signups
    total = await db.waitlist.count_documents({})
    
    # Today's signups
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    today_count = await db.waitlist.count_documents({
        "created_at": {"$gte": today_start.isoformat()}
    })
    
    # This week's signups (last 7 days)
    week_start = today_start - timedelta(days=7)
    week_count = await db.waitlist.count_documents({
        "created_at": {"$gte": week_start.isoformat()}
    })
    
    # Total referrals
    pipeline = [
        {"$group": {"_id": None, "total_referrals": {"$sum": "$referral_count"}}}
    ]
    result = await db.waitlist.aggregate(pipeline).to_list(1)
    total_referrals = result[0]["total_referrals"] if result else 0
    
    return WaitlistStats(
        total_signups=total,
        today_signups=today_count,
        this_week_signups=week_count,
        total_referrals=total_referrals
    )


@api_router.get("/admin/waitlist/export")
async def export_waitlist(admin: str = Depends(verify_admin)):
    # Get all entries
    entries = await db.waitlist.find({}, {"_id": 0}).sort("created_at", -1).to_list(10000)
    
    # Create CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Email", "Referral Code", "Referred By", "Referral Count", "Signed Up At", "ID"])
    
    for entry in entries:
        created_at = entry.get('created_at', '')
        if isinstance(created_at, datetime):
            created_at = created_at.isoformat()
        writer.writerow([
            entry.get('email', ''),
            entry.get('referral_code', ''),
            entry.get('referred_by', ''),
            entry.get('referral_count', 0),
            created_at,
            entry.get('id', '')
        ])
    
    output.seek(0)
    
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=waitlist_export.csv"}
    )


@api_router.delete("/admin/waitlist/{entry_id}")
async def delete_waitlist_entry(entry_id: str, admin: str = Depends(verify_admin)):
    result = await db.waitlist.delete_one({"id": entry_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Entry not found")
    return {"success": True, "message": "Entry deleted successfully"}


# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
