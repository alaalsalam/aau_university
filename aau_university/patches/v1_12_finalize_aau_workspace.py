# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from pathlib import Path

import frappe

from aau_university.content_access import (
    CONTENT_DOCTYPES,
    PRIMARY_WORKSPACE,
    PRIMARY_WORKSPACE_LABEL,
    PRIMARY_WORKSPACE_TITLE,
    ensure_doctype_permission,
    ensure_role,
    ensure_workspace_access,
    hide_legacy_workspace,
    sync_content_manager_user,
)

LEGACY_WORKSPACES = ["AAU", "AAU Content Hub"]


def _workspace_payload() -> dict:
    workspace_path = (
        Path(frappe.get_app_path("aau_university"))
        / "aau"
        / "workspace"
        / "aau"
        / "aau.json"
    )
    if not workspace_path.exists():
        frappe.throw(f"AAU workspace file not found: {workspace_path}")
    return json.loads(workspace_path.read_text())


def _sync_workspace() -> None:
    payload = _workspace_payload()
    workspace_name = payload["name"]

    if frappe.db.exists("Workspace", workspace_name):
        doc = frappe.get_doc("Workspace", workspace_name)
        doc.update(payload)
        doc.set("roles", payload.get("roles") or [])
        doc.set("links", payload.get("links") or [])
        doc.save(ignore_permissions=True)
    else:
        frappe.get_doc(payload).insert(ignore_permissions=True)

    ensure_workspace_access(workspace_name)


def _finalize_workspace_row(workspace_name: str = PRIMARY_WORKSPACE) -> None:
    frappe.db.sql(
        """
        update `tabWorkspace`
        set title=%s, label=%s, public=0, is_hidden=0
        where name=%s
        """,
        (PRIMARY_WORKSPACE_TITLE, PRIMARY_WORKSPACE_LABEL, workspace_name),
    )


def execute():
    ensure_role()

    for doctype_name in CONTENT_DOCTYPES:
        ensure_doctype_permission(doctype_name)

    _sync_workspace()

    for workspace_name in LEGACY_WORKSPACES:
        if workspace_name != PRIMARY_WORKSPACE:
            hide_legacy_workspace(workspace_name)

    sync_content_manager_user()
    _finalize_workspace_row()
    frappe.clear_cache()
    frappe.db.commit()
