# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from pathlib import Path

import frappe
from frappe.model.rename_doc import rename_doc
from aau_university.content_access import (
    PRIMARY_WORKSPACE_LABEL,
    PRIMARY_WORKSPACE_TITLE,
    ensure_workspace_access,
    hide_legacy_workspace,
)

LOG_PREFIX = "[AAU WORKSPACE]"
PRIMARY_WORKSPACE = "aau"
LEGACY_WORKSPACES = ["AAU", "AAU Content Hub"]


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

    payload = json.loads(workspace_path.read_text())
    workspace_name = payload["name"]
    if frappe.db.exists("Workspace", workspace_name):
        doc = frappe.get_doc("Workspace", workspace_name)
        doc.update(payload)
        doc.save(ignore_permissions=True)
    else:
        frappe.get_doc(payload).insert(ignore_permissions=True)


def _activate_workspace():
    if frappe.db.exists("Workspace", "AAU") and not frappe.db.exists("Workspace", PRIMARY_WORKSPACE):
        rename_doc("Workspace", "AAU", PRIMARY_WORKSPACE, force=True, ignore_permissions=True)

    if frappe.db.exists("Workspace", PRIMARY_WORKSPACE):
        frappe.db.set_value("Workspace", PRIMARY_WORKSPACE, "is_hidden", 0, update_modified=False)
        frappe.db.set_value("Workspace", PRIMARY_WORKSPACE, "title", PRIMARY_WORKSPACE_TITLE, update_modified=False)
        frappe.db.set_value("Workspace", PRIMARY_WORKSPACE, "label", PRIMARY_WORKSPACE_LABEL, update_modified=False)
        ensure_workspace_access(PRIMARY_WORKSPACE)

    for workspace_name in LEGACY_WORKSPACES:
        if workspace_name != PRIMARY_WORKSPACE and frappe.db.exists("Workspace", workspace_name):
            hide_legacy_workspace(workspace_name)
