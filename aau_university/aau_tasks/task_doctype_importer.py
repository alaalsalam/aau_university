# -*- coding: utf-8 -*-
"""
AAU - Import DocTypes from JSON by saving an ERPNext Task

Trigger:
- Task.subject starts with: "AAU:IMPORT"
Controls (inside Task.description):
- SPEC_PATH=/absolute/path/aau_doctypes_spec.json
- UPDATE_EXISTING=0 or 1
Optional:
- FORCE=1  (forces run even if already completed)

Logging:
- Appends logs into Task.description (no Server Script needed)

Safe:
- Uses frappe.db.set_value (does not re-trigger Task hooks)
"""

from __future__ import annotations

import json
import frappe
from frappe.utils import now_datetime


TRIGGER_PREFIX = "AAU:IMPORT"
LOG_PREFIX = "[AAU IMPORT]"


def on_task_update(doc, method=None):
    """Doc Event: Task.on_update"""
    try:
        subject = (doc.subject or "").strip()
        if not subject.upper().startswith(TRIGGER_PREFIX):
            return

        desc = (doc.description or "")
        spec_path = _extract_value(desc, "SPEC_PATH")
        update_existing = _extract_value(desc, "UPDATE_EXISTING") or "0"
        force = _extract_value(desc, "FORCE") or "0"

        # normalize
        spec_path = (spec_path or "").strip()
        update_existing_bool = str(update_existing).strip() in ("1", "true", "True", "yes", "YES")
        force_bool = str(force).strip() in ("1", "true", "True", "yes", "YES")

        # basic validation
        if not spec_path:
            _log(doc.name, f"{LOG_PREFIX} STOP: SPEC_PATH missing\n")
            return

        # avoid repeated runs (unless FORCE=1)
        existing_desc = frappe.db.get_value("Task", doc.name, "description") or ""
        if (f"{LOG_PREFIX} COMPLETED" in existing_desc) and not force_bool:
            _log(doc.name, f"{LOG_PREFIX} SKIP: already completed (set FORCE=1 to rerun)\n")
            return

        run_import(
            task_name=doc.name,
            spec_path=spec_path,
            update_existing=update_existing_bool
        )

    except Exception:
        # write traceback into description for visibility
        _log(doc.name, f"{LOG_PREFIX} FAILED ❌\n{frappe.get_traceback()}\n")


@frappe.whitelist()
def run_import(task_name: str, spec_path: str, update_existing: bool = False):
    """Callable manually or via Task hook."""
    _log(task_name, f"\n{LOG_PREFIX} START {now_datetime()}\n")
    _log(task_name, f"{LOG_PREFIX} SPEC_PATH={spec_path}\n")
    _log(task_name, f"{LOG_PREFIX} UPDATE_EXISTING={update_existing}\n")

    # Read JSON
    spec_text = _read_text_file(spec_path)
    spec = json.loads(spec_text)

    doctypes = spec.get("doctypes") or []
    if not doctypes:
        _log(task_name, f"{LOG_PREFIX} ERROR: Spec has no doctypes\n")
        return

    child = [d for d in doctypes if int(d.get("istable", 0) or 0) == 1]
    parent = [d for d in doctypes if int(d.get("istable", 0) or 0) == 0]
    _log(task_name, f"{LOG_PREFIX} DOCTYPES total={len(doctypes)} child={len(child)} parent={len(parent)}\n")

    # Create child tables first
    for dt in child:
        _create_or_update_doctype(dt, update_existing, task_name)

    # Then parents
    for dt in parent:
        _create_or_update_doctype(dt, update_existing, task_name)

    _log(task_name, f"{LOG_PREFIX} COMPLETED ✅ {now_datetime()}\n")


# -------------------------
# Internals
# -------------------------

def _extract_value(desc: str, key: str) -> str:
    """
    Robust key extraction from description.
    Accepts:
      KEY=value
    Supports any newline type.
    """
    if not desc:
        return ""

    # normalize newlines
    text = desc.replace("\r\n", "\n").replace("\r", "\n").replace("\u2028", "\n").replace("\u2029", "\n")

    needle = f"{key}="
    if needle not in text:
        return ""

    # get substring after KEY=
    part = text.split(needle, 1)[1]

    # stop at next line
    first_line = part.split("\n", 1)[0].strip()

    # sometimes people put extra spaces, keep it clean
    return first_line.strip()


def _read_text_file(path: str) -> str:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        raise RuntimeError(f"Cannot read spec file: {path} | {e}")


def _log(task_name: str, msg: str):
    """Append logs to Task.description without triggering hooks."""
    current = frappe.db.get_value("Task", task_name, "description") or ""
    frappe.db.set_value("Task", task_name, "description", current + msg, update_modified=False)


def _ensure_module_def(module_name: str, app_name: str = "aau_university"):
    if not frappe.db.exists("Module Def", module_name):
        doc = frappe.get_doc({
            "doctype": "Module Def",
            "module_name": module_name,
            "app_name": app_name,
            "custom": 1
        })
        doc.insert(ignore_permissions=True)


def _create_or_update_doctype(dt_spec: dict, update_existing: bool, task_name: str):
    name = dt_spec.get("name")
    module = dt_spec.get("module") or "AAU"
    _ensure_module_def(module)

    exists = frappe.db.exists("DocType", name)
    if exists and not update_existing:
        _log(task_name, f"{LOG_PREFIX} SKIP (exists): {name}\n")
        return

    payload = {
        "doctype": "DocType",
        "name": name,
        "module": module,
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
        "states": dt_spec.get("states", [])
    }

    if exists:
        dt = frappe.get_doc("DocType", name)
        for k, v in payload.items():
            if k in ("doctype", "name"):
                continue
            try:
                dt.set(k, v)
            except Exception:
                pass
        dt.save(ignore_permissions=True)
        frappe.db.commit()
        _log(task_name, f"{LOG_PREFIX} UPDATED: {name}\n")
    else:
        dt = frappe.get_doc(payload)
        dt.insert(ignore_permissions=True)
        frappe.db.commit()
        _log(task_name, f"{LOG_PREFIX} CREATED: {name}\n")
