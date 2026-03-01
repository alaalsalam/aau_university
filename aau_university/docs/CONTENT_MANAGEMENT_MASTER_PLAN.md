# AAU Content Management Master Plan

## 1) Current State (Deep Audit Summary)

### 1.1 Canonical web delivery path
- Public website content is served mainly through:
  - `GET /api/aau/home`
  - `GET /api/aau/news`, `GET /api/aau/news/:slug`
  - `GET /api/aau/events`, `GET /api/aau/events/:slug`
  - `GET /api/aau/colleges`, `GET /api/aau/colleges/:slug`
  - `GET /api/aau/page/:slug`
  - `GET /api/aau/menu/:key`
- Core implementation file:
  - `aau_university/api/v1/public.py`

### 1.2 Legacy JSON dependency found
- `Home Page.home_sections_json`
- `Colleges.programs_json`
- Both are legacy convenience fields and not suitable as the primary CMS source for production.

### 1.3 Active content DocTypes currently aligned with website
- `Home Page`
- `News`
- `Events` (runtime-created in many sites)
- `Colleges`
- `Academic Programs`
- `AAU Page` / `Static Page`
- `AAU Menu`
- `Website Settings`
- `Contact Us Messages`
- `Join Requests`

### 1.4 Candidate legacy/unused screens (no active website/API references)
- `About Page`
- `Contact Page`
- `Academic Calendar`
- `Course Section`
- `Course Withdrawal Request`
- `Grade Review Request`
- `Final Result`
- `Dashboard Metrics` (optional keep if management wants dashboard view)

These are candidates for cleanup, not hard-deleted immediately.

## 2) Target Content Architecture

### 2.1 Data source policy
- Every section must read from dedicated structured fields/records.
- JSON blob fields are fallback-only during migration window.
- No section should rely on a single JSON field as primary source.

### 2.2 Content ownership map
- Home Hero/About/Stats: `Home Page` fields.
- News: `News` fields (`title_ar`, `title_en`, `description_ar`, `description_en`, `content_ar`, `content_en`, etc.).
- Events: `Events` fields (`title_ar`, `title_en`, `description_ar`, `description_en`, etc.).
- Colleges: `Colleges` fields.
- Programs per college: linked `Academic Programs` by `college`.
- Menus: `AAU Menu` + child items.
- Static pages: `AAU Page` (or `Static Page` until unified).

## 3) Execution Plan (Phased)

### Phase A (Completed)
1. Migrate legacy JSON values to structured fields/records.
2. Switch API reads to structured fields first.
3. Keep JSON fallback flag `AAU_ENABLE_JSON_FALLBACK` (default OFF).

### Phase B (Completed)
1. Normalize serializers to strict bilingual mapping with deterministic defaults.
2. Add validation rules for mandatory website fields in key DocTypes.
3. Add content QA checks (missing slug, empty AR/EN text, unpublished required records).

### Phase C (In Progress)
1. Archive candidate unused screens for one release cycle.
2. Remove them after sign-off from content/business owners.
3. Keep only website-relevant DocTypes in the primary workspace.

### Phase D (Professional CMS operations)
1. Add role model for content team:
   - `AAU Content Manager`
   - `AAU Content Editor`
   - `AAU Reviewer`
2. Add workflow for key content (Draft -> Review -> Published).
3. Add audit report page for content completeness.

## 4) Safe Deletion Procedure for Unused Screens

1. Mark candidate DocTypes as hidden from workspace first.
2. Export backup of records per candidate DocType.
3. Keep one release cycle in archive state.
4. Delete only after sign-off.

## 5) Workspace Design Standard

Main cards:
1. Core Website Content
2. Academic Content
3. Navigation & Pages
4. Audience Interaction
5. Settings & Governance

## 6) Definition of Done

- All public APIs read from structured fields/links (not JSON blobs).
- Content team can manage full site from one clear workspace.
- Legacy/unused screens are archived or removed with traceability.
- QA report shows no critical missing content for live pages.

## 7) Implemented Artifacts

- JSON-to-fields migration patch:
  - `aau_university.patches.v1_1_migrate_json_content_to_fields`
- Cleanup + workspace activation patch:
  - `aau_university.patches.v1_2_cleanup_unused_screens_and_workspace`
- New workspace:
  - `AAU Content Hub`
