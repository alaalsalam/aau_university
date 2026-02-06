# AAU API Runbook

## Install/apply
```
bench --site <site> install-app aau_university
bench --site <site> migrate
```

## Migrations
```
bench --site <site> migrate
```

## Smoke test
```
bench --site <site> console
from aau_university.api.v1.utils import smoke_test
smoke_test()
```

## Audit fixer verification
```
bench --site <site> console
from aau_university.setup.aau_screen_audit_fix import run
report = run(update_existing=True, dry_run=True)
report.get("missing_doctypes")
frappe.get_all("DocType", filters={"module": ["!=", "AAU"]}, fields=["name", "module"])
```

## API curl samples (10 endpoints)
```
curl -s https://<host>/api/news
curl -s https://<host>/api/news/featured
curl -s https://<host>/api/news/latest?limit=5
curl -s https://<host>/api/events
curl -s https://<host>/api/colleges
curl -s https://<host>/api/programs
curl -s https://<host>/api/faculty
curl -s https://<host>/api/projects
curl -s https://<host>/api/blog
curl -s https://<host>/api/search?q=engineering
```

## Guest access (safe enablement)
```
# Guest access is controlled per endpoint via allow_guest=True decorators.
# Review roles in api/v1/registry.py and adjust ADMIN_ROLES if needed.
```
