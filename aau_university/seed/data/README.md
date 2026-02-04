# Home Seed Data

<!-- WHY+WHAT: We version extracted AAU-16.24 mock home content here so any Frappe site can be bootstrapped quickly and consistently from git-tracked JSON. -->

## Why
- Bootstrap public home content quickly on any new or existing site.
- Keep seed content deterministic and reviewable in git history.

## What
- `home_content.json` is extracted from frontend mock sources in `AAU-16.24/services/data`.
- `news.json` is extracted from `AAU-16.24/services/data/news.service.mock.ts` for news list/detail seeding.
- `events.json` is extracted from `AAU-16.24/services/data/events.service.mock.ts` for events list/detail seeding.
- `colleges.json` is extracted from `AAU-16.24/services/data/colleges.service.mock.ts` for colleges detail (with embedded programs) seeding.
- `pages.json` is extracted from static frontend pages (`about`, `admission`, `contact`) for AAU Page content seeding.
- `menus.json` is extracted from frontend header/footer navigation links for main/footer/social menu seeding.
- `home_content.json` keeps the `/api/aau/home` contract keys: `news`, `events`, `colleges`, `faqs`.
- `news.json` is consumed by `aau_university.utils.seed_news.seed_news` for idempotent upserts by `slug`.
- `events.json` is consumed by `aau_university.utils.seed_events.seed_events` for idempotent upserts by `slug`.
- `colleges.json` is consumed by `aau_university.utils.seed_colleges.seed_colleges` for idempotent upserts by `slug`.
- `pages.json` is consumed by `aau_university.utils.seed_pages.seed_pages` for idempotent upserts by `slug`.
- `menus.json` is consumed by `aau_university.utils.seed_menus.seed_menus` for idempotent upserts by `key`.
