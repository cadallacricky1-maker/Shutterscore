from fastapi import FastAPI, APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
import re
import io
import csv
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import List, Optional
import uuid
from datetime import datetime, timezone


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")


# Define Models
class StatusCheck(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class StatusCheckCreate(BaseModel):
    client_name: str


# Waitlist Models
class WaitlistEntry(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class WaitlistCreate(BaseModel):
    email: str
    
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
        return WaitlistResponse(
            success=True,
            message="You're already on the waitlist! We'll notify you soon.",
            entry=WaitlistEntry(**existing) if isinstance(existing.get('created_at'), datetime) else WaitlistEntry(
                id=existing['id'],
                email=existing['email'],
                created_at=datetime.fromisoformat(existing['created_at']) if isinstance(existing['created_at'], str) else existing['created_at']
            )
        )
    
    # Create new entry
    entry = WaitlistEntry(email=input.email)
    doc = entry.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    
    await db.waitlist.insert_one(doc)
    
    return WaitlistResponse(
        success=True,
        message="Welcome to the waitlist! We'll be in touch soon.",
        entry=entry
    )

@api_router.get("/waitlist/count")
async def get_waitlist_count():
    count = await db.waitlist.count_documents({})
    return {"count": count}


# Admin Routes
@api_router.get("/admin/waitlist", response_model=WaitlistListResponse)
async def get_waitlist_entries(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = None
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
async def get_waitlist_stats():
    # Total signups
    total = await db.waitlist.count_documents({})
    
    # Today's signups
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    today_count = await db.waitlist.count_documents({
        "created_at": {"$gte": today_start.isoformat()}
    })
    
    # This week's signups (last 7 days)
    from datetime import timedelta
    week_start = today_start - timedelta(days=7)
    week_count = await db.waitlist.count_documents({
        "created_at": {"$gte": week_start.isoformat()}
    })
    
    return WaitlistStats(
        total_signups=total,
        today_signups=today_count,
        this_week_signups=week_count
    )


@api_router.get("/admin/waitlist/export")
async def export_waitlist():
    # Get all entries
    entries = await db.waitlist.find({}, {"_id": 0}).sort("created_at", -1).to_list(10000)
    
    # Create CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Email", "Signed Up At", "ID"])
    
    for entry in entries:
        created_at = entry.get('created_at', '')
        if isinstance(created_at, datetime):
            created_at = created_at.isoformat()
        writer.writerow([entry.get('email', ''), created_at, entry.get('id', '')])
    
    output.seek(0)
    
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=waitlist_export.csv"}
    )


@api_router.delete("/admin/waitlist/{entry_id}")
async def delete_waitlist_entry(entry_id: str):
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

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
