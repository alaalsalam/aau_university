# -*- coding: utf-8 -*-
from __future__ import annotations

import frappe

LOG_PREFIX = "[AAU INSTRUCTOR LINK]"
INSTRUCTOR_DOCTYPE = "Instructor"
FIELDNAME = "custom_user_id"


def execute():
    logger = frappe.logger("aau_university")
    logger.info(f"{LOG_PREFIX} START")
    try:
        field_created = _ensure_instructor_user_field()
        summary = _backfill_instructor_user_links()
        frappe.db.commit()
        logger.info(
            f"{LOG_PREFIX} DONE | field_created={int(field_created)} linked={summary['linked']} "
            f"already_linked={summary['already_linked']} skipped={summary['skipped']}"
        )
    except Exception:
        logger.error(f"{LOG_PREFIX} FAILED\n{frappe.get_traceback()}")


def _ensure_instructor_user_field() -> bool:
    if not frappe.db.exists("DocType", INSTRUCTOR_DOCTYPE):
        return False
    if frappe.db.exists("Custom Field", {"dt": INSTRUCTOR_DOCTYPE, "fieldname": FIELDNAME}):
        return False
    if frappe.db.exists("DocField", {"parent": INSTRUCTOR_DOCTYPE, "fieldname": FIELDNAME}):
        return False

    insert_after = "employee"
    if not frappe.db.exists("DocField", {"parent": INSTRUCTOR_DOCTYPE, "fieldname": insert_after}):
        insert_after = "instructor_name"

    doc = frappe.get_doc(
        {
            "doctype": "Custom Field",
            "dt": INSTRUCTOR_DOCTYPE,
            "fieldname": FIELDNAME,
            "label": "Portal User",
            "fieldtype": "Link",
            "options": "User",
            "insert_after": insert_after,
            "in_list_view": 1,
            "description": "Portal account linked to this instructor profile.",
        }
    )
    doc.insert(ignore_permissions=True)
    frappe.clear_cache(doctype=INSTRUCTOR_DOCTYPE)
    return True


def _backfill_instructor_user_links() -> dict:
    summary = {"linked": 0, "already_linked": 0, "skipped": 0}
    if not frappe.db.exists("DocType", INSTRUCTOR_DOCTYPE):
        return summary
    if not frappe.db.exists("DocType", "Employee"):
        return summary

    rows = frappe.get_all(
        INSTRUCTOR_DOCTYPE,
        fields=["name", "employee", FIELDNAME],
        ignore_permissions=True,
        limit_page_length=0,
    )
    employee_names = {row.get("employee") for row in rows if row.get("employee")}
    if not employee_names:
        summary["skipped"] = len(rows)
        return summary

    employee_rows = frappe.get_all(
        "Employee",
        filters={"name": ["in", list(employee_names)]},
        fields=["name", "user_id"],
        ignore_permissions=True,
        limit_page_length=0,
    )
    employee_user_map = {row.get("name"): row.get("user_id") for row in employee_rows if row.get("name") and row.get("user_id")}

    for row in rows:
        if row.get(FIELDNAME):
            summary["already_linked"] += 1
            continue
        employee = row.get("employee")
        user_id = employee_user_map.get(employee)
        if not employee or not user_id:
            summary["skipped"] += 1
            continue
        frappe.db.set_value(INSTRUCTOR_DOCTYPE, row["name"], FIELDNAME, user_id, update_modified=False)
        summary["linked"] += 1
    return summary
