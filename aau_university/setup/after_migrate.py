# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import frappe

LOG_PREFIX = "[AAU DOCTYPE IMPORT]"

def run():
    """
    Runs after migrate.
    - Creates/updates DocTypes from docs/aau_doctypes_spec.json
    - Idempotent: runs once unless you force rerun.
    """

    # 1) Safety: only run if app is installed on the site
    if not frappe.db.exists("Module Def", "AAU"):
        # Not mandatory, but a quick signal the app likely isn't installed/configured
        pass

    # 2) Run-once guard (stored in DB)
    if _is_done() and not _force():
        frappe.logger("aau_university").info(f"{LOG_PREFIX} SKIP: already completed")
        return

    try:
        spec_path = frappe.get_app_path("aau_university", "aau_university", "docs", "aau_doctypes_spec.json")
        spec = _read_json(spec_path)
        doctypes = spec.get("doctypes") or []
        if not doctypes:
            raise RuntimeError("Spec has no doctypes")

        # child first
        child = [d for d in doctypes if int(d.get("istable", 0) or 0) == 1]
        parent = [d for d in doctypes if int(d.get("istable", 0) or 0) == 0]

        _log(f"START | spec={spec_path} | total={len(doctypes)} child={len(child)} parent={len(parent)}")

        # Create modules defensively if spec references them
        for d in doctypes:
            module = (d.get("module") or "AAU").strip()
            _ensure_module_def(module)

        update_existing = True  # ✅ توصية: بعد migrate خله يضمن التوافق دائمًا

        for dt in child:
            _create_or_update_doctype(dt, update_existing=update_existing)

        for dt in parent:
            _create_or_update_doctype(dt, update_existing=update_existing)

        _mark_done()
        _log("COMPLETED ✅")

    except Exception:
        tb = frappe.get_traceback()
        _log("FAILED ❌\n" + tb)
        # لا نكسر migrate، لكن نسجل الخطأ
        frappe.logger("aau_university").error(f"{LOG_PREFIX} FAILED\n{tb}")


# -----------------------------
# Internals
# -----------------------------

def _read_json(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def _ensure_module_def(module_name: str, app_name: str = "aau_university"):
    if not frappe.db.exists("Module Def", module_name):
        doc = frappe.get_doc({
            "doctype": "Module Def",
            "module_name": module_name,
            "app_name": app_name,
            "custom": 1
        })
        doc.insert(ignore_permissions=True)

def _create_or_update_doctype(dt_spec: dict, update_existing: bool = True):
    name = dt_spec["name"]
    exists = frappe.db.exists("DocType", name)

    if exists and not update_existing:
        _log(f"SKIP (exists): {name}")
        return

    payload = {
        "doctype": "DocType",
        "name": name,
        "module": dt_spec.get("module") or "AAU",
        "custom": int(dt_spec.get("custom", 1) or 1),
        "istable": int(dt_spec.get("istable", 0) or 0),
        "issingle": int(dt_spec.get("issingle", 0) or 0),
        "allow_rename": int(dt_spec.get("allow_rename", 1) or 1),
        "engine": dt_spec.get("engine", "InnoDB"),
        "track_changes": int(dt_spec.get("track_changes", 1) or 1),
        "sort_field": dt_spec.get("sort_field", "modified"),
        "sort_order": dt_spec.get("sort_order", "DESC"),
        "row_format": dt_spec.get("row_format", "Dynamic"),
        "grid_page_length": int(dt_spec.get("grid_page_length", 50) or 50),
        "rows_threshold_for_grid_search": int(dt_spec.get("rows_threshold_for_grid_search", 20) or 20),
        "fields": dt_spec.get("fields", []),
        "field_order": dt_spec.get("field_order", []),
        "permissions": dt_spec.get("permissions", []),
        "actions": dt_spec.get("actions", []),
        "links": dt_spec.get("links", []),
        "states": dt_spec.get("states", []),
    }

    if exists:
        doc = frappe.get_doc("DocType", name)
        for k, v in payload.items():
            if k in ("doctype", "name"):
                continue
            try:
                doc.set(k, v)
            except Exception:
                pass
        doc.save(ignore_permissions=True)
        frappe.db.commit()
        _log(f"UPDATED: {name}")
    else:
        doc = frappe.get_doc(payload)
        doc.insert(ignore_permissions=True)
        frappe.db.commit()
        _log(f"CREATED: {name}")

def _log(msg: str):
    frappe.logger("aau_university").info(f"{LOG_PREFIX} {msg}")

def _is_done() -> bool:
    return bool(frappe.db.get_single_value("System Settings", "aau_doctype_import_done") or 0) if _has_flag_field() else False

def _mark_done():
    _ensure_flag_field()
    frappe.db.set_value("System Settings", "System Settings", "aau_doctype_import_done", 1)
    frappe.db.commit()

def _force() -> bool:
    # Force rerun by setting env var: AAU_FORCE_DOCTYPE_IMPORT=1
    return str(frappe.conf.get("AAU_FORCE_DOCTYPE_IMPORT") or "").strip() in ("1", "true", "True", "yes", "YES")

def _has_flag_field() -> bool:
    return frappe.db.exists("DocField", {"parent": "System Settings", "fieldname": "aau_doctype_import_done"})

def _ensure_flag_field():
    # Adds a small flag field into System Settings to mark run-once
    if _has_flag_field():
        return

    # Insert custom field into System Settings
    df = frappe.get_doc({
        "doctype": "DocField",
        "parent": "System Settings",
        "parenttype": "DocType",
        "parentfield": "fields",
        "fieldname": "aau_doctype_import_done",
        "label": "AAU Doctype Import Done",
        "fieldtype": "Check",
        "insert_after": "language",
        "read_only": 1,
        "hidden": 1,
    })
    df.insert(ignore_permissions=True)
    frappe.db.commit()
