# -*- coding: utf-8 -*-
from __future__ import annotations

from datetime import datetime
import re
import unicodedata

import frappe
from frappe.utils import get_datetime, today

from .registry import ADMIN_ROLES, ENTITY_CONFIG, ENTITY_ROLE_PERMISSIONS, SUPER_ADMIN_ROLES
from .utils import ApiError, api_endpoint, require_roles


DOCTOR_ROLE = "Instructor"
STUDENT_ROLE = "Student"
PORTAL_ROLE = "AAU Portal User"
AAU_STUDENT_ROLE = "AAU Student User"
AAU_INSTRUCTOR_ROLE = "AAU Instructor User"
AAU_EDITOR_ROLE = "AAU Editor"
AAU_COORDINATOR_ROLE = "AAU Coordinator"
AAU_SITE_MANAGER_ROLE = "AAU Site Manager"
AAU_EXECUTIVE_ROLE = "AAU Executive Manager"

PERMISSION_CATALOG = [
    {
        "id": "p1",
        "key": "users.view",
        "nameAr": "عرض المستخدمين",
        "nameEn": "View Users",
        "descriptionAr": "عرض قائمة المستخدمين",
        "descriptionEn": "View users list",
        "category": "users",
    },
    {
        "id": "p2",
        "key": "users.create",
        "nameAr": "إضافة مستخدم",
        "nameEn": "Create User",
        "descriptionAr": "إضافة مستخدم جديد",
        "descriptionEn": "Create new user",
        "category": "users",
    },
    {
        "id": "p3",
        "key": "users.edit",
        "nameAr": "تعديل مستخدم",
        "nameEn": "Edit User",
        "descriptionAr": "تعديل بيانات المستخدمين",
        "descriptionEn": "Edit user data",
        "category": "users",
    },
    {
        "id": "p4",
        "key": "users.delete",
        "nameAr": "حذف مستخدم",
        "nameEn": "Delete User",
        "descriptionAr": "حذف المستخدمين",
        "descriptionEn": "Delete users",
        "category": "users",
    },
    {
        "id": "p5",
        "key": "roles.manage",
        "nameAr": "إدارة الأدوار",
        "nameEn": "Manage Roles",
        "descriptionAr": "إضافة وتعديل الأدوار والصلاحيات",
        "descriptionEn": "Add and edit roles and permissions",
        "category": "users",
    },
    {
        "id": "p6",
        "key": "content.news",
        "nameAr": "إدارة الأخبار",
        "nameEn": "Manage News",
        "descriptionAr": "إضافة وتعديل وحذف الأخبار",
        "descriptionEn": "Add, edit and delete news",
        "category": "content",
    },
    {
        "id": "p7",
        "key": "content.events",
        "nameAr": "إدارة الفعاليات",
        "nameEn": "Manage Events",
        "descriptionAr": "إضافة وتعديل وحذف الفعاليات",
        "descriptionEn": "Add, edit and delete events",
        "category": "content",
    },
    {
        "id": "p8",
        "key": "content.projects",
        "nameAr": "إدارة المشاريع",
        "nameEn": "Manage Projects",
        "descriptionAr": "إضافة وتعديل وحذف المشاريع",
        "descriptionEn": "Add, edit and delete projects",
        "category": "content",
    },
    {
        "id": "p9",
        "key": "content.media",
        "nameAr": "إدارة الوسائط",
        "nameEn": "Manage Media",
        "descriptionAr": "رفع وحذف ملفات الوسائط",
        "descriptionEn": "Upload and delete media files",
        "category": "content",
    },
    {
        "id": "p10",
        "key": "settings.general",
        "nameAr": "الإعدادات العامة",
        "nameEn": "General Settings",
        "descriptionAr": "تعديل إعدادات الموقع",
        "descriptionEn": "Edit site settings",
        "category": "settings",
    },
    {
        "id": "p11",
        "key": "settings.appearance",
        "nameAr": "إعدادات المظهر",
        "nameEn": "Appearance Settings",
        "descriptionAr": "تعديل مظهر الموقع",
        "descriptionEn": "Edit site appearance",
        "category": "settings",
    },
    {
        "id": "p12",
        "key": "reports.view",
        "nameAr": "عرض التقارير",
        "nameEn": "View Reports",
        "descriptionAr": "عرض تقارير النظام",
        "descriptionEn": "View system reports",
        "category": "reports",
    },
    {
        "id": "p13",
        "key": "reports.export",
        "nameAr": "تصدير التقارير",
        "nameEn": "Export Reports",
        "descriptionAr": "تصدير التقارير",
        "descriptionEn": "Export reports",
        "category": "reports",
    },
    {
        "id": "p14",
        "key": "users.reset_password",
        "nameAr": "إعادة تعيين كلمات المرور",
        "nameEn": "Reset User Passwords",
        "descriptionAr": "إعادة تعيين كلمة مرور المستخدم",
        "descriptionEn": "Reset user passwords",
        "category": "users",
    },
    {
        "id": "p15",
        "key": "system.backup",
        "nameAr": "النسخ الاحتياطي",
        "nameEn": "Backup Management",
        "descriptionAr": "الوصول إلى النسخ الاحتياطية وإدارتها",
        "descriptionEn": "Access and manage backups",
        "category": "settings",
    },
    {
        "id": "p16",
        "key": "content.publish",
        "nameAr": "اعتماد ونشر المحتوى",
        "nameEn": "Publish Content",
        "descriptionAr": "اعتماد المحتوى قبل النشر وإظهاره في الموقع",
        "descriptionEn": "Approve and publish content",
        "category": "content",
    },
    {
        "id": "p17",
        "key": "academic.manage",
        "nameAr": "إدارة الكليات والبرامج",
        "nameEn": "Manage Colleges and Programs",
        "descriptionAr": "إدارة الكليات والمراكز والأقسام والبرامج",
        "descriptionEn": "Manage colleges, centers, departments and programs",
        "category": "content",
    },
    {
        "id": "p18",
        "key": "visibility.toggle",
        "nameAr": "إظهار وإخفاء العناصر",
        "nameEn": "Toggle Visibility",
        "descriptionAr": "إظهار وإخفاء الكليات والهيئة والمحتوى",
        "descriptionEn": "Show and hide colleges, faculty and content",
        "category": "content",
    },
]

ALL_PERMISSION_KEYS = [item["key"] for item in PERMISSION_CATALOG]
SYSTEM_ROLE_KEYS = {
    "System Manager",
    "Administrator",
    "AAU Admin",
    "AAU Content Manager",
    AAU_EXECUTIVE_ROLE,
    AAU_SITE_MANAGER_ROLE,
    AAU_EDITOR_ROLE,
    AAU_COORDINATOR_ROLE,
    PORTAL_ROLE,
    AAU_STUDENT_ROLE,
    AAU_INSTRUCTOR_ROLE,
    "Website Manager",
    "Blogger",
    STUDENT_ROLE,
    DOCTOR_ROLE,
}

ROLE_PERMISSION_MAP = {
    "System Manager": ALL_PERMISSION_KEYS,
    "Administrator": ALL_PERMISSION_KEYS,
    "AAU Admin": ALL_PERMISSION_KEYS,
    "AAU Content Manager": ["content.news", "content.events", "content.projects", "content.media", "settings.general"],
    "Website Manager": ["content.news", "content.events", "content.projects", "content.media", "settings.general"],
    "Blogger": ["content.news"],
    AAU_SITE_MANAGER_ROLE: ALL_PERMISSION_KEYS,
    AAU_EXECUTIVE_ROLE: ["reports.view", "reports.export", "users.view", "content.publish", "system.backup"],
    AAU_EDITOR_ROLE: [
        "content.news",
        "content.events",
        "content.projects",
        "content.media",
        "content.publish",
        "reports.view",
        "visibility.toggle",
    ],
    AAU_COORDINATOR_ROLE: [
        "academic.manage",
        "reports.view",
        "reports.export",
        "visibility.toggle",
    ],
    PORTAL_ROLE: [],
    AAU_STUDENT_ROLE: [],
    AAU_INSTRUCTOR_ROLE: ["reports.view"],
    DOCTOR_ROLE: ["reports.view"],
    STUDENT_ROLE: [],
}


def _role_permissions(role_name: str) -> list[str]:
    if role_name in ROLE_PERMISSION_MAP:
        return ROLE_PERMISSION_MAP[role_name]
    return []


def _primary_role(user_roles: list[str]) -> str:
    priority = [
        "System Manager",
        "Administrator",
        "AAU Admin",
        AAU_SITE_MANAGER_ROLE,
        AAU_EXECUTIVE_ROLE,
        "AAU Content Manager",
        AAU_EDITOR_ROLE,
        AAU_COORDINATOR_ROLE,
        "Website Manager",
        AAU_INSTRUCTOR_ROLE,
        DOCTOR_ROLE,
        AAU_STUDENT_ROLE,
        STUDENT_ROLE,
        PORTAL_ROLE,
    ]
    for role_name in priority:
        if role_name in user_roles:
            return role_name
    custom_roles = [role for role in user_roles if role not in {"All", "Guest"}]
    return custom_roles[0] if custom_roles else ""


def _user_payload(user_id: str) -> dict:
    user = frappe.get_doc("User", user_id)
    roles = [row.role for row in user.roles or [] if row.role not in {"All", "Guest"}]
    primary_role = _primary_role(roles)
    return {
        "id": user.name,
        "nameAr": user.full_name or user.first_name or user.name,
        "nameEn": user.full_name or user.first_name or user.name,
        "email": user.email,
        "phone": user.mobile_no or user.phone,
        "avatar": user.user_image,
        "roleId": primary_role,
        "status": "active" if user.enabled else "inactive",
        "lastLogin": user.last_login,
        "createdAt": user.creation,
    }


def _set_user_primary_role(user_doc, role_name: str | None):
    next_role = (role_name or "").strip()
    user_doc.roles = []
    if next_role:
        user_doc.append("roles", {"role": next_role})


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


@frappe.whitelist(allow_guest=True)
@api_endpoint
def resolve_login_identifier(identifier: str | None = None):
    """Resolve login identifier (email/username/academic no.) to Frappe login user id."""
    raw = _clean(identifier or frappe.form_dict.get("identifier"))
    if not raw:
        raise ApiError("VALIDATION_ERROR", "identifier is required", status_code=400)

    # Direct User id / email match
    if frappe.db.exists("User", raw):
        return {"identifier": raw}
    user_by_email = frappe.db.get_value("User", {"email": raw}, "name")
    if user_by_email:
        return {"identifier": user_by_email}
    # Local-part fallback (e.g., "instructor01" -> "instructor01@aau.edu.ye")
    user_from_local_part = frappe.db.sql(
        """
        select name
        from `tabUser`
        where enabled = 1 and LOCATE('@', name) > 1 and SUBSTRING_INDEX(name, '@', 1) = %s
        limit 1
        """,
        (raw,),
        as_dict=True,
    )
    if user_from_local_part:
        return {"identifier": _clean(user_from_local_part[0].get("name"))}

    # Student mapping: allow login by academic number / student code / email.
    if frappe.db.exists("DocType", "Student"):
        student_meta = frappe.get_meta("Student")
        valid_cols = set(student_meta.get_valid_columns())
        candidate_fields = ["name", "user", "student_email_id", "student_id", "custom_student_id"]
        student_fields = [f for f in candidate_fields if f in valid_cols or f == "name"]
        student_rows = []
        try:
            for search_field in ("name", "student_email_id", "student_id", "custom_student_id"):
                if search_field != "name" and search_field not in valid_cols:
                    continue
                student_rows = frappe.get_all(
                    "Student",
                    filters={search_field: raw},
                    fields=student_fields,
                    limit_page_length=1,
                    ignore_permissions=True,
                )
                if student_rows:
                    break
        except Exception:
            student_rows = []
        if student_rows:
            row = student_rows[0]
            mapped = _clean(row.get("user")) or _clean(row.get("student_email_id"))
            if mapped and frappe.db.exists("User", mapped):
                return {"identifier": mapped}
            if mapped:
                user_from_email = frappe.db.get_value("User", {"email": mapped}, "name")
                if user_from_email:
                    return {"identifier": user_from_email}

    # Instructor mapping fallback (e.g., employee code/user link).
    if frappe.db.exists("DocType", "Instructor"):
        instructor_meta = frappe.get_meta("Instructor")
        valid_cols = set(instructor_meta.get_valid_columns())
        link_field = next((f for f in ("custom_user_id", "user_id", "user") if f in valid_cols), None)
        instructor_fields = ["name"]
        if link_field:
            instructor_fields.append(link_field)
        try:
            instructor_rows = frappe.get_all(
                "Instructor",
                filters={"name": raw},
                fields=instructor_fields,
                limit_page_length=1,
                ignore_permissions=True,
            )
            if not instructor_rows and "employee" in valid_cols:
                instructor_rows = frappe.get_all(
                    "Instructor",
                    filters={"employee": raw},
                    fields=instructor_fields,
                    limit_page_length=1,
                    ignore_permissions=True,
                )
            if not instructor_rows and "instructor_name" in valid_cols:
                instructor_rows = frappe.get_all(
                    "Instructor",
                    filters={"instructor_name": raw},
                    fields=instructor_fields,
                    limit_page_length=1,
                    ignore_permissions=True,
                )
        except Exception:
            instructor_rows = []
        if instructor_rows and link_field:
            mapped = _clean(instructor_rows[0].get(link_field))
            if mapped and frappe.db.exists("User", mapped):
                return {"identifier": mapped}
            if mapped:
                user_from_email = frappe.db.get_value("User", {"email": mapped}, "name")
                if user_from_email:
                    return {"identifier": user_from_email}

        # Fuzzy instructor name/code matching to tolerate punctuation/spacing variants
        normalized_raw = _normalize_login_key(raw)
        if normalized_raw:
            fuzzy_fields = ["name"]
            if "instructor_name" in valid_cols:
                fuzzy_fields.append("instructor_name")
            if "employee" in valid_cols:
                fuzzy_fields.append("employee")
            if link_field and link_field not in fuzzy_fields:
                fuzzy_fields.append(link_field)
            fuzzy_rows = frappe.get_all(
                "Instructor",
                fields=fuzzy_fields,
                ignore_permissions=True,
                limit_page_length=0,
            )
            for row in fuzzy_rows:
                candidates = {
                    _normalize_login_key(row.get("name")),
                    _normalize_login_key(row.get("instructor_name")),
                    _normalize_login_key(row.get("employee")),
                }
                mapped_user = _clean(row.get(link_field)) if link_field else ""
                if mapped_user:
                    candidates.add(_normalize_login_key(mapped_user))
                    candidates.add(_normalize_login_key(mapped_user.split("@")[0]))
                if normalized_raw in {value for value in candidates if value}:
                    if mapped_user and frappe.db.exists("User", mapped_user):
                        return {"identifier": mapped_user}
                    if mapped_user:
                        user_from_email = frappe.db.get_value("User", {"email": mapped_user}, "name")
                        if user_from_email:
                            return {"identifier": user_from_email}

    return {"identifier": raw}


@frappe.whitelist(allow_guest=True)
@api_endpoint
def portal_login(identifier: str | None = None, password: str | None = None):
    """Login endpoint that resolves student/doctor identifiers before auth."""
    payload = frappe._dict({})
    payload.update(getattr(frappe.local, "form_dict", {}) or {})
    if frappe.request:
        try:
            body = frappe.request.get_json(silent=True) or {}
            if isinstance(body, dict):
                payload.update(body)
        except Exception:
            pass
    if isinstance(identifier, str) and identifier.strip():
        payload["identifier"] = identifier
    if isinstance(password, str) and password:
        payload["password"] = password

    raw_identifier = _clean(payload.get("identifier") or payload.get("username") or payload.get("usr"))
    raw_password = str(payload.get("password") or payload.get("pwd") or "")
    if not raw_identifier or not raw_password:
        raise ApiError("VALIDATION_ERROR", "identifier and password are required", status_code=400)

    resolved = resolve_login_identifier(raw_identifier).get("identifier") or raw_identifier
    from frappe.auth import LoginManager

    login_manager = LoginManager()
    login_manager.authenticate(user=resolved, pwd=raw_password)
    login_manager.post_login()
    return {"message": "Logged In", "identifier": resolved, "user": frappe.session.user}


@frappe.whitelist()
@api_endpoint
def list_users():
    """List users."""
    require_roles(ADMIN_ROLES)
    users = frappe.get_all(
        "User",
        fields=["name"],
        filters={"user_type": "System User"},
        ignore_permissions=True,
    )
    return [_user_payload(user["name"]) for user in users]


@frappe.whitelist()
@api_endpoint
def get_user(user_id: str):
    """Get user details."""
    require_roles(ADMIN_ROLES)
    return _user_payload(user_id)


@frappe.whitelist()
@api_endpoint
def create_user(**payload):
    """Create user."""
    require_roles(ADMIN_ROLES)
    email = payload.get("email")
    if not email:
        raise ApiError("VALIDATION_ERROR", "Email is required", status_code=400)
    role_id = (payload.get("roleId") or "").strip()
    if role_id and not frappe.db.exists("Role", role_id):
        raise ApiError("VALIDATION_ERROR", "Role does not exist", status_code=400)
    user = frappe.get_doc(
        {
            "doctype": "User",
            "email": email,
            "first_name": payload.get("nameAr") or payload.get("nameEn") or email,
            "enabled": 1,
            "user_type": "System User",
            "mobile_no": payload.get("phone"),
            "send_welcome_email": 0,
        }
    )
    _set_user_primary_role(user, role_id)
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
        user.mobile_no = payload["phone"]
    if payload.get("avatar"):
        user.user_image = payload["avatar"]
    if payload.get("status") in ("active", "inactive", "suspended"):
        user.enabled = 1 if payload["status"] == "active" else 0
    if "roleId" in payload:
        role_id = (payload.get("roleId") or "").strip()
        if role_id and not frappe.db.exists("Role", role_id):
            raise ApiError("VALIDATION_ERROR", "Role does not exist", status_code=400)
        _set_user_primary_role(user, role_id)
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
    roles = frappe.get_all("Role", fields=["name", "creation"], ignore_permissions=True, order_by="name asc")
    return [
        {
            "id": role["name"],
            "key": role["name"],
            "nameAr": role["name"],
            "nameEn": role["name"],
            "descriptionAr": role["name"],
            "descriptionEn": role["name"],
            "permissions": _role_permissions(role["name"]),
            "isSystem": role["name"] in SYSTEM_ROLE_KEYS,
            "createdAt": role["creation"],
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
        "permissions": _role_permissions(role.name),
        "isSystem": role.name in SYSTEM_ROLE_KEYS,
        "createdAt": role.creation,
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
    if role.name in SYSTEM_ROLE_KEYS:
        raise ApiError("FORBIDDEN", "System roles cannot be modified", status_code=403)
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
    if role_id in SYSTEM_ROLE_KEYS:
        raise ApiError("FORBIDDEN", "System roles cannot be deleted", status_code=403)
    frappe.delete_doc("Role", role_id, ignore_permissions=True)
    return {"deleted": True}


@frappe.whitelist()
@api_endpoint
def list_permissions(category: str | None = None):
    """List permissions (mapped from Role)."""
    require_roles(ADMIN_ROLES)
    permissions = PERMISSION_CATALOG
    if category:
        permissions = [item for item in permissions if item["category"] == category]
    return permissions


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


def _normalize_login_key(value) -> str:
    text = _clean(value).lower()
    if not text:
        return ""
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    replacements = {
        "أ": "ا",
        "إ": "ا",
        "آ": "ا",
        "ة": "ه",
        "ى": "ي",
        "ؤ": "و",
        "ئ": "ي",
    }
    for src, dst in replacements.items():
        text = text.replace(src, dst)
    text = re.sub(r"[^a-z0-9\u0600-\u06FF]+", "", text)
    return text


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
