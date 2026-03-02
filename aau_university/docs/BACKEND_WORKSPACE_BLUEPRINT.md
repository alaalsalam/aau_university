# AAU Backend + Workspace Blueprint

## Backend (API v1) واضح ومنظم

### Domain split
- `api/v1/content.py`: محتوى الموقع (news/events/offers/pages/team/blog/centers/partners/projects/campus-life)
- `api/v1/academic.py`: الأكاديمي (colleges/programs/faculty/study plans)
- `api/v1/cms.py`: وسائط وإعدادات
- `api/v1/public.py`: public website endpoints
- `api/v1/access.py`: صلاحيات وإدارة المستخدمين
- `api/v1/resources.py`: CRUD layer + RBAC + payload allowlist
- `api/v1/routes.py`: تسجيل المسارات

### Security baseline
- RBAC entity-level مفعل.
- حقول النشر/الترتيب محمية لـ Super Admin فقط.
- payload allowlist مفعل (رفض أي حقول غير معرّفة).

### Health checks
```bash
bench --site edu.yemenfrappe.com execute aau_university.api.v1.utils.rbac_smoke_test
bench --site edu.yemenfrappe.com execute aau_university.api.v1.utils.payload_validation_smoke_test
bench --site edu.yemenfrappe.com execute aau_university.api.v1.utils.launch_readiness_e2e_check
```

## Workspace (Desk) واضح للمحتوى

### Workspace primary
- `AAU` هو الـ workspace المعتمد (Control Center).
- `AAU Content Hub` تم تحويله Legacy ومخفي لتقليل الازدواجية.

### Cards داخل `AAU`
- Core Content
- Academic
- Marketing
- Engagement
- Settings & Navigation

### Validate workspace
```bash
bench --site edu.yemenfrappe.com migrate
bench --site edu.yemenfrappe.com clear-cache
bench --site edu.yemenfrappe.com clear-website-cache
```
