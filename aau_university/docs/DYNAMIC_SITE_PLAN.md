# Dynamic Website Plan (AAU) — Home First

## Goal
Make the public website (starting with **Home**) fully dynamic: content is managed in Frappe DocTypes, fetched via public/guest API endpoints, and rendered by the frontend **without changing the existing AAU-16.24 UI/design** (only replacing hardcoded data sources).

## Repo / runtime context
- Frontend: `AAU-16.24/` (Next.js App Router)
- Backend app: `aau_university/` (Frappe app)
- Site: `edu.yemenfrappe.com`
- Constraints:
  - No websockets/background jobs/long-lived sessions/over-engineering.
  - Prefer `allow_guest=True` read endpoints for website content.
  - Keep payloads minimal and stable (match frontend parsing contracts).

## Current state audit (findings)

### Frontend (AAU-16.24)
- Framework: **Next.js** (App Router). Public layout: `AAU-16.24/app/(public)/layout.tsx`.
- Home entry: `AAU-16.24/app/(public)/page.tsx`.
- Home uses a single aggregated server-layer call: `AAU-16.24/services/server/home.ts` → `GET /api/aau/home`.
- Base API URL wiring:
  - `NEXT_PUBLIC_AAU_API_BASE_URL` (see `AAU-16.24/.env.example`)
  - Resolved by server fetch layer: `AAU-16.24/services/server/aauApi.ts`
- Home sections wired from API payload already:
  - hero/stat/about/news/events/colleges/faqs: `AAU-16.24/components/HomeContent.tsx`
- Remaining "not fully dynamic" pieces on Home:
  - Hero background image is hardcoded (ignores API `hero.image`): `AAU-16.24/components/HeroSection.tsx`
  - About section image is hardcoded (ignores API `about.image`): `AAU-16.24/components/AboutSection.tsx`

### Backend (aau_university)
- Routes are registered onto Frappe `/api/*` router by `aau_university/api/v1/routes.py` via `before_request` hook (`aau_university/hooks.py`).
- Public/guest website endpoints used by the frontend:
  - `GET /api/aau/home` (aggregated home)
  - `GET /api/aau/menu/:key` (header/footer/social menus)
  - `GET /api/aau/page/:slug` (static pages)
  - `GET /api/aau/news` + `/api/aau/news/:slug` (news list/detail)
  - `GET /api/aau/events` + `/api/aau/events/:slug` (events list/detail)
  - `GET /api/aau/colleges` + `/api/aau/colleges/:slug` (colleges list/detail)
- Some “domain” endpoints (e.g. `/api/faculty`, `/api/partners`, `/api/campus-life`) were returning **500** due to a backend resource-layer bug (see issue list).
- Some endpoints return **404** because referenced DocTypes don’t exist in the site DB (intentional to defer unless those pages are needed now).

## Issue list (root causes)
1) **500 INTERNAL SERVER ERROR on multiple `/api/*` endpoints** (faculty/partners/campus-life/colleges/news lists)
   - Root cause: `list_entities()` selected non-DB layout/table fields (Section Break / Column Break / Tab Break / etc), producing SQL “Unknown column …”.
   - Code: `aau_university/api/v1/resources.py`

2) **404 for some content endpoints** because the corresponding DocTypes are missing in the site DB
   - Examples: `/api/centers`, `/api/offers`, `/api/blog`, `/api/projects`, `/api/team`
   - Deferred by design unless those pages must go live now.

3) **Home endpoint payload includes extra keys** for list sections
   - Root cause: `_normalize_home_record()` returned camelCased raw rows (spills doctype columns not needed by UI).
   - Code: `aau_university/api/v1/public.py`

4) **Home still uses hardcoded images** for hero/about
   - Root cause: frontend components use imported assets instead of payload-driven images.

## Execution phases (minimal + pragmatic)

### Phase 1 — Home 100% dynamic via one endpoint
- Backend: keep `GET /api/aau/home` and make its payload minimal + aligned with frontend Home parsers.
- Frontend: keep UI unchanged; switch hero/about images to use `hero.image` and `about.image` when provided (safe local paths).

### Phase 2 — Fix secondary public pages only if broken
- News list/detail, Events list/detail (already wired). Fix only mapping/serializer bugs, no new pagination/filters.

### Phase 3 — Cleanup / stabilization
- Add/sync missing DocTypes only when needed for non-empty pages (Centers/Offers/Team/Projects/Blog/FAQs).
- Keep a short runbook for migrate/seed/verify.

## Public API contracts (Home)
Endpoint: `GET /api/aau/home` (guest/public).

Payload (inside the standard AAU API envelope):
- `hero`: `badgeAr, badgeEn, titlePrimaryAr, titlePrimaryEn, titleSecondaryAr, titleSecondaryEn, descriptionAr, descriptionEn, applyTextAr, applyTextEn, applyLink, exploreTextAr, exploreTextEn, exploreLink, discoverTextAr, discoverTextEn, image?`
- `stats`: `[{ key, number, labelAr, labelEn, icon }]`
- `about`: `titleAr, titleEn, descriptionAr, descriptionEn, image?, values[], president{}`
- `news[]`: `id, slug, titleAr, titleEn, descriptionAr, descriptionEn, image?, date?, tags[], views`
- `events[]`: `id, slug, titleAr, titleEn, descriptionAr, descriptionEn, contentAr?, contentEn?, date?, endDate?, locationAr?, locationEn?, organizerAr?, organizerEn?, category, status, registrationRequired, registrationLink?, image?, tags[]`
- `colleges[]`: `id, slug, nameAr, nameEn, descriptionAr, descriptionEn, image?, icon?, programs[]` (minimal program shape)
- `faqs[]`: `id, questionAr, questionEn, answerAr, answerEn, category?`
- `meta`: `{ generated_at, source }`

## Verification commands (quick smoke)

### Backend (HTTP)
```bash
curl -sS https://edu.yemenfrappe.com/api/aau/home | head -c 800
curl -sS https://edu.yemenfrappe.com/api/aau/menu/main | head -c 800
curl -i 'https://edu.yemenfrappe.com/api/faculty?limit=1&page=1'
curl -i 'https://edu.yemenfrappe.com/api/partners?limit=1&page=1'
curl -i 'https://edu.yemenfrappe.com/api/campus-life?limit=1&page=1'
curl -i 'https://edu.yemenfrappe.com/api/colleges?limit=1&page=1'
```

### Frontend (build)
```bash
cd /home/frappe/frappe-bench/apps/aau_university/AAU-16.24
export NEXT_PUBLIC_AAU_API_BASE_URL=https://edu.yemenfrappe.com
npm run build
```

## Rollout notes
```bash
cd /home/frappe/frappe-bench
bench --site edu.yemenfrappe.com migrate
bench --site edu.yemenfrappe.com execute aau_university.utils.seed_home.seed_home
bench --site edu.yemenfrappe.com execute aau_university.utils.seed_menus.seed_menus
bench restart
```

