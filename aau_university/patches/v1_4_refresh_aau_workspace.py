# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path

import frappe
from frappe.modules.import_file import import_file_by_path
from aau_university.content_access import ensure_workspace_access, hide_legacy_workspace

LOG_PREFIX = "[AAU WORKSPACE]"


def execute():
    logger = frappe.logger("aau_university")
    logger.info(f"{LOG_PREFIX} START")
    try:
        _sync_workspace_json()
        _activate_workspace()
        frappe.clear_cache()
        frappe.db.commit()
        logger.info(f"{LOG_PREFIX} DONE")
    except Exception:
        logger.error(f"{LOG_PREFIX} FAILED\\n{frappe.get_traceback()}")
        raise


def _sync_workspace_json():
    workspace_path = (
        Path(frappe.get_app_path("aau_university"))
        / "aau"
        / "workspace"
        / "aau"
        / "aau.json"
    )
    if not workspace_path.exists():
        frappe.throw(f"AAU workspace file not found: {workspace_path}")

    import_file_by_path(str(workspace_path), force=True)


def _activate_workspace():
    if frappe.db.exists("Workspace", "AAU"):
        frappe.db.set_value("Workspace", "AAU", "is_hidden", 0, update_modified=False)
        frappe.db.set_value("Workspace", "AAU", "title", "AAU", update_modified=False)
        frappe.db.set_value("Workspace", "AAU", "label", "مركز إدارة موقع الجامعة", update_modified=False)
        ensure_workspace_access("AAU")

    # Keep legacy workspace out of sidebar to avoid confusion.
    if frappe.db.exists("Workspace", "AAU Content Hub"):
        hide_legacy_workspace("AAU Content Hub")
