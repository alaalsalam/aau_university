# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import re
import uuid
from functools import wraps
from typing import Any, Iterable

import frappe
from frappe import _
from frappe.utils import now


class ApiError(Exception):
    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = 400,
        details: Any | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details


def api_endpoint(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
            meta = None
            status_code = 200
            if isinstance(result, dict) and result.pop("__meta__", False):
                meta = result.get("meta")
                result = result.get("data")
            elif isinstance(result, tuple):
                if len(result) == 2:
                    result, status_code = result
                elif len(result) == 3:
                    result, meta, status_code = result
            return ok_response(result, meta=meta, status_code=status_code)
        except ApiError as exc:
            return error_response(
                exc.code,
                exc.message,
                details=exc.details,
                status_code=exc.status_code,
            )
        except frappe.PermissionError:
            return error_response("FORBIDDEN", _("Not permitted"), status_code=403)
        except frappe.DoesNotExistError:
            return error_response("NOT_FOUND", _("Not found"), status_code=404)
        except frappe.ValidationError as exc:
            return error_response("VALIDATION_ERROR", str(exc), status_code=400)
        except Exception:
            tb = frappe.get_traceback()
            frappe.logger("aau_university").error("[AAU API] UNHANDLED\n" + tb)
            return error_response("SERVER_ERROR", _("Unexpected server error"), status_code=500)

    return wrapper


def ok_response(data: Any = None, meta: dict | None = None, status_code: int = 200) -> dict:
    frappe.response.http_status_code = status_code
    return {"ok": True, "data": data, "error": None, "meta": meta or {}}


def error_response(
    code: str,
    message: str,
    details: Any | None = None,
    status_code: int = 400,
) -> dict:
    frappe.response.http_status_code = status_code
    return {"ok": False, "data": None, "error": {"code": code, "message": message, "details": details}, "meta": {}}


def require_auth():
    if frappe.session.user == "Guest":
        raise ApiError("UNAUTHORIZED", _("Authentication required"), status_code=401)


def require_roles(roles: Iterable[str]):
    require_auth()
    user_roles = set(frappe.get_roles(frappe.session.user))
    if not any(role in user_roles for role in roles):
        raise ApiError("FORBIDDEN", _("Insufficient permissions"), status_code=403)


def to_snake(value: str) -> str:
    value = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", value)
    value = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", value)
    return value.replace("-", "_").lower()


def to_camel(value: str) -> str:
    parts = value.split("_")
    return parts[0] + "".join(word.capitalize() for word in parts[1:])


def normalize_payload(data: dict, fieldnames: Iterable[str]) -> dict:
    normalized = {}
    allowed = set(fieldnames)
    for key, value in (data or {}).items():
        candidate = key if key in allowed else to_snake(key)
        if candidate in allowed:
            normalized[candidate] = value
    return normalized


def ensure_uuid(value: str | None = None) -> str:
    if value:
        return value
    return str(uuid.uuid4())


def now_ts() -> str:
    return now()


def parse_json_list(value: Any) -> list:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except Exception:
            return []
        if isinstance(parsed, list):
            return parsed
    return []


def parse_pagination():
    page = int(frappe.form_dict.get("page") or 1)
    limit = frappe.form_dict.get("limit") or frappe.form_dict.get("page_size") or 20
    limit = int(limit)
    offset = (page - 1) * limit
    return {"page": page, "limit": limit, "offset": offset}


def parse_sort(default: str = "modified desc") -> str:
    sort = frappe.form_dict.get("sort") or frappe.form_dict.get("sort_by")
    order = frappe.form_dict.get("order") or frappe.form_dict.get("sort_order")
    if sort:
        order = (order or "desc").lower()
        direction = "desc" if order not in ("asc", "desc") else order
        return f"{sort} {direction}"
    return default


def build_filters(allowed_fields: Iterable[str]) -> list:
    filters = []
    allowed = set(allowed_fields)
    for key, value in frappe.form_dict.items():
        if key in ("page", "limit", "page_size", "offset", "sort", "sort_by", "order", "sort_order", "q"):
            continue
        if key.endswith("_from") and key[:-5] in allowed:
            filters.append([key[:-5], ">=", value])
            continue
        if key.endswith("_to") and key[:-3] in allowed:
            filters.append([key[:-3], "<=", value])
            continue
        if key in allowed:
            filters.append([key, "=", value])
    return filters


def serialize_doc(doc: dict, table_fields: dict[str, str]) -> dict:
    output = {}
    for key, value in doc.items():
        if key in ("doctype", "name", "owner", "creation", "modified", "modified_by"):
            continue
        if key in table_fields:
            output[to_camel(key)] = serialize_child_rows(value, table_fields[key])
        else:
            output[to_camel(key)] = value
    return output


def serialize_child_rows(rows: list, value_field: str) -> list:
    values = []
    for row in rows or []:
        if isinstance(row, dict):
            if value_field in row:
                values.append(row[value_field])
        else:
            if hasattr(row, value_field):
                values.append(getattr(row, value_field))
    return values


def deserialize_child_rows(values: list, doctype: str, value_field: str) -> list:
    return [{"doctype": doctype, value_field: value} for value in values or []]


def get_table_field_map(meta) -> dict[str, str]:
    mapping = {}
    for field in meta.get_table_fields():
        child_meta = frappe.get_meta(field.options)
        value_field = None
        for df in child_meta.fields:
            if df.fieldname == "value":
                value_field = "value"
                break
        if value_field:
            mapping[field.fieldname] = value_field
    return mapping


def smoke_test() -> dict:
    """Basic smoke test for AAU APIs (internal calls)."""
    frappe.form_dict = frappe._dict({})
    from .resources import list_entities, get_entity

    results = {
        "news": list_entities("news", public=True)["data"],
        "events": list_entities("events", public=True)["data"],
        "colleges": list_entities("colleges", public=True)["data"],
    }
    if results["news"]:
        first_news = results["news"][0] or {}
        identifier = first_news.get("id")
        lookup_by = "id"
        if not identifier and first_news.get("slug"):
            identifier = first_news.get("slug")
            lookup_by = "slug"
        if identifier:
            results["news_detail"] = get_entity("news", identifier, by=lookup_by, public=True)
        else:
            results["news_detail"] = None
    return results


def _find_user_with_roles(required_roles: set[str], exclude_roles: set[str] | None = None) -> str | None:
    exclude_roles = exclude_roles or set()
    role_rows = frappe.get_all(
        "Has Role",
        filters={"role": ["in", list(required_roles)]},
        fields=["parent"],
        distinct=True,
        ignore_permissions=True,
    )
    for row in role_rows:
        user = row.get("parent")
        if not user or user in {"Guest", "Administrator"}:
            continue
        if not frappe.db.get_value("User", user, "enabled"):
            continue
        user_roles = set(frappe.get_roles(user))
        if not user_roles.intersection(required_roles):
            continue
        if user_roles.intersection(exclude_roles):
            continue
        return user
    return None


def rbac_smoke_test(content_user: str | None = None, super_admin_user: str | None = None) -> dict:
    """RBAC smoke test for publish/order field restrictions (no DB writes)."""
    from .registry import CONTENT_MANAGER_ROLES, ENTITY_SUPERADMIN_ONLY_FIELDS, SUPER_ADMIN_ROLES
    from .resources import _enforce_super_admin_field_restrictions

    original_user = frappe.session.user
    checks: list[dict] = []
    skipped: list[str] = []

    if not super_admin_user:
        super_admin_user = _find_user_with_roles(SUPER_ADMIN_ROLES) or "Administrator"
    if not content_user:
        content_user = _find_user_with_roles(CONTENT_MANAGER_ROLES, exclude_roles=SUPER_ADMIN_ROLES)

    def run_case(user: str, entity_key: str, payload: dict, expect_blocked: bool, case: str):
        frappe.set_user(user)
        blocked = False
        try:
            _enforce_super_admin_field_restrictions(entity_key, payload)
        except ApiError as exc:
            if exc.code == "FORBIDDEN":
                blocked = True
            else:
                raise
        checks.append(
            {
                "case": case,
                "user": user,
                "entity": entity_key,
                "payloadKeys": sorted(payload.keys()),
                "expectedBlocked": expect_blocked,
                "blocked": blocked,
                "passed": blocked == expect_blocked,
            }
        )

    try:
        if content_user:
            for entity_key, fields in ENTITY_SUPERADMIN_ONLY_FIELDS.items():
                restricted_key = sorted(fields)[0]
                run_case(content_user, entity_key, {restricted_key: "x"}, expect_blocked=True, case="content_restricted")
                run_case(content_user, entity_key, {"titleAr": "Smoke Test"}, expect_blocked=False, case="content_allowed")
        else:
            skipped.append("No enabled content-manager user found for restriction checks")

        if super_admin_user:
            for entity_key, fields in ENTITY_SUPERADMIN_ONLY_FIELDS.items():
                restricted_key = sorted(fields)[0]
                run_case(super_admin_user, entity_key, {restricted_key: "x"}, expect_blocked=False, case="superadmin_allowed")
        else:
            skipped.append("No enabled super-admin user found for restriction checks")
    finally:
        frappe.set_user(original_user)

    ok = all(row.get("passed") for row in checks) and not skipped
    return {
        "ok": ok,
        "users": {
            "contentManagerUser": content_user,
            "superAdminUser": super_admin_user,
        },
        "summary": {
            "totalChecks": len(checks),
            "passedChecks": sum(1 for row in checks if row.get("passed")),
            "failedChecks": sum(1 for row in checks if not row.get("passed")),
            "skipped": skipped,
        },
        "checks": checks,
    }


def payload_validation_smoke_test() -> dict:
    """Validate strict payload allowlist behavior for entity writes."""
    from .resources import _assert_payload_keys, _get_entity_config, _get_payload_fieldnames, _resolve_doctype

    entity_key = "news"
    config = _get_entity_config(entity_key)
    doctype = _resolve_doctype(config)
    payload_fieldnames = _get_payload_fieldnames(doctype)

    checks = []

    try:
        _assert_payload_keys(entity_key, {"titleAr": "x", "descriptionEn": "y"}, payload_fieldnames)
        checks.append({"case": "camelCase_allowed", "passed": True})
    except ApiError:
        checks.append({"case": "camelCase_allowed", "passed": False})

    unknown_blocked = False
    details = None
    try:
        _assert_payload_keys(entity_key, {"titleAr": "x", "unknownFieldZZ": "bad"}, payload_fieldnames)
    except ApiError as exc:
        unknown_blocked = exc.code == "VALIDATION_ERROR"
        details = exc.details

    checks.append(
        {
            "case": "unknown_field_blocked",
            "passed": unknown_blocked,
            "details": details,
        }
    )

    return {
        "ok": all(item.get("passed") for item in checks),
        "entity": entity_key,
        "checks": checks,
    }


def _call_api_method(method, *args, form_dict: dict | None = None, **kwargs):
    original_form_dict = getattr(frappe.local, "form_dict", None)
    try:
        frappe.form_dict = frappe._dict(form_dict or {})
        result = method(*args, **kwargs)
    finally:
        frappe.form_dict = original_form_dict if original_form_dict is not None else frappe._dict({})

    if isinstance(result, dict) and "ok" in result:
        if not result.get("ok"):
            error = result.get("error") or {}
            raise ApiError(
                code=error.get("code") or "SERVER_ERROR",
                message=error.get("message") or "API method failed",
                details=error.get("details"),
                status_code=400,
            )
        return result.get("data")
    return result


def portal_smoke_test(student_user: str | None = None, doctor_user: str | None = None) -> dict:
    """Read-only smoke test for student/doctor portal endpoints."""
    from . import portal

    original_user = frappe.session.user
    checks: list[dict] = []
    skipped: list[str] = []

    if not doctor_user:
        role_rows = frappe.get_all(
            "Has Role",
            filters={"role": ["in", ["Instructor", "Education Manager", "System Manager", "AAU Admin", "AUU Admin"]]},
            fields=["parent"],
            distinct=True,
            ignore_permissions=True,
        )
        candidates = [row.get("parent") for row in role_rows if row.get("parent")]
        for candidate in candidates:
            if candidate in {"Guest"}:
                continue
            if not frappe.db.get_value("User", candidate, "enabled"):
                continue
            try:
                frappe.set_user(candidate)
                _call_api_method(portal.list_doctor_courses)
                doctor_user = candidate
                break
            except Exception:
                continue

    if not student_user and frappe.db.exists("DocType", "Student"):
        student_rows = frappe.get_all(
            "Student",
            filters={"user": ["is", "set"]},
            fields=["user"],
            order_by="modified desc",
            ignore_permissions=True,
            limit_page_length=50,
        )
        for row in student_rows:
            user = row.get("user")
            if user and frappe.db.get_value("User", user, "enabled"):
                student_user = user
                break

    def run_case(user: str, name: str, method, form_dict: dict | None = None):
        frappe.set_user(user)
        data = _call_api_method(method, form_dict=form_dict)
        size = len(data) if isinstance(data, list) else None
        checks.append({"user": user, "case": name, "passed": True, "size": size})

    try:
        if doctor_user:
            run_case(doctor_user, "doctor.profile", portal.get_doctor_profile)
            run_case(doctor_user, "doctor.courses", portal.list_doctor_courses)
            run_case(doctor_user, "doctor.students", portal.list_doctor_students)
            run_case(doctor_user, "doctor.schedule", portal.list_doctor_schedule)
            run_case(doctor_user, "doctor.finance", portal.get_doctor_finance)
            run_case(doctor_user, "doctor.announcements", portal.list_doctor_announcements)
            run_case(doctor_user, "doctor.materials", portal.list_doctor_materials)
            run_case(doctor_user, "doctor.messages", portal.list_doctor_messages)
            run_case(doctor_user, "doctor.conversations", portal.list_conversations, form_dict={"view": "doctor"})
            run_case(doctor_user, "doctor.unread", portal.unread_message_count)
        else:
            skipped.append("No doctor user found")

        if student_user:
            run_case(student_user, "student.profile", portal.get_student_profile)
            run_case(student_user, "student.courses", portal.list_student_courses)
            run_case(student_user, "student.schedule", portal.list_student_schedule)
            run_case(student_user, "student.grades", portal.list_student_grades)
            run_case(student_user, "student.finance", portal.get_student_finance)
            run_case(student_user, "student.materials", portal.list_student_materials)
            run_case(student_user, "student.announcements", portal.list_student_announcements)
            run_case(student_user, "student.notifications", portal.list_student_notifications)
            run_case(student_user, "student.conversations", portal.list_conversations, form_dict={"view": "student"})
            run_case(student_user, "student.unread", portal.unread_message_count)
        else:
            skipped.append("No student user found")
    finally:
        frappe.set_user(original_user)

    return {
        "ok": not skipped and all(item.get("passed") for item in checks),
        "users": {"doctor": doctor_user, "student": student_user},
        "summary": {
            "checks": len(checks),
            "passed": sum(1 for item in checks if item.get("passed")),
            "failed": sum(1 for item in checks if not item.get("passed")),
            "skipped": skipped,
        },
        "checks": checks,
    }


def account_linking_smoke_test(admin_user: str | None = None) -> dict:
    """Smoke test for account-link management endpoints."""
    from . import access

    original_user = frappe.session.user
    checks: list[dict] = []
    skipped: list[str] = []

    if not admin_user:
        admin_user = _find_user_with_roles({"System Manager", "Administrator", "AAU Admin"}) or "Administrator"

    try:
        frappe.set_user(admin_user)
        summary = _call_api_method(access.get_account_link_summary)
        checks.append(
            {
                "case": "summary",
                "passed": bool(summary and "doctor" in summary and "student" in summary),
                "doctor": (summary or {}).get("doctor"),
                "student": (summary or {}).get("student"),
            }
        )

        users = _call_api_method(access.list_linkable_users, form_dict={"page": 1, "page_size": 5}) or {}
        user_items = users.get("items") if isinstance(users, dict) else None
        checks.append(
            {
                "case": "users_list",
                "passed": isinstance(user_items, list),
                "count": len(user_items or []),
            }
        )

        doctors = _call_api_method(access.list_doctor_links, form_dict={"status": "all", "page": 1, "page_size": 5}) or {}
        doctor_items = doctors.get("items") if isinstance(doctors, dict) else None
        checks.append(
            {
                "case": "doctor_links_list",
                "passed": isinstance(doctor_items, list),
                "count": len(doctor_items or []),
            }
        )

        students = _call_api_method(access.list_student_links, form_dict={"status": "all", "page": 1, "page_size": 5}) or {}
        student_items = students.get("items") if isinstance(students, dict) else None
        checks.append(
            {
                "case": "student_links_list",
                "passed": isinstance(student_items, list),
                "count": len(student_items or []),
            }
        )
    except Exception as exc:
        skipped.append(str(exc))
    finally:
        frappe.set_user(original_user)

    return {
        "ok": not skipped and all(item.get("passed") for item in checks),
        "adminUser": admin_user,
        "summary": {
            "checks": len(checks),
            "passed": sum(1 for item in checks if item.get("passed")),
            "failed": sum(1 for item in checks if not item.get("passed")),
            "skipped": skipped,
        },
        "checks": checks,
    }


def launch_readiness_e2e_check() -> dict:
    """End-to-end launch readiness checks for backend-backed CMS/public flow."""
    from . import cms, content, public

    checks: list[dict] = []

    def run_check(name: str, fn):
        try:
            details = fn()
            checks.append({"name": name, "passed": True, "details": details})
        except Exception as exc:
            checks.append({"name": name, "passed": False, "error": str(exc)})

    def check_public_lists():
        news = _call_api_method(public.list_public_news, limit=3, page=1)
        events = _call_api_method(public.list_public_events, limit=3, page=1)
        colleges = _call_api_method(public.list_public_colleges, limit=3, page=1)
        return {
            "newsItems": len((news or {}).get("items") or []),
            "eventsItems": len((events or {}).get("items") or []),
            "collegesItems": len((colleges or {}).get("items") or []),
        }

    def check_admin_lists():
        news = _call_api_method(content.list_news) or []
        events = _call_api_method(content.list_events) or []
        offers = _call_api_method(content.list_offers) or []
        centers = _call_api_method(content.list_centers) or []
        team = _call_api_method(content.list_team_members) or []
        blog = _call_api_method(content.list_blog_posts) or []
        media = _call_api_method(cms.list_media) or []
        return {
            "news": len(news),
            "events": len(events),
            "offers": len(offers),
            "centers": len(centers),
            "team": len(team),
            "blog": len(blog),
            "media": len(media),
        }

    def check_profile_roundtrip():
        original = _call_api_method(public.get_site_profile) or {}
        original_name = original.get("siteName") or ""
        marker = f"{original_name} E2E".strip() or "AAU E2E"
        _call_api_method(public.update_site_profile, siteName=marker)
        updated = _call_api_method(public.get_site_profile) or {}
        _call_api_method(public.update_site_profile, siteName=original_name)
        restored = _call_api_method(public.get_site_profile) or {}
        if updated.get("siteName") != marker:
            raise Exception("site profile update did not persist")
        if (restored.get("siteName") or "") != original_name:
            raise Exception("site profile restore failed")
        return {"updatedSiteName": updated.get("siteName"), "restoredSiteName": restored.get("siteName")}

    def check_page_roundtrip():
        slug = "about"
        public_snapshot = _call_api_method(public.get_public_page, slug=slug) or {}
        try:
            editable_snapshot = _call_api_method(content.get_page, slug=slug) or {}
        except Exception:
            return {"slug": slug, "status": "public_read_only", "publicTitleEn": public_snapshot.get("titleEn")}

        candidate_keys = ["titleEn", "titleAr", "contentEn", "contentAr", "title", "content"]
        target_key = next((key for key in candidate_keys if key in editable_snapshot), None)
        if not target_key:
            return {"slug": slug, "status": "no_editable_fields", "keys": sorted(editable_snapshot.keys())}

        original_value = editable_snapshot.get(target_key) or ""
        marker = f"{original_value} E2E".strip() or "AAU E2E"
        _call_api_method(content.update_page, slug=slug, **{target_key: marker})
        updated = _call_api_method(content.get_page, slug=slug) or {}
        _call_api_method(content.update_page, slug=slug, **{target_key: original_value})
        restored = _call_api_method(content.get_page, slug=slug) or {}
        if updated.get(target_key) != marker:
            raise Exception("page update did not persist")
        if (restored.get(target_key) or "") != original_value:
            raise Exception("page restore failed")
        return {"slug": slug, "field": target_key, "updated": updated.get(target_key), "restored": restored.get(target_key)}

    run_check("public_lists_available", check_public_lists)
    run_check("admin_lists_available", check_admin_lists)
    run_check("site_profile_update_roundtrip", check_profile_roundtrip)
    run_check("about_page_update_roundtrip", check_page_roundtrip)

    return {
        "ok": all(item.get("passed") for item in checks),
        "summary": {
            "total": len(checks),
            "passed": sum(1 for item in checks if item.get("passed")),
            "failed": sum(1 for item in checks if not item.get("passed")),
        },
        "checks": checks,
    }
