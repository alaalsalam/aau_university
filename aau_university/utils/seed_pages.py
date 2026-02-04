# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from pathlib import Path

import frappe

SEED_FILE = Path(__file__).resolve().parents[1] / "seed" / "data" / "pages.json"


def seed_pages(site: str | None = None):
    connected_here = _connect_if_needed(site)
    try:
        rows = _load_pages_seed_data()
        doctype = _first_existing_doctype(["AAU Page", "Static Page"])
        if not doctype:
            return {"ok": True, "data": {"doctype": None, "created": 0, "updated": 0, "skipped": len(rows), "message": "DocType missing"}}

        created = 0
        updated = 0
        skipped = 0

        for row in rows:
            action = _upsert_page(doctype, _map_page_row(row or {}))
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


def _load_pages_seed_data() -> list[dict]:
    # WHY+WHAT: load git-versioned static page content extracted from frontend so new sites can bootstrap About/Admission/Contact immediately.
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


def _upsert_page(doctype: str, payload: dict) -> str:
    meta = frappe.get_meta(doctype)
    allowed_fields = {df.fieldname for df in meta.fields if df.fieldname}
    values = {key: value for key, value in payload.items() if key in allowed_fields and value not in (None, "")}
    if not values:
        return "skipped"

    slug = values.get("slug")
    existing = frappe.db.get_value(doctype, {"slug": slug}, "name") if slug else None
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


def _map_page_row(row: dict) -> dict:
    published = 1 if row.get("published", 1) else 0
    return {
        "slug": row.get("slug"),
        "title_ar": row.get("titleAr"),
        "title_en": row.get("titleEn"),
        "content_ar": row.get("contentAr"),
        "content_en": row.get("contentEn"),
        "hero_image": row.get("heroImage"),
        "published": published,
        "is_published": published,
        "page_title": row.get("titleEn"),
        "content": row.get("contentEn") or row.get("contentAr"),
        "banner_image": row.get("heroImage"),
    }
