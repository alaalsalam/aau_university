# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from pathlib import Path

import frappe

LOG_PREFIX = "[AAU CLEANUP]"
UNUSED_DOCTYPES = [
    "About Page",
    "Contact Page",
    "Academic Calendar",
    "Course Section",
    "Course Withdrawal Request",
    "Grade Review Request",
    "Final Result",
]


def execute():
    logger = frappe.logger("aau_university")
    logger.info(f"{LOG_PREFIX} START")
    try:
        _activate_new_workspace()
        summary = _cleanup_unused_doctypes()
        frappe.db.commit()
        logger.info(
            f"{LOG_PREFIX} DONE | deleted={summary['deleted']} skipped={summary['skipped']} backup_dir={summary['backup_dir']}"
        )
    except Exception:
        logger.error(f"{LOG_PREFIX} FAILED\n{frappe.get_traceback()}")


def _activate_new_workspace():
    if frappe.db.exists("Workspace", "AAU"):
        frappe.db.set_value("Workspace", "AAU", "is_hidden", 1, update_modified=False)
    if frappe.db.exists("Workspace", "AAU Content Hub"):
        frappe.db.set_value("Workspace", "AAU Content Hub", "is_hidden", 0, update_modified=False)


def _cleanup_unused_doctypes() -> dict:
    deleted = 0
    skipped = 0
    backup_dir = _backup_dir()
    for doctype_name in UNUSED_DOCTYPES:
        if not frappe.db.exists("DocType", doctype_name):
            skipped += 1
            continue
        _backup_doctype_data(doctype_name, backup_dir)
        try:
            frappe.delete_doc("DocType", doctype_name, ignore_permissions=True, force=1)
            deleted += 1
        except Exception:
            frappe.logger("aau_university").warning(
                f"{LOG_PREFIX} Skip delete failed for {doctype_name}\n{frappe.get_traceback()}"
            )
            skipped += 1
    return {"deleted": deleted, "skipped": skipped, "backup_dir": str(backup_dir)}


def _backup_dir() -> Path:
    root = Path(frappe.get_site_path("private", "backups", "aau_cleanup"))
    root.mkdir(parents=True, exist_ok=True)
    return root


def _backup_doctype_data(doctype_name: str, backup_dir: Path):
    filename = backup_dir / f"{frappe.scrub(doctype_name)}.json"
    if filename.exists():
        return
    meta = frappe.get_meta(doctype_name)
    valid_columns = list(meta.get_valid_columns()) if hasattr(meta, "get_valid_columns") else []
    rows = frappe.get_all(
        doctype_name,
        fields=valid_columns or ["name"],
        ignore_permissions=True,
        limit_page_length=0,
    )
    payload = {"doctype": doctype_name, "rows": rows}
    filename.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
