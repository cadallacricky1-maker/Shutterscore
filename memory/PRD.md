# Shutterscore - Product Requirements Document

## Original Problem Statement
Build a landing page for Shutterscore - a photo contest platform with seamless payments, fair judging, and automated donations to causes.

## User Personas
- **Photography Enthusiasts**: Want to participate in contests and showcase their work
- **Contest Organizers**: Need tools to run fair, transparent photo competitions
- **Admins**: Need to manage waitlist signups and track growth

## What's Been Implemented (Feb 2026)

### Phase 1 - MVP Landing Page ✅
- Hero section with dramatic landscape background
- Features bento grid (6 features)
- Impact stats section
- Waitlist form with validation
- Toast notifications, Framer Motion animations

### Phase 2 - Admin & Sharing ✅
- Admin panel at `/admin` with stats dashboard
- CSV export, search, delete functionality
- Share with Friends modal (Twitter, Facebook, LinkedIn, Email)
- Open Graph meta tags

### Phase 3 - Auth, Referrals & Email ✅
- Admin password protection ("shutterscore2026")
- Referral tracking (unique codes, referral links)
- Welcome emails via Resend with position info

### Phase 4 - Leaderboard, Position & Milestones ✅
- **Public Leaderboard** (`/leaderboard`):
  - Top referrers with rank badges (crown, medal, award)
  - Masked emails for privacy (r***e@e***.com)
  - Referral codes and counts displayed
  - "X people with referrals" counter
- **Waitlist Position Display**:
  - Shows "#X out of Y people" after signup
  - Position based on referral count (more referrals = better rank)
  - Beautiful purple gradient position card
  - "Share & Move Up" + "View Leaderboard" buttons
- **Milestone Emails**:
  - Top 100, Top 50, Top 10 position milestones
  - 5 referrals, 10 referrals milestones
  - Beautiful HTML email templates with position info

## API Endpoints
- `POST /api/waitlist` - Join (returns position, total_waitlist)
- `GET /api/leaderboard` - Public leaderboard (limit param)
- `GET /api/waitlist/position/{email}` - Lookup position
- `POST /api/admin/login` - Admin login
- `GET /api/admin/waitlist` - List entries (protected)
- `GET /api/admin/waitlist/stats` - Statistics (protected)
- `GET /api/admin/waitlist/export` - CSV export (protected)
- `DELETE /api/admin/waitlist/{id}` - Delete entry (protected)

## Environment Variables
- `ADMIN_PASSWORD` - Admin panel password
- `RESEND_API_KEY` - Emergent LLM key for email
- `SENDER_EMAIL` - Email sender address

## Prioritized Backlog

### P0 - Complete ✅
All requested features implemented

### P1 - Future Enhancements
- Waitlist position lookup by email on landing page
- Weekly digest emails to waitlist
- Social proof counter on hero ("X people joined")

### P2 - Product Features
- Contest creation flow
- Payment integration (Stripe)
- Judge panel system
- Charity API integration

## Tech Stack
- Frontend: React, Tailwind CSS, Framer Motion, Shadcn/UI
- Backend: FastAPI, MongoDB, Resend
- Auth: Simple password (HTTP Basic)
