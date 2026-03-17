# -*- coding: utf-8 -*-
from __future__ import annotations

import hashlib
import re

import frappe

INSTRUCTOR_DOCTYPE = "Instructor"
USER_ROLE = "Instructor"
EMAIL_DOMAIN = "edu.yemenfrappe.com"


def _clean(value) -> str:
    return str(value or "").strip()


def _normalize(value) -> str:
    return re.sub(r"\s+", " ", _clean(value)).casefold()


def _link_field() -> str | None:
    if not frappe.db.exists("DocType", INSTRUCTOR_DOCTYPE):
        return None
    valid_columns = set(frappe.get_meta(INSTRUCTOR_DOCTYPE).get_valid_columns())
    for fieldname in ("custom_user_id", "user_id", "user", "custom_user"):
        if fieldname in valid_columns:
            return fieldname
    return None


def _user_map() -> dict[str, dict]:
    rows = frappe.get_all(
        "User",
        filters={"enabled": 1, "user_type": "System User"},
        fields=["name", "email", "full_name"],
        ignore_permissions=True,
        limit_page_length=0,
    )
    mapped = {}
    for row in rows:
        keys = {
            _normalize(row.get("name")),
            _normalize(row.get("email")),
            _normalize(row.get("full_name")),
        }
        local_part = _clean(row.get("email")).split("@", 1)[0]
        if local_part:
            keys.add(_normalize(local_part))
        for key in keys:
            if key:
                mapped.setdefault(key, row)
    return mapped


def _ensure_role(user_id: str, role: str = USER_ROLE) -> None:
    if frappe.db.exists("Has Role", {"parenttype": "User", "parent": user_id, "role": role}):
        return
    user_doc = frappe.get_doc("User", user_id)
    user_doc.append("roles", {"role": role})
    user_doc.save(ignore_permissions=True)


def _email_for_instructor(name: str, docname: str) -> str:
    ascii_slug = re.sub(r"[^a-z0-9]+", "-", _normalize(name or docname))
    ascii_slug = ascii_slug.strip("-")
    digest = hashlib.sha1(_clean(docname).encode("utf-8")).hexdigest()[:6]
    local = f"doctor-{ascii_slug}-{digest}" if ascii_slug else f"doctor-{digest}"
    local = re.sub(r"-{2,}", "-", local).strip("-")
    email = f"{local}@{EMAIL_DOMAIN}"

    if not frappe.db.exists("User", email):
        return email

    counter = 2
    while True:
        candidate = f"{local}-{counter}@{EMAIL_DOMAIN}"
        if not frappe.db.exists("User", candidate):
            return candidate
        counter += 1


def _match_existing_user(user_rows: dict[str, dict], instructor: dict) -> dict | None:
    candidates = [
        instructor.get("instructor_name"),
        instructor.get("name"),
    ]
    for value in candidates:
        matched = user_rows.get(_normalize(value))
        if matched:
            return matched
    return None


def _create_user(instructor: dict) -> dict:
    display_name = _clean(instructor.get("instructor_name") or instructor.get("name"))
    email = _email_for_instructor(display_name, _clean(instructor.get("name")))
    user = frappe.get_doc(
        {
            "doctype": "User",
            "email": email,
            "first_name": display_name or email,
            "full_name": display_name or email,
            "enabled": 1,
            "user_type": "System User",
            "send_welcome_email": 0,
        }
    )
    user.append("roles", {"role": USER_ROLE})
    user.insert(ignore_permissions=True)
    return {"name": user.name, "email": user.email, "full_name": user.full_name}


def execute():
    link_field = _link_field()
    if not link_field:
        return {"linked": 0, "created_users": 0, "matched_users": 0, "already_linked": 0, "skipped": 0}

    rows = frappe.get_all(
        INSTRUCTOR_DOCTYPE,
        fields=["name", "instructor_name", link_field],
        ignore_permissions=True,
        limit_page_length=0,
    )
    users = _user_map()
    summary = {"linked": 0, "created_users": 0, "matched_users": 0, "already_linked": 0, "skipped": 0}

    for instructor in rows:
        current = _clean(instructor.get(link_field))
        if current:
            _ensure_role(current)
            summary["already_linked"] += 1
            continue

        matched = _match_existing_user(users, instructor)
        if matched:
            user_row = matched
            summary["matched_users"] += 1
        else:
            user_row = _create_user(instructor)
            users = _user_map()
            summary["created_users"] += 1

        if not user_row or not _clean(user_row.get("name")):
            summary["skipped"] += 1
            continue

        frappe.db.set_value(INSTRUCTOR_DOCTYPE, instructor["name"], link_field, user_row["name"], update_modified=False)
        _ensure_role(user_row["name"])
        summary["linked"] += 1

    frappe.db.commit()
    return summary
