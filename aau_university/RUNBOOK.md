# AAU Stabilization Runbook

## 1) Apply changes
```bash
cd ~/frappe-bench
bench --site edu.yemenfrappe.com migrate
bench --site edu.yemenfrappe.com clear-cache
bench --site edu.yemenfrappe.com clear-website-cache
# If API workers are managed by supervisor/systemd, restart them to load Python changes:
# sudo supervisorctl restart all
# or: sudo systemctl restart frappe-bench-web frappe-bench-workers
```

## 2) Run audit/fixer manually
```bash
bench --site edu.yemenfrappe.com console
from aau_university.setup.aau_screen_audit_fix import run
run(update_existing=True, dry_run=True)
run(update_existing=True, dry_run=False)
```

## 3) Verify no legacy screens + module normalization
```bash
bench --site edu.yemenfrappe.com console
import frappe
legacy = ["About Page","Contact Page","Academic Calendar","Course Section","Course Withdrawal Request","Grade Review Request","Final Result"]
print(frappe.get_all("DocType", filters={"name": ["in", legacy]}, fields=["name","module"]))
print(frappe.get_all("Workspace", filters={"name": ["in", ["AAU","AAU Content Hub"]]}, fields=["name","is_hidden"]))
```

## 4) Verify website API reads structured fields (not JSON blob by default)
```bash
bench --site edu.yemenfrappe.com execute aau_university.api.v1.public.get_home
# Ensure site_config does not enable JSON fallback:
# "AAU_ENABLE_JSON_FALLBACK": 0
```

## 5) Patch rerun (if required)
```bash
bench --site edu.yemenfrappe.com console
import frappe
frappe.db.delete("Patch Log", {"patch": "aau_university.patches.v1_0_run_screen_audit_fix"})
frappe.db.delete("Patch Log", {"patch": "aau_university.patches.v1_1_migrate_json_content_to_fields"})
frappe.db.delete("Patch Log", {"patch": "aau_university.patches.v1_2_cleanup_unused_screens_and_workspace"})
frappe.db.commit()
```

## 6) Verify Phase-1 CMS DocTypes and modules
```bash
bench --site edu.yemenfrappe.com console
import frappe
targets = ["Centers","Offers","Projects","Team Members","Blog Posts","FAQ","Contact Us Messages","Join Requests"]
print(frappe.get_all("DocType", filters={"name": ["in", targets]}, fields=["name","module"], order_by="name asc"))
print(frappe.get_all("DocType", filters={"name": ["in", targets], "module": ["!=", "AAU"]}, fields=["name","module"]))
```

## 7) Verify fixed public APIs
```bash
curl -sS https://edu.yemenfrappe.com/api/centers
curl -sS https://edu.yemenfrappe.com/api/offers
curl -sS https://edu.yemenfrappe.com/api/projects
curl -sS https://edu.yemenfrappe.com/api/team
curl -sS https://edu.yemenfrappe.com/api/blog
curl -sS https://edu.yemenfrappe.com/api/faq
curl -sS https://edu.yemenfrappe.com/api/aau/profile
```

## 8) RBAC verification (publish/order fields protected in backend)
```bash
bench --site edu.yemenfrappe.com execute aau_university.api.v1.utils.rbac_smoke_test
```

```bash
bench --site edu.yemenfrappe.com console
from aau_university.api.v1.utils import rbac_smoke_test
print(rbac_smoke_test())  # auto-detect users
# or explicit users:
# print(rbac_smoke_test(content_user="content.manager@edu.yemenfrappe.com", super_admin_user="Administrator"))
```

## Renamed DocTypes (valid technical names)
- `University Vision and Mission` (was `University Vision & Mission`)
- `Research and Publications` (was `Research & Publications`)
