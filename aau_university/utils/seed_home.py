# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from pathlib import Path

import frappe

SEED_FILE = Path(__file__).resolve().parents[1] / "seed" / "data" / "home_content.json"


def seed_home(site: str | None = None):
    connected_here = _connect_if_needed(site)
    try:
        payload = _load_home_seed_data()
        summary = {
            "home_page": _seed_home_page(payload),
            "news": _seed_records(
                section="news",
                rows=payload.get("news", []),
                doctype_candidates=["News"],
                unique_fields=["slug", "title", "title_en", "title_ar"],
                mapper=_map_news,
            ),
            "events": _seed_records(
                section="events",
                rows=payload.get("events", []),
                doctype_candidates=["Events", "Event"],
                unique_fields=["slug", "event_title", "title"],
                mapper=_map_event,
            ),
            "colleges": _seed_records(
                section="colleges",
                rows=payload.get("colleges", []),
                doctype_candidates=["Colleges", "College"],
                unique_fields=["slug", "college_name", "name", "name_en", "name_ar"],
                mapper=_map_college,
            ),
            "faqs": _seed_records(
                section="faqs",
                rows=payload.get("faqs", []),
                doctype_candidates=["FAQs", "FAQ"],
                unique_fields=["slug", "title", "question", "question_en", "question_ar"],
                mapper=_map_faq,
            ),
        }
        frappe.db.commit()
        return {"ok": True, "data": summary}
    finally:
        if connected_here:
            frappe.destroy()


def _connect_if_needed(site: str | None) -> bool:
    if not site or getattr(frappe.local, "site", None):
        return False
    frappe.init(site=site)
    frappe.connect()
    return True


def _load_home_seed_data() -> dict:
    # WHY+WHAT: load git-versioned home JSON extracted from frontend mocks so any site can be populated consistently with one command.
    if not SEED_FILE.exists():
        frappe.throw(f"Seed file not found: {SEED_FILE}")
    with SEED_FILE.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _first_existing_doctype(candidates: list[str]) -> str | None:
    for doctype in candidates:
        if frappe.db.exists("DocType", doctype):
            return doctype
    return None


def _seed_home_page(seed_payload: dict) -> dict:
    doctype = _first_existing_doctype(["Home Page"])
    if not doctype:
        return {"doctype": None, "created": 0, "updated": 0, "skipped": 1, "message": "DocType missing"}

    home_sections_payload = {
        "hero": seed_payload.get("hero", {}),
        "stats": seed_payload.get("stats", []),
        "about": seed_payload.get("about", {}),
        "partners": seed_payload.get("partners", []),
        "testimonials": seed_payload.get("testimonials", []),
    }

    # WHY+WHAT: persist structured home sections JSON in Home Page so /api/aau/home can serve the non-list sections from database-backed seed content.
    payload = {
        "page_title": "AAU University Home",
        "hero_title": seed_payload.get("hero", {}).get("titlePrimaryEn", "Welcome to AAU University"),
        "hero_subtitle": seed_payload.get("hero", {}).get("badgeEn", "Welcome to AJ JEEL ALJADEED UNIVERSITY"),
        "hero_description": seed_payload.get("hero", {}).get("descriptionEn", "Discover programs, events, and student opportunities."),
        "hero_image": seed_payload.get("hero", {}).get("image"),
        "hero_cta_text": seed_payload.get("hero", {}).get("applyTextEn", "Apply Now"),
        "hero_cta_link": seed_payload.get("hero", {}).get("applyLink", "/admission"),
        "about_title": seed_payload.get("about", {}).get("titleEn", "About the University"),
        "about_description": seed_payload.get("about", {}).get("descriptionEn", ""),
        "students_count": _to_int(seed_payload.get("stats", [{}])[0].get("number")),
        "programs_count": _to_int(seed_payload.get("stats", [{}, {}, {}])[2].get("number")),
        "graduates_count": 0,
        "home_sections_json": json.dumps(home_sections_payload, ensure_ascii=False),
        "is_published": 1,
    }
    action = _upsert_doc(doctype, payload, unique_fields=["page_title", "name"])
    return {
        "doctype": doctype,
        "created": 1 if action == "created" else 0,
        "updated": 1 if action == "updated" else 0,
        "skipped": 1 if action == "skipped" else 0,
    }


def _seed_records(
    section: str,
    rows: list[dict],
    doctype_candidates: list[str],
    unique_fields: list[str],
    mapper,
) -> dict:
    doctype = _first_existing_doctype(doctype_candidates)
    if not doctype:
        return {"doctype": None, "created": 0, "updated": 0, "skipped": len(rows), "message": "DocType missing"}

    created = 0
    updated = 0
    skipped = 0

    for index, row in enumerate(rows, start=1):
        payload = mapper(row or {}, index)
        action = _upsert_doc(doctype, payload, unique_fields=unique_fields)
        if action == "created":
            created += 1
        elif action == "updated":
            updated += 1
        else:
            skipped += 1

    return {
        "section": section,
        "doctype": doctype,
        "created": created,
        "updated": updated,
        "skipped": skipped,
    }


def _upsert_doc(doctype: str, payload: dict, unique_fields: list[str]) -> str:
    meta = frappe.get_meta(doctype)
    allowed_fields = {df.fieldname for df in meta.fields if df.fieldname}
    values = _normalize_values(payload, allowed_fields)

    if not values:
        return "skipped"

    existing_name = _find_existing_docname(doctype, values, allowed_fields, unique_fields)
    if existing_name:
        doc = frappe.get_doc(doctype, existing_name)
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


def _find_existing_docname(doctype: str, values: dict, allowed_fields: set[str], unique_fields: list[str]) -> str | None:
    for fieldname in unique_fields:
        if fieldname in allowed_fields and values.get(fieldname) not in (None, ""):
            existing = frappe.db.get_value(doctype, {fieldname: values[fieldname]}, "name")
            if existing:
                return existing

    fallback_fields = ["title", "event_title", "college_name", "page_title", "name"]
    for fieldname in fallback_fields:
        if fieldname in allowed_fields and values.get(fieldname) not in (None, ""):
            existing = frappe.db.get_value(doctype, {fieldname: values[fieldname]}, "name")
            if existing:
                return existing

    return None


def _normalize_values(payload: dict, allowed_fields: set[str]) -> dict:
    values = {key: value for key, value in payload.items() if key in allowed_fields}

    if "event_title" in allowed_fields and "event_title" not in values:
        values["event_title"] = payload.get("event_title") or payload.get("title") or payload.get("title_en")
    if "event_date" in allowed_fields and "event_date" not in values:
        values["event_date"] = payload.get("event_date") or payload.get("date") or payload.get("publish_date")
    if "location" in allowed_fields and "location" not in values:
        values["location"] = payload.get("location") or payload.get("location_en") or payload.get("location_ar")

    if "title" in allowed_fields and "title" not in values:
        values["title"] = payload.get("title") or payload.get("event_title") or payload.get("question")
    if "content" in allowed_fields and "content" not in values:
        values["content"] = payload.get("content") or payload.get("description") or payload.get("answer")
    if "publish_date" in allowed_fields and "publish_date" not in values:
        values["publish_date"] = payload.get("publish_date") or payload.get("date")
    if "college_name" in allowed_fields and "college_name" not in values:
        values["college_name"] = payload.get("college_name") or payload.get("name") or payload.get("name_en")

    return {key: value for key, value in values.items() if value not in (None, "")}


def _map_news(row: dict, index: int) -> dict:
    date_value = _to_iso_date(row.get("date"))
    return {
        "id": row.get("id"),
        "slug": row.get("slug"),
        "title": row.get("titleEn") or row.get("titleAr") or row.get("title"),
        "title_en": row.get("titleEn"),
        "title_ar": row.get("titleAr"),
        "summary": row.get("descriptionEn") or row.get("descriptionAr") or row.get("summary"),
        "description_en": row.get("descriptionEn"),
        "description_ar": row.get("descriptionAr"),
        "content": row.get("contentEn") or row.get("contentAr") or row.get("content"),
        "content_en": row.get("contentEn"),
        "content_ar": row.get("contentAr"),
        "publish_date": date_value,
        "date": date_value,
        "image": row.get("image"),
        "is_published": 1,
        "is_featured": row.get("isFeatured", 0),
        "display_order": index,
        "views": row.get("views", 0),
    }


def _map_event(row: dict, index: int) -> dict:
    return {
        "id": row.get("id"),
        "slug": row.get("slug"),
        "event_title": row.get("titleEn") or row.get("titleAr") or row.get("title"),
        "title": row.get("titleEn") or row.get("titleAr") or row.get("title"),
        "title_en": row.get("titleEn"),
        "title_ar": row.get("titleAr"),
        "description": row.get("descriptionEn") or row.get("descriptionAr") or row.get("description"),
        "description_en": row.get("descriptionEn"),
        "description_ar": row.get("descriptionAr"),
        "content": row.get("contentEn") or row.get("contentAr") or row.get("content"),
        "content_en": row.get("contentEn"),
        "content_ar": row.get("contentAr"),
        "event_date": _to_iso_date(row.get("date")),
        "date": _to_iso_date(row.get("date")),
        "end_date": _to_iso_date(row.get("endDate")),
        "location": row.get("locationEn") or row.get("locationAr") or row.get("location"),
        "location_en": row.get("locationEn"),
        "location_ar": row.get("locationAr"),
        "organizer_en": row.get("organizerEn"),
        "organizer_ar": row.get("organizerAr"),
        "category": row.get("category"),
        "status": row.get("status"),
        "registration_required": row.get("registrationRequired", False),
        "registration_link": row.get("registrationLink"),
        "image": row.get("image"),
        "is_published": 1,
        "display_order": index,
    }


def _map_college(row: dict, index: int) -> dict:
    return {
        "id": row.get("id"),
        "slug": row.get("slug"),
        "college_name": row.get("nameEn") or row.get("nameAr") or row.get("name"),
        "name": row.get("nameEn") or row.get("nameAr") or row.get("name"),
        "name_en": row.get("nameEn"),
        "name_ar": row.get("nameAr"),
        "description": row.get("descriptionEn") or row.get("descriptionAr") or row.get("description"),
        "description_en": row.get("descriptionEn"),
        "description_ar": row.get("descriptionAr"),
        "vision_en": row.get("visionEn"),
        "vision_ar": row.get("visionAr"),
        "mission_en": row.get("missionEn"),
        "mission_ar": row.get("missionAr"),
        "admission_requirements_en": row.get("admissionRequirementsEn"),
        "admission_requirements_ar": row.get("admissionRequirementsAr"),
        "icon": row.get("icon"),
        "image": row.get("image"),
        "is_active": 1,
        "display_order": index,
    }


def _map_faq(row: dict, index: int) -> dict:
    return {
        "id": row.get("id"),
        "slug": row.get("slug"),
        "title": row.get("questionEn") or row.get("questionAr") or row.get("question"),
        "question": row.get("questionEn") or row.get("questionAr") or row.get("question"),
        "question_en": row.get("questionEn"),
        "question_ar": row.get("questionAr"),
        "content": row.get("answerEn") or row.get("answerAr") or row.get("answer"),
        "answer_en": row.get("answerEn"),
        "answer_ar": row.get("answerAr"),
        "category": row.get("category"),
        "is_published": 1,
        "display_order": index,
    }


def _to_iso_date(value: str | None) -> str | None:
    if not value:
        return None
    value = str(value)
    if len(value) >= 10:
        return value[:10]
    return None


def _to_int(value: str | int | None) -> int:
    if value is None:
        return 0
    if isinstance(value, int):
        return value
    digits = "".join(char for char in str(value) if char.isdigit())
    return int(digits) if digits else 0
