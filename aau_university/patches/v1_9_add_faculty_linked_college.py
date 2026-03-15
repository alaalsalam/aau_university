from __future__ import annotations

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
    if not frappe.db.exists("DocType", "Faculty Members"):
        return

    meta = frappe.get_meta("Faculty Members")
    if meta.get_field("linked_college"):
        return

    create_custom_fields(
        {
            "Faculty Members": [
                {
                    "fieldname": "linked_college",
                    "label": "الكلية المرتبطة",
                    "fieldtype": "Link",
                    "options": "Colleges",
                    "insert_after": "academic_title",
                }
            ]
        },
        update=True,
    )
