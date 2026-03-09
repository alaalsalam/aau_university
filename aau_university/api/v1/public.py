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
    settings = _get_website_settings_payload()
    social_links = _get_social_links_from_menu()
    return {
        "siteName": _as_text(settings.get("site_name") or settings.get("app_name")),
        "siteNameAr": _as_text(settings.get("site_name_ar") or settings.get("site_name")),
        "siteDescriptionAr": _as_text(settings.get("site_description_ar") or settings.get("about_short")),
        "siteDescriptionEn": _as_text(settings.get("site_description_en") or settings.get("about_short_en")),
        "contactPhone": _as_text(settings.get("contact_phone") or settings.get("phone")),
        "contactEmail": _as_text(settings.get("contact_email") or settings.get("email")),
        "addressAr": _as_text(settings.get("address_ar") or settings.get("address")),
        "addressEn": _as_text(settings.get("address_en") or settings.get("address")),
        "mapLocation": _as_text(settings.get("map_location")),
        "socialLinks": social_links,
    }


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
        return {"hero": {}, "stats": [], "about": {}, "partners": [], "testimonials": []}

    meta = frappe.get_meta("Home Page")
    if not getattr(meta, "issingle", 0):
        rows = frappe.get_all("Home Page", fields=["name"], limit_page_length=1, ignore_permissions=True)
        if not rows:
            return {"hero": {}, "stats": [], "about": {}, "partners": [], "testimonials": []}
        row = frappe.get_doc("Home Page", rows[0]["name"]).as_dict()
    else:
        row = frappe.get_cached_doc("Home Page").as_dict()

    if not row:
        return {"hero": {}, "stats": [], "about": {}, "partners": [], "testimonials": []}

    def _text(*candidates, default=""):
        for candidate in candidates:
            value = _as_text(candidate)
            if value:
                return value
        return _as_text(default)

    hero = {
        "badgeAr": _text(row.get("hero_badge_ar"), default="مرحباً بكم في جامعة الجيل الجديد"),
        "badgeEn": _text(row.get("hero_badge_en"), default="Welcome to AJ JEEL ALJADEED UNIVERSITY"),
        "titlePrimaryAr": _text(row.get("hero_title_primary_ar"), default="جامعة الجيل الجديد"),
        "titlePrimaryEn": _text(row.get("hero_title_primary_en"), default="AJ JEEL ALJADEED"),
        "titleSecondaryAr": _text(row.get("hero_title_secondary_ar"), default="الجامعة"),
        "titleSecondaryEn": _text(row.get("hero_title_secondary_en"), default="UNIVERSITY"),
        "descriptionAr": _text(row.get("hero_description_ar")),
        "descriptionEn": _text(row.get("hero_description_en")),
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
            "labelEn": _text(row.get("stats_students_label_en"), default="Students"),
            "icon": "GraduationCap",
        },
        {
            "key": "faculty",
            "number": str(faculty_count),
            "labelAr": _text(row.get("stats_faculty_label_ar"), default="عضو هيئة تدريس"),
            "labelEn": _text(row.get("stats_faculty_label_en"), default="Faculty Members"),
            "icon": "Users",
        },
        {
            "key": "programs",
            "number": str(row.get("programs_count") or 0),
            "labelAr": _text(row.get("stats_programs_label_ar"), default="برنامج أكاديمي"),
            "labelEn": _text(row.get("stats_programs_label_en"), default="Academic Programs"),
            "icon": "BookOpen",
        },
        {
            "key": "colleges",
            "number": str(colleges_count or 0),
            "labelAr": _text(row.get("stats_colleges_label_ar"), default="كليات متخصصة"),
            "labelEn": _text(row.get("stats_colleges_label_en"), default="Specialized Colleges"),
            "icon": "Award",
        },
    ]

    about = {
        "titleAr": _text(row.get("about_title_ar"), default="عن الجامعة"),
        "titleEn": _text(row.get("about_title_en"), default="About the University"),
        "descriptionAr": _text(row.get("about_description_ar")),
        "descriptionEn": _text(row.get("about_description_en")),
        "image": _text(row.get("about_image")),
    }

    return {"hero": hero, "stats": stats, "about": about, "partners": [], "testimonials": []}

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
        "facebook",
        "twitter",
        "instagram",
        "linkedin",
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
    title_en = _as_text(row.get("title_en") or row.get("title") or title_ar)
    description_ar = _as_text(row.get("description_ar") or row.get("summary"))
    description_en = _as_text(row.get("description_en") or row.get("summary") or description_ar)
    content_ar = _as_text(row.get("content_ar") or row.get("content"))
    content_en = _as_text(row.get("content_en") or row.get("content") or content_ar)
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
    title_en = _as_text(row.get("title_en") or row.get("title") or row.get("event_title") or title_ar)
    description_ar = _as_text(row.get("description_ar") or row.get("description"))
    description_en = _as_text(row.get("description_en") or row.get("description") or description_ar)
    content_ar = _as_text(row.get("content_ar") or row.get("content"))
    content_en = _as_text(row.get("content_en") or row.get("content") or content_ar)
    date = row.get("date") or row.get("event_date")
    end_date = row.get("end_date")
    location_ar = _as_text(row.get("location_ar") or row.get("location"))
    location_en = _as_text(row.get("location_en") or row.get("location") or location_ar)
    organizer_ar = _as_text(row.get("organizer_ar") or row.get("organizer"))
    organizer_en = _as_text(row.get("organizer_en") or row.get("organizer") or organizer_ar)
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
    name_en = _as_text(row.get("name_en") or row.get("college_name") or row.get("name") or name_ar)
    description_ar = _as_text(row.get("description_ar") or row.get("description"))
    description_en = _as_text(row.get("description_en") or row.get("description") or description_ar)

    return {
        "id": row.get("id") or slug or row.get("name"),
        "slug": slug,
        "nameAr": name_ar,
        "nameEn": name_en,
        "descriptionAr": description_ar,
        "descriptionEn": description_en,
        "visionAr": _as_text(row.get("vision_ar")),
        "visionEn": _as_text(row.get("vision_en")),
        "missionAr": _as_text(row.get("mission_ar")),
        "missionEn": _as_text(row.get("mission_en")),
        "goalsAr": _as_text(row.get("goals_ar")),
        "goalsEn": _as_text(row.get("goals_en")),
        "admissionRequirementsAr": _as_text(row.get("admission_requirements_ar")),
        "admissionRequirementsEn": _as_text(row.get("admission_requirements_en")),
        "icon": _as_text(row.get("icon")),
        "image": _as_text(row.get("image")),
        "programs": programs,
    }


def _get_college_programs_from_doctype(college_row: dict) -> list[dict]:
    doctype = _first_existing_doctype(["Academic Programs"])
    if not doctype:
        return []

    college_key = college_row.get("name")
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
                "image": program.get("image"),
                "descriptionAr": program.get("description_ar") or program.get("description") or "",
                "descriptionEn": program.get("description_en") or program.get("description") or "",
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
