# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Iterable

import frappe
from frappe.utils import cint
from frappe.utils.password import update_password


FULL_KEYS = [
    "read",
    "write",
    "create",
    "delete",
    "submit",
    "cancel",
    "amend",
    "report",
    "export",
    "print",
    "email",
    "share",
]

ADMIN_ROLES = ["System Manager", "Workspace Manager", "AAU Site Manager"]
EDITOR_ROLE = "AAU Editor"
COORDINATOR_ROLE = "AAU Coordinator"


def _perm_payload(role: str, mode: str) -> dict:
    data = {"role": role, "permlevel": 0}
    if mode == "full":
        data.update(
            {
                "read": 1,
                "write": 1,
                "create": 1,
                "delete": 1,
                "submit": 0,
                "cancel": 0,
                "amend": 0,
                "report": 1,
                "export": 1,
                "print": 1,
                "email": 1,
                "share": 1,
            }
        )
    elif mode == "none":
        data.update({k: 0 for k in FULL_KEYS})
    else:
        raise ValueError(f"Unknown mode: {mode}")
    return data


def _set_role_permission_on_doctype(doctype_name: str, role: str, mode: str) -> None:
    if not frappe.db.exists("DocType", doctype_name):
        return

    doc = frappe.get_doc("DocType", doctype_name)
    target = None
    for perm in doc.permissions or []:
        if perm.role == role and cint(getattr(perm, "permlevel", 0)) == 0:
            target = perm
            break

    if mode == "none":
        if target:
            doc.permissions.remove(target)
            doc.save(ignore_permissions=True)
        return

    desired = _perm_payload(role, mode)

    if target:
        changed = False
        for k, v in desired.items():
            if getattr(target, k, None) != v:
                setattr(target, k, v)
                changed = True
        if changed:
            doc.save(ignore_permissions=True)
        return

    doc.append("permissions", desired)
    doc.save(ignore_permissions=True)


def _restrict_role_to_doctypes(role: str, allowed_full: Iterable[str]) -> None:
    allowed = set(allowed_full)

    # Scope: all AAU doctypes + File (for media upload)
    target_doctypes = set(frappe.get_all("DocType", filters={"module": "AAU"}, pluck="name"))
    if frappe.db.exists("DocType", "File"):
        target_doctypes.add("File")

    for dt in sorted(target_doctypes):
        if dt in allowed:
            _set_role_permission_on_doctype(dt, role, "full")
        else:
            _set_role_permission_on_doctype(dt, role, "none")


def _ensure_role(role_name: str, desk_access: int = 1) -> None:
    if frappe.db.exists("Role", role_name):
        frappe.db.set_value("Role", role_name, "desk_access", cint(desk_access), update_modified=False)
        return
    frappe.get_doc({"doctype": "Role", "role_name": role_name, "desk_access": cint(desk_access)}).insert(ignore_permissions=True)


def _ensure_user(email: str, first_name: str, roles: list[str], password: str, role_profile: str | None = None) -> None:
    if frappe.db.exists("User", email):
        user = frappe.get_doc("User", email)
    else:
        user = frappe.get_doc(
            {
                "doctype": "User",
                "email": email,
                "first_name": first_name,
                "enabled": 1,
                "send_welcome_email": 0,
                "user_type": "System User",
            }
        )
        user.insert(ignore_permissions=True)

    user.first_name = first_name
    user.enabled = 1
    user.user_type = "System User"
    user.send_welcome_email = 0
    if role_profile is None:
        user.role_profile_name = ""
    else:
        user.role_profile_name = role_profile

    current_roles = {d.role for d in (user.roles or [])}
    for r in roles:
        if not frappe.db.exists("Role", r):
            continue
        if r not in current_roles:
            user.append("roles", {"role": r})

    user.save(ignore_permissions=True)
    frappe.db.commit()

    # Set/reset password without triggering email flow.
    update_password(user.name, password, logout_all_sessions=False)


def _set_workspace_link_only_for(parent: str, link_filters: set[str], roles: list[str]) -> None:
    if not link_filters:
        return
    only_for = ", ".join(roles)
    rows = frappe.get_all(
        "Workspace Link",
        filters={"parent": parent},
        fields=["name", "link_to", "label"],
        limit_page_length=500,
    )
    for row in rows:
        target = (row.get("link_to") or "").strip() or (row.get("label") or "").strip()
        if target in link_filters:
            frappe.db.set_value("Workspace Link", row["name"], "only_for", only_for, update_modified=False)


def _apply_workspace_visibility() -> None:
    admin_only_roles = ADMIN_ROLES

    # 1) Main AAU workspace: default admin-only, then open selected links for editor/coordinator.
    all_aau_links = frappe.get_all(
        "Workspace Link",
        filters={"parent": "aau"},
        pluck="name",
        limit_page_length=1000,
    )
    for link_name in all_aau_links:
        frappe.db.set_value("Workspace Link", link_name, "only_for", ", ".join(admin_only_roles), update_modified=False)

    editor_aau_targets = {
        "المحتوى الرئيسي",
        "المحتوى المنشور",
        "الأكاديمي والكليات",
        "الصفحة الرئيسية",
        "عن الجامعة",
        "الفريق الإداري",
        "صفحات AAU",
        "الأخبار",
        "الفعاليات",
        "المشاريع",
        "العروض",
        "الشركاء",
        "أعضاء هيئة التدريس",
        "Home Page",
        "About University",
        "About Team Member",
        "AAU Page",
        "News",
        "Events",
        "Projects",
        "Offers",
        "Partners",
        "Faculty Members",
    }
    _set_workspace_link_only_for("aau", editor_aau_targets, [*admin_only_roles, EDITOR_ROLE])

    coordinator_aau_targets = {
        "المراكز والحياة الجامعية",
        "الأكاديمي والكليات",
        "المراكز",
        "الكليات",
        "Centers",
        "Colleges",
    }
    _set_workspace_link_only_for("aau", coordinator_aau_targets, [*admin_only_roles, COORDINATOR_ROLE])

    # 2) Content operations workspace: keep it content-only for editor; admin keeps all links.
    all_content_links = frappe.get_all(
        "Workspace Link",
        filters={"parent": "aau-content-operations"},
        pluck="name",
        limit_page_length=1000,
    )
    for link_name in all_content_links:
        frappe.db.set_value("Workspace Link", link_name, "only_for", ", ".join(admin_only_roles), update_modified=False)

    editor_content_targets = {
        "صفحات الموقع",
        "النشر",
        "الصفحة الرئيسية",
        "عن الجامعة",
        "صفحات AAU",
        "الأخبار",
        "الفعاليات",
        "Home Page",
        "About University",
        "AAU Page",
        "News",
        "Events",
    }
    _set_workspace_link_only_for("aau-content-operations", editor_content_targets, [*admin_only_roles, EDITOR_ROLE])

    # 3) Academic operations workspace: coordinator sees colleges/centers only.
    all_academic_links = frappe.get_all(
        "Workspace Link",
        filters={"parent": "aau-academic-operations"},
        pluck="name",
        limit_page_length=1000,
    )
    for link_name in all_academic_links:
        frappe.db.set_value("Workspace Link", link_name, "only_for", ", ".join(admin_only_roles), update_modified=False)

    coordinator_academic_targets = {
        "البنية الأكاديمية",
        "الكليات",
        "Colleges",
    }
    _set_workspace_link_only_for(
        "aau-academic-operations",
        coordinator_academic_targets,
        [*admin_only_roles, COORDINATOR_ROLE],
    )


def apply_control_roles_and_users() -> dict:
    # Ensure roles exist
    for role in ("AAU Site Manager", "AAU Editor", "AAU Coordinator", "Desk User", "System Manager", "Website Manager", "Workspace Manager"):
        _ensure_role(role, desk_access=1)

    # Restrict role scopes exactly as requested
    _restrict_role_to_doctypes(
        "AAU Editor",
        allowed_full=[
            "News",
            "Events",
            "Projects",
            "About University",
            "AAU Page",
            "Home Page",
            "Faculty Members",
            "About Team Member",
            "Partners",
            "Offers",
            "File",
        ],
    )
    _restrict_role_to_doctypes("AAU Coordinator", allowed_full=["Colleges", "Centers", "File"])

    # Create/update users
    creds = {
        "admin": {
            "email": "admin.control@aau.local",
            "first_name": "AAU Admin",
            "password": "Aau@2026#Admin",
            "roles": ["System Manager", "Desk User", "Website Manager", "Workspace Manager", "AAU Site Manager"],
            "role_profile": None,
        },
        "editor": {
            "email": "editor.content@aau.local",
            "first_name": "AAU Editor",
            "password": "Aau@2026#Editor",
            "roles": ["Desk User", "AAU Editor"],
            "role_profile": "AAU Editor",
        },
        "coordinator": {
            "email": "coordinator.academic@aau.local",
            "first_name": "AAU Coordinator",
            "password": "Aau@2026#Coord",
            "roles": ["Desk User", "AAU Coordinator"],
            "role_profile": "AAU Coordinator",
        },
    }

    for cfg in creds.values():
        _ensure_user(
            email=cfg["email"],
            first_name=cfg["first_name"],
            roles=cfg["roles"],
            password=cfg["password"],
            role_profile=cfg["role_profile"],
        )

    _apply_workspace_visibility()

    frappe.clear_cache()

    return {
        "ok": True,
        "message": "roles-and-users-updated",
        "users": {k: {"email": v["email"], "password": v["password"]} for k, v in creds.items()},
        "editor_scope": [
            "News",
            "Events",
            "Projects",
            "About University",
            "AAU Page",
            "Home Page",
            "Faculty Members",
            "About Team Member",
            "Partners",
            "Offers",
            "File",
        ],
        "coordinator_scope": ["Colleges", "Centers", "File"],
    }


def assign_college_editor_permissions(editor_user: str = "editor.content@aau.local", college_slug: str = "engineering-it") -> dict:
    """Allow a content editor to edit only one college document by slug."""
    if not frappe.db.exists("User", editor_user):
        frappe.throw(f"User not found: {editor_user}")

    college_name = frappe.db.get_value("Colleges", {"slug": college_slug}, "name")
    if not college_name:
        frappe.throw(f"College not found for slug: {college_slug}")

    # Ensure editor has doctype-level access to Colleges (without create/delete).
    if not frappe.db.exists("Role", "AAU Editor"):
        _ensure_role("AAU Editor", desk_access=1)

    perm_name = frappe.db.get_value("DocPerm", {"parent": "Colleges", "role": "AAU Editor", "permlevel": 0}, "name")
    if perm_name:
        frappe.db.sql(
            """
            update `tabDocPerm`
            set `read`=1, `write`=1, `create`=0, `delete`=0, `report`=1, `export`=1, `print`=1, `email`=0, `share`=0,
                `submit`=0, `cancel`=0, `amend`=0
            where name=%s
            """,
            (perm_name,),
        )
    else:
        doc = frappe.get_doc("DocType", "Colleges")
        doc.append(
            "permissions",
            {
                "role": "AAU Editor",
                "permlevel": 0,
                "read": 1,
                "write": 1,
                "create": 0,
                "delete": 0,
                "submit": 0,
                "cancel": 0,
                "amend": 0,
                "report": 1,
                "export": 1,
                "print": 1,
                "email": 0,
                "share": 0,
            },
        )
        doc.save(ignore_permissions=True)

    # Remove previous Colleges restrictions for this user, then apply engineering only.
    old_perms = frappe.get_all(
        "User Permission",
        filters={"user": editor_user, "allow": "Colleges"},
        pluck="name",
        limit_page_length=500,
    )
    for name in old_perms:
        frappe.delete_doc("User Permission", name, ignore_permissions=True, force=True)

    frappe.get_doc(
        {
            "doctype": "User Permission",
            "user": editor_user,
            "allow": "Colleges",
            "for_value": college_name,
            "apply_to_all_doctypes": 1,
            "is_default": 1,
        }
    ).insert(ignore_permissions=True)

    frappe.clear_cache(user=editor_user)
    frappe.clear_cache()
    frappe.db.commit()

    return {
        "ok": True,
        "editor_user": editor_user,
        "college": {"name": college_name, "slug": college_slug},
        "message": "Editor restricted to single college",
    }
