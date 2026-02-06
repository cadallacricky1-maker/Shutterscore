# Shutterscore - Product Requirements Document

## Original Problem Statement
Build a landing page for Shutterscore - a photo contest platform with seamless payments, fair judging, and automated donations to causes.

## What's Been Implemented (Feb 2026)

### Phase 1 - MVP Landing Page ✅
- Hero section with dramatic background
- Features bento grid, Impact stats section
- Waitlist form with validation
- Framer Motion animations

### Phase 2 - Admin & Sharing ✅
- Admin panel with stats, search, delete, CSV export
- Share modal (Twitter, Facebook, LinkedIn, Email)
- Open Graph meta tags

### Phase 3 - Auth, Referrals & Email ✅
- Admin password protection
- Referral tracking system with unique codes
- Welcome emails via Resend

### Phase 4 - Leaderboard, Position & Milestones ✅
- Public leaderboard page
- Position display after signup
- Milestone emails (Top 100/50/10, 5/10 referrals)

### Phase 5 - Social Proof, Lookup & Digest ✅
- **Social Proof Counter**: "Join X+ photographers • +Y today" in hero
- **Position Lookup Form**: Check your rank by email
  - Toggle to expand form
  - Shows position, referrals, total waitlist
  - Link to leaderboard
- **Weekly Digest Emails**:
  - Admin trigger button: "Send Weekly Digest"
  - Email includes: position, position change, referrals, total waitlist, top 5 leaderboard
  - Stores last_position for week-over-week comparison

## API Endpoints
- `GET /api/stats/social-proof` - Public social proof stats
- `GET /api/waitlist/position/{email}` - Position lookup
- `POST /api/admin/send-weekly-digest` - Trigger weekly digest (protected)
- Plus all previous endpoints...

## Tech Stack
- Frontend: React, Tailwind CSS, Framer Motion, Shadcn/UI
- Backend: FastAPI, MongoDB, Resend (Emergent LLM key)
- Auth: Simple password (HTTP Basic)

## All Features Complete ✅

| Feature | Status |
|---------|--------|
| Landing page | ✅ |
| Waitlist signup | ✅ |
| Admin panel | ✅ |
| Admin auth | ✅ |
| Referral tracking | ✅ |
| Welcome emails | ✅ |
| Share modal | ✅ |
| Open Graph tags | ✅ |
| Leaderboard | ✅ |
| Position display | ✅ |
| Milestone emails | ✅ |
| Social proof counter | ✅ |
| Position lookup | ✅ |
| Weekly digest | ✅ |
