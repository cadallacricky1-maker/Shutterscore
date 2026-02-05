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
3. Admin panel for waitlist management
4. Social sharing capabilities
5. Open Graph meta tags for social previews

## What's Been Implemented (Feb 2026)

### Phase 1 - MVP Landing Page ✅
- Hero section with dramatic landscape background
- Features bento grid (6 features)
- Impact stats section
- Waitlist form with validation
- Toast notifications
- Framer Motion animations

### Phase 2 - Admin & Sharing ✅
- Admin panel at `/admin` with:
  - Stats dashboard (Total, Today, This Week)
  - Waitlist entries table with search
  - CSV export functionality
  - Delete entries with confirmation
  - Pagination support
- Share with Friends modal:
  - Twitter, Facebook, LinkedIn, Email sharing
  - Copy link functionality
  - Auto-opens after successful signup
  - "You're In!" state after joining
- Open Graph meta tags:
  - og:title, og:description, og:image
  - twitter:card, twitter:image

## API Endpoints
- `POST /api/waitlist` - Join waitlist
- `GET /api/waitlist/count` - Get total count
- `GET /api/admin/waitlist` - List entries (paginated, searchable)
- `GET /api/admin/waitlist/stats` - Signup statistics
- `GET /api/admin/waitlist/export` - Export CSV
- `DELETE /api/admin/waitlist/{id}` - Remove entry

## Prioritized Backlog

### P0 - Complete ✅
- Landing page with all sections
- Waitlist functionality
- Admin panel
- Share with friends
- Open Graph meta tags

### P1 - Next Phase
- Email notifications on signup (Resend/SendGrid)
- Admin authentication (protect /admin route)
- Referral tracking system

### P2 - Future
- Contest creation flow
- Payment integration (Stripe)
- Judge panel system
- Charity API integration
- User authentication

## Tech Stack
- Frontend: React, Tailwind CSS, Framer Motion, Shadcn/UI
- Backend: FastAPI, MongoDB
- Fonts: Cormorant Garamond, Manrope

## Next Tasks
1. Add admin authentication to protect /admin route
2. Implement email notifications when someone joins
3. Add referral tracking to reward sharers
