# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from pathlib import Path

import frappe

SEED_FILE = Path(__file__).resolve().parents[1] / "seed" / "data" / "events.json"


def seed_events(site: str | None = None):
    connected_here = _connect_if_needed(site)
    try:
        rows = _load_events_seed_data()
        doctype = _first_existing_doctype(["Events", "Event"])
        if not doctype:
            return {"ok": True, "data": {"doctype": None, "created": 0, "updated": 0, "skipped": len(rows), "message": "DocType missing"}}

        created = 0
        updated = 0
        skipped = 0

        for index, row in enumerate(rows, start=1):
            action = _upsert_event(doctype, _map_event_row(row or {}, index))
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


def _load_events_seed_data() -> list[dict]:
    # WHY+WHAT: load git-versioned events extracted from frontend mock data so public event pages can be populated consistently on any site.
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


def _upsert_event(doctype: str, payload: dict) -> str:
    meta = frappe.get_meta(doctype)
    allowed_fields = {df.fieldname for df in meta.fields if df.fieldname}
    values = {key: value for key, value in payload.items() if key in allowed_fields and value not in (None, "")}
    if not values:
        return "skipped"

    existing = _find_existing_event(doctype, values, allowed_fields)
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


def _find_existing_event(doctype: str, values: dict, allowed_fields: set[str]) -> str | None:
    if "slug" in allowed_fields and values.get("slug"):
        name = frappe.db.get_value(doctype, {"slug": values["slug"]}, "name")
        if name:
            return name

    for fieldname in ["title_en", "title_ar", "event_title", "title", "id"]:
        if fieldname in allowed_fields and values.get(fieldname):
            name = frappe.db.get_value(doctype, {fieldname: values[fieldname]}, "name")
            if name:
                return name
    return None


def _map_event_row(row: dict, index: int) -> dict:
    return {
        "id": row.get("id"),
        "slug": row.get("slug"),
        "event_title": row.get("titleEn") or row.get("titleAr"),
        "title": row.get("titleEn") or row.get("titleAr"),
        "title_en": row.get("titleEn"),
        "title_ar": row.get("titleAr"),
        "description": row.get("descriptionEn") or row.get("descriptionAr"),
        "description_en": row.get("descriptionEn"),
        "description_ar": row.get("descriptionAr"),
        "content": row.get("contentEn") or row.get("contentAr"),
        "content_en": row.get("contentEn"),
        "content_ar": row.get("contentAr"),
        "date": _to_iso_date(row.get("date")),
        "event_date": _to_iso_date(row.get("date")),
        "end_date": _to_iso_date(row.get("endDate")),
        "location": row.get("locationEn") or row.get("locationAr"),
        "location_en": row.get("locationEn"),
        "location_ar": row.get("locationAr"),
        "organizer": row.get("organizerEn") or row.get("organizerAr"),
        "organizer_en": row.get("organizerEn"),
        "organizer_ar": row.get("organizerAr"),
        "category": row.get("category") or "other",
        "status": row.get("status") or "upcoming",
        "registration_required": 1 if row.get("registrationRequired") else 0,
        "registration_link": row.get("registrationLink"),
        "image": row.get("image"),
        "is_published": 1,
        "display_order": index,
    }


def _to_iso_date(value: str | None) -> str | None:
    if not value:
        return None
    raw = str(value)
    return raw[:10] if len(raw) >= 10 else None
