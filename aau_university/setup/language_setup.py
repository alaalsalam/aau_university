# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any

import frappe


def apply_arabic_defaults() -> dict[str, Any]:
    """Set Arabic as default language for AAU site and users (idempotent)."""

    changed = {
        "system_settings": False,
        "website_settings": False,
        "users_updated": 0,
    }

    if frappe.db.exists("Language", "ar"):
        # In some installations Language has enabled flag, keep it enabled when available.
        if frappe.db.has_column("Language", "enabled"):
            frappe.db.set_value("Language", "ar", "enabled", 1, update_modified=False)

    # Global defaults (used by new sessions and defaults APIs)
    frappe.db.set_default("lang", "ar")
    frappe.db.set_default("language", "ar")

    # System Settings language
    current_lang = frappe.db.get_single_value("System Settings", "language")
    if current_lang != "ar":
        frappe.db.set_single_value("System Settings", "language", "ar")
        changed["system_settings"] = True

    # Website Settings default language if field exists
    if frappe.db.exists("DocType", "Website Settings"):
        meta = frappe.get_meta("Website Settings")
        fieldnames = {f.fieldname for f in meta.fields}
        for candidate in ("default_language", "language"):
            if candidate in fieldnames:
                cur = frappe.db.get_single_value("Website Settings", candidate)
                if cur != "ar":
                    frappe.db.set_single_value("Website Settings", candidate, "ar")
                    changed["website_settings"] = True
                break

    # Make all real users default to Arabic (excluding Guest)
    users = frappe.get_all(
        "User",
        filters={"name": ["!=", "Guest"]},
        fields=["name", "language", "enabled"],
        limit_page_length=200000,
    )
    for user in users:
        if user.get("language") != "ar":
            frappe.db.set_value("User", user["name"], "language", "ar", update_modified=False)
            changed["users_updated"] += 1

    frappe.db.commit()
    frappe.clear_cache()
    return {"ok": True, **changed}
