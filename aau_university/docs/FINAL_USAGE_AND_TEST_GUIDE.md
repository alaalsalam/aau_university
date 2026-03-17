# Final Usage and Test Guide

## Purpose

This guide covers final content management, translation management, portal test accounts, and the verification flow for the AAU University project.

## 1) Apply final seed data

Run the final seed once per site to provision:

- baseline English translations
- contact address and map fields
- additional faculty showcase records
- ready-to-use content manager, student, and doctor test accounts

```bash
cd /home/frappe/frappe-bench
bench --site edu.yemenfrappe.com execute aau_university.setup.final_project_readiness_seed.run
```

## 2) Core management URLs

- Backend desk: `https://edu.yemenfrappe.com/app`
- AAU workspace: `https://edu.yemenfrappe.com/app/aau`
- Frontend site: `https://auusite.yemenfrappe.com`

## 3) Content editing flow

Use the `AAU` workspace for day-to-day content updates.

Primary screens:

- `Home Page`
- `About University`
- `Website Settings`
- `AAU Page`
- `News`
- `Events`
- `Colleges`
- `Academic Programs`
- `Faculty Members`
- `Centers`
- `Offers`
- `Partners`
- `Projects`
- `Research and Publications`
- `Blog Posts`

Editing rule:

- Arabic content is the source of truth.
- English output is generated from `Translation`.
- UI labels, button styles, and layout remain frontend-owned.

## 4) Translation workflow

Open:

- `https://edu.yemenfrappe.com/app/translation`

For each translation entry:

1. Set `Language = en`
2. Paste the exact Arabic source text in `Source Text`
3. Add the English value in `Translated Text`
4. Save

The final seed already provisions a baseline translation set for the main public sections. Additional content can be translated incrementally using the same screen.

## 5) Contact and address management

Open:

- `Website Settings`

Manage:

- page badge and title
- contact page description
- contact email and phone
- `address_ar`
- `map_location`
- social links

## 6) Portal test flow

Use the seeded portal accounts to verify end-to-end scenarios:

### Student tests

- login
- profile view
- courses
- schedule
- grades
- finance
- materials
- notifications
- conversations

### Doctor tests

- login
- profile view
- courses
- students
- schedule
- finance
- materials
- announcements
- conversations

### Content manager tests

- login to desk
- open `AAU` workspace
- edit `Home Page`
- edit `News`
- edit `Website Settings`
- verify frontend changes

## 7) Verification commands

### Content readiness

```bash
bench --site edu.yemenfrappe.com execute aau_university.api.v1.utils.content_readiness_report
```

### Portal smoke test

```bash
bench --site edu.yemenfrappe.com execute aau_university.api.v1.utils.portal_smoke_test
```

### Admin workflow smoke test

```bash
bench --site edu.yemenfrappe.com execute aau_university.api.v1.utils.admin_workflow_smoke_test
```

### Launch readiness E2E

```bash
bench --site edu.yemenfrappe.com execute aau_university.api.v1.utils.launch_readiness_e2e_check
```

## 8) Frontend verification

```bash
cd /home/frappe/frappe-bench/apps/aau_university/AAU-16.24
npm run build
curl -I http://127.0.0.1:3000/api/health
curl -I https://auusite.yemenfrappe.com/api/health
```

## 9) Final acceptance checklist

- Public pages open without fallback or mock data
- CMS content updates reflect on frontend
- English output resolves from `Translation`
- Student and doctor accounts can log in and access their dashboards
- Content manager can access `AAU` workspace and edit core sections
- Readiness and smoke tests pass without blockers
