# Shutterscore - Product Requirements Document

## Original Problem Statement
Build a landing page for Shutterscore - a photo contest platform with seamless payments, fair judging, and automated donations to causes.

## User Personas
- **Photography Enthusiasts**: Want to participate in contests and showcase their work
- **Contest Organizers**: Need tools to run fair, transparent photo competitions
- **Admins**: Need to manage waitlist signups and track growth

## Core Requirements (Static)
1. Stunning, premium landing page with dark theme
2. Email waitlist collection with MongoDB storage
3. Admin panel for waitlist management (password protected)
4. Referral tracking system
5. Email notifications on signup
6. Social sharing capabilities
7. Open Graph meta tags for social previews

## What's Been Implemented (Feb 2026)

### Phase 1 - MVP Landing Page ✅
- Hero section with dramatic landscape background
- Features bento grid (6 features)
- Impact stats section
- Waitlist form with validation
- Toast notifications
- Framer Motion animations

### Phase 2 - Admin & Sharing ✅
- Admin panel at `/admin` with stats dashboard
- CSV export functionality
- Share with Friends modal
- Open Graph meta tags

### Phase 3 - Auth, Referrals & Email ✅
- **Admin Authentication**: Password protection ("shutterscore2026")
  - Login page with password input
  - Session stored in sessionStorage (Basic auth)
  - Logout functionality
- **Referral Tracking System**:
  - Each user gets unique 8-char referral code
  - Referral links: `?ref=CODE`
  - Referrer's count increments when someone signs up with their code
  - Admin can see: Referral Code, Referred By, Referral Count
  - Total Referrals stat in dashboard
- **Email Notifications** (Resend via Emergent LLM key):
  - Welcome email sent on signup
  - Includes referral code and link
  - Dark themed HTML email template

## API Endpoints
- `POST /api/waitlist` - Join waitlist (accepts `ref` param for referrals)
- `GET /api/waitlist/count` - Get total count
- `POST /api/admin/login` - Admin login
- `GET /api/admin/verify` - Verify admin session
- `GET /api/admin/waitlist` - List entries (protected)
- `GET /api/admin/waitlist/stats` - Statistics including total_referrals (protected)
- `GET /api/admin/waitlist/export` - Export CSV (protected)
- `DELETE /api/admin/waitlist/{id}` - Remove entry (protected)

## Environment Variables
- `ADMIN_PASSWORD` - Admin panel password
- `RESEND_API_KEY` - Emergent LLM key for email
- `SENDER_EMAIL` - Email sender address

## Prioritized Backlog

### P0 - Complete ✅
- Landing page, Admin panel, Referral tracking, Email notifications

### P1 - Next Phase
- Leaderboard page showing top referrers
- Waitlist position/rank display
- Custom email templates per milestone

### P2 - Future
- Contest creation flow
- Payment integration (Stripe)
- Judge panel system

## Tech Stack
- Frontend: React, Tailwind CSS, Framer Motion, Shadcn/UI
- Backend: FastAPI, MongoDB, Resend
- Auth: Simple password (HTTP Basic)

## Next Tasks
1. Create public leaderboard showing top referrers
2. Show user's waitlist position after signup
3. Milestone emails (e.g., "You're in top 100!")
