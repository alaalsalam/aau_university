# -*- coding: utf-8 -*-
from __future__ import annotations

import frappe

LOG_PREFIX = "[AAU HOME SINGLE CMS]"

CMS_FIELDS = [
    "hero_badge_ar",
    "hero_badge_en",
    "hero_title_primary_ar",
    "hero_title_primary_en",
    "hero_title_secondary_ar",
    "hero_title_secondary_en",
    "hero_description_ar",
    "hero_description_en",
    "hero_image",
    "about_title_ar",
    "about_title_en",
    "about_description_ar",
    "about_description_en",
    "about_image",
    "students_count",
    "faculty_count",
    "programs_count",
    "colleges_count",
    "stats_students_label_ar",
    "stats_students_label_en",
    "stats_faculty_label_ar",
    "stats_faculty_label_en",
    "stats_programs_label_ar",
    "stats_programs_label_en",
    "stats_colleges_label_ar",
    "stats_colleges_label_en",
]


def execute():
    logger = frappe.logger("aau_university")
    logger.info(f"{LOG_PREFIX} START")

    try:
        if not frappe.db.exists("DocType", "Home Page"):
            logger.info(f"{LOG_PREFIX} Home Page doctype missing, skip")
            return

        legacy_values = _read_latest_legacy_row()

        frappe.reload_doc("aau", "doctype", "home_page")
        meta = frappe.get_meta("Home Page")
        if not getattr(meta, "issingle", 0):
            frappe.db.set_value("DocType", "Home Page", "issingle", 1, update_modified=False)
            frappe.reload_doc("aau", "doctype", "home_page")
            meta = frappe.get_meta("Home Page")

        valid_single_fields = {df.fieldname for df in (meta.fields or []) if df.fieldname}
        applied = 0
        for fieldname, value in legacy_values.items():
            if fieldname not in valid_single_fields:
                continue
            if value in (None, ""):
                continue
            frappe.db.set_single_value("Home Page", fieldname, value)
            applied += 1

        frappe.clear_cache(doctype="Home Page")
        frappe.db.commit()
        logger.info(f"{LOG_PREFIX} DONE | migrated_fields={applied}")
    except Exception:
        logger.error(f"{LOG_PREFIX} FAILED\n{frappe.get_traceback()}")
        raise


def _read_latest_legacy_row() -> dict:
    table_exists = frappe.db.sql("SHOW TABLES LIKE 'tabHome Page'")
    if not table_exists:
        return {}

    desc_rows = frappe.db.sql("DESC `tabHome Page`", as_dict=True) or []
    columns = {row["Field"] for row in desc_rows if row.get("Field")}
    selected = [field for field in CMS_FIELDS if field in columns]
    if not selected:
        return {}

    select_sql = ", ".join(f"`{field}`" for field in selected)
    order_clause = "`modified` desc" if "modified" in columns else "`creation` desc"
    row = frappe.db.sql(
        f"SELECT {select_sql} FROM `tabHome Page` ORDER BY {order_clause} LIMIT 1",
        as_dict=True,
    )
    return row[0] if row else {}
