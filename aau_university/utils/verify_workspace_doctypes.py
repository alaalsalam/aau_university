# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from pathlib import Path

import frappe

WORKSPACE_FILE = Path("/home/frappe/frappe-bench/apps/aau_university/aau_university/aau/workspace/aau/aau.json")


def verify_workspace_doctypes(site: str = "edu.yemenfrappe.com"):
    """Verify AAU workspace DocType links resolve on the current site."""
    if not WORKSPACE_FILE.exists():
        frappe.throw(f"Workspace file not found: {WORKSPACE_FILE}")

    with WORKSPACE_FILE.open("r", encoding="utf-8") as handle:
        workspace = json.load(handle)

    doctypes = []
    for link in workspace.get("links", []):
        if not isinstance(link, dict):
            continue
        if link.get("type") != "Link" or link.get("link_type") != "DocType":
            continue
        link_to = link.get("link_to")
        if isinstance(link_to, str) and link_to.strip():
            doctypes.append(link_to.strip())

    existing = []
    missing = []
    for doctype in sorted(set(doctypes)):
        try:
            frappe.get_meta(doctype)
            existing.append(doctype)
        except Exception:
            missing.append(doctype)

    print(f"[workspace] checked={len(set(doctypes))}")
    print(f"[workspace] existing={existing}")
    print(f"[workspace] missing={missing}")

    return {"existing": existing, "missing": missing, "ok": len(missing) == 0}
