# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any

import frappe


DELETE_CANDIDATES = {
    "Job Opportunities",
    "Registration Guide",
    "Testimonials",
    "University Administration",
    "University Vision and Mission",
    "Menus",
    "Sliders",
}


def promote_aau_doctypes_to_standard() -> dict[str, Any]:
    """Promote useful AAU custom DocTypes to standard app DocTypes and delete dead ones safely."""

    custom_doctypes = [
        row.name
        for row in frappe.get_all(
            "DocType",
            filters={"module": "AAU", "custom": 1},
            fields=["name"],
            order_by="name asc",
        )
    ]

    promoted: list[str] = []
    deleted: list[str] = []
    skipped: list[str] = []

    for doctype_name in custom_doctypes:
        count = frappe.db.count(doctype_name)
        incoming_links = frappe.db.count(
            "DocField",
            {
                "fieldtype": ["in", ["Link", "Table"]],
                "options": doctype_name,
            },
        )

        if doctype_name in DELETE_CANDIDATES:
            if count == 0 and incoming_links == 0:
                try:
                    frappe.delete_doc("DocType", doctype_name, force=True, ignore_permissions=True)
                    deleted.append(doctype_name)
                except Exception as exc:  # pragma: no cover - operational safeguard
                    skipped.append(f"{doctype_name}: delete failed ({exc})")
            else:
                skipped.append(
                    f"{doctype_name}: kept (records={count}, incoming_links={incoming_links})"
                )
            continue

        try:
            frappe.db.set_value("DocType", doctype_name, "custom", 0, update_modified=False)
            frappe.db.set_value("DocType", doctype_name, "module", "AAU", update_modified=False)
            frappe.clear_cache(doctype=doctype_name)
            promoted.append(doctype_name)
        except Exception as exc:  # pragma: no cover - operational safeguard
            skipped.append(f"{doctype_name}: promote failed ({exc})")

    frappe.db.commit()
    frappe.clear_cache()

    remaining_custom = frappe.get_all(
        "DocType",
        filters={"module": "AAU", "custom": 1},
        fields=["name"],
        order_by="name asc",
    )

    return {
        "ok": True,
        "promoted_count": len(promoted),
        "deleted_count": len(deleted),
        "remaining_custom_count": len(remaining_custom),
        "promoted": promoted,
        "deleted": deleted,
        "remaining_custom": [d.name for d in remaining_custom],
        "skipped": skipped,
    }
