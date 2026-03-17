from __future__ import annotations

import frappe

CONTENT_MANAGER_ROLE = "AAU Content Manager"
CONTENT_MANAGER_USER = "content.manager@edu.yemenfrappe.com"
PRIMARY_WORKSPACE = "aau"
LEGACY_WORKSPACES = ["AAU", "AAU Content Hub"]

CONTENT_DOCTYPES = [
    "Home Page",
    "About University",
    "AAU Page",
    "AAU Menu",
    "Website Settings",
    "Slider",
    "News",
    "Events",
    "Blog Posts",
    "FAQ",
    "Offers",
    "Partners",
    "Projects",
    "Campus Life",
    "Centers",
    "Colleges",
    "Academic Programs",
    "Faculty Members",
    "Media Library",
    "Contact Us Messages",
    "Join Requests",
]

WORKSPACE_ROLES = [
    CONTENT_MANAGER_ROLE,
    "System Manager",
]

PRIMARY_WORKSPACE_TITLE = "AAU"
PRIMARY_WORKSPACE_LABEL = "مركز إدارة موقع الجامعة"


def manager_permission(role: str = CONTENT_MANAGER_ROLE) -> dict:
    return {
        "role": role,
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


def ensure_role() -> bool:
    if frappe.db.exists("Role", CONTENT_MANAGER_ROLE):
        return False
    frappe.get_doc(
        {
            "doctype": "Role",
            "role_name": CONTENT_MANAGER_ROLE,
            "desk_access": 1,
        }
    ).insert(ignore_permissions=True)
    return True


def ensure_doctype_permission(doctype_name: str, role: str = CONTENT_MANAGER_ROLE) -> bool:
    if not frappe.db.exists("DocType", doctype_name):
        return False

    doc = frappe.get_doc("DocType", doctype_name)
    for perm in doc.permissions or []:
        if perm.role == role:
            changed = False
            desired = manager_permission(role)
            for key, value in desired.items():
                if getattr(perm, key, None) != value:
                    setattr(perm, key, value)
                    changed = True
            if changed:
                doc.save(ignore_permissions=True)
            return changed

    doc.append("permissions", manager_permission(role))
    doc.save(ignore_permissions=True)
    return True


def ensure_workspace_access(workspace_name: str = PRIMARY_WORKSPACE) -> bool:
    if not frappe.db.exists("Workspace", workspace_name):
        return False

    doc = frappe.get_doc("Workspace", workspace_name)
    changed = False

    if doc.is_hidden:
        doc.is_hidden = 0
        changed = True
    if doc.public:
        doc.public = 0
        changed = True
    if getattr(doc, "title", None) != PRIMARY_WORKSPACE_TITLE:
        doc.title = PRIMARY_WORKSPACE_TITLE
        changed = True
    if getattr(doc, "label", None) != PRIMARY_WORKSPACE_LABEL:
        doc.label = PRIMARY_WORKSPACE_LABEL
        changed = True

    existing_roles = {row.role for row in (doc.roles or [])}
    for role in WORKSPACE_ROLES:
        if role not in existing_roles:
            doc.append("roles", {"role": role})
            changed = True

    if changed:
        doc.save(ignore_permissions=True)
    return changed


def normalize_primary_workspace() -> bool:
    return ensure_workspace_access(PRIMARY_WORKSPACE)


def hide_legacy_workspace(workspace_name: str) -> bool:
    if not frappe.db.exists("Workspace", workspace_name):
        return False
    changed = False
    doc = frappe.get_doc("Workspace", workspace_name)
    if not doc.is_hidden:
        doc.is_hidden = 1
        changed = True
    if doc.public:
        doc.public = 0
        changed = True
    if changed:
        doc.save(ignore_permissions=True)
    return changed


def sync_content_manager_user(email: str = CONTENT_MANAGER_USER) -> bool:
    if not frappe.db.exists("User", email):
        return False

    user = frappe.get_doc("User", email)
    changed = False
    desired_roles = {CONTENT_MANAGER_ROLE, "Desk User", "Website Manager", "Workspace Manager"}
    current_roles = {row.role for row in (user.roles or [])}

    for role in desired_roles - current_roles:
        user.append("roles", {"role": role})
        changed = True

    remaining_roles = [row for row in (user.roles or []) if row.role != "System Manager"]
    if len(remaining_roles) != len(user.roles or []):
        user.set("roles", [{"role": row.role} for row in remaining_roles])
        changed = True

    if changed:
        user.save(ignore_permissions=True)
    return changed
