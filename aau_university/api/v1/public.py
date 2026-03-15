# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import re

import frappe
from frappe.translate import get_all_translations

from .registry import ADMIN_ROLES, SEARCH_TYPES
from .resources import (
    create_entity,
    delete_entity,
    get_entity,
    list_entities,
    update_status,
)
from .utils import api_endpoint, now_ts, require_roles, to_camel


@frappe.whitelist(allow_guest=True)
@api_endpoint
def create_contact_message(**payload):
    """Create a contact message."""
    payload = _merge_request_payload(payload)
    if payload.get("name") and not payload.get("sender_name"):
        payload["sender_name"] = payload.get("name")
    if payload.get("full_name") and not payload.get("sender_name"):
        payload["sender_name"] = payload.get("full_name")
    if payload.get("sender_name") and not payload.get("name"):
        payload["name"] = payload.get("sender_name")
    payload.setdefault("status", "new")
    return create_entity("contact_messages", payload, public=True), 201


@frappe.whitelist()
@api_endpoint
def list_contact_messages():
    """List contact messages."""
    require_roles(ADMIN_ROLES)
    result = list_entities("contact_messages", public=False)
    return {"data": result["data"], "meta": result["meta"], "__meta__": True}


@frappe.whitelist()
@api_endpoint
def get_contact_message(message_id: str):
    """Get a contact message by id."""
    require_roles(ADMIN_ROLES)
    return get_entity("contact_messages", message_id, by="id", public=False)


@frappe.whitelist()
@api_endpoint
def update_contact_message_status(message_id: str, status: str):
    """Update contact message status."""
    require_roles(ADMIN_ROLES)
    return update_status("contact_messages", message_id, "status", status)


@frappe.whitelist()
@api_endpoint
def delete_contact_message(message_id: str):
    """Delete a contact message."""
    require_roles(ADMIN_ROLES)
    return delete_entity("contact_messages", message_id, by="id")


@frappe.whitelist(allow_guest=True)
@api_endpoint
def create_join_request(**payload):
    """Create a join request."""
    payload = _merge_request_payload(payload)
    if payload.get("name") and not payload.get("full_name"):
        payload["full_name"] = payload.get("name")
    if payload.get("program") and not payload.get("specialty"):
        payload["specialty"] = payload.get("program")
    if payload.get("major") and not payload.get("specialty"):
        payload["specialty"] = payload.get("major")
    payload.setdefault("title", payload.get("full_name") or payload.get("name"))
    payload.setdefault("status", "pending")
    payload.setdefault("type", "student")
    return create_entity("join_requests", payload, public=True), 201


@frappe.whitelist()
@api_endpoint
def list_join_requests():
    """List join requests."""
    require_roles(ADMIN_ROLES)
    result = list_entities("join_requests", public=False)
    return {"data": result["data"], "meta": result["meta"], "__meta__": True}


@frappe.whitelist()
@api_endpoint
def get_join_request(request_id: str):
    """Get a join request by id."""
    require_roles(ADMIN_ROLES)
    return get_entity("join_requests", request_id, by="id", public=False)


@frappe.whitelist()
@api_endpoint
def update_join_request_status(request_id: str, status: str):
    """Update join request status."""
    require_roles(ADMIN_ROLES)
    return update_status("join_requests", request_id, "status", status)


@frappe.whitelist()
@api_endpoint
def delete_join_request(request_id: str):
    """Delete a join request."""
    require_roles(ADMIN_ROLES)
    return delete_entity("join_requests", request_id, by="id")


@frappe.whitelist(allow_guest=True)
@api_endpoint
def search(q: str, type: str | None = None):
    """Search across entities."""
    if not q:
        return {"results": [], "total": 0}

    types = [type] if type else list(SEARCH_TYPES.keys())
    results = []
    total = 0
    for key in types:
        doctype = SEARCH_TYPES.get(key)
        if not doctype:
            continue
        if not frappe.db.exists("DocType", doctype):
            continue
        meta = frappe.get_meta(doctype)
        selectable = _selectable_fields(doctype)
        search_fields = [f for f in ["title_ar", "title_en", "description_ar", "description_en"] if f in selectable]
        if not search_fields:
            continue
        or_filters = [[doctype, field, "like", f"%{q}%"] for field in search_fields]
        fields = [field for field in ["id", "title_ar", "title_en", "description_ar", "description_en", "image", "slug"] if field in selectable]
        if "name" not in fields:
            fields.append("name")
        rows = frappe.get_all(
            doctype,
            fields=fields,
            or_filters=or_filters,
            limit=20,
            ignore_permissions=True,
        )
        total += len(rows)
        for row in rows:
            results.append(
                {
                    "id": row.get("id") or row.get("name"),
                    "type": key,
                    "titleAr": row.get("title_ar"),
                    "titleEn": row.get("title_en"),
                    "descriptionAr": row.get("description_ar"),
                    "descriptionEn": row.get("description_en"),
                    "link": _build_link(key, row.get("slug") or row.get("id")),
                    "image": row.get("image"),
                }
            )
    return {"results": results, "total": total}


@frappe.whitelist(allow_guest=True)
@api_endpoint
def get_home():
    # WHY+WHAT: aggregate home sections in one public call to reduce frontend round-trips and return news/events/colleges/faqs with generation metadata.
    try:
        home_sections = _get_home_sections()
        return {
            "hero": home_sections["hero"],
            "stats": home_sections["stats"],
            "about": home_sections["about"],
            "sections": home_sections["sections"],
            "siteProfile": _build_site_profile_payload(),
            "campusLife": _list_home_campus_life(limit=3),
            "projects": _list_home_projects(limit=3),
            "partners": home_sections["partners"],
            "testimonials": home_sections["testimonials"],
            # WHY+WHAT: return minimal, frontend-shaped payloads for list sections (avoid raw DocType column spillover).
            "news": _list_home_news(limit=4),
            "events": _list_home_events(limit=4),
            "colleges": _list_home_colleges(limit=6),
            "faqs": _list_home_faqs(limit=6),
            "meta": {
                "generated_at": now_ts(),
                "source": _home_source(),
            },
        }
    except Exception:
        # WHY+WHAT: log minimal server-side diagnostics for unexpected home aggregation failures while keeping the public response contract stable.
        frappe.log_error(frappe.get_traceback(), "AAU Home API get_home failure")
        return {
            "hero": {},
            "stats": [],
            "about": {},
            "sections": {},
            "siteProfile": _build_site_profile_payload(),
            "campusLife": [],
            "projects": [],
            "partners": [],
            "testimonials": [],
            "news": [],
            "events": [],
            "colleges": [],
            "faqs": [],
            "meta": {
                "generated_at": now_ts(),
                "source": _home_source(),
            },
        }


@frappe.whitelist(allow_guest=True)
@api_endpoint
def get_about_page():
    try:
        return _build_about_page_payload()
    except Exception:
        frappe.log_error(frappe.get_traceback(), "AAU About API get_about_page failure")
        return {
            "pageHeader": {},
            "intro": {},
            "identity": [],
            "presidentMessage": {},
            "team": {"titleAr": "", "titleEn": "", "descriptionAr": "", "descriptionEn": "", "groups": []},
            "meta": {"generated_at": now_ts(), "source": "About University"},
        }


@frappe.whitelist(allow_guest=True)
@api_endpoint
def get_contact_page():
    try:
        return _build_contact_page_payload()
    except Exception:
        frappe.log_error(frappe.get_traceback(), "AAU Contact API get_contact_page failure")
        return {
            "pageHeader": {},
            "form": {},
            "social": {},
            "siteProfile": _build_site_profile_payload(),
            "meta": {"generated_at": now_ts(), "source": "Website Settings"},
        }


@frappe.whitelist(allow_guest=True)
@api_endpoint
def list_public_news(limit: int | None = None, page: int | None = None):
    # WHY+WHAT: keep separate list/detail news endpoints so listing stays lightweight while detail fetches one record, which is low-risk and scales cleanly.
    doctype = _first_existing_doctype(["News"])
    if not doctype:
        return {"items": [], "pagination": {"page": 1, "limit": 10, "total": 0, "has_more": False}}

    form_dict = getattr(frappe.local, "form_dict", {}) or {}
    parsed_limit = max(1, min(int(limit or form_dict.get("limit") or 10), 50))
    parsed_page = max(1, int(page or form_dict.get("page") or 1))
    offset = (parsed_page - 1) * parsed_limit

    meta = frappe.get_meta(doctype)
    db_fields = {
        df.fieldname
        for df in meta.fields
        if df.fieldname and df.fieldtype not in {"Section Break", "Column Break", "Tab Break", "Fold", "HTML", "Button"}
    }
    filters = {"is_published": 1} if "is_published" in db_fields else {}
    total = frappe.db.count(doctype, filters=filters)
    order_by = "date desc, publish_date desc, modified desc"
    if "display_order" in db_fields:
        order_by = "display_order asc, date desc, publish_date desc, modified desc"

    rows = frappe.get_all(
        doctype,
        fields=list(db_fields),
        filters=filters,
        order_by=order_by,
        limit_start=offset,
        limit_page_length=parsed_limit,
        ignore_permissions=True,
    )
    items = [_serialize_news_item(row) for row in rows]
    return {
        "items": items,
        "pagination": {
            "page": parsed_page,
            "limit": parsed_limit,
            "total": total,
            "has_more": offset + len(items) < total,
        },
    }


@frappe.whitelist(allow_guest=True)
@api_endpoint
def get_public_news(slug: str):
    doctype = _first_existing_doctype(["News"])
    if not doctype:
        raise frappe.DoesNotExistError("News not found")

    meta = frappe.get_meta(doctype)
    db_fields = {
        df.fieldname
        for df in meta.fields
        if df.fieldname and df.fieldtype not in {"Section Break", "Column Break", "Tab Break", "Fold", "HTML", "Button"}
    }
    filters = {"slug": slug} if "slug" in db_fields else {"name": slug}
    if "is_published" in db_fields:
        filters["is_published"] = 1

    row = frappe.db.get_value(doctype, filters, list(db_fields), as_dict=True)
    if not row:
        # WHY+WHAT: keep detail endpoint resilient for pre-existing rows that may not have slug populated by matching computed slug from title.
        fallback_filters = {"is_published": 1} if "is_published" in db_fields else {}
        candidates = frappe.get_all(
            doctype,
            fields=list(db_fields),
            filters=fallback_filters,
            ignore_permissions=True,
            limit_page_length=200,
            order_by="modified desc",
        )
        for candidate in candidates:
            candidate_slug = _serialize_news_item(candidate).get("slug")
            if candidate_slug == slug or candidate.get("name") == slug:
                row = candidate
                break
    if not row:
        raise frappe.DoesNotExistError("News not found")

    return _serialize_news_item(row)


@frappe.whitelist(allow_guest=True)
@api_endpoint
def list_public_events(limit: int | None = None, page: int | None = None):
    # WHY+WHAT: keep list+detail public endpoints separate so event listing stays lean and details are fetched only when needed for low-risk scaling.
    doctype = _first_existing_doctype(["Events", "Event"])
    if not doctype:
        return {"items": [], "pagination": {"page": 1, "limit": 10, "total": 0, "has_more": False}}

    form_dict = getattr(frappe.local, "form_dict", {}) or {}
    parsed_limit = max(1, min(int(limit or form_dict.get("limit") or 10), 50))
    parsed_page = max(1, int(page or form_dict.get("page") or 1))
    offset = (parsed_page - 1) * parsed_limit

    meta = frappe.get_meta(doctype)
    db_fields = {
        df.fieldname
        for df in meta.fields
        if df.fieldname and df.fieldtype not in {"Section Break", "Column Break", "Tab Break", "Fold", "HTML", "Button"}
    }
    filters = {"is_published": 1} if "is_published" in db_fields else {}
    total = frappe.db.count(doctype, filters=filters)
    sort_parts = []
    if "display_order" in db_fields:
        sort_parts.append("display_order asc")
    if "date" in db_fields:
        sort_parts.append("date desc")
    if "event_date" in db_fields:
        sort_parts.append("event_date desc")
    sort_parts.append("modified desc")
    order_by = ", ".join(sort_parts)

    rows = frappe.get_all(
        doctype,
        fields=list(db_fields),
        filters=filters,
        order_by=order_by,
        limit_start=offset,
        limit_page_length=parsed_limit,
        ignore_permissions=True,
    )
    items = [_serialize_event_item(row) for row in rows]
    return {
        "items": items,
        "pagination": {
            "page": parsed_page,
            "limit": parsed_limit,
            "total": total,
            "has_more": offset + len(items) < total,
        },
    }


@frappe.whitelist(allow_guest=True)
@api_endpoint
def get_public_event(slug: str):
    doctype = _first_existing_doctype(["Events", "Event"])
    if not doctype:
        raise frappe.DoesNotExistError("Event not found")

    meta = frappe.get_meta(doctype)
    db_fields = {
        df.fieldname
        for df in meta.fields
        if df.fieldname and df.fieldtype not in {"Section Break", "Column Break", "Tab Break", "Fold", "HTML", "Button"}
    }
    filters = {"slug": slug} if "slug" in db_fields else {"name": slug}
    if "is_published" in db_fields:
        filters["is_published"] = 1

    row = frappe.db.get_value(doctype, filters, list(db_fields), as_dict=True)
    if not row:
        # WHY+WHAT: support existing rows missing slug by matching the computed slug from title/event_title so rollout is backward-compatible.
        fallback_filters = {"is_published": 1} if "is_published" in db_fields else {}
        candidates = frappe.get_all(
            doctype,
            fields=list(db_fields),
            filters=fallback_filters,
            ignore_permissions=True,
            limit_page_length=200,
            order_by="modified desc",
        )
        for candidate in candidates:
            candidate_slug = _serialize_event_item(candidate).get("slug")
            if candidate_slug == slug or candidate.get("name") == slug:
                row = candidate
                break
    if not row:
        raise frappe.DoesNotExistError("Event not found")

    return _serialize_event_item(row)


@frappe.whitelist(allow_guest=True)
@api_endpoint
def list_public_colleges(limit: int | None = None, page: int | None = None):
    # WHY+WHAT: expose colleges via minimal guest list/detail endpoints, embedding programs only where current UI needs them to avoid extra endpoints.
    doctype = _first_existing_doctype(["Colleges", "College"])
    if not doctype:
        return {"items": [], "pagination": {"page": 1, "limit": 10, "total": 0, "has_more": False}}

    form_dict = getattr(frappe.local, "form_dict", {}) or {}
    parsed_limit = max(1, min(int(limit or form_dict.get("limit") or 10), 50))
    parsed_page = max(1, int(page or form_dict.get("page") or 1))
    offset = (parsed_page - 1) * parsed_limit

    meta = frappe.get_meta(doctype)
    db_fields = {
        df.fieldname
        for df in meta.fields
        if df.fieldname and df.fieldtype not in {"Section Break", "Column Break", "Tab Break", "Fold", "HTML", "Button"}
    }
    filters = {"is_active": 1} if "is_active" in db_fields else {}
    total = frappe.db.count(doctype, filters=filters)
    sort_parts = []
    if "display_order" in db_fields:
        sort_parts.append("display_order asc")
    sort_parts.append("modified desc")
    order_by = ", ".join(sort_parts)

    fields = ["name", *sorted(db_fields)] if "name" not in db_fields else sorted(db_fields)
    rows = frappe.get_all(
        doctype,
        fields=fields,
        filters=filters,
        order_by=order_by,
        limit_start=offset,
        limit_page_length=parsed_limit,
        ignore_permissions=True,
    )
    items = [_serialize_college_item(row) for row in rows]
    return {
        "items": items,
        "pagination": {
            "page": parsed_page,
            "limit": parsed_limit,
            "total": total,
            "has_more": offset + len(items) < total,
        },
    }


@frappe.whitelist(allow_guest=True)
@api_endpoint
def get_public_college(slug: str):
    doctype = _first_existing_doctype(["Colleges", "College"])
    if not doctype:
        raise frappe.DoesNotExistError("College not found")

    meta = frappe.get_meta(doctype)
    db_fields = {
        df.fieldname
        for df in meta.fields
        if df.fieldname and df.fieldtype not in {"Section Break", "Column Break", "Tab Break", "Fold", "HTML", "Button"}
    }

    filters = {"slug": slug} if "slug" in db_fields else {"name": slug}
    if "is_active" in db_fields:
        filters["is_active"] = 1

    fields = ["name", *sorted(db_fields)] if "name" not in db_fields else sorted(db_fields)
    row = frappe.db.get_value(doctype, filters, fields, as_dict=True)
    if not row:
        fallback_filters = {"is_active": 1} if "is_active" in db_fields else {}
        candidates = frappe.get_all(
            doctype,
            fields=fields,
            filters=fallback_filters,
            ignore_permissions=True,
            limit_page_length=200,
            order_by="modified desc",
        )
        for candidate in candidates:
            candidate_slug = _serialize_college_item(candidate).get("slug")
            if candidate_slug == slug or candidate.get("name") == slug:
                row = candidate
                break
    if not row:
        raise frappe.DoesNotExistError("College not found")
    return _serialize_college_item(row)


@frappe.whitelist(allow_guest=True)
@api_endpoint
def get_public_page(slug: str):
    # WHY+WHAT: use one lightweight AAU Page doctype + endpoint for static website pages to keep admin editing simple and rollout low-risk.
    doctype = _first_existing_doctype(["Pages", "AAU Page", "Static Page"])
    if not doctype:
        return {
            "slug": slug,
            "titleAr": slug,
            "titleEn": slug,
            "contentAr": "",
            "contentEn": "",
            "heroImage": None,
        }

    meta = frappe.get_meta(doctype)
    db_fields = {
        df.fieldname
        for df in meta.fields
        if df.fieldname and df.fieldtype not in {"Section Break", "Column Break", "Tab Break", "Fold", "HTML", "Button"}
    }
    filters = {"slug": slug}
    row = frappe.db.get_value(doctype, filters, list(db_fields), as_dict=True)
    if not row:
        return {
            "slug": slug,
            "titleAr": slug,
            "titleEn": slug,
            "contentAr": "",
            "contentEn": "",
            "heroImage": None,
        }

    if "published" in db_fields and not row.get("published") and frappe.session.user == "Guest":
        raise frappe.DoesNotExistError("Page not found")
    if "is_published" in db_fields and not row.get("is_published") and frappe.session.user == "Guest":
        raise frappe.DoesNotExistError("Page not found")

    return _serialize_page_item(row)


@frappe.whitelist(allow_guest=True)
@api_endpoint
def get_public_menu(key: str):
    # WHY+WHAT: expose all navigation/footer links via one public menu endpoint keyed by menu type for low-risk dynamic header/footer management.
    doctype = _first_existing_doctype(["AAU Menu"])
    if not doctype:
        raise frappe.DoesNotExistError("Menu not found")

    try:
        docname = frappe.db.get_value(doctype, {"key": key}, "name")
        if not docname:
            raise frappe.DoesNotExistError("Menu not found")
        doc = frappe.get_doc(doctype, docname)
        if not doc.get("published") and frappe.session.user == "Guest":
            raise frappe.DoesNotExistError("Menu not found")
        return _serialize_menu(doc)
    except frappe.DoesNotExistError:
        raise
    except Exception:
        frappe.log_error(frappe.get_traceback(), f"AAU Menu API get_public_menu failure ({key})")
        raise


@frappe.whitelist(allow_guest=True)
@api_endpoint
def get_site_profile():
    return _build_site_profile_payload()


@frappe.whitelist()
@api_endpoint
def update_site_profile(**payload):
    require_roles(ADMIN_ROLES)
    doctype = "Website Settings"
    if not frappe.db.exists("DocType", doctype):
        raise frappe.DoesNotExistError("Website Settings not found")

    meta = frappe.get_meta(doctype)
    field_map = {
        "siteName": "site_name",
        "siteNameAr": "site_name_ar",
        "siteDescriptionAr": "site_description_ar",
        "siteDescriptionEn": "site_description_en",
        "contactPhone": "contact_phone",
        "contactEmail": "contact_email",
        "addressAr": "address_ar",
        "addressEn": "address_en",
        "mapLocation": "map_location",
        "facebook": "facebook",
        "twitter": "twitter",
        "instagram": "instagram",
        "linkedin": "linkedin",
        "youtube": "youtube",
    }

    updates = {}
    for key, value in (payload or {}).items():
        fieldname = field_map.get(key, key)
        if meta.get_field(fieldname):
            updates[fieldname] = value

    if not updates:
        return get_site_profile()

    if getattr(meta, "issingle", 0):
        for fieldname, value in updates.items():
            frappe.db.set_single_value(doctype, fieldname, value)
    else:
        row = frappe.get_all(doctype, fields=["name"], order_by="modified desc", limit_page_length=1, ignore_permissions=True)
        if row:
            for fieldname, value in updates.items():
                frappe.db.set_value(doctype, row[0]["name"], fieldname, value)
        else:
            doc = frappe.get_doc({"doctype": doctype, **updates})
            doc.insert(ignore_permissions=True)

    frappe.db.commit()
    return get_site_profile()


def _get_home_sections() -> dict:
    if not frappe.db.exists("DocType", "Home Page"):
        return {"hero": {}, "stats": [], "about": {}, "sections": {}, "partners": [], "testimonials": []}

    meta = frappe.get_meta("Home Page")
    if not getattr(meta, "issingle", 0):
        rows = frappe.get_all("Home Page", fields=["name"], limit_page_length=1, ignore_permissions=True)
        if not rows:
            return {"hero": {}, "stats": [], "about": {}, "sections": {}, "partners": [], "testimonials": []}
        row = frappe.get_doc("Home Page", rows[0]["name"]).as_dict()
    else:
        row = frappe.get_cached_doc("Home Page").as_dict()

    if not row:
        return {"hero": {}, "stats": [], "about": {}, "sections": {}, "partners": [], "testimonials": []}

    def _text(*candidates, default=""):
        for candidate in candidates:
            value = _as_text(candidate)
            if value:
                return value
        return _as_text(default)

    def _translated(value: str, lang: str = "en") -> str:
        source = _as_text(value)
        if not source:
            return ""
        translations = get_all_translations(lang) or {}
        return _as_text(translations.get(source), default=source)

    hero = {
        "badgeAr": _text(row.get("hero_badge_ar"), default="مرحباً بكم في جامعة الجيل الجديد"),
        "badgeEn": _translated(_text(row.get("hero_badge_ar"), default="مرحباً بكم في جامعة الجيل الجديد")),
        "titlePrimaryAr": _text(row.get("hero_title_primary_ar"), default="جامعة الجيل الجديد"),
        "titlePrimaryEn": _translated(_text(row.get("hero_title_primary_ar"), default="جامعة الجيل الجديد")),
        "titleSecondaryAr": _text(row.get("hero_title_secondary_ar"), default="الجامعة"),
        "titleSecondaryEn": _translated(_text(row.get("hero_title_secondary_ar"), default="الجامعة")),
        "descriptionAr": _text(row.get("hero_description_ar")),
        "descriptionEn": _translated(_text(row.get("hero_description_ar"))),
        "image": _text(row.get("hero_image")),
    }

    colleges_count = row.get("colleges_count")
    if not colleges_count:
        colleges_count = frappe.db.count("Colleges") if frappe.db.exists("DocType", "Colleges") else 0

    faculty_count = row.get("faculty_count") or 500
    stats = [
        {
            "key": "students",
            "number": str(row.get("students_count") or 0),
            "labelAr": _text(row.get("stats_students_label_ar"), default="طالب وطالبة"),
            "labelEn": _translated(_text(row.get("stats_students_label_ar"), default="طالب وطالبة")),
            "icon": "GraduationCap",
        },
        {
            "key": "faculty",
            "number": str(faculty_count),
            "labelAr": _text(row.get("stats_faculty_label_ar"), default="عضو هيئة تدريس"),
            "labelEn": _translated(_text(row.get("stats_faculty_label_ar"), default="عضو هيئة تدريس")),
            "icon": "Users",
        },
        {
            "key": "programs",
            "number": str(row.get("programs_count") or 0),
            "labelAr": _text(row.get("stats_programs_label_ar"), default="برنامج أكاديمي"),
            "labelEn": _translated(_text(row.get("stats_programs_label_ar"), default="برنامج أكاديمي")),
            "icon": "BookOpen",
        },
        {
            "key": "colleges",
            "number": str(colleges_count or 0),
            "labelAr": _text(row.get("stats_colleges_label_ar"), default="كليات متخصصة"),
            "labelEn": _translated(_text(row.get("stats_colleges_label_ar"), default="كليات متخصصة")),
            "icon": "Award",
        },
    ]

    about_title_ar = _text(row.get("about_title_ar"), default="عن الجامعة")
    about_description_ar = _text(row.get("about_description_ar"))
    about_vision_ar = _text(
        row.get("about_vision_ar"),
        default="مؤسسة تعليمية رائدة وطنيا ومتميزة إقليميا وفعالة في بناء مجتمع المعرفة",
    )
    about_mission_ar = _text(
        row.get("about_mission_ar"),
        default="إعداد خريجين يتمتعون بالكفاءة العلمية والمهنية والتعلم مدى الحياة من خلال بيئة تعليمية داعمة وبرامج أكاديمية نوعية.",
    )
    about_goals_ar = _text(
        row.get("about_goals_ar"),
        default="تحقيق التميز الأكاديمي والبحثي وتعزيز الشراكة المجتمعية وتوفير بيئة تعليمية محفزة.",
    )
    about_values_ar = _text(
        row.get("about_values_ar"),
        default="الريادة والتعلم المستمر، الابتكار والإبداع، المسؤولية والشفافية، والعمل بروح الفريق.",
    )
    about_highlight_title_ar = _text(row.get("about_highlight_title_ar"), default="بيئة تعليمية متميزة")
    about_highlight_text_ar = _text(
        row.get("about_highlight_text_ar"),
        default="نوفر بيئة تعليمية حديثة بمختبرات متطورة ومساحات تعلم محفزة.",
    )
    president_message_intro_ar = _text(
        row.get("president_message_intro_ar"),
        default="بسم الله الرحمن الرحيم. الحمد لله رب العالمين، والصلاة والسلام على خاتم الأنبياء والمرسلين.",
    )
    president_message_body_ar = _text(
        row.get("president_message_body_ar"),
        default="يسرني أن أرحب بطلابنا وطالباتنا، ونؤكد التزام الجامعة بتقديم تعليم نوعي وبيئة جامعية تشجع على الإبداع والريادة والتميز.",
    )
    president_message_closing_ar = _text(
        row.get("president_message_closing_ar"),
        default="نثق بأنكم ستكونون على قدر المسؤولية في تمثيل الجامعة وبناء مستقبل مشرق لكم ولوطنكم.",
    )
    president_name_ar = _text(row.get("president_name_ar"), default="أ.د/ همدان الشامي")
    president_role_ar = _text(row.get("president_role_ar"), default="رئيس الجامعة")

    about = {
        "titleAr": about_title_ar,
        "titleEn": _translated(about_title_ar),
        "descriptionAr": about_description_ar,
        "descriptionEn": _translated(about_description_ar),
        "image": _text(row.get("about_image")),
        "visionAr": about_vision_ar,
        "visionEn": _translated(about_vision_ar),
        "missionAr": about_mission_ar,
        "missionEn": _translated(about_mission_ar),
        "goalsAr": about_goals_ar,
        "goalsEn": _translated(about_goals_ar),
        "valuesAr": about_values_ar,
        "valuesEn": _translated(about_values_ar),
        "highlightTitleAr": about_highlight_title_ar,
        "highlightTitleEn": _translated(about_highlight_title_ar),
        "highlightTextAr": about_highlight_text_ar,
        "highlightTextEn": _translated(about_highlight_text_ar),
        "presidentMessageIntroAr": president_message_intro_ar,
        "presidentMessageIntroEn": _translated(president_message_intro_ar),
        "presidentMessageBodyAr": president_message_body_ar,
        "presidentMessageBodyEn": _translated(president_message_body_ar),
        "presidentMessageClosingAr": president_message_closing_ar,
        "presidentMessageClosingEn": _translated(president_message_closing_ar),
        "presidentNameAr": president_name_ar,
        "presidentNameEn": _translated(president_name_ar),
        "presidentRoleAr": president_role_ar,
        "presidentRoleEn": _translated(president_role_ar),
    }

    def _section_content(prefix: str, title_ar: str, title_en: str, description_ar: str, description_en: str):
        title_value = _text(row.get(f"{prefix}_title_ar"), default=title_ar)
        description_value = _text(row.get(f"{prefix}_description_ar"), default=description_ar)
        return {
            "titleAr": title_value,
            "titleEn": _translated(title_value) or title_en,
            "descriptionAr": description_value,
            "descriptionEn": _translated(description_value) or description_en,
        }

    sections = {
        "campusLife": _section_content(
            "campus_life",
            "الحياة الجامعية",
            "Campus Life",
            "تجربة جامعية متكاملة ومميزة تجمع بين التعليم والأنشطة والمتعة",
            "A complete and distinctive university experience combining education, activities, and fun",
        ),
        "projects": _section_content(
            "projects",
            "مشاريع التخرج",
            "Graduation Projects",
            "اكتشف المشاريع الإبداعية والابتكارية لطلابنا الموهوبين",
            "Discover the creative and innovative projects of our talented students",
        ),
        "colleges": _section_content(
            "colleges",
            "كلياتنا",
            "Our Colleges",
            "نقدم مجموعة متنوعة من البرامج الأكاديمية المتميزة في مختلف التخصصات",
            "We offer a diverse range of distinguished academic programs in various specializations",
        ),
        "news": _section_content(
            "news",
            "الأخبار",
            "News",
            "تابع آخر أخبار الجامعة ومستجداتها",
            "Follow the latest university news and updates",
        ),
        "events": _section_content(
            "events",
            "الفعاليات",
            "Events",
            "اكتشف الفعاليات والأنشطة المتنوعة التي تقدمها الجامعة",
            "Discover the diverse events and activities offered by the university",
        ),
        "faq": _section_content(
            "faq",
            "الأسئلة المتكررة",
            "Frequently Asked Questions",
            "إجابات للأسئلة الشائعة",
            "Answers to common questions",
        ),
        "video": {
            **_section_content(
                "video",
                "لقطات من جامعتنا",
                "Glimpses of Our University",
                "شاهد بيئة التعليم الحديثة والمرافق المتطورة التي نقدمها لطلابنا",
                "Experience our modern learning environment and advanced facilities.",
            ),
            "overlayTitleAr": _text(row.get("video_overlay_title_ar"), default="جولة في الحرم الجامعي"),
            "overlayTitleEn": _translated(_text(row.get("video_overlay_title_ar"), default="جولة في الحرم الجامعي")) or "Campus Virtual Tour",
            "overlayDescriptionAr": _text(
                row.get("video_overlay_description_ar"),
                default="استكشف القاعات الدراسية والمعامل المجهزة بأحدث التقنيات.",
            ),
            "overlayDescriptionEn": _translated(
                _text(row.get("video_overlay_description_ar"), default="استكشف القاعات الدراسية والمعامل المجهزة بأحدث التقنيات.")
            )
            or "Explore classrooms and laboratories equipped with the latest technologies.",
        },
        "contact": _section_content(
            "contact",
            "تواصل معنا",
            "Contact Us",
            "نحن هنا للإجابة على استفساراتكم ومساعدتكم",
            "We are here to answer your questions and assist you",
        ),
    }

    return {"hero": hero, "stats": stats, "about": about, "sections": sections, "partners": [], "testimonials": []}


def _build_site_profile_payload() -> dict:
    settings = _get_website_settings_payload()
    social_links = _get_social_links_from_menu()
    site_name_ar = _as_text(settings.get("site_name_ar") or settings.get("site_name") or settings.get("app_name"))
    site_description_ar = _as_text(settings.get("site_description_ar") or settings.get("about_short"))
    address_ar = _as_text(settings.get("address_ar") or settings.get("address"))
    return {
        "siteName": _as_text(settings.get("site_name") or settings.get("app_name") or site_name_ar),
        "siteNameAr": site_name_ar,
        "siteDescriptionAr": site_description_ar,
        "siteDescriptionEn": _as_text(settings.get("site_description_en") or settings.get("about_short_en") or _translated_text(site_description_ar)),
        "contactPhone": _as_text(settings.get("contact_phone") or settings.get("phone")),
        "contactEmail": _as_text(settings.get("contact_email") or settings.get("email")),
        "addressAr": address_ar,
        "addressEn": _as_text(settings.get("address_en") or _translated_text(address_ar)),
        "mapLocation": _as_text(settings.get("map_location")),
        "socialLinks": social_links,
    }


def _build_contact_page_payload() -> dict:
    settings = _get_website_settings_payload()
    profile = _build_site_profile_payload()

    badge_ar = _as_text(settings.get("contact_page_badge_ar"), default="تواصل معنا")
    title_ar = _as_text(settings.get("contact_page_title_ar"), default="نحن هنا للإجابة على استفساراتكم")
    description_ar = _as_text(
        settings.get("contact_page_description_ar"),
        default="تواصل مع جامعة الجيل الجديد للاستفسار عن القبول والبرامج الأكاديمية والخدمات الطلابية.",
    )
    form_title_ar = _as_text(settings.get("contact_form_title_ar"), default="أرسل رسالة")
    social_title_ar = _as_text(settings.get("social_section_title_ar"), default="تابعنا على")

    return {
        "pageHeader": {
            "badgeAr": badge_ar,
            "badgeEn": _translated_text(badge_ar, "en") or "Contact Us",
            "titleAr": title_ar,
            "titleEn": _translated_text(title_ar, "en") or "Contact AJ JEEL ALJADEED UNIVERSITY",
            "descriptionAr": description_ar,
            "descriptionEn": _translated_text(description_ar, "en"),
        },
        "form": {
            "titleAr": form_title_ar,
            "titleEn": _translated_text(form_title_ar, "en") or "Send a Message",
        },
        "social": {
            "titleAr": social_title_ar,
            "titleEn": _translated_text(social_title_ar, "en") or "Follow Us",
        },
        "siteProfile": profile,
        "meta": {"generated_at": now_ts(), "source": "Website Settings"},
    }


def _build_about_page_payload() -> dict:
    if not frappe.db.exists("DocType", "About University"):
        return {
            "pageHeader": {},
            "intro": {},
            "identity": [],
            "presidentMessage": {},
            "team": {"titleAr": "", "titleEn": "", "descriptionAr": "", "descriptionEn": "", "groups": []},
            "meta": {"generated_at": now_ts(), "source": "About University"},
        }

    row = frappe.get_doc("About University", "About University")

    def _translated(value: str, fallback: str = "") -> str:
        translated = _translated_text(value)
        return translated or fallback or value

    page_badge_ar = _as_text(row.get("page_badge_ar"), default="تعرف علينا")
    page_title_ar = _as_text(row.get("page_title_ar"), default="عن جامعة الجيل الجديد")
    page_description_ar = _as_text(row.get("page_description_ar"))
    intro_body_ar = _as_text(row.get("intro_body_ar"))

    identity = [
        {
            "key": "vision",
            "titleAr": _as_text(row.get("vision_title_ar"), default="الرؤية"),
            "titleEn": _translated(_as_text(row.get("vision_title_ar"), default="الرؤية"), "Vision"),
            "descriptionAr": _as_text(row.get("vision_description_ar")),
            "descriptionEn": _translated(_as_text(row.get("vision_description_ar"))),
        },
        {
            "key": "mission",
            "titleAr": _as_text(row.get("mission_title_ar"), default="الرسالة"),
            "titleEn": _translated(_as_text(row.get("mission_title_ar"), default="الرسالة"), "Mission"),
            "descriptionAr": _as_text(row.get("mission_description_ar")),
            "descriptionEn": _translated(_as_text(row.get("mission_description_ar"))),
        },
        {
            "key": "goals",
            "titleAr": _as_text(row.get("goals_title_ar"), default="الأهداف"),
            "titleEn": _translated(_as_text(row.get("goals_title_ar"), default="الأهداف"), "Goals"),
            "descriptionAr": _as_text(row.get("goals_description_ar")),
            "descriptionEn": _translated(_as_text(row.get("goals_description_ar"))),
        },
        {
            "key": "values",
            "titleAr": _as_text(row.get("values_title_ar"), default="القيم"),
            "titleEn": _translated(_as_text(row.get("values_title_ar"), default="القيم"), "Values"),
            "descriptionAr": _as_text(row.get("values_description_ar")),
            "descriptionEn": _translated(_as_text(row.get("values_description_ar"))),
        },
    ]

    team_groups: dict[str, list[dict]] = {}
    for member in sorted(row.get("team_members") or [], key=lambda item: int(item.get("display_order") or 0)):
        group_name_ar = _as_text(member.get("group_name_ar"), default="الفريق الإداري")
        team_groups.setdefault(group_name_ar, []).append(
            {
                "nameAr": _as_text(member.get("full_name_ar")),
                "nameEn": _translated(_as_text(member.get("full_name_ar"))),
                "roleAr": _as_text(member.get("job_title_ar")),
                "roleEn": _translated(_as_text(member.get("job_title_ar"))),
                "image": _as_text(member.get("member_image")),
                "displayOrder": int(member.get("display_order") or 0),
            }
        )

    groups = [
        {
            "titleAr": group_name_ar,
            "titleEn": _translated(group_name_ar),
            "members": members,
        }
        for group_name_ar, members in team_groups.items()
    ]

    return {
        "pageHeader": {
            "badgeAr": page_badge_ar,
            "badgeEn": _translated(page_badge_ar, "About Us"),
            "titleAr": page_title_ar,
            "titleEn": _translated(page_title_ar, "About AJ JEEL ALJADEED UNIVERSITY"),
            "descriptionAr": page_description_ar,
            "descriptionEn": _translated(page_description_ar),
        },
        "intro": {
            "bodyAr": intro_body_ar,
            "bodyEn": _translated(intro_body_ar),
            "image": _as_text(row.get("intro_image")),
        },
        "identity": identity,
        "presidentMessage": {
            "sectionTitleAr": _as_text(row.get("president_section_title_ar"), default="كلمة رئيس الجامعة"),
            "sectionTitleEn": _translated(_as_text(row.get("president_section_title_ar"), default="كلمة رئيس الجامعة"), "President's Message"),
            "introAr": _as_text(row.get("president_message_intro_ar")),
            "introEn": _translated(_as_text(row.get("president_message_intro_ar"))),
            "bodyAr": _as_text(row.get("president_message_body_ar")),
            "bodyEn": _translated(_as_text(row.get("president_message_body_ar"))),
            "closingAr": _as_text(row.get("president_message_closing_ar")),
            "closingEn": _translated(_as_text(row.get("president_message_closing_ar"))),
            "nameAr": _as_text(row.get("president_name_ar")),
            "nameEn": _translated(_as_text(row.get("president_name_ar"))),
            "roleAr": _as_text(row.get("president_role_ar")),
            "roleEn": _translated(_as_text(row.get("president_role_ar"))),
            "image": _as_text(row.get("president_image")),
        },
        "team": {
            "titleAr": _as_text(row.get("team_section_title_ar"), default="الفريق الإداري"),
            "titleEn": _translated(_as_text(row.get("team_section_title_ar"), default="الفريق الإداري"), "Administrative Team"),
            "descriptionAr": _as_text(row.get("team_section_description_ar")),
            "descriptionEn": _translated(_as_text(row.get("team_section_description_ar"))),
            "groups": groups,
        },
        "meta": {"generated_at": now_ts(), "source": "About University"},
    }

def _list_home_section(entity_key: str, limit: int, filters: dict | None = None) -> list[dict]:
    candidates = {
        "news": ["News"],
        "events": ["Events", "Event"],
        "colleges": ["Colleges", "College"],
        "faqs": ["FAQs", "FAQ"],
    }.get(entity_key, [])
    return _list_home_doctype(candidates=candidates, limit=limit, filters=filters)


def _selectable_fields(doctype: str) -> set[str]:
    # WHY+WHAT: use only real DB columns (plus `name`) for home list queries; avoids layout/table fields.
    meta = frappe.get_meta(doctype)
    get_valid_columns = getattr(meta, "get_valid_columns", None)
    if callable(get_valid_columns):
        columns = set(get_valid_columns())
    else:
        non_column_fieldtypes = {
            "Section Break",
            "Column Break",
            "Tab Break",
            "Fold",
            "HTML",
            "Button",
            "Heading",
            "Read Only",
            "Table",
            "Table MultiSelect",
            "Image",
        }
        columns = {df.fieldname for df in meta.fields if df.fieldname and df.fieldtype not in non_column_fieldtypes}
    columns.add("name")
    return columns


def _list_home_news(limit: int) -> list[dict]:
    doctype = _first_existing_doctype(["News"])
    if not doctype:
        return []

    available = _selectable_fields(doctype)
    desired = [
        "name",
        "slug",
        "title",
        "title_ar",
        "title_en",
        "description_ar",
        "description_en",
        "summary",
        "content",
        "content_ar",
        "content_en",
        "image",
        "featured_image",
        "date",
        "publish_date",
        "tags",
        "views",
        "display_order",
        "is_published",
    ]
    fields = [field for field in desired if field in available]

    filters = {"is_published": 1} if "is_published" in available else {}
    order_by = "date desc, publish_date desc, modified desc"
    if "display_order" in available:
        order_by = "display_order asc, date desc, publish_date desc, modified desc"

    rows = frappe.get_all(
        doctype,
        fields=fields,
        filters=filters,
        order_by=order_by,
        limit_page_length=limit,
        ignore_permissions=True,
    )
    items = [_serialize_news_item(row) for row in rows]
    # WHY+WHAT: keep home payload minimal (only what Home UI consumes) while allowing richer list/detail endpoints elsewhere.
    return [
        {
            "id": item.get("id"),
            "slug": item.get("slug"),
            "titleAr": item.get("titleAr"),
            "titleEn": item.get("titleEn"),
            "descriptionAr": item.get("descriptionAr"),
            "descriptionEn": item.get("descriptionEn"),
            "image": item.get("image"),
            "date": item.get("date"),
            "tags": item.get("tags") or [],
            "views": item.get("views") or 0,
        }
        for item in items
    ]


def _list_home_events(limit: int) -> list[dict]:
    doctype = _first_existing_doctype(["Events", "Event"])
    if not doctype:
        return []

    available = _selectable_fields(doctype)
    desired = [
        "name",
        "slug",
        "title",
        "event_title",
        "title_ar",
        "title_en",
        "description",
        "description_ar",
        "description_en",
        "content",
        "content_ar",
        "content_en",
        "image",
        "date",
        "event_date",
        "end_date",
        "location",
        "location_ar",
        "location_en",
        "organizer",
        "organizer_ar",
        "organizer_en",
        "category",
        "status",
        "registration_required",
        "registration_link",
        "tags",
        "display_order",
        "is_published",
    ]
    fields = [field for field in desired if field in available]

    filters = {"is_published": 1} if "is_published" in available else {}
    sort_parts = []
    if "display_order" in available:
        sort_parts.append("display_order asc")
    if "date" in available:
        sort_parts.append("date desc")
    if "event_date" in available:
        sort_parts.append("event_date desc")
    sort_parts.append("modified desc")
    order_by = ", ".join(sort_parts)

    rows = frappe.get_all(
        doctype,
        fields=fields,
        filters=filters,
        order_by=order_by,
        limit_page_length=limit,
        ignore_permissions=True,
    )
    items = [_serialize_event_item(row) for row in rows]
    # WHY+WHAT: keep home payload minimal (only what Home UI consumes).
    return [
        {
            "id": item.get("id"),
            "slug": item.get("slug"),
            "titleAr": item.get("titleAr"),
            "titleEn": item.get("titleEn"),
            "descriptionAr": item.get("descriptionAr"),
            "descriptionEn": item.get("descriptionEn"),
            "date": item.get("date"),
            "endDate": item.get("endDate"),
            "locationAr": item.get("locationAr"),
            "locationEn": item.get("locationEn"),
            "organizerAr": item.get("organizerAr"),
            "organizerEn": item.get("organizerEn"),
            "category": item.get("category"),
            "status": item.get("status"),
            "registrationRequired": item.get("registrationRequired"),
            "registrationLink": item.get("registrationLink"),
            "image": item.get("image"),
            "tags": item.get("tags") or [],
        }
        for item in items
    ]


def _home_minimal_programs(programs: list) -> list[dict]:
    # WHY+WHAT: Home only needs program counts, but we return a small stable shape that matches the
    # frontend `AcademicProgram` required keys (without heavy optional blobs).
    output = []
    for program in programs or []:
        if not isinstance(program, dict):
            continue
        output.append(
            {
                "id": program.get("id"),
                "nameAr": program.get("nameAr") or "",
                "nameEn": program.get("nameEn") or "",
                "departmentAr": program.get("departmentAr") or "",
                "departmentEn": program.get("departmentEn") or "",
                "admissionRate": int(program.get("admissionRate") or 0),
                "highSchoolType": program.get("highSchoolType") or "علمي",
                "highSchoolTypeEn": program.get("highSchoolTypeEn") or "Scientific",
                "studyYears": str(program.get("studyYears") or ""),
                "image": program.get("image"),
            }
        )
    return output


def _list_home_colleges(limit: int) -> list[dict]:
    doctype = _first_existing_doctype(["Colleges", "College"])
    if not doctype:
        return []

    available = _selectable_fields(doctype)
    desired = [
        "name",
        "slug",
        "college_name",
        "colleges_name",
        "name_ar",
        "name_en",
        "description",
        "description_ar",
        "description_en",
        "vision_ar",
        "vision_en",
        "mission_ar",
        "mission_en",
        "goals_ar",
        "goals_en",
        "admission_requirements_ar",
        "admission_requirements_en",
        "icon",
        "image",
        "display_order",
        "is_active",
    ]
    if _json_fallback_enabled():
        desired.append("programs_json")
    fields = [field for field in desired if field in available]

    filters = {"is_active": 1} if "is_active" in available else {}
    order_by = "display_order asc, modified desc" if "display_order" in available else "modified desc"

    rows = frappe.get_all(
        doctype,
        fields=fields,
        filters=filters,
        order_by=order_by,
        limit_page_length=limit,
        ignore_permissions=True,
    )
    items = [_serialize_college_item(row) for row in rows]
    # WHY+WHAT: keep home payload minimal (only fields needed for home cards + program counts).
    return [
        {
            "id": item.get("id"),
            "slug": item.get("slug"),
            "nameAr": item.get("nameAr"),
            "nameEn": item.get("nameEn"),
            "descriptionAr": item.get("descriptionAr"),
            "descriptionEn": item.get("descriptionEn"),
            "icon": item.get("icon"),
            "image": item.get("image"),
            "programs": _home_minimal_programs(item.get("programs") or []),
        }
        for item in items
    ]


def _list_home_faqs(limit: int) -> list[dict]:
    doctype = _first_existing_doctype(["FAQs", "FAQ"])
    if not doctype:
        return []

    available = _selectable_fields(doctype)
    desired = [
        "name",
        "id",
        "slug",
        "title",
        "question",
        "question_ar",
        "question_en",
        "answer",
        "answer_ar",
        "answer_en",
        "content",
        "category",
        "display_order",
        "is_published",
        "published",
    ]
    fields = [field for field in desired if field in available]

    filters: dict = {}
    if "is_published" in available:
        filters["is_published"] = 1
    elif "published" in available:
        filters["published"] = 1
    order_by = "display_order asc, modified desc" if "display_order" in available else "modified desc"

    rows = frappe.get_all(
        doctype,
        fields=fields,
        filters=filters,
        order_by=order_by,
        limit_page_length=limit,
        ignore_permissions=True,
    )
    return [_serialize_faq_item(row) for row in rows]


def _list_home_campus_life(limit: int) -> list[dict]:
    doctype = _first_existing_doctype(["Campus Life"])
    if not doctype:
        return []

    available = _selectable_fields(doctype)
    desired = ["name", "title", "content", "image", "display_order", "is_published"]
    fields = [field for field in desired if field in available]
    filters = {"is_published": 1} if "is_published" in available else {}
    order_by = "display_order asc, modified desc" if "display_order" in available else "modified desc"

    rows = frappe.get_all(
        doctype,
        fields=fields,
        filters=filters,
        order_by=order_by,
        limit_page_length=limit,
        ignore_permissions=True,
    )
    return [_serialize_campus_life_item(row) for row in rows]


def _list_home_projects(limit: int) -> list[dict]:
    doctype = _first_existing_doctype(["Projects"])
    if not doctype:
        return []

    available = _selectable_fields(doctype)
    desired = [
        "name",
        "id",
        "slug",
        "title_ar",
        "title_en",
        "desc_ar",
        "desc_en",
        "details_ar",
        "details_en",
        "status",
        "year",
        "progress",
        "start_date",
        "end_date",
        "display_order",
        "is_published",
    ]
    fields = [field for field in desired if field in available]
    filters = {"is_published": 1} if "is_published" in available else {}
    order_by = "display_order asc, modified desc" if "display_order" in available else "modified desc"

    rows = frappe.get_all(
        doctype,
        fields=fields,
        filters=filters,
        order_by=order_by,
        limit_page_length=limit,
        ignore_permissions=True,
    )
    return [_serialize_project_item(row) for row in rows]


def _home_source() -> str:
    source_doctypes = ["News", "Events", "Colleges", "FAQ", "Campus Life", "Projects"]
    if frappe.db.exists("DocType", "Home Page"):
        source_doctypes.insert(0, "Home Page")
    if frappe.db.exists("DocType", "FAQs"):
        source_doctypes[-1] = "FAQs"
    return ", ".join(source_doctypes)


def _list_home_doctype(candidates: list[str], limit: int, filters: dict | None = None) -> list[dict]:
    doctype = next((name for name in candidates if frappe.db.exists("DocType", name)), None)
    if not doctype:
        return []
    try:
        meta = frappe.get_meta(doctype)
        db_fields = [
            df.fieldname
            for df in meta.fields
            if df.fieldname
            and df.fieldtype
            not in {"Section Break", "Column Break", "Tab Break", "Fold", "HTML", "Button"}
        ]
        list_filters = {key: value for key, value in (filters or {}).items() if key in db_fields}
        order_by = "display_order asc" if "display_order" in db_fields else "modified desc"
        rows = frappe.get_all(
            doctype,
            fields=db_fields,
            filters=list_filters,
            ignore_permissions=True,
            limit_page_length=limit,
            order_by=order_by,
        )
        return [_normalize_home_record(row) for row in rows]
    except Exception:
        frappe.logger("aau_university").warning(f"[AAU API] Home section unavailable: {doctype}")
        return []


def _normalize_home_record(row: dict) -> dict:
    normalized = {to_camel(key): value for key, value in row.items()}

    if "event_title" in row and "title" not in row:
        normalized["title"] = row.get("event_title")
    if "event_date" in row and "date" not in row:
        normalized["date"] = row.get("event_date")
    if "publish_date" in row and "date" not in row:
        normalized["date"] = row.get("publish_date")
    if "college_name" in row and "name" not in row:
        normalized["name"] = row.get("college_name")
    if (
        "title" in row
        and "content" in row
        and "question" not in row
        and "publish_date" not in row
        and "event_title" not in row
        and "college_name" not in row
    ):
        normalized["question"] = row.get("title")
        normalized["answer"] = row.get("content")
    return normalized


def _build_link(entity_key: str, identifier: str | None) -> str:
    if not identifier:
        return ""
    return f"/{to_camel(entity_key)}/{identifier}"


def _first_existing_doctype(candidates: list[str]) -> str | None:
    for candidate in candidates:
        if frappe.db.exists("DocType", candidate):
            return candidate
    return None


def _get_website_settings_payload() -> dict:
    doctype = "Website Settings"
    if not frappe.db.exists("DocType", doctype):
        return {}
    meta = frappe.get_meta(doctype)
    candidate_fields = [
        "site_name",
        "site_name_ar",
        "site_description_ar",
        "site_description_en",
        "about_short",
        "about_short_en",
        "app_name",
        "contact_phone",
        "phone",
        "contact_email",
        "email",
        "address",
        "address_ar",
        "address_en",
        "map_location",
        "contact_page_badge_ar",
        "contact_page_title_ar",
        "contact_page_description_ar",
        "contact_form_title_ar",
        "social_section_title_ar",
        "facebook",
        "twitter",
        "instagram",
        "linkedin",
        "youtube",
    ]
    available = [field for field in candidate_fields if meta.get_field(field)]
    if not available:
        return {}

    if getattr(meta, "issingle", 0):
        payload = {}
        for fieldname in available:
            payload[fieldname] = frappe.db.get_single_value(doctype, fieldname)
        return payload

    row = frappe.get_all(
        doctype,
        fields=["name"] + available,
        order_by="modified desc",
        limit_page_length=1,
        ignore_permissions=True,
    )
    return row[0] if row else {}


def _get_social_links_from_menu() -> list[dict]:
    doctype = _first_existing_doctype(["AAU Menu"])
    if not doctype:
        return []
    menu_name = frappe.db.get_value(doctype, {"key": "social"}, "name")
    if not menu_name:
        return []
    doc = frappe.get_doc(doctype, menu_name)
    links = []
    for item in doc.get("items") or []:
        label_ar = _as_text(item.get("label_ar") or item.get("label"))
        label_en = _as_text(item.get("label_en") or item.get("label") or label_ar)
        url = _as_text(item.get("url"))
        if not url:
            continue
        links.append(
            {
                "labelAr": label_ar,
                "labelEn": label_en,
                "url": url,
                "openInNewTab": int(item.get("open_in_new_tab") or 0) == 1,
            }
        )
    return links


def _merge_request_payload(payload: dict | None) -> frappe._dict:
    merged = frappe._dict(payload or {})
    form_dict = getattr(frappe.local, "form_dict", {}) or {}
    for key, value in form_dict.items():
        if key in {"cmd", "data"}:
            continue
        merged.setdefault(key, value)

    request = getattr(frappe.local, "request", None)
    if request:
        try:
            json_payload = request.get_json(silent=True)
        except Exception:
            json_payload = None
        if isinstance(json_payload, dict):
            for key, value in json_payload.items():
                merged.setdefault(key, value)

    data_payload = form_dict.get("data")
    if data_payload and isinstance(data_payload, str):
        try:
            parsed = frappe.parse_json(data_payload)
        except Exception:
            parsed = None
        if isinstance(parsed, dict):
            for key, value in parsed.items():
                merged.setdefault(key, value)
    return merged


def _as_text(value, default: str = "") -> str:
    if value is None:
        return default
    if isinstance(value, str):
        cleaned = value.strip()
        return cleaned if cleaned else default
    return str(value).strip() or default


def _serialize_news_item(row: dict) -> dict:
    slug = _as_text(row.get("slug")) or _slugify_news_value(
        row.get("title_en") or row.get("title_ar") or row.get("title")
    )
    title_ar = _as_text(row.get("title_ar") or row.get("title"))
    title_en = _as_text(row.get("title_en") or _translated_text(title_ar) or row.get("title") or title_ar)
    description_ar = _as_text(row.get("description_ar") or row.get("summary"))
    description_en = _as_text(row.get("description_en") or _translated_text(description_ar) or row.get("summary") or description_ar)
    content_ar = _as_text(row.get("content_ar") or row.get("content"))
    content_en = _as_text(row.get("content_en") or _translated_text(content_ar) or row.get("content") or content_ar)
    image = _as_text(row.get("image") or row.get("featured_image"))
    date = row.get("date") or row.get("publish_date")
    raw_tags = row.get("tags")
    if isinstance(raw_tags, str):
        tags = [part.strip() for part in raw_tags.split(",") if part.strip()]
    elif isinstance(raw_tags, (list, tuple)):
        tags = [str(part).strip() for part in raw_tags if str(part).strip()]
    else:
        tags = []

    return {
        "id": row.get("id") or row.get("name") or slug,
        "slug": slug,
        "titleAr": title_ar,
        "titleEn": title_en,
        "descriptionAr": description_ar,
        "descriptionEn": description_en,
        "contentAr": content_ar,
        "contentEn": content_en,
        "image": image,
        "date": str(date)[:10] if date else "",
        "tags": tags,
        "views": int(row.get("views") or 0),
    }


def _serialize_faq_item(row: dict) -> dict:
    question_ar = _as_text(row.get("question_ar") or row.get("question") or row.get("title"))
    question_en = _as_text(row.get("question_en") or row.get("question") or row.get("title") or question_ar)
    answer_ar = _as_text(row.get("answer_ar") or row.get("answer") or row.get("content"))
    answer_en = _as_text(row.get("answer_en") or row.get("answer") or row.get("content") or answer_ar)
    category = _as_text(row.get("category"))
    fallback_id = _slugify_news_value(question_en or question_ar)

    return {
        "id": row.get("id") or row.get("name") or fallback_id,
        "questionAr": question_ar,
        "questionEn": question_en,
        "answerAr": answer_ar,
        "answerEn": answer_en,
        "category": category,
    }


def _serialize_campus_life_item(row: dict) -> dict:
    title_ar = _as_text(row.get("title"))
    content_ar = _as_text(row.get("content"))
    slug = _as_text(row.get("name")) or _slugify_news_value(title_ar)
    return {
        "id": slug,
        "slug": slug,
        "titleAr": title_ar,
        "titleEn": _translated_text(title_ar),
        "descriptionAr": content_ar,
        "descriptionEn": _translated_text(content_ar),
        "contentAr": content_ar,
        "contentEn": _translated_text(content_ar),
        "category": "",
        "image": _as_text(row.get("image")),
    }


def _serialize_project_item(row: dict) -> dict:
    title_ar = _as_text(row.get("title_ar"))
    desc_ar = _as_text(row.get("desc_ar"))
    details_ar = _as_text(row.get("details_ar"))
    return {
        "id": _as_text(row.get("id") or row.get("name") or row.get("slug")),
        "slug": _as_text(row.get("slug") or row.get("name")),
        "titleAr": title_ar,
        "titleEn": _as_text(row.get("title_en"), default=_translated_text(title_ar)),
        "descAr": desc_ar,
        "descEn": _as_text(row.get("desc_en"), default=_translated_text(desc_ar)),
        "detailsAr": details_ar,
        "detailsEn": _as_text(row.get("details_en"), default=_translated_text(details_ar)),
        "students": [],
        "progress": row.get("progress"),
        "year": row.get("year"),
        "status": _as_text(row.get("status"), default="current"),
        "type": "graduation",
        "images": [],
        "startDate": row.get("start_date"),
        "endDate": row.get("end_date"),
    }


def _translated_text(value: str, lang: str = "en") -> str:
    source = _as_text(value)
    if not source:
        return ""
    translations = get_all_translations(lang) or {}
    return _as_text(translations.get(source), default=source)


def _slugify_news_value(value: str | None) -> str:
    if not value:
        return ""
    slug = re.sub(r"[^\w\s-]", "", str(value).strip().lower())
    slug = re.sub(r"[-\s]+", "-", slug)
    return slug.strip("-")


def _serialize_event_item(row: dict) -> dict:
    slug = _as_text(row.get("slug")) or _slugify_news_value(
        row.get("title_en")
        or row.get("title_ar")
        or row.get("event_title")
        or row.get("title")
    )
    title_ar = _as_text(row.get("title_ar") or row.get("title") or row.get("event_title"))
    title_en = _as_text(row.get("title_en") or _translated_text(title_ar) or row.get("title") or row.get("event_title") or title_ar)
    description_ar = _as_text(row.get("description_ar") or row.get("description"))
    description_en = _as_text(row.get("description_en") or _translated_text(description_ar) or row.get("description") or description_ar)
    content_ar = _as_text(row.get("content_ar") or row.get("content") or description_ar)
    content_en = _as_text(row.get("content_en") or _translated_text(content_ar) or row.get("content") or content_ar)
    date = row.get("date") or row.get("event_date")
    end_date = row.get("end_date")
    location_ar = _as_text(row.get("location_ar") or row.get("location"))
    location_en = _as_text(row.get("location_en") or _translated_text(location_ar) or row.get("location") or location_ar)
    organizer_ar = _as_text(row.get("organizer_ar") or row.get("organizer"))
    organizer_en = _as_text(row.get("organizer_en") or _translated_text(organizer_ar) or row.get("organizer") or organizer_ar)
    raw_tags = row.get("tags")
    if isinstance(raw_tags, str):
        tags = [part.strip() for part in raw_tags.split(",") if part.strip()]
    elif isinstance(raw_tags, (list, tuple)):
        tags = [str(part).strip() for part in raw_tags if str(part).strip()]
    else:
        tags = []

    return {
        "id": row.get("id") or row.get("name") or slug,
        "slug": slug,
        "titleAr": title_ar,
        "titleEn": title_en,
        "descriptionAr": description_ar,
        "descriptionEn": description_en,
        "contentAr": content_ar,
        "contentEn": content_en,
        "date": str(date)[:10] if date else "",
        "endDate": str(end_date)[:10] if end_date else "",
        "locationAr": location_ar,
        "locationEn": location_en,
        "organizerAr": organizer_ar,
        "organizerEn": organizer_en,
        "category": _as_text(row.get("category"), "other"),
        "status": _as_text(row.get("status"), "upcoming"),
        "registrationRequired": bool(row.get("registration_required")),
        "registrationLink": _as_text(row.get("registration_link")),
        "image": _as_text(row.get("image")),
        "tags": tags,
    }


def _serialize_college_item(row: dict) -> dict:
    programs = _get_college_programs_from_doctype(row)
    if not programs and _json_fallback_enabled():
        programs = _parse_programs_json(row.get("programs_json"))
    slug = row.get("slug") or _slugify_news_value(
        row.get("name_en")
        or row.get("name_ar")
        or row.get("college_name")
        or row.get("name")
    )
    name_ar = _as_text(row.get("name_ar") or row.get("college_name") or row.get("name"))
    name_en = _as_text(row.get("name_en") or _translated_text(name_ar) or row.get("college_name") or row.get("name") or name_ar)
    description_ar = _as_text(row.get("description_ar") or row.get("description"))
    description_en = _as_text(row.get("description_en") or _translated_text(description_ar) or row.get("description") or description_ar)
    vision_ar = _as_text(row.get("vision_ar"))
    mission_ar = _as_text(row.get("mission_ar"))
    goals_ar = _as_text(row.get("goals_ar"))
    quality_ar = _as_text(row.get("quality_ar"))
    values_ar = _as_text(row.get("values_ar"))
    strategy_ar = _as_text(row.get("strategy_ar"))
    admission_requirements_ar = _as_text(row.get("admission_requirements_ar"))

    return {
        "id": row.get("id") or slug or row.get("name"),
        "slug": slug,
        "nameAr": name_ar,
        "nameEn": name_en,
        "descriptionAr": description_ar,
        "descriptionEn": description_en,
        "visionAr": vision_ar,
        "visionEn": _as_text(row.get("vision_en") or _translated_text(vision_ar)),
        "missionAr": mission_ar,
        "missionEn": _as_text(row.get("mission_en") or _translated_text(mission_ar)),
        "goalsAr": goals_ar,
        "goalsEn": _as_text(row.get("goals_en") or _translated_text(goals_ar)),
        "qualityAr": quality_ar,
        "qualityEn": _as_text(row.get("quality_en") or _translated_text(quality_ar)),
        "valuesAr": values_ar,
        "valuesEn": _as_text(row.get("values_en") or _translated_text(values_ar)),
        "strategyAr": strategy_ar,
        "strategyEn": _as_text(row.get("strategy_en") or _translated_text(strategy_ar)),
        "admissionRequirementsAr": admission_requirements_ar,
        "admissionRequirementsEn": _as_text(row.get("admission_requirements_en") or _translated_text(admission_requirements_ar)),
        "icon": _as_text(row.get("icon")),
        "image": _as_text(row.get("image")),
        "programs": programs,
    }


def _get_college_programs_from_doctype(college_row: dict) -> list[dict]:
    doctype = _first_existing_doctype(["Academic Programs"])
    if not doctype:
        return []

    college_key = college_row.get("name") or college_row.get("id") or college_row.get("slug")
    if not college_key:
        return []

    cache_key = "_aau_college_programs_cache"
    cache = getattr(frappe.local, cache_key, None)
    if cache is None:
        cache = {}
        setattr(frappe.local, cache_key, cache)
    if college_key in cache:
        return cache[college_key]

    available = _selectable_fields(doctype)
    desired = [
        "name",
        "id",
        "program_name",
        "name_ar",
        "name_en",
        "department_ar",
        "department_en",
        "admission_rate",
        "high_school_type",
        "high_school_type_en",
        "study_years",
        "duration",
        "description",
        "description_ar",
        "description_en",
        "image",
        "college",
        "degree_type",
        "is_active",
    ]
    fields = [field for field in desired if field in available]
    if not fields or "college" not in available:
        cache[college_key] = []
        return []

    filters = {"college": college_key}
    if "is_active" in available:
        filters["is_active"] = 1

    rows = frappe.get_all(
        doctype,
        fields=fields,
        filters=filters,
        order_by="modified desc",
        ignore_permissions=True,
    )
    programs = []
    for program in rows:
        programs.append(
            {
                "id": program.get("id") or program.get("name"),
                "nameAr": program.get("name_ar") or program.get("program_name") or "",
                "nameEn": program.get("name_en") or program.get("program_name") or "",
                "departmentAr": program.get("department_ar") or "",
                "departmentEn": program.get("department_en") or "",
                "admissionRate": int(program.get("admission_rate") or 0),
                "highSchoolType": program.get("high_school_type") or "علمي",
                "highSchoolTypeEn": program.get("high_school_type_en") or "Scientific",
                "studyYears": str(program.get("study_years") or program.get("duration") or ""),
                "degreeType": _as_text(program.get("degree_type")),
                "image": program.get("image"),
                "descriptionAr": program.get("description_ar") or program.get("description") or "",
                "descriptionEn": program.get("description_en") or _translated_text(program.get("description_ar") or "") or program.get("description") or "",
                "objectives": [],
                "studyPlan": [],
                "careerProspectsAr": [],
                "careerProspectsEn": [],
                "facultyMembers": [],
            }
        )
    cache[college_key] = programs
    return programs


def _parse_programs_json(raw: str | None) -> list[dict]:
    if not raw:
        return []
    try:
        parsed = json.loads(raw)
    except Exception:
        return []
    if not isinstance(parsed, list):
        return []
    output = []
    for item in parsed:
        if not isinstance(item, dict):
            continue
        output.append(
            {
                "id": item.get("id"),
                "nameAr": item.get("nameAr"),
                "nameEn": item.get("nameEn"),
                "departmentAr": item.get("departmentAr") or "",
                "departmentEn": item.get("departmentEn") or "",
                "admissionRate": int(item.get("admissionRate") or 0),
                "highSchoolType": item.get("highSchoolType") or "علمي",
                "highSchoolTypeEn": item.get("highSchoolTypeEn") or "Scientific",
                "studyYears": item.get("studyYears") or "",
                "image": item.get("image"),
                "descriptionAr": item.get("descriptionAr") or "",
                "descriptionEn": item.get("descriptionEn") or "",
                "objectives": item.get("objectives") if isinstance(item.get("objectives"), list) else [],
                "studyPlan": item.get("studyPlan") if isinstance(item.get("studyPlan"), list) else [],
                "careerProspectsAr": item.get("careerProspectsAr") if isinstance(item.get("careerProspectsAr"), list) else [],
                "careerProspectsEn": item.get("careerProspectsEn") if isinstance(item.get("careerProspectsEn"), list) else [],
                "facultyMembers": item.get("facultyMembers") if isinstance(item.get("facultyMembers"), list) else [],
            }
        )
    return output


def _json_fallback_enabled() -> bool:
    raw = frappe.conf.get("AAU_ENABLE_JSON_FALLBACK", 0)
    return str(raw).strip().lower() not in {"0", "false", "no"}


def _serialize_page_item(row: dict) -> dict:
    return {
        "slug": row.get("slug"),
        "titleAr": row.get("title_ar") or row.get("page_title") or "",
        "titleEn": row.get("title_en") or row.get("page_title") or "",
        "contentAr": row.get("content_ar") or row.get("content") or "",
        "contentEn": row.get("content_en") or row.get("content") or "",
        "heroImage": row.get("hero_image") or row.get("banner_image"),
    }


def _serialize_menu(doc) -> dict:
    items = []
    for item in doc.get("items") or []:
        items.append(
            {
                "labelAr": item.get("label_ar") or "",
                "labelEn": item.get("label_en") or "",
                "url": item.get("url") or "",
                "group": item.get("group") or "",
                "openInNewTab": bool(item.get("open_in_new_tab")),
                "order": int(item.get("order") or item.get("idx") or 0),
            }
        )
    items.sort(key=lambda row: row.get("order", 0))
    return {"key": doc.get("key"), "items": items}
