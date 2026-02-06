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
    position: Optional[int] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class WaitlistCreate(BaseModel):
    email: str
    ref: Optional[str] = None
    
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
    position: Optional[int] = None
    total_waitlist: Optional[int] = None


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


# Leaderboard Models
class LeaderboardEntry(BaseModel):
    rank: int
    email_masked: str
    referral_code: str
    referral_count: int

class LeaderboardResponse(BaseModel):
    entries: List[LeaderboardEntry]
    total_participants: int


# Position lookup model
class PositionResponse(BaseModel):
    email: str
    position: int
    total_waitlist: int
    referral_count: int
    referral_code: str


# Email templates
def get_welcome_email_html(referral_code: str, referral_link: str, position: int, total: int):
    """Generate welcome email HTML with position info"""
    return f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="utf-8"></head>
    <body style="font-family: Arial, sans-serif; background-color: #050505; color: #ffffff; padding: 40px; margin: 0;">
        <div style="max-width: 600px; margin: 0 auto; background-color: #0A0A0A; border-radius: 16px; padding: 40px; border: 1px solid #27272A;">
            <div style="text-align: center; margin-bottom: 32px;">
                <h1 style="font-size: 36px; margin: 0; color: #ffffff;">
                    Shutter<span style="color: #7C3AED;">score</span>
                </h1>
            </div>
            
            <h2 style="color: #ffffff; font-size: 24px; margin-bottom: 16px;">Welcome to the Waitlist! 🎉</h2>
            
            <div style="background-color: #7C3AED; border-radius: 12px; padding: 24px; margin: 24px 0; text-align: center;">
                <p style="color: rgba(255,255,255,0.8); font-size: 14px; margin: 0 0 8px 0;">Your Position</p>
                <p style="color: #ffffff; font-size: 48px; font-weight: bold; margin: 0;">#{position}</p>
                <p style="color: rgba(255,255,255,0.6); font-size: 14px; margin: 8px 0 0 0;">out of {total} people</p>
            </div>
            
            <p style="color: #A1A1AA; font-size: 16px; line-height: 1.6;">
                Thanks for joining Shutterscore! You're now on the list for early access to our photo contest platform.
            </p>
            
            <p style="color: #A1A1AA; font-size: 16px; line-height: 1.6;">
                <strong style="color: #10B981;">Want to move up?</strong> Share your unique referral link with friends:
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


def get_milestone_email_html(referral_code: str, referral_link: str, position: int, milestone: str):
    """Generate milestone email HTML"""
    milestone_messages = {
        "top_100": ("🏆 You're in the Top 100!", "You've climbed to the top 100 on the Shutterscore waitlist! Keep sharing to secure your spot."),
        "top_50": ("🥈 Top 50 Achieved!", "Amazing! You've reached the top 50. You're getting closer to early access."),
        "top_10": ("🥇 Elite Status: Top 10!", "Incredible! You're now in the top 10. You'll be among the first to access Shutterscore!"),
        "referral_5": ("🎯 5 Referrals!", "You've referred 5 friends! Your position just got a major boost."),
        "referral_10": ("🔥 10 Referrals!", "10 referrals! You're a Shutterscore ambassador. Amazing work!"),
    }
    
    title, message = milestone_messages.get(milestone, ("🎉 Milestone Reached!", "You've achieved a new milestone!"))
    
    return f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="utf-8"></head>
    <body style="font-family: Arial, sans-serif; background-color: #050505; color: #ffffff; padding: 40px; margin: 0;">
        <div style="max-width: 600px; margin: 0 auto; background-color: #0A0A0A; border-radius: 16px; padding: 40px; border: 1px solid #27272A;">
            <div style="text-align: center; margin-bottom: 32px;">
                <h1 style="font-size: 36px; margin: 0; color: #ffffff;">
                    Shutter<span style="color: #7C3AED;">score</span>
                </h1>
            </div>
            
            <div style="background-color: #10B981; border-radius: 12px; padding: 24px; margin: 24px 0; text-align: center;">
                <h2 style="color: #ffffff; font-size: 28px; margin: 0;">{title}</h2>
            </div>
            
            <p style="color: #A1A1AA; font-size: 18px; line-height: 1.6; text-align: center;">
                {message}
            </p>
            
            <div style="background-color: #121212; border-radius: 12px; padding: 24px; margin: 24px 0; text-align: center;">
                <p style="color: rgba(255,255,255,0.6); font-size: 14px; margin: 0 0 8px 0;">Your Current Position</p>
                <p style="color: #7C3AED; font-size: 48px; font-weight: bold; margin: 0;">#{position}</p>
            </div>
            
            <p style="color: #A1A1AA; font-size: 16px; line-height: 1.6; text-align: center;">
                Keep climbing! Share your link to move up even more:
            </p>
            
            <div style="background-color: #121212; border-radius: 8px; padding: 16px; margin: 24px 0; text-align: center;">
                <a href="{referral_link}" style="color: #7C3AED; font-size: 16px; word-break: break-all;">{referral_link}</a>
            </div>
            
            <div style="margin-top: 32px; padding-top: 24px; border-top: 1px solid #27272A; text-align: center;">
                <p style="color: #52525B; font-size: 12px; margin: 0;">
                    © 2026 Shutterscore. Photo contests with purpose.
                </p>
            </div>
        </div>
    </body>
    </html>
    """


# Email sending functions
async def send_welcome_email(email: str, referral_code: str, referral_link: str, position: int, total: int):
    """Send welcome email to new waitlist signup"""
    try:
        html_content = get_welcome_email_html(referral_code, referral_link, position, total)
        
        params = {
            "from": SENDER_EMAIL,
            "to": [email],
            "subject": f"Welcome to Shutterscore! 📷 You're #{position} on the waitlist",
            "html": html_content
        }
        
        result = await asyncio.to_thread(resend.Emails.send, params)
        logger.info(f"Welcome email sent to {email}, ID: {result.get('id', 'unknown')}")
        return True
    except Exception as e:
        logger.error(f"Failed to send welcome email to {email}: {str(e)}")
        return False


async def send_milestone_email(email: str, referral_code: str, referral_link: str, position: int, milestone: str):
    """Send milestone notification email"""
    try:
        html_content = get_milestone_email_html(referral_code, referral_link, position, milestone)
        
        milestone_subjects = {
            "top_100": "🏆 You're in the Top 100!",
            "top_50": "🥈 Top 50 Achieved!",
            "top_10": "🥇 You Made the Top 10!",
            "referral_5": "🎯 5 Referrals Milestone!",
            "referral_10": "🔥 10 Referrals Achieved!",
        }
        
        subject = milestone_subjects.get(milestone, "🎉 New Milestone Reached!")
        
        params = {
            "from": SENDER_EMAIL,
            "to": [email],
            "subject": f"Shutterscore: {subject}",
            "html": html_content
        }
        
        result = await asyncio.to_thread(resend.Emails.send, params)
        logger.info(f"Milestone email ({milestone}) sent to {email}, ID: {result.get('id', 'unknown')}")
        return True
    except Exception as e:
        logger.error(f"Failed to send milestone email to {email}: {str(e)}")
        return False


async def check_and_send_milestones(email: str, referral_code: str, referral_link: str, old_position: int, new_position: int, old_referral_count: int, new_referral_count: int):
    """Check for milestones and send appropriate emails"""
    # Position milestones (only when crossing threshold going up)
    if old_position > 100 and new_position <= 100:
        asyncio.create_task(send_milestone_email(email, referral_code, referral_link, new_position, "top_100"))
    if old_position > 50 and new_position <= 50:
        asyncio.create_task(send_milestone_email(email, referral_code, referral_link, new_position, "top_50"))
    if old_position > 10 and new_position <= 10:
        asyncio.create_task(send_milestone_email(email, referral_code, referral_link, new_position, "top_10"))
    
    # Referral milestones
    if old_referral_count < 5 and new_referral_count >= 5:
        asyncio.create_task(send_milestone_email(email, referral_code, referral_link, new_position, "referral_5"))
    if old_referral_count < 10 and new_referral_count >= 10:
        asyncio.create_task(send_milestone_email(email, referral_code, referral_link, new_position, "referral_10"))


async def calculate_position(entry_id: str) -> int:
    """Calculate waitlist position based on referral count and signup date"""
    # Get all entries sorted by referral_count (desc) then created_at (asc)
    pipeline = [
        {"$sort": {"referral_count": -1, "created_at": 1}},
        {"$group": {"_id": None, "entries": {"$push": "$id"}}}
    ]
    result = await db.waitlist.aggregate(pipeline).to_list(1)
    
    if result and result[0].get("entries"):
        entries = result[0]["entries"]
        try:
            return entries.index(entry_id) + 1
        except ValueError:
            return len(entries) + 1
    return 1


def mask_email(email: str) -> str:
    """Mask email for privacy: john.doe@example.com -> j***e@e***.com"""
    parts = email.split("@")
    if len(parts) != 2:
        return "***@***.***"
    
    local = parts[0]
    domain = parts[1].split(".")
    
    if len(local) > 2:
        masked_local = local[0] + "***" + local[-1]
    else:
        masked_local = local[0] + "***"
    
    if len(domain) >= 2:
        masked_domain = domain[0][0] + "***." + domain[-1]
    else:
        masked_domain = "***"
    
    return f"{masked_local}@{masked_domain}"


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
        position = await calculate_position(existing['id'])
        total = await db.waitlist.count_documents({})
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
                position=position,
                created_at=datetime.fromisoformat(existing['created_at']) if isinstance(existing['created_at'], str) else existing['created_at']
            ),
            referral_link=referral_link,
            position=position,
            total_waitlist=total
        )
    
    # Check if referral code exists and update referrer's count
    referred_by = None
    referrer_info = None
    if input.ref:
        referrer = await db.waitlist.find_one({"referral_code": input.ref.upper()}, {"_id": 0})
        if referrer:
            referred_by = input.ref.upper()
            old_referral_count = referrer.get('referral_count', 0)
            old_position = await calculate_position(referrer['id'])
            
            # Increment referrer's count
            await db.waitlist.update_one(
                {"referral_code": input.ref.upper()},
                {"$inc": {"referral_count": 1}}
            )
            
            referrer_info = {
                "email": referrer['email'],
                "referral_code": referrer['referral_code'],
                "old_referral_count": old_referral_count,
                "old_position": old_position
            }
            logger.info(f"Referral credited to {referrer['email']}")
    
    # Create new entry
    entry = WaitlistEntry(email=input.email, referred_by=referred_by)
    doc = entry.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    del doc['position']  # Don't store position, it's calculated dynamically
    
    await db.waitlist.insert_one(doc)
    
    # Calculate position and total
    total = await db.waitlist.count_documents({})
    position = await calculate_position(entry.id)
    entry.position = position
    
    # Generate referral link
    referral_link = f"https://shutterscore.com/?ref={entry.referral_code}"
    
    # Send welcome email (non-blocking)
    asyncio.create_task(send_welcome_email(input.email, entry.referral_code, referral_link, position, total))
    
    # Check milestones for referrer
    if referrer_info:
        new_position = await calculate_position(referrer_info['referral_code'])
        # Find referrer by code to get updated count
        updated_referrer = await db.waitlist.find_one({"referral_code": referrer_info['referral_code']}, {"_id": 0})
        if updated_referrer:
            new_referral_count = updated_referrer.get('referral_count', 0)
            referrer_link = f"https://shutterscore.com/?ref={referrer_info['referral_code']}"
            asyncio.create_task(check_and_send_milestones(
                referrer_info['email'],
                referrer_info['referral_code'],
                referrer_link,
                referrer_info['old_position'],
                new_position,
                referrer_info['old_referral_count'],
                new_referral_count
            ))
    
    return WaitlistResponse(
        success=True,
        message=f"Welcome to the waitlist! You're #{position}. Check your email for your referral link.",
        entry=entry,
        referral_link=referral_link,
        position=position,
        total_waitlist=total
    )

@api_router.get("/waitlist/count")
async def get_waitlist_count():
    count = await db.waitlist.count_documents({})
    return {"count": count}


# Public Leaderboard Route
@api_router.get("/leaderboard", response_model=LeaderboardResponse)
async def get_leaderboard(limit: int = Query(10, ge=1, le=50)):
    """Get top referrers leaderboard (public, no auth required)"""
    # Get top referrers sorted by referral_count
    cursor = db.waitlist.find(
        {"referral_count": {"$gt": 0}},
        {"_id": 0}
    ).sort("referral_count", -1).limit(limit)
    
    entries_raw = await cursor.to_list(limit)
    total_participants = await db.waitlist.count_documents({"referral_count": {"$gt": 0}})
    
    entries = []
    for idx, entry in enumerate(entries_raw):
        entries.append(LeaderboardEntry(
            rank=idx + 1,
            email_masked=mask_email(entry.get('email', '')),
            referral_code=entry.get('referral_code', ''),
            referral_count=entry.get('referral_count', 0)
        ))
    
    return LeaderboardResponse(
        entries=entries,
        total_participants=total_participants
    )


# Position Lookup Route
@api_router.get("/waitlist/position/{email}")
async def get_position_by_email(email: str):
    """Get waitlist position by email"""
    email = email.lower().strip()
    entry = await db.waitlist.find_one({"email": email}, {"_id": 0})
    
    if not entry:
        raise HTTPException(status_code=404, detail="Email not found on waitlist")
    
    position = await calculate_position(entry['id'])
    total = await db.waitlist.count_documents({})
    
    return PositionResponse(
        email=mask_email(email),
        position=position,
        total_waitlist=total,
        referral_count=entry.get('referral_count', 0),
        referral_code=entry.get('referral_code', '')
    )


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
    query = {}
    if search:
        query["email"] = {"$regex": search, "$options": "i"}
    
    total = await db.waitlist.count_documents(query)
    total_pages = (total + page_size - 1) // page_size
    
    skip = (page - 1) * page_size
    cursor = db.waitlist.find(query, {"_id": 0}).sort("referral_count", -1).skip(skip).limit(page_size)
    entries_raw = await cursor.to_list(page_size)
    
    entries = []
    for entry in entries_raw:
        if isinstance(entry.get('created_at'), str):
            entry['created_at'] = datetime.fromisoformat(entry['created_at'])
        position = await calculate_position(entry['id'])
        entries.append(WaitlistEntry(position=position, **entry))
    
    return WaitlistListResponse(
        entries=entries,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@api_router.get("/admin/waitlist/stats", response_model=WaitlistStats)
async def get_waitlist_stats(admin: str = Depends(verify_admin)):
    total = await db.waitlist.count_documents({})
    
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    today_count = await db.waitlist.count_documents({
        "created_at": {"$gte": today_start.isoformat()}
    })
    
    week_start = today_start - timedelta(days=7)
    week_count = await db.waitlist.count_documents({
        "created_at": {"$gte": week_start.isoformat()}
    })
    
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
    entries = await db.waitlist.find({}, {"_id": 0}).sort("referral_count", -1).to_list(10000)
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Position", "Email", "Referral Code", "Referred By", "Referral Count", "Signed Up At", "ID"])
    
    for idx, entry in enumerate(entries):
        created_at = entry.get('created_at', '')
        if isinstance(created_at, datetime):
            created_at = created_at.isoformat()
        writer.writerow([
            idx + 1,
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
