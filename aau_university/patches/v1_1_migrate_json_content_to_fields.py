# -*- coding: utf-8 -*-
from __future__ import annotations

import json

import frappe

LOG_PREFIX = "[AAU JSON MIGRATION]"


def execute():
    logger = frappe.logger("aau_university")
    logger.info(f"{LOG_PREFIX} START")
    try:
        home_summary = _migrate_home_sections_json()
        programs_summary = _migrate_college_programs_json()
        frappe.db.commit()
        logger.info(
            f"{LOG_PREFIX} DONE | home_updated={home_summary['updated']} "
            f"programs_created={programs_summary['created']} programs_updated={programs_summary['updated']}"
        )
    except Exception:
        logger.error(f"{LOG_PREFIX} FAILED\n{frappe.get_traceback()}")


def _migrate_home_sections_json() -> dict:
    summary = {"updated": 0, "skipped": 0}
    if not frappe.db.exists("DocType", "Home Page"):
        return summary

    meta = frappe.get_meta("Home Page")
    if not meta.get_field("home_sections_json"):
        return summary

    rows = frappe.get_all(
        "Home Page",
        fields=["name", "home_sections_json", "hero_title", "hero_description", "hero_image", "hero_cta_text", "hero_cta_link", "about_title", "about_description"],
        ignore_permissions=True,
    )
    for row in rows:
        raw = row.get("home_sections_json")
        if not raw:
            summary["skipped"] += 1
            continue
        try:
            parsed = json.loads(raw)
        except Exception:
            summary["skipped"] += 1
            continue
        if not isinstance(parsed, dict):
            summary["skipped"] += 1
            continue

        hero = parsed.get("hero") if isinstance(parsed.get("hero"), dict) else {}
        about = parsed.get("about") if isinstance(parsed.get("about"), dict) else {}
        updates = {}

        if meta.get_field("hero_title") and not row.get("hero_title"):
            updates["hero_title"] = hero.get("titlePrimaryEn") or hero.get("titlePrimaryAr")
        if meta.get_field("hero_description") and not row.get("hero_description"):
            updates["hero_description"] = hero.get("descriptionEn") or hero.get("descriptionAr")
        if meta.get_field("hero_image") and not row.get("hero_image"):
            updates["hero_image"] = hero.get("image")
        if meta.get_field("hero_cta_text") and not row.get("hero_cta_text"):
            updates["hero_cta_text"] = hero.get("applyTextEn") or hero.get("applyTextAr")
        if meta.get_field("hero_cta_link") and not row.get("hero_cta_link"):
            updates["hero_cta_link"] = hero.get("applyLink")
        if meta.get_field("about_title") and not row.get("about_title"):
            updates["about_title"] = about.get("titleEn") or about.get("titleAr")
        if meta.get_field("about_description") and not row.get("about_description"):
            updates["about_description"] = about.get("descriptionEn") or about.get("descriptionAr")

        updates = {key: value for key, value in updates.items() if value not in (None, "")}
        if not updates:
            summary["skipped"] += 1
            continue

        frappe.db.set_value("Home Page", row["name"], updates, update_modified=False)
        summary["updated"] += 1

    return summary


def _migrate_college_programs_json() -> dict:
    summary = {"created": 0, "updated": 0, "skipped": 0}
    if not frappe.db.exists("DocType", "Colleges"):
        return summary
    if not frappe.db.exists("DocType", "Academic Programs"):
        return summary

    college_meta = frappe.get_meta("Colleges")
    if not college_meta.get_field("programs_json"):
        return summary

    program_meta = frappe.get_meta("Academic Programs")
    rows = frappe.get_all(
        "Colleges",
        fields=["name", "programs_json"],
        filters={"programs_json": ["is", "set"]},
        ignore_permissions=True,
    )
    for row in rows:
        parsed = _parse_programs_json(row.get("programs_json"))
        if not parsed:
            summary["skipped"] += 1
            continue

        for item in parsed:
            program_name = (item.get("nameEn") or item.get("nameAr") or "").strip()
            if not program_name:
                continue
            existing = frappe.db.get_value(
                "Academic Programs",
                {"college": row["name"], "program_name": program_name},
                "name",
            )

            payload = _map_program_payload(item, row["name"], program_meta)
            if existing:
                doc = frappe.get_doc("Academic Programs", existing)
                changed = False
                for fieldname, value in payload.items():
                    if doc.get(fieldname) != value:
                        doc.set(fieldname, value)
                        changed = True
                if changed:
                    doc.save(ignore_permissions=True)
                    summary["updated"] += 1
                else:
                    summary["skipped"] += 1
            else:
                doc = frappe.get_doc({"doctype": "Academic Programs", **payload})
                doc.insert(ignore_permissions=True)
                summary["created"] += 1
    return summary


def _map_program_payload(item: dict, college_name: str, meta) -> dict:
    payload = {"college": college_name}
    values = {
        "program_name": item.get("nameEn") or item.get("nameAr"),
        "description": item.get("descriptionEn") or item.get("descriptionAr"),
        "duration": item.get("studyYears"),
        "is_active": 1,
    }
    for fieldname, value in values.items():
        if meta.get_field(fieldname) and value not in (None, ""):
            payload[fieldname] = value
    return payload


def _parse_programs_json(raw: str | None) -> list[dict]:
    if not raw:
        return []
    try:
        parsed = json.loads(raw)
    except Exception:
        return []
    if not isinstance(parsed, list):
        return []
    return [row for row in parsed if isinstance(row, dict)]
