# Home Seed Data

<!-- WHY+WHAT: We version extracted AAU-16.24 mock home content here so any Frappe site can be bootstrapped quickly and consistently from git-tracked JSON. -->

## Why
- Bootstrap public home content quickly on any new or existing site.
- Keep seed content deterministic and reviewable in git history.

## What
- `home_content.json` is extracted from frontend mock sources in `AAU-16.24/services/data`.
- It contains four top-level keys aligned with `/api/aau/home`: `news`, `events`, `colleges`, `faqs`.
