# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import re

import frappe

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
        meta = frappe.get_meta(doctype)
        search_fields = [f for f in ["title_ar", "title_en", "description_ar", "description_en"] if meta.get_field(f)]
        if not search_fields:
            continue
        or_filters = [[doctype, field, "like", f"%{q}%"] for field in search_fields]
        rows = frappe.get_all(
            doctype,
            fields=["id", "title_ar", "title_en", "description_ar", "description_en", "image", "slug"],
            or_filters=or_filters,
            limit=20,
            ignore_permissions=True,
        )
        total += len(rows)
        for row in rows:
            results.append(
                {
                    "id": row.get("id"),
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

    rows = frappe.get_all(
        doctype,
        fields=list(db_fields),
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

    row = frappe.db.get_value(doctype, filters, list(db_fields), as_dict=True)
    if not row:
        fallback_filters = {"is_active": 1} if "is_active" in db_fields else {}
        candidates = frappe.get_all(
            doctype,
            fields=list(db_fields),
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
    doctype = _first_existing_doctype(["AAU Page", "Static Page"])
    if not doctype:
        raise frappe.DoesNotExistError("Page not found")

    meta = frappe.get_meta(doctype)
    db_fields = {
        df.fieldname
        for df in meta.fields
        if df.fieldname and df.fieldtype not in {"Section Break", "Column Break", "Tab Break", "Fold", "HTML", "Button"}
    }
    filters = {"slug": slug}
    row = frappe.db.get_value(doctype, filters, list(db_fields), as_dict=True)
    if not row:
        raise frappe.DoesNotExistError("Page not found")

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


def _get_home_sections() -> dict:
    if not frappe.db.exists("DocType", "Home Page"):
        return {"hero": {}, "stats": [], "about": {}, "partners": [], "testimonials": []}

    meta = frappe.get_meta("Home Page")
    fields = [
        "hero_title",
        "hero_subtitle",
        "hero_description",
        "hero_image",
        "hero_cta_text",
        "hero_cta_link",
        "about_title",
        "about_description",
        "students_count",
        "programs_count",
        "graduates_count",
    ]
    if meta.get_field("home_sections_json"):
        fields.append("home_sections_json")
    rows = frappe.get_all(
        "Home Page",
        fields=fields,
        filters={"is_published": 1} if meta.get_field("is_published") else None,
        order_by="display_order asc, modified desc",
        limit_page_length=1,
        ignore_permissions=True,
    )
    if not rows:
        return {"hero": {}, "stats": [], "about": {}, "partners": [], "testimonials": []}

    row = rows[0]
    extra = _parse_home_sections_json(row.get("home_sections_json"))
    hero = {
        "badgeAr": extra.get("hero", {}).get("badgeAr", "مرحباً بكم في جامعة الجيل الجديد"),
        "badgeEn": extra.get("hero", {}).get("badgeEn", "Welcome to AJ JEEL ALJADEED UNIVERSITY"),
        "titlePrimaryAr": extra.get("hero", {}).get("titlePrimaryAr", row.get("hero_title") or "جامعة الجيل الجديد"),
        "titlePrimaryEn": extra.get("hero", {}).get("titlePrimaryEn", row.get("hero_title") or "AJ JEEL ALJADEED"),
        "titleSecondaryAr": extra.get("hero", {}).get("titleSecondaryAr", "الجامعة"),
        "titleSecondaryEn": extra.get("hero", {}).get("titleSecondaryEn", "UNIVERSITY"),
        "descriptionAr": extra.get("hero", {}).get("descriptionAr", row.get("hero_description") or row.get("hero_subtitle") or ""),
        "descriptionEn": extra.get("hero", {}).get("descriptionEn", row.get("hero_description") or row.get("hero_subtitle") or ""),
        "applyTextAr": extra.get("hero", {}).get("applyTextAr", row.get("hero_cta_text") or "التقديم الآن"),
        "applyTextEn": extra.get("hero", {}).get("applyTextEn", row.get("hero_cta_text") or "Apply Now"),
        "applyLink": extra.get("hero", {}).get("applyLink", row.get("hero_cta_link") or "/admission"),
        "exploreTextAr": extra.get("hero", {}).get("exploreTextAr", "استكشف الكليات"),
        "exploreTextEn": extra.get("hero", {}).get("exploreTextEn", "Explore Colleges"),
        "exploreLink": extra.get("hero", {}).get("exploreLink", "/colleges"),
        "discoverTextAr": extra.get("hero", {}).get("discoverTextAr", "اكتشف المزيد"),
        "discoverTextEn": extra.get("hero", {}).get("discoverTextEn", "Discover More"),
        "image": extra.get("hero", {}).get("image", row.get("hero_image")),
    }

    colleges_count = frappe.db.count("Colleges") if frappe.db.exists("DocType", "Colleges") else 0
    stats = extra.get("stats", []) if isinstance(extra.get("stats"), list) else []
    if not stats:
        stats = [
            {"key": "students", "number": str(row.get("students_count") or 0), "labelAr": "طالب وطالبة", "labelEn": "Students", "icon": "GraduationCap"},
            {"key": "faculty", "number": "500+", "labelAr": "عضو هيئة تدريس", "labelEn": "Faculty Members", "icon": "Users"},
            {"key": "programs", "number": str(row.get("programs_count") or 0), "labelAr": "برنامج أكاديمي", "labelEn": "Academic Programs", "icon": "BookOpen"},
            {"key": "colleges", "number": str(colleges_count or 0), "labelAr": "كليات متخصصة", "labelEn": "Specialized Colleges", "icon": "Award"},
        ]

    about = extra.get("about", {}) if isinstance(extra.get("about"), dict) else {}
    about.setdefault("titleAr", row.get("about_title") or "عن الجامعة")
    about.setdefault("titleEn", row.get("about_title") or "About the University")
    about.setdefault("descriptionAr", row.get("about_description") or "")
    about.setdefault("descriptionEn", row.get("about_description") or "")
    # WHY+WHAT: include about image from Home Page JSON so the frontend can fully de-hardcode home imagery.
    about.setdefault("image", extra.get("about", {}).get("image"))

    partners = extra.get("partners", []) if isinstance(extra.get("partners"), list) else []
    testimonials = extra.get("testimonials", []) if isinstance(extra.get("testimonials"), list) else []

    return {"hero": hero, "stats": stats, "about": about, "partners": partners, "testimonials": testimonials}


def _parse_home_sections_json(raw: str | None) -> dict:
    if not raw:
        return {}
    try:
        parsed = json.loads(raw)
    except Exception:
        frappe.logger("aau_university").warning("[AAU API] Invalid home_sections_json payload on Home Page")
        return {}
    return parsed if isinstance(parsed, dict) else {}


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
        "programs_json",
        "display_order",
        "is_active",
    ]
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
            "programs": item.get("programs") or [],
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


def _home_source() -> str:
    source_doctypes = ["News", "Events", "Colleges", "FAQ"]
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


def _serialize_news_item(row: dict) -> dict:
    slug = row.get("slug") or _slugify_news_value(row.get("title_en") or row.get("title_ar") or row.get("title"))
    title_ar = row.get("title_ar") or row.get("title")
    title_en = row.get("title_en") or row.get("title")
    description_ar = row.get("description_ar") or row.get("summary") or row.get("content") or ""
    description_en = row.get("description_en") or row.get("summary") or row.get("content") or ""
    content_ar = row.get("content_ar") or row.get("content") or description_ar
    content_en = row.get("content_en") or row.get("content") or description_en
    image = row.get("image") or row.get("featured_image")
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
        "date": str(date)[:10] if date else None,
        "tags": tags,
        "views": int(row.get("views") or 0),
    }


def _serialize_faq_item(row: dict) -> dict:
    question_ar = row.get("question_ar") or row.get("question") or row.get("title") or ""
    question_en = row.get("question_en") or row.get("question") or row.get("title") or ""
    answer_ar = row.get("answer_ar") or row.get("answer") or row.get("content") or ""
    answer_en = row.get("answer_en") or row.get("answer") or row.get("content") or ""
    category = row.get("category")
    fallback_id = _slugify_news_value(question_en or question_ar)

    return {
        "id": row.get("id") or row.get("name") or fallback_id,
        "questionAr": question_ar,
        "questionEn": question_en,
        "answerAr": answer_ar,
        "answerEn": answer_en,
        "category": category,
    }


def _slugify_news_value(value: str | None) -> str:
    if not value:
        return ""
    slug = re.sub(r"[^\w\s-]", "", str(value).strip().lower())
    slug = re.sub(r"[-\s]+", "-", slug)
    return slug.strip("-")


def _serialize_event_item(row: dict) -> dict:
    slug = row.get("slug") or _slugify_news_value(
        row.get("title_en")
        or row.get("title_ar")
        or row.get("event_title")
        or row.get("title")
    )
    title_ar = row.get("title_ar") or row.get("title") or row.get("event_title")
    title_en = row.get("title_en") or row.get("title") or row.get("event_title")
    description_ar = row.get("description_ar") or row.get("description") or row.get("content") or ""
    description_en = row.get("description_en") or row.get("description") or row.get("content") or ""
    content_ar = row.get("content_ar") or row.get("content") or description_ar
    content_en = row.get("content_en") or row.get("content") or description_en
    date = row.get("date") or row.get("event_date")
    end_date = row.get("end_date")
    location_ar = row.get("location_ar") or row.get("location")
    location_en = row.get("location_en") or row.get("location")
    organizer_ar = row.get("organizer_ar") or row.get("organizer")
    organizer_en = row.get("organizer_en") or row.get("organizer")
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
        "date": str(date)[:10] if date else None,
        "endDate": str(end_date)[:10] if end_date else None,
        "locationAr": location_ar,
        "locationEn": location_en,
        "organizerAr": organizer_ar,
        "organizerEn": organizer_en,
        "category": row.get("category") or "other",
        "status": row.get("status") or "upcoming",
        "registrationRequired": bool(row.get("registration_required")),
        "registrationLink": row.get("registration_link"),
        "image": row.get("image"),
        "tags": tags,
    }


def _serialize_college_item(row: dict) -> dict:
    programs = _parse_programs_json(row.get("programs_json"))
    slug = row.get("slug") or _slugify_news_value(
        row.get("name_en")
        or row.get("name_ar")
        or row.get("college_name")
        or row.get("name")
    )
    name_ar = row.get("name_ar") or row.get("college_name") or row.get("name")
    name_en = row.get("name_en") or row.get("college_name") or row.get("name")
    description_ar = row.get("description_ar") or row.get("description") or ""
    description_en = row.get("description_en") or row.get("description") or ""

    return {
        "id": row.get("id") or slug or row.get("name"),
        "slug": slug,
        "nameAr": name_ar,
        "nameEn": name_en,
        "descriptionAr": description_ar,
        "descriptionEn": description_en,
        "visionAr": row.get("vision_ar") or "",
        "visionEn": row.get("vision_en") or "",
        "missionAr": row.get("mission_ar") or "",
        "missionEn": row.get("mission_en") or "",
        "goalsAr": row.get("goals_ar") or "",
        "goalsEn": row.get("goals_en") or "",
        "admissionRequirementsAr": row.get("admission_requirements_ar") or "",
        "admissionRequirementsEn": row.get("admission_requirements_en") or "",
        "icon": row.get("icon"),
        "image": row.get("image"),
        "programs": programs,
    }


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
