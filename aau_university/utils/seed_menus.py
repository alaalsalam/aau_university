# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from pathlib import Path

import frappe

SEED_FILE = Path(__file__).resolve().parents[1] / "seed" / "data" / "menus.json"


def seed_menus(site: str | None = None):
    connected_here = _connect_if_needed(site)
    try:
        payload = _load_menus_seed_data()
        doctype = "AAU Menu" if frappe.db.exists("DocType", "AAU Menu") else None
        if not doctype:
            return {"ok": True, "data": {"created": 0, "updated": 0, "skipped": 0, "total": 0, "message": "DocType missing"}}

        created = 0
        updated = 0
        skipped = 0

        for key, raw_items in payload.items():
            items = _normalize_items(raw_items)
            action = _upsert_menu(doctype, key, items)
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
                "created": created,
                "updated": updated,
                "skipped": skipped,
                "total": len(payload),
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


def _load_menus_seed_data() -> dict:
    # WHY+WHAT: load git-versioned main/footer/social link sets extracted from frontend so header/footer menus can be seeded consistently across sites.
    if not SEED_FILE.exists():
        frappe.throw(f"Seed file not found: {SEED_FILE}")
    with SEED_FILE.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    return payload if isinstance(payload, dict) else {}


def _normalize_items(raw_items: list[dict]) -> list[dict]:
    output = []
    for index, item in enumerate(raw_items or [], start=1):
        if not isinstance(item, dict):
            continue
        output.append(
            {
                "label_ar": item.get("labelAr") or "",
                "label_en": item.get("labelEn") or "",
                "url": item.get("url") or "",
                "group": item.get("group") or "",
                "open_in_new_tab": 1 if item.get("openInNewTab") else 0,
                "order": int(item.get("order") or index),
            }
        )
    output.sort(key=lambda row: (row["order"], row["url"]))
    return output


def _upsert_menu(doctype: str, key: str, items: list[dict]) -> str:
    existing_name = frappe.db.get_value(doctype, {"key": key}, "name")
    if not existing_name:
        doc = frappe.get_doc({"doctype": doctype, "key": key, "published": 1})
        for item in items:
            doc.append("items", {"doctype": "AAU Menu Item", **item})
        doc.insert(ignore_permissions=True)
        return "created"

    doc = frappe.get_doc(doctype, existing_name)
    current = [
        {
            "label_ar": row.get("label_ar") or "",
            "label_en": row.get("label_en") or "",
            "url": row.get("url") or "",
            "group": row.get("group") or "",
            "open_in_new_tab": 1 if row.get("open_in_new_tab") else 0,
            "order": int(row.get("order") or row.get("idx") or 0),
        }
        for row in (doc.get("items") or [])
    ]
    current.sort(key=lambda row: (row["order"], row["url"]))

    needs_update = current != items or not doc.get("published")
    if not needs_update:
        return "skipped"

    doc.set("published", 1)
    doc.set("items", [])
    for item in items:
        doc.append("items", {"doctype": "AAU Menu Item", **item})
    doc.save(ignore_permissions=True)
    return "updated"
