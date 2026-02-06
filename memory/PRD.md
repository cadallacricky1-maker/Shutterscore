# Shutterscore - Product Requirements Document

## Original Problem Statement
Build a landing page for Shutterscore - a photo contest platform with seamless payments, fair judging, and automated donations.

## What's Been Implemented (Feb 2026)

### Phase 1-5 - Core Platform ✅
- Landing page with waitlist
- Admin panel with stats
- Referral system with leaderboard
- Email notifications (Resend)
- Social proof & position tracking

### Phase 6 - Judging System ✅
**AI-Powered Judging (GPT-4o Vision)**
- Automatic photo analysis
- Structured scoring feedback
- One-click AI scoring button

**Manual Human Judging**
- Professional scoring rubric (100 points total):
  - Creativity & Originality: 30 pts (×3 weight)
  - Technical Composition: 25 pts (×2.5 weight)
  - Theme Relevance: 25 pts (×2.5 weight)
  - Emotional Impact: 20 pts (×2 weight)
- Anyone can judge (open access)

**Judge Dashboard** (`/judge`)
- Stats: Pending, Judged, Active Contests, Points
- Photo grid with "Judge Now" buttons
- Set email to track judgments

**Individual Judging Pages** (`/judge/{photoId}`)
- Large photo preview with metadata
- AI Score button (GPT-4o integration)
- 0-10 scoring sliders for each criterion
- Comments/feedback textarea
- Total score display (out of 100)

**Contest Management**
- `/contests` - List all contests with filters
- `/contests/{id}` - Contest detail with leaderboard
- Photo submission dialog
- Admin contest creation (protected)

## API Endpoints
**Judging System:**
- `POST /api/contests` - Create contest (admin)
- `GET /api/contests` - List contests
- `GET /api/contests/{id}` - Contest detail
- `PATCH /api/contests/{id}/status` - Update status
- `POST /api/photos` - Submit photo
- `GET /api/photos` - List photos
- `GET /api/photos/{id}` - Photo detail
- `POST /api/judge/ai-score` - Get AI scores
- `POST /api/judge/submit` - Submit judgment
- `GET /api/judge/pending` - Pending photos
- `GET /api/judge/stats` - Judge statistics
- `GET /api/contests/{id}/leaderboard` - Rankings

## Tech Stack
- Frontend: React, Tailwind CSS, Framer Motion, Shadcn/UI
- Backend: FastAPI, MongoDB
- AI: GPT-4o Vision via emergentintegrations
- Email: Resend (Emergent LLM key)
- Auth: Simple password (admin)

## All Features Complete ✅
| Feature | Status |
|---------|--------|
| Landing page | ✅ |
| Waitlist system | ✅ |
| Admin panel | ✅ |
| Referral tracking | ✅ |
| Email notifications | ✅ |
| Position tracking | ✅ |
| Social proof | ✅ |
| Weekly digest | ✅ |
| **AI Judging (GPT-4o)** | ✅ |
| **Manual Judging** | ✅ |
| **Judge Dashboard** | ✅ |
| **Contest Management** | ✅ |
| **Photo Submission** | ✅ |
| **Leaderboards** | ✅ |
