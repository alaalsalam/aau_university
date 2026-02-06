# -*- coding: utf-8 -*-
"""
AAU - Import DocTypes from JSON Spec (screen by screen)

Project: AAU
Stage: MVP
Objective: استيراد/إنشاء جميع الشاشات (DocTypes) من ملف JSON شامل

Usage (bench console):
    import importlib
    from aau_university import aau_import_doctypes_from_json as imp
    importlib.reload(imp)
    imp.import_all("/path/to/aau_doctypes_spec.json", update_existing=False)

Notes:
- update_existing=False: يتخطى DocTypes الموجودة.
- update_existing=True : يحدث DocTypes الموجودة (حقول/خصائص) بما يطابق الـ JSON.
"""

import json
import frappe

def _ensure_module_def(module_name: str, app_name: str = "aau_university"):
    if not frappe.db.exists("Module Def", module_name):
        doc = frappe.get_doc({
            "doctype": "Module Def",
            "module_name": module_name,
            "app_name": app_name,
            "custom": 1
        })
        doc.insert(ignore_permissions=True)

def _create_or_update_doctype(dt_spec: dict, update_existing: bool = False):
    name = dt_spec["name"]
    module = dt_spec.get("module") or "AAU"
    _ensure_module_def(module)

    exists = frappe.db.exists("DocType", name)
    if exists and not update_existing:
        print(f"SKIP (exists): {name}")
        return

    payload = {
        "doctype": "DocType",
        "name": name,
        "module": module,
        "custom": int(dt_spec.get("custom", 1)),
        "istable": int(dt_spec.get("istable", 0)),
        "issingle": int(dt_spec.get("issingle", 0)),
        "allow_rename": int(dt_spec.get("allow_rename", 1)),
        "engine": dt_spec.get("engine", "InnoDB"),
        "track_changes": int(dt_spec.get("track_changes", 1)),
        "sort_field": dt_spec.get("sort_field", "modified"),
        "sort_order": dt_spec.get("sort_order", "DESC"),
        "row_format": dt_spec.get("row_format", "Dynamic"),
        "grid_page_length": int(dt_spec.get("grid_page_length", 50)),
        "rows_threshold_for_grid_search": int(dt_spec.get("rows_threshold_for_grid_search", 20)),
        "fields": dt_spec.get("fields", []),
        "field_order": dt_spec.get("field_order", []),
        "permissions": dt_spec.get("permissions", []),
        "actions": dt_spec.get("actions", []),
        "links": dt_spec.get("links", []),
        "states": dt_spec.get("states", [])
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
        print(f"UPDATED: {name}")
    else:
        doc = frappe.get_doc(payload)
        doc.insert(ignore_permissions=True)
        frappe.db.commit()
        print(f"CREATED: {name}")

def import_all(spec_path: str, update_existing: bool = False):
    with open(spec_path, "r", encoding="utf-8") as f:
        spec = json.load(f)

    doctypes = spec.get("doctypes") or []
    if not doctypes:
        raise RuntimeError("Spec file has no doctypes")

    # Create child tables first
    child = [d for d in doctypes if int(d.get("istable", 0)) == 1]
    parent = [d for d in doctypes if int(d.get("istable", 0)) == 0]

    for dt in child:
        _create_or_update_doctype(dt, update_existing=update_existing)

    for dt in parent:
        _create_or_update_doctype(dt, update_existing=update_existing)

    print("DONE ✅  تم استيراد جميع الشاشات")
