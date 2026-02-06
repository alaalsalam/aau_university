# -*- coding: utf-8 -*-
import frappe
from frappe.utils import now_datetime

def _append_to_task(task_name: str, msg: str):
    # يضيف السجل إلى description بشكل تراكمي
    current = frappe.db.get_value("Task", task_name, "description") or ""
    frappe.db.set_value("Task", task_name, "description", current + msg)

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
    name = dt_spec["name"]
    module = dt_spec.get("module") or "AAU"
    _ensure_module_def(module)

    exists = frappe.db.exists("DocType", name)
    if exists and not update_existing:
        _append_to_task(task_name, f"[{now_datetime()}] SKIP (exists): {name}\n")
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
                # بعض الخصائص قد تختلف حسب نسخة frappe
                pass
        doc.save(ignore_permissions=True)
        frappe.db.commit()
        _append_to_task(task_name, f"[{now_datetime()}] UPDATED: {name}\n")
    else:
        doc = frappe.get_doc(payload)
        doc.insert(ignore_permissions=True)
        frappe.db.commit()
        _append_to_task(task_name, f"[{now_datetime()}] CREATED: {name}\n")

@frappe.whitelist()
def run_import(task_name: str, spec_path: str, update_existing: int = 0):
    """
    يشغّل استيراد جميع DocTypes من JSON ويكتب الـ log في Task.description
    - task_name: اسم الـ Task
    - spec_path: مسار ملف JSON على السيرفر
    - update_existing: 0/1
    """
    update_existing = bool(int(update_existing or 0))

    _append_to_task(task_name, f"\n[{now_datetime()}] AAU Import started\n")
    _append_to_task(task_name, f"[{now_datetime()}] spec_path: {spec_path}\n")
    _append_to_task(task_name, f"[{now_datetime()}] update_existing: {update_existing}\n")

    # قراءة JSON كنص ثم parse بدون استيراد json (نستخدم frappe.parse_json)
    with open(spec_path, "r", encoding="utf-8") as f:
        raw = f.read()

    spec = frappe.parse_json(raw)
    doctypes = spec.get("doctypes") or []
    if not doctypes:
        _append_to_task(task_name, f"[{now_datetime()}] ERROR: Spec has no doctypes\n")
        return

    child = [d for d in doctypes if int(d.get("istable", 0)) == 1]
    parent = [d for d in doctypes if int(d.get("istable", 0)) == 0]

    _append_to_task(task_name, f"[{now_datetime()}] Doctypes total={len(doctypes)} child={len(child)} parent={len(parent)}\n")

    for dt in child:
        _create_or_update_doctype(dt, update_existing, task_name)

    for dt in parent:
        _create_or_update_doctype(dt, update_existing, task_name)

    _append_to_task(task_name, f"[{now_datetime()}] AAU Import completed ✅\n")
