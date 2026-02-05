# Shutterscore - Product Requirements Document

## Original Problem Statement
Build a landing page for Shutterscore - a photo contest platform with seamless payments, fair judging, and automated donations to causes. Features include:
- Hero section with gradient background and CTAs
- Features grid (6 features)
- Impact stats section
- Waitlist email signup form
- Footer

## User Personas
- **Photography Enthusiasts**: Want to participate in contests and showcase their work
- **Contest Organizers**: Need tools to run fair, transparent photo competitions
- **Brands**: Looking to engage communities through photo contests
- **Nonprofits**: Want to benefit from charity integration

## Core Requirements (Static)
1. Stunning, premium landing page with dark theme
2. Email waitlist collection with MongoDB storage
3. Smooth scroll navigation
4. Responsive design for all devices
5. Accessible and performant

## What's Been Implemented (Feb 2026)
- [x] Hero section with dramatic landscape background, elegant Cormorant Garamond typography
- [x] "Get Early Access" and "Explore Features" CTAs with smooth scroll
- [x] Features bento grid: Seamless Payments, Fair Judging, Charity Integration, Beautiful Galleries, Real-time Dashboard, Smart Notifications
- [x] Impact stats section (5-50%, 100+, Instant)
- [x] Waitlist form with backend API (/api/waitlist)
- [x] Email validation (client + server side)
- [x] Duplicate email handling
- [x] Toast notifications (sonner)
- [x] Framer Motion animations
- [x] Dark premium theme with glass-morphism effects

## API Endpoints
- `POST /api/waitlist` - Join waitlist (email validation, duplicate check)
- `GET /api/waitlist/count` - Get total waitlist count

## Prioritized Backlog

### P0 - MVP Complete ✅
- Landing page with all sections
- Waitlist functionality

### P1 - Next Phase
- Email notification on signup (SendGrid/Resend)
- Admin dashboard to view waitlist entries
- Social sharing meta tags

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
1. Add email notification when someone joins waitlist
2. Create admin panel to view/export waitlist
3. Add social meta tags for sharing
