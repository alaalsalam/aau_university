# -*- coding: utf-8 -*-
from __future__ import annotations

import frappe

from .registry import ADMIN_ROLES
from .utils import ApiError, api_endpoint, require_roles


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
        }

    roles = frappe.get_roles(user)
    admin_roles = sorted([role for role in roles if role in ADMIN_ROLES])
    return {
        "authenticated": True,
        "user": user,
        "roles": roles,
        "adminRoles": admin_roles,
        "canAccessAdmin": bool(admin_roles),
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
