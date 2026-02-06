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


# Social Proof Stats (Public)
class SocialProofStats(BaseModel):
    total_signups: int
    recent_signups: int  # Last 24 hours
    total_referrals: int
    top_referrer_count: int


@api_router.get("/stats/social-proof", response_model=SocialProofStats)
async def get_social_proof_stats():
    """Public endpoint for social proof counter on landing page"""
    total = await db.waitlist.count_documents({})
    
    # Recent signups (last 24 hours)
    yesterday = datetime.now(timezone.utc) - timedelta(hours=24)
    recent = await db.waitlist.count_documents({
        "created_at": {"$gte": yesterday.isoformat()}
    })
    
    # Total referrals
    pipeline = [
        {"$group": {"_id": None, "total": {"$sum": "$referral_count"}}}
    ]
    result = await db.waitlist.aggregate(pipeline).to_list(1)
    total_referrals = result[0]["total"] if result else 0
    
    # Top referrer count
    top_referrer = await db.waitlist.find_one(
        {},
        {"_id": 0, "referral_count": 1},
        sort=[("referral_count", -1)]
    )
    top_count = top_referrer.get("referral_count", 0) if top_referrer else 0
    
    return SocialProofStats(
        total_signups=total,
        recent_signups=recent,
        total_referrals=total_referrals,
        top_referrer_count=top_count
    )


# Weekly Digest Email Template
def get_weekly_digest_email_html(
    email: str,
    position: int,
    total: int,
    referral_count: int,
    referral_code: str,
    referral_link: str,
    position_change: int,
    new_signups_this_week: int,
    top_referrers: list
):
    """Generate weekly digest email HTML"""
    position_text = ""
    if position_change > 0:
        position_text = f'<span style="color: #10B981;">↑ Moved up {position_change} spots!</span>'
    elif position_change < 0:
        position_text = f'<span style="color: #EF4444;">↓ Dropped {abs(position_change)} spots</span>'
    else:
        position_text = '<span style="color: #A1A1AA;">No change this week</span>'
    
    leaderboard_html = ""
    for idx, leader in enumerate(top_referrers[:5]):
        leaderboard_html += f'''
        <tr style="border-bottom: 1px solid #27272A;">
            <td style="padding: 12px; color: #A1A1AA;">#{idx + 1}</td>
            <td style="padding: 12px; color: #ffffff;">{leader['email_masked']}</td>
            <td style="padding: 12px; color: #10B981; text-align: right;">{leader['referral_count']} referrals</td>
        </tr>
        '''
    
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
                <p style="color: #A1A1AA; margin-top: 8px;">Weekly Waitlist Update</p>
            </div>
            
            <h2 style="color: #ffffff; font-size: 24px; margin-bottom: 24px; text-align: center;">
                Your Weekly Stats 📊
            </h2>
            
            <!-- Position Card -->
            <div style="background: linear-gradient(135deg, #7C3AED 0%, #6D28D9 100%); border-radius: 12px; padding: 24px; margin: 24px 0; text-align: center;">
                <p style="color: rgba(255,255,255,0.8); font-size: 14px; margin: 0 0 8px 0;">Your Position</p>
                <p style="color: #ffffff; font-size: 48px; font-weight: bold; margin: 0;">#{position}</p>
                <p style="font-size: 14px; margin: 8px 0 0 0;">{position_text}</p>
            </div>
            
            <!-- Stats Grid -->
            <div style="display: flex; gap: 16px; margin: 24px 0;">
                <div style="flex: 1; background-color: #121212; border-radius: 8px; padding: 16px; text-align: center;">
                    <p style="color: #A1A1AA; font-size: 12px; margin: 0;">Your Referrals</p>
                    <p style="color: #10B981; font-size: 24px; font-weight: bold; margin: 4px 0 0 0;">{referral_count}</p>
                </div>
                <div style="flex: 1; background-color: #121212; border-radius: 8px; padding: 16px; text-align: center;">
                    <p style="color: #A1A1AA; font-size: 12px; margin: 0;">Total Waitlist</p>
                    <p style="color: #7C3AED; font-size: 24px; font-weight: bold; margin: 4px 0 0 0;">{total}</p>
                </div>
                <div style="flex: 1; background-color: #121212; border-radius: 8px; padding: 16px; text-align: center;">
                    <p style="color: #A1A1AA; font-size: 12px; margin: 0;">New This Week</p>
                    <p style="color: #F59E0B; font-size: 24px; font-weight: bold; margin: 4px 0 0 0;">+{new_signups_this_week}</p>
                </div>
            </div>
            
            <!-- Leaderboard -->
            <div style="margin: 32px 0;">
                <h3 style="color: #ffffff; font-size: 18px; margin-bottom: 16px;">🏆 Top Referrers This Week</h3>
                <table style="width: 100%; border-collapse: collapse;">
                    {leaderboard_html}
                </table>
            </div>
            
            <!-- CTA -->
            <div style="background-color: #121212; border-radius: 12px; padding: 24px; margin: 24px 0; text-align: center;">
                <p style="color: #ffffff; font-size: 16px; margin: 0 0 16px 0;">
                    Want to climb higher? Share your referral link!
                </p>
                <a href="{referral_link}" style="display: inline-block; background-color: #7C3AED; color: #ffffff; padding: 12px 24px; border-radius: 8px; text-decoration: none; font-weight: bold;">
                    Share Now →
                </a>
                <p style="color: #A1A1AA; font-size: 12px; margin: 16px 0 0 0;">
                    Your code: <span style="color: #10B981;">{referral_code}</span>
                </p>
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


async def send_weekly_digest_email(
    email: str,
    position: int,
    total: int,
    referral_count: int,
    referral_code: str,
    referral_link: str,
    position_change: int,
    new_signups_this_week: int,
    top_referrers: list
):
    """Send weekly digest email"""
    try:
        html_content = get_weekly_digest_email_html(
            email, position, total, referral_count, referral_code,
            referral_link, position_change, new_signups_this_week, top_referrers
        )
        
        params = {
            "from": SENDER_EMAIL,
            "to": [email],
            "subject": f"📊 Shutterscore Weekly: You're #{position} — Here's your update",
            "html": html_content
        }
        
        result = await asyncio.to_thread(resend.Emails.send, params)
        logger.info(f"Weekly digest sent to {email}, ID: {result.get('id', 'unknown')}")
        return True
    except Exception as e:
        logger.error(f"Failed to send weekly digest to {email}: {str(e)}")
        return False


# Admin endpoint to trigger weekly digest (can be called by cron job)
class WeeklyDigestResponse(BaseModel):
    success: bool
    emails_sent: int
    message: str


@api_router.post("/admin/send-weekly-digest", response_model=WeeklyDigestResponse)
async def trigger_weekly_digest(admin: str = Depends(verify_admin)):
    """Send weekly digest to all waitlist members (admin only)"""
    # Get all waitlist entries
    entries = await db.waitlist.find({}, {"_id": 0}).to_list(10000)
    total = len(entries)
    
    # Calculate new signups this week
    week_ago = datetime.now(timezone.utc) - timedelta(days=7)
    new_signups = await db.waitlist.count_documents({
        "created_at": {"$gte": week_ago.isoformat()}
    })
    
    # Get top referrers for leaderboard
    top_referrers_raw = await db.waitlist.find(
        {"referral_count": {"$gt": 0}},
        {"_id": 0}
    ).sort("referral_count", -1).limit(5).to_list(5)
    
    top_referrers = [
        {"email_masked": mask_email(r.get('email', '')), "referral_count": r.get('referral_count', 0)}
        for r in top_referrers_raw
    ]
    
    emails_sent = 0
    
    for entry in entries:
        email = entry.get('email', '')
        referral_code = entry.get('referral_code', '')
        referral_count = entry.get('referral_count', 0)
        entry_id = entry.get('id', '')
        
        # Calculate current position
        position = await calculate_position(entry_id)
        
        # Get previous position from stored field or estimate
        previous_position = entry.get('last_position', position)
        position_change = previous_position - position  # Positive = moved up
        
        referral_link = f"https://shutterscore.com/?ref={referral_code}"
        
        # Send email
        success = await send_weekly_digest_email(
            email, position, total, referral_count, referral_code,
            referral_link, position_change, new_signups, top_referrers
        )
        
        if success:
            emails_sent += 1
            # Update last_position for next week's comparison
            await db.waitlist.update_one(
                {"id": entry_id},
                {"$set": {"last_position": position}}
            )
    
    return WeeklyDigestResponse(
        success=True,
        emails_sent=emails_sent,
        message=f"Weekly digest sent to {emails_sent} of {total} subscribers"
    )


# ============================================
# JUDGING SYSTEM
# ============================================

from emergentintegrations.llm.chat import LlmChat, UserMessage
import httpx
import base64

EMERGENT_LLM_KEY = os.environ.get('EMERGENT_LLM_KEY', '')

# Scoring weights
SCORING_WEIGHTS = {
    "creativity": 3.0,      # 30 points max
    "composition": 2.5,     # 25 points max
    "theme_fit": 2.5,       # 25 points max
    "impact": 2.0           # 20 points max
}


# Contest Models
class Contest(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: str
    theme: str
    prize_amount: float = 0
    entry_fee: float = 0
    start_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    end_date: datetime
    status: str = "active"  # active, judging, completed
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ContestCreate(BaseModel):
    title: str
    description: str
    theme: str
    prize_amount: float = 0
    entry_fee: float = 0
    end_date: datetime


# Photo Entry Models
class PhotoEntry(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    contest_id: str
    photographer_name: str
    photographer_email: str
    photo_url: str
    title: str
    description: Optional[str] = None
    status: str = "pending"  # pending, judged
    total_score: float = 0
    judge_count: int = 0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class PhotoEntryCreate(BaseModel):
    contest_id: str
    photographer_name: str
    photographer_email: str
    photo_url: str
    title: str
    description: Optional[str] = None


# Score Models
class ScoreBreakdown(BaseModel):
    creativity: float = Field(ge=0, le=10)
    composition: float = Field(ge=0, le=10)
    theme_fit: float = Field(ge=0, le=10)
    impact: float = Field(ge=0, le=10)


class JudgeScore(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    photo_id: str
    contest_id: str
    judge_name: str
    judge_email: str
    scores: ScoreBreakdown
    weighted_total: float
    normalized_score: float  # Out of 40 for leaderboard
    comments: str = ""
    is_ai_generated: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class JudgeScoreCreate(BaseModel):
    photo_id: str
    judge_name: str
    judge_email: str
    scores: ScoreBreakdown
    comments: str = ""
    is_ai_generated: bool = False


class AIScoreRequest(BaseModel):
    photo_url: str
    contest_theme: str


class AIScoreResponse(BaseModel):
    scores: ScoreBreakdown
    comments: str
    weighted_total: float
    normalized_score: float


# Helper function to calculate weighted score
def calculate_weighted_score(scores: ScoreBreakdown) -> tuple:
    """Calculate weighted total and normalized score"""
    weighted = (
        scores.creativity * SCORING_WEIGHTS["creativity"] +
        scores.composition * SCORING_WEIGHTS["composition"] +
        scores.theme_fit * SCORING_WEIGHTS["theme_fit"] +
        scores.impact * SCORING_WEIGHTS["impact"]
    )
    # Normalize to 40 points for leaderboard compatibility
    normalized = (weighted / 100) * 40
    return round(weighted, 2), round(normalized, 2)


# AI Judging function
async def get_ai_scores(photo_url: str, theme: str) -> dict:
    """Use GPT-4o to analyze photo and generate scores"""
    try:
        # Download image and convert to base64
        async with httpx.AsyncClient() as client:
            response = await client.get(photo_url, timeout=30)
            if response.status_code != 200:
                raise Exception(f"Failed to fetch image: {response.status_code}")
            
            image_base64 = base64.b64encode(response.content).decode('utf-8')
            
            # Determine mime type
            content_type = response.headers.get('content-type', 'image/jpeg')
            if 'png' in content_type:
                mime_type = 'image/png'
            elif 'webp' in content_type:
                mime_type = 'image/webp'
            else:
                mime_type = 'image/jpeg'
        
        # Create chat instance
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"judge-{uuid.uuid4()}",
            system_message="""You are an expert photography judge. Analyze photos and provide scores based on:
1. Creativity & Originality (0-10): Unique perspective, innovative approach
2. Technical Composition (0-10): Rule of thirds, leading lines, framing, focus
3. Theme Relevance (0-10): How well it fits the contest theme
4. Emotional Impact (0-10): Ability to evoke feelings, storytelling

Respond ONLY with valid JSON in this exact format:
{
    "creativity": <number 0-10>,
    "composition": <number 0-10>,
    "theme_fit": <number 0-10>,
    "impact": <number 0-10>,
    "comments": "<detailed feedback string>"
}"""
        ).with_model("openai", "gpt-4o")
        
        # Create message with image
        from emergentintegrations.llm.chat import ImageContent
        image_content = ImageContent(image_base64=image_base64)
        
        user_message = UserMessage(
            text=f"""Analyze this photo for a contest with the theme: "{theme}"
            
Score each criterion from 0-10 and provide detailed feedback. Be fair but constructive.""",
            file_contents=[image_content]
        )
        
        # Get response
        response_text = await chat.send_message(user_message)
        
        # Parse JSON response
        import json
        # Clean response if needed
        response_text = response_text.strip()
        if response_text.startswith("```"):
            response_text = response_text.split("```")[1]
            if response_text.startswith("json"):
                response_text = response_text[4:]
        response_text = response_text.strip()
        
        result = json.loads(response_text)
        
        return {
            "creativity": min(10, max(0, float(result.get("creativity", 5)))),
            "composition": min(10, max(0, float(result.get("composition", 5)))),
            "theme_fit": min(10, max(0, float(result.get("theme_fit", 5)))),
            "impact": min(10, max(0, float(result.get("impact", 5)))),
            "comments": result.get("comments", "AI analysis complete.")
        }
        
    except Exception as e:
        logger.error(f"AI scoring failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"AI scoring failed: {str(e)}")


# Contest Routes
@api_router.post("/contests", response_model=Contest)
async def create_contest(input: ContestCreate, admin: str = Depends(verify_admin)):
    """Create a new photo contest (admin only)"""
    contest = Contest(**input.model_dump())
    doc = contest.model_dump()
    doc['start_date'] = doc['start_date'].isoformat()
    doc['end_date'] = doc['end_date'].isoformat()
    doc['created_at'] = doc['created_at'].isoformat()
    
    await db.contests.insert_one(doc)
    return contest


@api_router.get("/contests")
async def list_contests(status: Optional[str] = None):
    """List all contests"""
    query = {}
    if status:
        query["status"] = status
    
    contests = await db.contests.find(query, {"_id": 0}).sort("created_at", -1).to_list(100)
    return {"contests": contests}


@api_router.get("/contests/{contest_id}")
async def get_contest(contest_id: str):
    """Get a single contest"""
    contest = await db.contests.find_one({"id": contest_id}, {"_id": 0})
    if not contest:
        raise HTTPException(status_code=404, detail="Contest not found")
    
    # Get photo count and judged count
    photo_count = await db.photo_entries.count_documents({"contest_id": contest_id})
    judged_count = await db.photo_entries.count_documents({"contest_id": contest_id, "status": "judged"})
    
    contest["photo_count"] = photo_count
    contest["judged_count"] = judged_count
    
    return contest


@api_router.patch("/contests/{contest_id}/status")
async def update_contest_status(contest_id: str, status: str, admin: str = Depends(verify_admin)):
    """Update contest status (admin only)"""
    if status not in ["active", "judging", "completed"]:
        raise HTTPException(status_code=400, detail="Invalid status")
    
    result = await db.contests.update_one(
        {"id": contest_id},
        {"$set": {"status": status}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Contest not found")
    
    return {"success": True, "message": f"Contest status updated to {status}"}


# Photo Entry Routes
@api_router.post("/photos", response_model=PhotoEntry)
async def submit_photo(input: PhotoEntryCreate):
    """Submit a photo entry to a contest"""
    # Verify contest exists and is active
    contest = await db.contests.find_one({"id": input.contest_id}, {"_id": 0})
    if not contest:
        raise HTTPException(status_code=404, detail="Contest not found")
    if contest.get("status") != "active":
        raise HTTPException(status_code=400, detail="Contest is not accepting entries")
    
    entry = PhotoEntry(**input.model_dump())
    doc = entry.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    
    await db.photo_entries.insert_one(doc)
    return entry


@api_router.get("/photos")
async def list_photos(contest_id: Optional[str] = None, status: Optional[str] = None):
    """List photo entries"""
    query = {}
    if contest_id:
        query["contest_id"] = contest_id
    if status:
        query["status"] = status
    
    photos = await db.photo_entries.find(query, {"_id": 0}).sort("created_at", -1).to_list(500)
    return {"photos": photos}


@api_router.get("/photos/{photo_id}")
async def get_photo(photo_id: str):
    """Get a single photo entry with scores"""
    photo = await db.photo_entries.find_one({"id": photo_id}, {"_id": 0})
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")
    
    # Get all scores for this photo
    scores = await db.judge_scores.find({"photo_id": photo_id}, {"_id": 0}).to_list(100)
    photo["scores"] = scores
    
    # Get contest info
    contest = await db.contests.find_one({"id": photo.get("contest_id")}, {"_id": 0})
    photo["contest"] = contest
    
    return photo


# Judging Routes
@api_router.post("/judge/ai-score", response_model=AIScoreResponse)
async def get_ai_score(request: AIScoreRequest):
    """Get AI-generated scores for a photo"""
    scores_dict = await get_ai_scores(request.photo_url, request.contest_theme)
    
    scores = ScoreBreakdown(
        creativity=scores_dict["creativity"],
        composition=scores_dict["composition"],
        theme_fit=scores_dict["theme_fit"],
        impact=scores_dict["impact"]
    )
    
    weighted, normalized = calculate_weighted_score(scores)
    
    return AIScoreResponse(
        scores=scores,
        comments=scores_dict["comments"],
        weighted_total=weighted,
        normalized_score=normalized
    )


@api_router.post("/judge/submit", response_model=JudgeScore)
async def submit_score(input: JudgeScoreCreate):
    """Submit a judge's score for a photo"""
    # Verify photo exists
    photo = await db.photo_entries.find_one({"id": input.photo_id}, {"_id": 0})
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")
    
    # Check if this judge already scored this photo
    existing = await db.judge_scores.find_one({
        "photo_id": input.photo_id,
        "judge_email": input.judge_email
    })
    if existing:
        raise HTTPException(status_code=400, detail="You have already judged this photo")
    
    # Calculate weighted score
    weighted, normalized = calculate_weighted_score(input.scores)
    
    score = JudgeScore(
        photo_id=input.photo_id,
        contest_id=photo.get("contest_id"),
        judge_name=input.judge_name,
        judge_email=input.judge_email,
        scores=input.scores,
        weighted_total=weighted,
        normalized_score=normalized,
        comments=input.comments,
        is_ai_generated=input.is_ai_generated
    )
    
    doc = score.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    doc['scores'] = doc['scores']
    
    await db.judge_scores.insert_one(doc)
    
    # Update photo's average score
    all_scores = await db.judge_scores.find({"photo_id": input.photo_id}, {"_id": 0}).to_list(100)
    total_weighted = sum(s.get("weighted_total", 0) for s in all_scores)
    avg_score = total_weighted / len(all_scores) if all_scores else 0
    
    await db.photo_entries.update_one(
        {"id": input.photo_id},
        {
            "$set": {
                "total_score": round(avg_score, 2),
                "judge_count": len(all_scores),
                "status": "judged" if len(all_scores) >= 1 else "pending"
            }
        }
    )
    
    return score


@api_router.get("/judge/pending")
async def get_pending_photos(contest_id: Optional[str] = None, judge_email: Optional[str] = None):
    """Get photos pending judgment"""
    query = {"status": "pending"}
    if contest_id:
        query["contest_id"] = contest_id
    
    photos = await db.photo_entries.find(query, {"_id": 0}).to_list(100)
    
    # If judge_email provided, filter out already judged
    if judge_email:
        judged_photo_ids = set()
        scores = await db.judge_scores.find({"judge_email": judge_email}, {"photo_id": 1, "_id": 0}).to_list(1000)
        judged_photo_ids = {s["photo_id"] for s in scores}
        photos = [p for p in photos if p["id"] not in judged_photo_ids]
    
    # Enrich with contest info
    for photo in photos:
        contest = await db.contests.find_one({"id": photo.get("contest_id")}, {"_id": 0, "title": 1, "theme": 1})
        photo["contest_title"] = contest.get("title") if contest else "Unknown"
        photo["contest_theme"] = contest.get("theme") if contest else ""
    
    return {"photos": photos, "count": len(photos)}


@api_router.get("/judge/stats")
async def get_judge_stats(judge_email: Optional[str] = None):
    """Get judging statistics"""
    total_pending = await db.photo_entries.count_documents({"status": "pending"})
    total_judged = await db.photo_entries.count_documents({"status": "judged"})
    active_contests = await db.contests.count_documents({"status": {"$in": ["active", "judging"]}})
    
    stats = {
        "total_pending": total_pending,
        "total_judged": total_judged,
        "active_contests": active_contests
    }
    
    if judge_email:
        my_judgments = await db.judge_scores.count_documents({"judge_email": judge_email})
        stats["my_judgments"] = my_judgments
        stats["my_points"] = my_judgments * 5  # 5 points per judgment
    
    return stats


@api_router.get("/contests/{contest_id}/leaderboard")
async def get_contest_leaderboard(contest_id: str):
    """Get leaderboard for a contest"""
    photos = await db.photo_entries.find(
        {"contest_id": contest_id, "judge_count": {"$gt": 0}},
        {"_id": 0}
    ).sort("total_score", -1).to_list(100)
    
    leaderboard = []
    for idx, photo in enumerate(photos):
        leaderboard.append({
            "rank": idx + 1,
            "photo_id": photo["id"],
            "title": photo["title"],
            "photographer_name": photo["photographer_name"],
            "photo_url": photo["photo_url"],
            "total_score": photo["total_score"],
            "judge_count": photo["judge_count"]
        })
    
    return {"leaderboard": leaderboard}


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
