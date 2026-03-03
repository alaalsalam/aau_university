# -*- coding: utf-8 -*-
from __future__ import annotations

from datetime import datetime

import frappe
from frappe.utils import get_datetime, today

from .registry import ADMIN_ROLES, ENTITY_CONFIG, ENTITY_ROLE_PERMISSIONS, SUPER_ADMIN_ROLES
from .utils import ApiError, api_endpoint, require_roles


DOCTOR_ROLE = "Instructor"
STUDENT_ROLE = "Student"


def _build_entity_permissions(user_roles: set[str]) -> dict:
    if user_roles.intersection(SUPER_ADMIN_ROLES):
        return {key: {"read": True, "write": True} for key in ENTITY_ROLE_PERMISSIONS.keys()}

    permissions = {}
    for entity_key, policy in ENTITY_ROLE_PERMISSIONS.items():
        read_roles = set(policy.get("read") or [])
        write_roles = set(policy.get("write") or read_roles)
        permissions[entity_key] = {
            "read": bool(user_roles.intersection(read_roles)),
            "write": bool(user_roles.intersection(write_roles)),
        }
    return permissions


@frappe.whitelist(allow_guest=True)
@api_endpoint
def get_current_access():
    """Return authenticated user access flags for admin UI guards."""
    user = frappe.session.user
    if not user or user == "Guest":
        return {
            "authenticated": False,
            "user": None,
            "roles": [],
            "adminRoles": [],
            "canAccessAdmin": False,
            "entityPermissions": {},
        }

    roles = frappe.get_roles(user)
    user_roles = set(roles)
    admin_roles = sorted([role for role in roles if role in ADMIN_ROLES])
    entity_permissions = _build_entity_permissions(user_roles)
    return {
        "authenticated": True,
        "user": user,
        "roles": roles,
        "adminRoles": admin_roles,
        "canAccessAdmin": bool(admin_roles),
        "entityPermissions": entity_permissions,
    }


@frappe.whitelist()
@api_endpoint
def list_users():
    """List users."""
    require_roles(ADMIN_ROLES)
    users = frappe.get_all(
        "User",
        fields=["name", "email", "enabled", "last_login", "creation"],
        filters={"user_type": "System User"},
        ignore_permissions=True,
    )
    data = []
    for user in users:
        data.append(
            {
                "id": user["name"],
                "nameAr": user["name"],
                "nameEn": user["name"],
                "email": user["email"],
                "status": "active" if user["enabled"] else "inactive",
                "lastLogin": user["last_login"],
                "createdAt": user["creation"],
            }
        )
    return data


@frappe.whitelist()
@api_endpoint
def get_user(user_id: str):
    """Get user details."""
    require_roles(ADMIN_ROLES)
    user = frappe.get_doc("User", user_id)
    return {
        "id": user.name,
        "nameAr": user.full_name or user.name,
        "nameEn": user.full_name or user.name,
        "email": user.email,
        "phone": user.phone,
        "avatar": user.user_image,
        "roleId": user.role_profile_name,
        "status": "active" if user.enabled else "inactive",
        "lastLogin": user.last_login,
        "createdAt": user.creation,
    }


@frappe.whitelist()
@api_endpoint
def create_user(**payload):
    """Create user."""
    require_roles(ADMIN_ROLES)
    email = payload.get("email")
    if not email:
        raise ApiError("VALIDATION_ERROR", "Email is required", status_code=400)
    user = frappe.get_doc(
        {
            "doctype": "User",
            "email": email,
            "first_name": payload.get("nameAr") or payload.get("nameEn") or email,
            "enabled": 1,
            "user_type": "System User",
        }
    )
    user.insert(ignore_permissions=True)
    return get_user(user.name), 201


@frappe.whitelist()
@api_endpoint
def update_user(user_id: str, **payload):
    """Update user."""
    require_roles(ADMIN_ROLES)
    user = frappe.get_doc("User", user_id)
    if payload.get("nameAr") or payload.get("nameEn"):
        user.first_name = payload.get("nameAr") or payload.get("nameEn")
    if payload.get("email"):
        user.email = payload["email"]
    if payload.get("phone"):
        user.phone = payload["phone"]
    if payload.get("avatar"):
        user.user_image = payload["avatar"]
    if payload.get("status") in ("active", "inactive", "suspended"):
        user.enabled = 1 if payload["status"] == "active" else 0
    user.save(ignore_permissions=True)
    return get_user(user.name)


@frappe.whitelist()
@api_endpoint
def delete_user(user_id: str):
    """Delete user."""
    require_roles(ADMIN_ROLES)
    frappe.delete_doc("User", user_id, ignore_permissions=True)
    return {"deleted": True}


@frappe.whitelist()
@api_endpoint
def list_roles():
    """List roles."""
    require_roles(ADMIN_ROLES)
    roles = frappe.get_all("Role", fields=["name"], ignore_permissions=True)
    return [
        {
            "id": role["name"],
            "key": role["name"],
            "nameAr": role["name"],
            "nameEn": role["name"],
            "descriptionAr": role["name"],
            "descriptionEn": role["name"],
            "permissions": [],
            "isSystem": True,
            "createdAt": None,
        }
        for role in roles
    ]


@frappe.whitelist()
@api_endpoint
def get_role(role_id: str):
    """Get role details."""
    require_roles(ADMIN_ROLES)
    role = frappe.get_doc("Role", role_id)
    return {
        "id": role.name,
        "key": role.name,
        "nameAr": role.name,
        "nameEn": role.name,
        "descriptionAr": role.name,
        "descriptionEn": role.name,
        "permissions": [],
        "isSystem": True,
        "createdAt": None,
    }


@frappe.whitelist()
@api_endpoint
def create_role(**payload):
    """Create role."""
    require_roles(ADMIN_ROLES)
    role_name = payload.get("key") or payload.get("nameEn") or payload.get("nameAr")
    if not role_name:
        raise ApiError("VALIDATION_ERROR", "Role key is required", status_code=400)
    role = frappe.get_doc({"doctype": "Role", "role_name": role_name})
    role.insert(ignore_permissions=True)
    return get_role(role.name), 201


@frappe.whitelist()
@api_endpoint
def update_role(role_id: str, **payload):
    """Update role."""
    require_roles(ADMIN_ROLES)
    role = frappe.get_doc("Role", role_id)
    role_name = payload.get("key") or payload.get("nameEn") or payload.get("nameAr")
    if role_name:
        role.role_name = role_name
    role.save(ignore_permissions=True)
    return get_role(role.name)


@frappe.whitelist()
@api_endpoint
def delete_role(role_id: str):
    """Delete role."""
    require_roles(ADMIN_ROLES)
    frappe.delete_doc("Role", role_id, ignore_permissions=True)
    return {"deleted": True}


@frappe.whitelist()
@api_endpoint
def list_permissions(category: str | None = None):
    """List permissions (mapped from Role)."""
    require_roles(ADMIN_ROLES)
    roles = frappe.get_all("Role", fields=["name"], ignore_permissions=True)
    return [
        {
            "id": role["name"],
            "key": role["name"],
            "nameAr": role["name"],
            "nameEn": role["name"],
            "descriptionAr": role["name"],
            "descriptionEn": role["name"],
            "category": category or "content",
        }
        for role in roles
    ]


def _resolve_entity_doctype(entity_key: str) -> str | None:
    config = ENTITY_CONFIG.get(entity_key) or {}
    candidates = []
    primary = config.get("doctype")
    if primary:
        candidates.append(primary)
    for item in config.get("doctype_candidates") or []:
        if item and item not in candidates:
            candidates.append(item)
    for doctype in candidates:
        if frappe.db.exists("DocType", doctype):
            return doctype
    return None


def _valid_columns(doctype: str | None) -> set[str]:
    if not doctype:
        return set()
    try:
        meta = frappe.get_meta(doctype)
    except Exception:
        return set()
    columns = set(meta.get_valid_columns() or [])
    columns.update({"name", "creation", "modified", "owner"})
    return columns


def _safe_count(doctype: str | None, filters: dict | None = None) -> int:
    if not doctype:
        return 0
    try:
        return int(frappe.db.count(doctype, filters=filters or {}))
    except Exception:
        frappe.logger("aau_university").warning(f"[AAU API] dashboard count failed for {doctype}")
        return 0


def _pick_value(record: dict, fields: list[str], fallback: str = "") -> str:
    for fieldname in fields:
        value = str(record.get(fieldname) or "").strip()
        if value:
            return value
    return fallback


def _timestamp_to_iso(value) -> str:
    if not value:
        return ""
    if isinstance(value, datetime):
        return value.isoformat()
    text = str(value).strip()
    if not text:
        return ""
    try:
        return get_datetime(text).isoformat()
    except Exception:
        return text


def _pending_count(doctype: str | None, fallback_to_unpublished: bool = True) -> int:
    valid_columns = _valid_columns(doctype)
    if "status" in valid_columns:
        status_values = [
            "pending",
            "Pending",
            "draft",
            "Draft",
            "under review",
            "Under Review",
            "under_review",
            "pending_review",
            "Pending Review",
            "new",
            "New",
            "قيد المراجعة",
            "مسودة",
        ]
        count = _safe_count(doctype, {"status": ["in", status_values]})
        if count > 0:
            return count
    if fallback_to_unpublished and "is_published" in valid_columns:
        return _safe_count(doctype, {"is_published": 0})
    return 0


def _recent_activity_for_doctype(
    doctype: str | None,
    activity_type: str,
    link: str,
    title_ar_fields: list[str],
    title_en_fields: list[str],
    limit: int = 4,
) -> list[dict]:
    valid_columns = _valid_columns(doctype)
    if not valid_columns:
        return []

    timestamp_field = "modified" if "modified" in valid_columns else ("creation" if "creation" in valid_columns else None)
    if not timestamp_field:
        return []

    wanted_fields = ["name", timestamp_field]
    for fieldname in title_ar_fields + title_en_fields:
        if fieldname in valid_columns and fieldname not in wanted_fields:
            wanted_fields.append(fieldname)

    try:
        rows = frappe.get_all(
            doctype,
            fields=wanted_fields,
            order_by=f"{timestamp_field} desc",
            limit_page_length=limit,
            ignore_permissions=True,
        )
    except Exception:
        frappe.logger("aau_university").warning(f"[AAU API] dashboard recent activity fetch failed for {doctype}")
        return []

    result: list[dict] = []
    for row in rows:
        fallback = str(row.get("name") or "").strip()
        title_ar = _pick_value(row, title_ar_fields, fallback=fallback)
        title_en = _pick_value(row, title_en_fields, fallback=title_ar or fallback)
        timestamp_iso = _timestamp_to_iso(row.get(timestamp_field))
        if not timestamp_iso:
            continue
        result.append(
            {
                "id": fallback,
                "type": activity_type,
                "titleAr": title_ar,
                "titleEn": title_en,
                "timestamp": timestamp_iso,
                "link": link,
            }
        )
    return result


@frappe.whitelist()
@api_endpoint
def get_admin_dashboard():
    """Return admin dashboard snapshot for control-panel overview."""
    require_roles(ADMIN_ROLES)

    news_doctype = _resolve_entity_doctype("news")
    projects_doctype = _resolve_entity_doctype("projects")
    contact_doctype = _resolve_entity_doctype("contact_messages")
    join_doctype = _resolve_entity_doctype("join_requests")
    students_doctype = "Student" if frappe.db.exists("DocType", "Student") else None

    today_start = f"{today()} 00:00:00"

    summary = {
        "usersTotal": _safe_count("User", {"user_type": "System User"}),
        "newsTotal": _safe_count(news_doctype),
        "projectsTotal": _safe_count(projects_doctype),
        "studentsTotal": _safe_count(students_doctype),
    }

    quick_stats = {
        "dailyRegistrations": _safe_count(students_doctype, {"creation": [">=", today_start]}),
        "pendingNews": _pending_count(news_doctype, fallback_to_unpublished=True),
        "projectsUnderReview": _pending_count(projects_doctype, fallback_to_unpublished=True),
        "newQuestions": _pending_count(contact_doctype, fallback_to_unpublished=False)
        + _pending_count(join_doctype, fallback_to_unpublished=False),
    }

    recent_activity = []
    recent_activity.extend(
        _recent_activity_for_doctype(
            news_doctype,
            "news",
            "/admin/news",
            title_ar_fields=["title_ar", "title"],
            title_en_fields=["title_en", "title"],
            limit=3,
        )
    )
    recent_activity.extend(
        _recent_activity_for_doctype(
            projects_doctype,
            "project",
            "/admin/projects",
            title_ar_fields=["title_ar", "id", "name"],
            title_en_fields=["title_en", "id", "name"],
            limit=3,
        )
    )
    recent_activity.extend(
        _recent_activity_for_doctype(
            contact_doctype,
            "contact",
            "/admin/settings",
            title_ar_fields=["subject", "sender_name", "email", "id"],
            title_en_fields=["subject", "sender_name", "email", "id"],
            limit=3,
        )
    )
    recent_activity.extend(
        _recent_activity_for_doctype(
            join_doctype,
            "join_request",
            "/admin/settings",
            title_ar_fields=["full_name", "email", "id"],
            title_en_fields=["full_name", "email", "id"],
            limit=3,
        )
    )
    recent_activity.sort(key=lambda row: row.get("timestamp") or "", reverse=True)
    recent_activity = recent_activity[:8]

    return {
        "summary": summary,
        "quickStats": quick_stats,
        "recentActivity": recent_activity,
    }


def _normalize(value) -> str:
    return str(value or "").strip().lower()


def _clean(value) -> str:
    return str(value or "").strip()


def _to_bool(value, default: bool = False) -> bool:
    if value is None:
        return default
    text = _normalize(value)
    if text in {"1", "true", "yes", "on"}:
        return True
    if text in {"0", "false", "no", "off"}:
        return False
    return default


def _to_int(value, default: int) -> int:
    try:
        return int(value)
    except Exception:
        return default


def _paginate() -> tuple[int, int, int]:
    page = max(_to_int(frappe.form_dict.get("page"), 1), 1)
    page_size = _to_int(frappe.form_dict.get("page_size"), _to_int(frappe.form_dict.get("limit"), 50))
    page_size = min(max(page_size, 1), 200)
    offset = (page - 1) * page_size
    return page, page_size, offset


def _instructor_user_link_field() -> str:
    if not frappe.db.exists("DocType", "Instructor"):
        raise ApiError("NOT_IMPLEMENTED", "Instructor doctype not configured", status_code=501)
    meta = frappe.get_meta("Instructor")
    valid_columns = set(meta.get_valid_columns())
    for fieldname in ("custom_user_id", "user_id", "user", "custom_user"):
        if fieldname in valid_columns:
            return fieldname
    raise ApiError(
        "NOT_IMPLEMENTED",
        "Instructor user link field not found. Run migrate to apply v1_3_add_instructor_user_link.",
        status_code=501,
    )


def _student_user_link_field() -> str:
    if not frappe.db.exists("DocType", "Student"):
        raise ApiError("NOT_IMPLEMENTED", "Student doctype not configured", status_code=501)
    meta = frappe.get_meta("Student")
    valid_columns = set(meta.get_valid_columns())
    for fieldname in ("user", "custom_user_id", "user_id"):
        if fieldname in valid_columns:
            return fieldname
    raise ApiError("NOT_IMPLEMENTED", "Student user link field not found", status_code=501)


def _get_user(user_id: str) -> dict:
    user = frappe.db.get_value("User", user_id, ["name", "email", "full_name", "enabled", "user_type"], as_dict=True)
    if not user:
        raise ApiError("NOT_FOUND", "User not found", status_code=404)
    if _normalize(user.get("user_type")) != "system user":
        raise ApiError("VALIDATION_ERROR", "Only System User can be linked", status_code=400)
    return user


def _get_instructor(instructor_id: str) -> dict:
    if not frappe.db.exists("Instructor", instructor_id):
        raise ApiError("NOT_FOUND", "Instructor not found", status_code=404)
    link_field = _instructor_user_link_field()
    row = frappe.db.get_value(
        "Instructor",
        instructor_id,
        ["name", "instructor_name", "employee", "department", link_field],
        as_dict=True,
    )
    if not row:
        raise ApiError("NOT_FOUND", "Instructor not found", status_code=404)
    row["__link_field"] = link_field
    return row


def _get_student(student_id: str) -> dict:
    if not frappe.db.exists("Student", student_id):
        raise ApiError("NOT_FOUND", "Student not found", status_code=404)
    link_field = _student_user_link_field()
    fields = ["name", "student_name", "student_email_id", "program", link_field]
    row = frappe.db.get_value("Student", student_id, fields, as_dict=True)
    if not row:
        raise ApiError("NOT_FOUND", "Student not found", status_code=404)
    row["__link_field"] = link_field
    return row


def _ensure_role(user_id: str, role: str):
    if not role:
        return
    if frappe.db.exists("Has Role", {"parenttype": "User", "parent": user_id, "role": role}):
        return
    user_doc = frappe.get_doc("User", user_id)
    user_doc.append("roles", {"role": role})
    user_doc.save(ignore_permissions=True)


def _user_map() -> dict[str, dict]:
    rows = frappe.get_all(
        "User",
        filters={"enabled": 1, "user_type": "System User"},
        fields=["name", "email", "full_name"],
        ignore_permissions=True,
        limit_page_length=0,
    )
    return {row["name"]: row for row in rows}


def _find_user_candidates(users: dict[str, dict], values: list[str]) -> list[dict]:
    needles = {_normalize(value) for value in values if _clean(value)}
    if not needles:
        return []
    out = []
    for user in users.values():
        keys = {
            _normalize(user.get("name")),
            _normalize(user.get("email")),
            _normalize(user.get("full_name")),
        }
        if keys.intersection(needles):
            out.append({"id": user.get("name"), "email": user.get("email"), "fullName": user.get("full_name")})
    return out[:5]


@frappe.whitelist()
@api_endpoint
def get_account_link_summary():
    """Return linking coverage summary for instructor and student accounts."""
    require_roles(ADMIN_ROLES)
    link_field = _instructor_user_link_field()
    student_link_field = _student_user_link_field()
    total_instructors = frappe.db.count("Instructor")
    total_students = frappe.db.count("Student")
    linked_instructors = frappe.db.count("Instructor", {link_field: ["is", "set"]})
    linked_students = frappe.db.count("Student", {student_link_field: ["is", "set"]})
    return {
        "doctor": {
            "doctype": "Instructor",
            "linkField": link_field,
            "total": total_instructors,
            "linked": linked_instructors,
            "unlinked": max(total_instructors - linked_instructors, 0),
        },
        "student": {
            "doctype": "Student",
            "linkField": student_link_field,
            "total": total_students,
            "linked": linked_students,
            "unlinked": max(total_students - linked_students, 0),
        },
    }


@frappe.whitelist()
@api_endpoint
def list_linkable_users():
    """List enabled system users for account linking (supports q filter)."""
    require_roles(ADMIN_ROLES)
    q = _normalize(frappe.form_dict.get("q"))
    page, page_size, offset = _paginate()
    rows = frappe.get_all(
        "User",
        filters={"enabled": 1, "user_type": "System User"},
        fields=["name", "email", "full_name"],
        order_by="modified desc",
        ignore_permissions=True,
        limit_page_length=0,
    )
    data = []
    for row in rows:
        if q:
            keys = (_normalize(row.get("name")), _normalize(row.get("email")), _normalize(row.get("full_name")))
            if not any(q in key for key in keys):
                continue
        data.append({"id": row.get("name"), "email": row.get("email"), "fullName": row.get("full_name")})
    total = len(data)
    items = data[offset : offset + page_size]
    return {"items": items, "meta": {"total": total, "page": page, "pageSize": page_size}}


@frappe.whitelist()
@api_endpoint
def list_doctor_links():
    """List instructor account linking state with optional filtering by status/q."""
    require_roles(ADMIN_ROLES)
    link_field = _instructor_user_link_field()
    status = _normalize(frappe.form_dict.get("status") or "all")
    q = _normalize(frappe.form_dict.get("q"))
    page, page_size, offset = _paginate()

    rows = frappe.get_all(
        "Instructor",
        fields=["name", "instructor_name", "employee", "department", link_field],
        order_by="modified desc",
        ignore_permissions=True,
        limit_page_length=0,
    )
    users = _user_map()
    data = []
    for row in rows:
        linked_user = _clean(row.get(link_field))
        is_linked = bool(linked_user)
        if status == "linked" and not is_linked:
            continue
        if status == "unlinked" and is_linked:
            continue

        if q:
            keys = [
                row.get("name"),
                row.get("instructor_name"),
                row.get("employee"),
                row.get("department"),
                linked_user,
            ]
            if not any(q in _normalize(value) for value in keys if value):
                continue

        linked_user_row = users.get(linked_user) if linked_user else None
        candidates = _find_user_candidates(
            users,
            [
                row.get("instructor_name"),
                row.get("name"),
                row.get("employee"),
            ],
        )
        data.append(
            {
                "id": row.get("name"),
                "name": row.get("instructor_name") or row.get("name"),
                "department": row.get("department"),
                "employee": row.get("employee"),
                "isLinked": is_linked,
                "linkedUserId": linked_user or None,
                "linkedUserEmail": (linked_user_row or {}).get("email"),
                "linkedUserFullName": (linked_user_row or {}).get("full_name"),
                "candidates": candidates,
            }
        )
    total = len(data)
    items = data[offset : offset + page_size]
    return {"items": items, "meta": {"total": total, "page": page, "pageSize": page_size}}


@frappe.whitelist()
@api_endpoint
def link_doctor_account(
    instructor_id: str,
    user_id: str | None = None,
    overwrite: int | str | None = None,
    **payload,
):
    """Link Instructor profile to User account and ensure Instructor role."""
    require_roles(ADMIN_ROLES)
    user_id = _clean(
        user_id
        or payload.get("user_id")
        or payload.get("userId")
        or frappe.form_dict.get("user_id")
        or frappe.form_dict.get("userId")
    )
    if not user_id:
        raise ApiError("VALIDATION_ERROR", "user_id is required", status_code=400)
    overwrite = overwrite if overwrite is not None else payload.get("overwrite") or frappe.form_dict.get("overwrite")
    overwrite_flag = _to_bool(overwrite, default=False)
    instructor = _get_instructor(instructor_id)
    user = _get_user(user_id)
    link_field = instructor["__link_field"]
    current = _clean(instructor.get(link_field))

    if current and current != user["name"] and not overwrite_flag:
        raise ApiError(
            "CONFLICT",
            "Instructor is already linked to another user. Pass overwrite=1 to replace.",
            status_code=409,
            details={"currentUserId": current},
        )

    frappe.db.set_value("Instructor", instructor["name"], link_field, user["name"], update_modified=False)
    _ensure_role(user["name"], DOCTOR_ROLE)
    frappe.db.commit()
    return {
        "linked": True,
        "entity": "doctor",
        "id": instructor["name"],
        "linkField": link_field,
        "user": {"id": user["name"], "email": user.get("email"), "fullName": user.get("full_name")},
    }


@frappe.whitelist()
@api_endpoint
def unlink_doctor_account(instructor_id: str):
    """Unlink Instructor profile from User account."""
    require_roles(ADMIN_ROLES)
    instructor = _get_instructor(instructor_id)
    link_field = instructor["__link_field"]
    current = _clean(instructor.get(link_field))
    if current:
        frappe.db.set_value("Instructor", instructor["name"], link_field, None, update_modified=False)
        frappe.db.commit()
    return {
        "linked": False,
        "entity": "doctor",
        "id": instructor["name"],
        "linkField": link_field,
        "previousUserId": current or None,
    }


@frappe.whitelist()
@api_endpoint
def list_student_links():
    """List student account linking state with optional filtering by status/q."""
    require_roles(ADMIN_ROLES)
    link_field = _student_user_link_field()
    status = _normalize(frappe.form_dict.get("status") or "all")
    q = _normalize(frappe.form_dict.get("q"))
    page, page_size, offset = _paginate()

    rows = frappe.get_all(
        "Student",
        fields=["name", "student_name", "student_email_id", "program", link_field],
        order_by="modified desc",
        ignore_permissions=True,
        limit_page_length=0,
    )
    users = _user_map()
    data = []
    for row in rows:
        linked_user = _clean(row.get(link_field))
        is_linked = bool(linked_user)
        if status == "linked" and not is_linked:
            continue
        if status == "unlinked" and is_linked:
            continue

        if q:
            keys = [row.get("name"), row.get("student_name"), row.get("student_email_id"), row.get("program"), linked_user]
            if not any(q in _normalize(value) for value in keys if value):
                continue

        linked_user_row = users.get(linked_user) if linked_user else None
        candidates = _find_user_candidates(users, [row.get("student_name"), row.get("student_email_id"), row.get("name")])
        data.append(
            {
                "id": row.get("name"),
                "name": row.get("student_name") or row.get("name"),
                "program": row.get("program"),
                "studentEmail": row.get("student_email_id"),
                "isLinked": is_linked,
                "linkedUserId": linked_user or None,
                "linkedUserEmail": (linked_user_row or {}).get("email"),
                "linkedUserFullName": (linked_user_row or {}).get("full_name"),
                "candidates": candidates,
            }
        )
    total = len(data)
    items = data[offset : offset + page_size]
    return {"items": items, "meta": {"total": total, "page": page, "pageSize": page_size}}


@frappe.whitelist()
@api_endpoint
def link_student_account(
    student_id: str,
    user_id: str | None = None,
    overwrite: int | str | None = None,
    **payload,
):
    """Link Student profile to User account and ensure Student role."""
    require_roles(ADMIN_ROLES)
    user_id = _clean(
        user_id
        or payload.get("user_id")
        or payload.get("userId")
        or frappe.form_dict.get("user_id")
        or frappe.form_dict.get("userId")
    )
    if not user_id:
        raise ApiError("VALIDATION_ERROR", "user_id is required", status_code=400)
    overwrite = overwrite if overwrite is not None else payload.get("overwrite") or frappe.form_dict.get("overwrite")
    overwrite_flag = _to_bool(overwrite, default=False)
    student = _get_student(student_id)
    user = _get_user(user_id)
    link_field = student["__link_field"]
    current = _clean(student.get(link_field))

    if current and current != user["name"] and not overwrite_flag:
        raise ApiError(
            "CONFLICT",
            "Student is already linked to another user. Pass overwrite=1 to replace.",
            status_code=409,
            details={"currentUserId": current},
        )

    updates = {link_field: user["name"]}
    if frappe.get_meta("Student").get_field("student_email_id") and _clean(user.get("email")):
        updates["student_email_id"] = user.get("email")

    frappe.db.set_value("Student", student["name"], updates, update_modified=False)
    _ensure_role(user["name"], STUDENT_ROLE)
    frappe.db.commit()
    return {
        "linked": True,
        "entity": "student",
        "id": student["name"],
        "linkField": link_field,
        "user": {"id": user["name"], "email": user.get("email"), "fullName": user.get("full_name")},
    }


@frappe.whitelist()
@api_endpoint
def unlink_student_account(student_id: str):
    """Unlink Student profile from User account."""
    require_roles(ADMIN_ROLES)
    student = _get_student(student_id)
    link_field = student["__link_field"]
    current = _clean(student.get(link_field))
    if current:
        frappe.db.set_value("Student", student["name"], link_field, None, update_modified=False)
        frappe.db.commit()
    return {
        "linked": False,
        "entity": "student",
        "id": student["name"],
        "linkField": link_field,
        "previousUserId": current or None,
    }
