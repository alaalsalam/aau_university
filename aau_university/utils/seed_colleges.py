# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from pathlib import Path

import frappe

SEED_FILE = Path(__file__).resolve().parents[1] / "seed" / "data" / "colleges.json"


def seed_colleges(site: str | None = None):
    connected_here = _connect_if_needed(site)
    try:
        rows = _load_colleges_seed_data()
        doctype = _first_existing_doctype(["Colleges", "College"])
        if not doctype:
            return {"ok": True, "data": {"doctype": None, "created": 0, "updated": 0, "skipped": len(rows), "message": "DocType missing"}}

        created = 0
        updated = 0
        skipped = 0

        for index, row in enumerate(rows, start=1):
            action = _upsert_college(doctype, _map_college_row(row or {}, index))
            if action == "created":
                created += 1
            elif action == "updated":
                updated += 1
            else:
                skipped += 1

        frappe.db.commit()
        return {
            "ok": True,
            "data": {
                "doctype": doctype,
                "created": created,
                "updated": updated,
                "skipped": skipped,
                "total": len(rows),
            },
        }
    finally:
        if connected_here:
            frappe.destroy()


def _connect_if_needed(site: str | None) -> bool:
    if not site or getattr(frappe.local, "site", None):
        return False
    frappe.init(site=site)
    frappe.connect()
    return True


def _load_colleges_seed_data() -> list[dict]:
    # WHY+WHAT: load git-versioned colleges and embedded programs extracted from frontend mocks so list/detail pages can be populated consistently on any site.
    if not SEED_FILE.exists():
        frappe.throw(f"Seed file not found: {SEED_FILE}")
    with SEED_FILE.open("r", encoding="utf-8") as handle:
        rows = json.load(handle)
    return rows if isinstance(rows, list) else []


def _first_existing_doctype(candidates: list[str]) -> str | None:
    for doctype in candidates:
        if frappe.db.exists("DocType", doctype):
            return doctype
    return None


def _upsert_college(doctype: str, payload: dict) -> str:
    meta = frappe.get_meta(doctype)
    allowed_fields = {df.fieldname for df in meta.fields if df.fieldname}
    values = {key: value for key, value in payload.items() if key in allowed_fields and value not in (None, "")}
    if not values:
        return "skipped"

    existing = _find_existing_college(doctype, values, allowed_fields)
    if existing:
        doc = frappe.get_doc(doctype, existing)
        changed = False
        for fieldname, value in values.items():
            if doc.get(fieldname) != value:
                doc.set(fieldname, value)
                changed = True
        if changed:
            doc.save(ignore_permissions=True)
            return "updated"
        return "skipped"

    doc = frappe.get_doc({"doctype": doctype, **values})
    doc.insert(ignore_permissions=True)
    return "created"


def _find_existing_college(doctype: str, values: dict, allowed_fields: set[str]) -> str | None:
    if "slug" in allowed_fields and values.get("slug"):
        name = frappe.db.get_value(doctype, {"slug": values["slug"]}, "name")
        if name:
            return name

    for fieldname in ["name_en", "name_ar", "college_name"]:
        if fieldname in allowed_fields and values.get(fieldname):
            name = frappe.db.get_value(doctype, {fieldname: values[fieldname]}, "name")
            if name:
                return name
    return None


def _map_college_row(row: dict, index: int) -> dict:
    programs = row.get("programs") if isinstance(row.get("programs"), list) else []
    return {
        "id": row.get("id"),
        "slug": row.get("slug"),
        "college_name": row.get("nameEn") or row.get("nameAr"),
        "name_ar": row.get("nameAr"),
        "name_en": row.get("nameEn"),
        "description": row.get("descriptionEn") or row.get("descriptionAr"),
        "description_ar": row.get("descriptionAr"),
        "description_en": row.get("descriptionEn"),
        "vision_ar": row.get("visionAr"),
        "vision_en": row.get("visionEn"),
        "mission_ar": row.get("missionAr"),
        "mission_en": row.get("missionEn"),
        "goals_ar": row.get("goalsAr"),
        "goals_en": row.get("goalsEn"),
        "admission_requirements_ar": row.get("admissionRequirementsAr"),
        "admission_requirements_en": row.get("admissionRequirementsEn"),
        "icon": row.get("icon"),
        "image": row.get("image"),
        "programs_json": json.dumps(programs, ensure_ascii=False),
        "is_active": 1,
        "display_order": index,
    }
