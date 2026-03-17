# -*- coding: utf-8 -*-
from __future__ import annotations

import frappe
from frappe.translate import get_all_translations

from .resources import (
    create_entity,
    delete_entity,
    get_entity,
    increment_counter,
    list_entities,
    update_entity,
)
from .utils import ApiError, api_endpoint


@frappe.whitelist(allow_guest=True)
@api_endpoint
def list_news():
    """List news items."""
    result = list_entities(
        "news",
        search_fields=["title_ar", "title_en", "description_ar", "description_en"],
        public=True,
    )
    return {"data": result["data"], "meta": result["meta"], "__meta__": True}


@frappe.whitelist(allow_guest=True)
@api_endpoint
def get_news(slug: str):
    """Get a news item by slug."""
    return get_entity("news", slug, by="slug", public=True)


@frappe.whitelist(allow_guest=True)
@api_endpoint
def list_news_featured():
    """List featured news."""
    frappe.form_dict["is_featured"] = 1
    result = list_entities("news", public=True)
    return {"data": result["data"], "meta": result["meta"], "__meta__": True}


@frappe.whitelist(allow_guest=True)
@api_endpoint
def list_news_recent(limit: int = 3):
    """List recent news."""
    frappe.form_dict["limit"] = limit
    result = list_entities("news", public=True)
    return {"data": result["data"], "meta": result["meta"], "__meta__": True}


@frappe.whitelist(allow_guest=True)
@api_endpoint
def list_news_latest(limit: int = 5):
    """List latest news."""
    frappe.form_dict["limit"] = limit
    result = list_entities("news", public=True)
    return {"data": result["data"], "meta": result["meta"], "__meta__": True}


@frappe.whitelist(allow_guest=True)
@api_endpoint
def search_news(q: str):
    """Search news."""
    frappe.form_dict["q"] = q
    result = list_entities(
        "news",
        search_fields=["title_ar", "title_en", "description_ar", "description_en"],
        public=True,
    )
    return {"data": result["data"], "meta": result["meta"], "__meta__": True}


@frappe.whitelist()
@api_endpoint
def create_news(**payload):
    """Create news."""
    return create_entity("news", payload), 201


@frappe.whitelist()
@api_endpoint
def update_news(news_id: str, **payload):
    """Update news."""
    return update_entity("news", news_id, payload, by="id")


@frappe.whitelist()
@api_endpoint
def delete_news(news_id: str):
    """Delete news."""
    return delete_entity("news", news_id, by="id")


@frappe.whitelist(allow_guest=True)
@api_endpoint
def increment_news_views(news_id: str):
    """Increment news views."""
    return increment_counter("news", news_id, "views")


@frappe.whitelist(allow_guest=True)
@api_endpoint
def list_events():
    """List events."""
    result = list_entities(
        "events",
        search_fields=["title_ar", "title_en", "description_ar", "description_en"],
        public=True,
    )
    return {"data": result["data"], "meta": result["meta"], "__meta__": True}


@frappe.whitelist(allow_guest=True)
@api_endpoint
def get_event(event_id: str):
    """Get an event by id."""
    return get_entity("events", event_id, by="id", public=True)


@frappe.whitelist(allow_guest=True)
@api_endpoint
def get_event_by_slug(slug: str):
    """Get an event by slug."""
    return get_entity("events", slug, by="slug", public=True)


@frappe.whitelist(allow_guest=True)
@api_endpoint
def list_events_upcoming():
    """List upcoming events."""
    frappe.form_dict["status"] = "upcoming"
    result = list_entities("events", public=True)
    return {"data": result["data"], "meta": result["meta"], "__meta__": True}


@frappe.whitelist(allow_guest=True)
@api_endpoint
def list_events_category(category: str):
    """List events by category."""
    frappe.form_dict["category"] = category
    result = list_entities("events", public=True)
    return {"data": result["data"], "meta": result["meta"], "__meta__": True}


@frappe.whitelist()
@api_endpoint
def create_event(**payload):
    """Create event."""
    return create_entity("events", payload), 201


@frappe.whitelist()
@api_endpoint
def update_event(event_id: str, **payload):
    """Update event."""
    return update_entity("events", event_id, payload, by="id")


@frappe.whitelist()
@api_endpoint
def delete_event(event_id: str):
    """Delete event."""
    return delete_entity("events", event_id, by="id")


@frappe.whitelist(allow_guest=True)
@api_endpoint
def list_centers():
    """List centers."""
    return {"data": _list_centers_payload(), "meta": _centers_meta(), "__meta__": True}


@frappe.whitelist(allow_guest=True)
@api_endpoint
def get_center(center_id: str):
    """Get center by id."""
    return _get_center_payload(center_id)


@frappe.whitelist()
@api_endpoint
def create_center(**payload):
    """Create center."""
    doc = frappe.get_doc(_normalize_center_payload(payload))
    doc.insert(ignore_permissions=True)
    return _serialize_center_row(doc), 201


@frappe.whitelist()
@api_endpoint
def update_center(center_id: str, **payload):
    """Update center."""
    docname = _resolve_center_docname(center_id)
    doc = frappe.get_doc("Centers", docname)
    doc.update(_normalize_center_payload(payload, is_update=True))
    doc.save(ignore_permissions=True)
    return _serialize_center_row(doc)


@frappe.whitelist()
@api_endpoint
def delete_center(center_id: str):
    """Delete center."""
    return delete_entity("centers", center_id, by="id")


@frappe.whitelist(allow_guest=True)
@api_endpoint
def list_partners():
    """List partners."""
    result = list_entities("partners", public=True)
    return {"data": result["data"], "meta": result["meta"], "__meta__": True}


@frappe.whitelist(allow_guest=True)
@api_endpoint
def list_partners_by_type(partner_type: str):
    """List partners by type."""
    frappe.form_dict["type"] = partner_type
    result = list_entities("partners", public=True)
    return {"data": result["data"], "meta": result["meta"], "__meta__": True}


@frappe.whitelist()
@api_endpoint
def create_partner(**payload):
    """Create partner."""
    return create_entity("partners", payload), 201


@frappe.whitelist()
@api_endpoint
def update_partner(partner_id: str, **payload):
    """Update partner."""
    return update_entity("partners", partner_id, payload, by="id")


@frappe.whitelist()
@api_endpoint
def delete_partner(partner_id: str):
    """Delete partner."""
    return delete_entity("partners", partner_id, by="id")


def _list_centers_payload(include_unpublished: bool = False) -> list[dict]:
    filters: dict[str, object] = {}
    if frappe.get_meta("Centers").get_field("is_published") and not include_unpublished:
        filters["is_published"] = 1

    rows = frappe.get_all(
        "Centers",
        filters=filters,
        fields=[
            "name",
            "id",
            "title_ar",
            "title_en",
            "desc_ar",
            "desc_en",
            "image",
            "location",
            "phone",
            "email",
            "display_order",
        ],
        order_by="display_order asc, modified desc",
        ignore_permissions=True,
        limit_page_length=0,
    )

    items = []
    for row in rows:
        doc = frappe.get_doc("Centers", row.get("name"))
        items.append(_serialize_center_row(doc))

    page = max(int(frappe.form_dict.get("page") or 1), 1)
    limit = max(int(frappe.form_dict.get("limit") or frappe.form_dict.get("page_size") or 20), 1)
    offset = (page - 1) * limit
    paged = items[offset : offset + limit]
    frappe.flags.aau_centers_meta = {
        "page": page,
        "limit": limit,
        "total": len(items),
        "totalPages": (len(items) + limit - 1) // limit if limit else 1,
    }
    return paged


def _get_center_payload(center_id: str) -> dict:
    docname = _resolve_center_docname(center_id)
    doc = frappe.get_doc("Centers", docname)
    if getattr(doc, "is_published", 1) in (0, "0", False):
        raise frappe.DoesNotExistError
    return _serialize_center_row(doc)


def _centers_meta() -> dict:
    return getattr(frappe.flags, "aau_centers_meta", {"page": 1, "limit": 20, "total": 0, "totalPages": 0})


def _resolve_center_docname(center_id: str) -> str:
    if frappe.db.exists("Centers", center_id):
        return center_id
    docname = frappe.db.get_value("Centers", {"id": center_id}, "name")
    if docname:
        return docname
    raise frappe.DoesNotExistError


def _serialize_center_row(doc) -> dict:
    title_ar = _as_text(doc.get("title_ar"))
    desc_ar = _as_text(doc.get("desc_ar"))
    title_en = _as_text(doc.get("title_en"), default=_translated_text(title_ar))
    desc_en = _as_text(doc.get("desc_en"), default=_translated_text(desc_ar))
    services = _serialize_center_items(doc.get("services") or [])
    programs = _serialize_center_items(doc.get("programs") or [])
    identifier = _as_text(doc.get("id"), default=doc.name)

    return {
        "id": identifier,
        "titleAr": title_ar,
        "titleEn": title_en,
        "descAr": desc_ar,
        "descEn": desc_en,
        "services": services,
        "programs": programs,
        "image": _as_text(doc.get("image")),
        "location": _as_text(doc.get("location")),
        "phone": _as_text(doc.get("phone")),
        "email": _as_text(doc.get("email")),
    }


def _serialize_center_items(rows) -> list[dict]:
    if isinstance(rows, str):
        rows = [line.strip() for line in rows.splitlines() if line and line.strip()]

    serialized = []
    for row in rows:
        if isinstance(row, dict):
            raw_value = row.get("value")
        elif isinstance(row, str):
            raw_value = row
        else:
            raw_value = row.value

        value_ar = _as_text(raw_value)
        if not value_ar:
            continue
        serialized.append({"ar": value_ar, "en": _translated_text(value_ar)})
    return serialized


def _normalize_center_payload(payload: dict, is_update: bool = False) -> dict:
    normalized = {}
    if not is_update:
        normalized["doctype"] = "Centers"

    title_ar = _payload_value(payload, "titleAr", "title_ar")
    title_en = _payload_value(payload, "titleEn", "title_en")
    desc_ar = _payload_value(payload, "descAr", "desc_ar")
    desc_en = _payload_value(payload, "descEn", "desc_en")
    center_id = _payload_value(payload, "id")
    image = _payload_value(payload, "image")
    location = _payload_value(payload, "location")
    phone = _payload_value(payload, "phone")
    email = _payload_value(payload, "email")
    display_order = payload.get("display_order", payload.get("displayOrder"))
    is_published = payload.get("is_published", payload.get("isPublished"))

    if title_ar:
        normalized["title_ar"] = title_ar
    if title_en:
        normalized["title_en"] = title_en
    if desc_ar:
        normalized["desc_ar"] = desc_ar
    if desc_en:
        normalized["desc_en"] = desc_en
    if center_id:
        normalized["id"] = center_id
    if image:
        normalized["image"] = image
    if location:
        normalized["location"] = location
    if phone:
        normalized["phone"] = phone
    if email:
        normalized["email"] = email
    if display_order is not None and str(display_order).strip():
        normalized["display_order"] = int(display_order)
    if is_published is not None:
        normalized["is_published"] = 1 if str(is_published).lower() in {"1", "true", "yes"} else 0

    services = payload.get("services")
    if isinstance(services, list):
        normalized["services"] = [{"value": _payload_list_value(item)} for item in services if _payload_list_value(item)]
    elif isinstance(services, str) and services.strip():
        normalized["services"] = services.strip()

    programs = payload.get("programs")
    if isinstance(programs, list):
        normalized["programs"] = [{"value": _payload_list_value(item)} for item in programs if _payload_list_value(item)]
    elif isinstance(programs, str) and programs.strip():
        normalized["programs"] = programs.strip()

    if not is_update and not normalized.get("title_ar"):
        raise ApiError("VALIDATION_ERROR", "Center titleAr is required", status_code=400)
    return normalized


def _payload_list_value(item) -> str:
    if isinstance(item, dict):
        for key in ("ar", "value", "titleAr", "nameAr"):
            value = item.get(key)
            if value is not None and str(value).strip():
                return str(value).strip()
        return ""
    return _as_text(item)


def _list_campus_life_payload() -> list[dict]:
    if not frappe.db.exists("DocType", "Campus Life"):
        return []

    rows = frappe.get_all(
        "Campus Life",
        filters={"is_published": 1} if frappe.get_meta("Campus Life").get_field("is_published") else None,
        fields=["name", "title", "content", "image", "display_order"],
        order_by="display_order asc, modified desc, name asc",
        ignore_permissions=True,
    )

    items: list[dict] = []
    used_slugs: set[str] = set()
    for row in rows:
        items.append(_serialize_campus_life_row(row, used_slugs))
    return items


def _list_research_publications_payload() -> list[dict]:
    if not frappe.db.exists("DocType", "Research and Publications"):
        return []

    filters: dict[str, object] = {}
    if frappe.get_meta("Research and Publications").get_field("is_published"):
        filters["is_published"] = 1

    rows = frappe.get_all(
        "Research and Publications",
        filters=filters or None,
        fields=["name", "title", "content", "image", "creation", "modified", "display_order"],
        order_by="display_order asc, creation desc, name asc",
        ignore_permissions=True,
    )
    return [_serialize_research_publication_row(row) for row in rows]


def _serialize_research_publication_row(row) -> dict:
    title_ar = _as_text(row.get("title"))
    title_en = _translated_text(title_ar)
    content_ar = _as_text(row.get("content"))
    content_en = _translated_text(content_ar)
    created_on = row.get("creation") or row.get("modified")
    publish_date = str(created_on.date()) if hasattr(created_on, "date") else _as_text(created_on)

    return {
        "id": _as_text(row.get("name")),
        "titleAr": title_ar,
        "titleEn": title_en,
        "authorAr": "هيئة التحرير البحثي",
        "authorEn": "Research Editorial Board",
        "categoryAr": "البحث العلمي",
        "categoryEn": "Research",
        "summaryAr": _excerpt_text(content_ar, limit=220),
        "summaryEn": _excerpt_text(content_en, limit=220),
        "contentAr": content_ar,
        "contentEn": content_en,
        "publishDateAr": publish_date,
        "publishDateEn": publish_date,
        "image": row.get("image") or "",
        "tags": [],
        "displayOrder": int(row.get("display_order") or 0),
    }


def _serialize_campus_life_row(row, used_slugs: set[str] | None = None) -> dict:
    title_ar = _as_text(row.get("title"))
    content_ar = _as_text(row.get("content"))
    title_en = _translated_text(title_ar)
    content_en = _translated_text(content_ar)
    category = _infer_campus_life_category(title_ar, content_ar)

    if used_slugs is None:
        used_slugs = set()
    slug = _unique_slug(_slugify_value(title_ar or row.get("name")), row.get("name"), used_slugs)

    return {
        "id": _as_text(row.get("name")),
        "slug": slug,
        "titleAr": title_ar,
        "titleEn": title_en,
        "descriptionAr": _excerpt_text(content_ar),
        "descriptionEn": _excerpt_text(content_en),
        "contentAr": content_ar,
        "contentEn": content_en,
        "category": category,
        "image": row.get("image") or "",
        "displayOrder": int(row.get("display_order") or 0),
    }


def _infer_campus_life_category(title: str, content: str) -> str:
    haystack = f"{title} {content}".lower()
    if any(keyword in haystack for keyword in ("نشاط", "فعالية", "نادي", "رياضي", "ثقافي", "تطوعي")):
        return "activities"
    if any(
        keyword in haystack
        for keyword in (
            "مكتبة",
            "مختبر",
            "ملعب",
            "مركز",
            "قاعة",
            "مطعم",
            "كافتيريا",
            "عيادة",
            "تقنية",
            "تقني",
            "مرفق",
        )
    ):
        return "facilities"
    return "campus"


def _excerpt_text(value: str, limit: int = 180) -> str:
    text = " ".join(_as_text(value).split())
    if not text:
        return ""
    if len(text) <= limit:
        return text
    return f"{text[: limit - 1].rstrip()}…"


def _slugify_value(value: str | None) -> str:
    source = _as_text(value)
    if not source:
        return ""
    return frappe.scrub(source).replace("_", "-").strip("-")


def _unique_slug(base_slug: str, fallback: str | None, used_slugs: set[str]) -> str:
    candidate = base_slug or _slugify_value(fallback) or "item"
    if candidate not in used_slugs:
        used_slugs.add(candidate)
        return candidate

    suffix = _slugify_value(fallback) or "item"
    unique_candidate = f"{candidate}-{suffix}"
    if unique_candidate not in used_slugs:
        used_slugs.add(unique_candidate)
        return unique_candidate

    index = 2
    while f"{unique_candidate}-{index}" in used_slugs:
        index += 1
    final_candidate = f"{unique_candidate}-{index}"
    used_slugs.add(final_candidate)
    return final_candidate


def _translated_text(value: str, lang: str = "en") -> str:
    source = _as_text(value)
    if not source:
        return ""
    translations = get_all_translations(lang) or {}
    return _as_text(translations.get(source), default=source)


def _as_text(value, default: str = "") -> str:
    if value is None:
        return default
    if isinstance(value, str):
        cleaned = value.strip()
        return cleaned if cleaned else default
    return str(value).strip() or default


def _payload_value(payload: dict, *keys: str) -> str:
    for key in keys:
        value = payload.get(key)
        if value is not None and str(value).strip():
            return str(value).strip()
    return ""


@frappe.whitelist(allow_guest=True)
@api_endpoint
def list_offers():
    """List offers."""
    result = list_entities("offers", public=True)
    return {"data": result["data"], "meta": result["meta"], "__meta__": True}


@frappe.whitelist(allow_guest=True)
@api_endpoint
def get_offer(offer_id: str):
    """Get offer by id."""
    return get_entity("offers", offer_id, by="id", public=True)


@frappe.whitelist(allow_guest=True)
@api_endpoint
def list_offers_active():
    """List active offers."""
    frappe.form_dict["is_active"] = 1
    result = list_entities("offers", public=True)
    return {"data": result["data"], "meta": result["meta"], "__meta__": True}


@frappe.whitelist(allow_guest=True)
@api_endpoint
def list_offers_by_category(category: str):
    """List offers by category."""
    frappe.form_dict["category"] = category
    result = list_entities("offers", public=True)
    return {"data": result["data"], "meta": result["meta"], "__meta__": True}


@frappe.whitelist(allow_guest=True)
@api_endpoint
def search_offers(q: str):
    """Search offers."""
    frappe.form_dict["q"] = q
    result = list_entities("offers", search_fields=["title_ar", "title_en", "desc_ar", "desc_en"], public=True)
    return {"data": result["data"], "meta": result["meta"], "__meta__": True}


@frappe.whitelist()
@api_endpoint
def create_offer(**payload):
    """Create offer."""
    return create_entity("offers", payload), 201


@frappe.whitelist()
@api_endpoint
def update_offer(offer_id: str, **payload):
    """Update offer."""
    return update_entity("offers", offer_id, payload, by="id")


@frappe.whitelist()
@api_endpoint
def delete_offer(offer_id: str):
    """Delete offer."""
    return delete_entity("offers", offer_id, by="id")


@frappe.whitelist(allow_guest=True)
@api_endpoint
def list_faqs():
    """List FAQs."""
    result = list_entities("faqs", public=True)
    return {"data": result["data"], "meta": result["meta"], "__meta__": True}


@frappe.whitelist(allow_guest=True)
@api_endpoint
def list_faqs_by_category(category: str):
    """List FAQs by category."""
    frappe.form_dict["category"] = category
    result = list_entities("faqs", public=True)
    return {"data": result["data"], "meta": result["meta"], "__meta__": True}


@frappe.whitelist()
@api_endpoint
def create_faq(**payload):
    """Create FAQ."""
    return create_entity("faqs", payload), 201


@frappe.whitelist()
@api_endpoint
def update_faq(faq_id: str, **payload):
    """Update FAQ."""
    return update_entity("faqs", faq_id, payload, by="id")


@frappe.whitelist()
@api_endpoint
def delete_faq(faq_id: str):
    """Delete FAQ."""
    return delete_entity("faqs", faq_id, by="id")


@frappe.whitelist(allow_guest=True)
@api_endpoint
def list_team_members():
    """List team members."""
    result = list_entities("team_members", public=True)
    return {"data": result["data"], "meta": result["meta"], "__meta__": True}


@frappe.whitelist(allow_guest=True)
@api_endpoint
def get_team_member(member_id: str):
    """Get team member by id."""
    return get_entity("team_members", member_id, by="id", public=True)


@frappe.whitelist()
@api_endpoint
def create_team_member(**payload):
    """Create team member."""
    return create_entity("team_members", payload), 201


@frappe.whitelist()
@api_endpoint
def update_team_member(member_id: str, **payload):
    """Update team member."""
    return update_entity("team_members", member_id, payload, by="id")


@frappe.whitelist()
@api_endpoint
def delete_team_member(member_id: str):
    """Delete team member."""
    return delete_entity("team_members", member_id, by="id")


@frappe.whitelist(allow_guest=True)
@api_endpoint
def list_projects():
    """List projects."""
    result = list_entities("projects", public=True)
    return {"data": result["data"], "meta": result["meta"], "__meta__": True}


@frappe.whitelist(allow_guest=True)
@api_endpoint
def get_project(slug: str):
    """Get project by slug."""
    return get_entity("projects", slug, by="slug", public=True)


@frappe.whitelist(allow_guest=True)
@api_endpoint
def list_projects_current():
    """List current projects."""
    frappe.form_dict["status"] = "current"
    result = list_entities("projects", public=True)
    return {"data": result["data"], "meta": result["meta"], "__meta__": True}


@frappe.whitelist(allow_guest=True)
@api_endpoint
def list_projects_completed():
    """List completed projects."""
    frappe.form_dict["status"] = "completed"
    result = list_entities("projects", public=True)
    return {"data": result["data"], "meta": result["meta"], "__meta__": True}


@frappe.whitelist(allow_guest=True)
@api_endpoint
def search_projects(q: str):
    """Search projects."""
    frappe.form_dict["q"] = q
    result = list_entities("projects", search_fields=["title_ar", "title_en", "desc_ar", "desc_en"], public=True)
    return {"data": result["data"], "meta": result["meta"], "__meta__": True}


@frappe.whitelist()
@api_endpoint
def create_project(**payload):
    """Create project."""
    return create_entity("projects", payload), 201


@frappe.whitelist()
@api_endpoint
def update_project(project_id: str, **payload):
    """Update project."""
    return update_entity("projects", project_id, payload, by="id")


@frappe.whitelist()
@api_endpoint
def delete_project(project_id: str):
    """Delete project."""
    return delete_entity("projects", project_id, by="id")


@frappe.whitelist(allow_guest=True)
@api_endpoint
def list_campus_life():
    """List campus life items."""
    items = _list_campus_life_payload()
    return {"data": items, "meta": {"total": len(items)}, "__meta__": True}


@frappe.whitelist(allow_guest=True)
@api_endpoint
def get_campus_life(slug: str):
    """Get campus life item by derived slug."""
    for item in _list_campus_life_payload():
        if item.get("slug") == slug:
            return item
    raise ApiError("NOT_FOUND", "Campus life item not found", status_code=404)


@frappe.whitelist(allow_guest=True)
@api_endpoint
def list_campus_life_by_category(category: str):
    """List campus life by category."""
    normalized_category = _as_text(category).lower()
    items = [item for item in _list_campus_life_payload() if item.get("category") == normalized_category]
    return {"data": items, "meta": {"total": len(items)}, "__meta__": True}


@frappe.whitelist()
@api_endpoint
def create_campus_life(**payload):
    """Create campus life item."""
    return create_entity("campus_life", payload), 201


@frappe.whitelist()
@api_endpoint
def update_campus_life(item_id: str, **payload):
    """Update campus life item."""
    return update_entity("campus_life", item_id, payload, by="id")


@frappe.whitelist()
@api_endpoint
def delete_campus_life(item_id: str):
    """Delete campus life item."""
    return delete_entity("campus_life", item_id, by="id")


@frappe.whitelist(allow_guest=True)
@api_endpoint
def list_blog_posts():
    """List blog posts."""
    result = list_entities("blog_posts", public=True)
    return {"data": result["data"], "meta": result["meta"], "__meta__": True}


@frappe.whitelist(allow_guest=True)
@api_endpoint
def list_research_publications():
    """List public research publications."""
    items = _list_research_publications_payload()
    return {"data": items, "meta": {"total": len(items)}, "__meta__": True}


@frappe.whitelist(allow_guest=True)
@api_endpoint
def get_research_publication(publication_id: str):
    """Get research publication by document name."""
    for item in _list_research_publications_payload():
        if item.get("id") == publication_id:
            return item
    raise ApiError("NOT_FOUND", "Research publication not found", status_code=404)


@frappe.whitelist(allow_guest=True)
@api_endpoint
def get_blog_post(blog_id: str):
    """Get blog post by id."""
    return get_entity("blog_posts", blog_id, by="id", public=True)


@frappe.whitelist(allow_guest=True)
@api_endpoint
def get_blog_post_by_slug(slug: str):
    """Get blog post by slug."""
    return get_entity("blog_posts", slug, by="slug", public=True)


@frappe.whitelist(allow_guest=True)
@api_endpoint
def list_blog_categories():
    """List blog categories."""
    if not frappe.db.exists("DocType", "Blog Posts"):
        return []
    rows = frappe.get_all(
        "Blog Posts",
        fields=["category"],
        distinct=True,
        ignore_permissions=True,
    )
    return [row["category"] for row in rows if row.get("category")]


@frappe.whitelist(allow_guest=True)
@api_endpoint
def list_blog_by_category(category: str):
    """List blog posts by category."""
    frappe.form_dict["category"] = category
    result = list_entities("blog_posts", public=True)
    return {"data": result["data"], "meta": result["meta"], "__meta__": True}


@frappe.whitelist()
@api_endpoint
def create_blog_post(**payload):
    """Create blog post."""
    return create_entity("blog_posts", payload), 201


@frappe.whitelist()
@api_endpoint
def update_blog_post(post_id: str, **payload):
    """Update blog post."""
    return update_entity("blog_posts", post_id, payload, by="id")


@frappe.whitelist()
@api_endpoint
def delete_blog_post(post_id: str):
    """Delete blog post."""
    return delete_entity("blog_posts", post_id, by="id")


@frappe.whitelist(allow_guest=True)
@api_endpoint
def increment_blog_views(post_id: str):
    """Increment blog post views."""
    return increment_counter("blog_posts", post_id, "views")


@frappe.whitelist(allow_guest=True)
@api_endpoint
def list_pages():
    """List managed static pages."""
    return list_entities("pages", search_fields=["slug", "title_ar", "title_en", "page_title"], public=False)


@frappe.whitelist(allow_guest=True)
@api_endpoint
def get_page(slug: str):
    """Get a page by slug."""
    return get_entity("pages", slug, by="slug", public=False)


@frappe.whitelist()
@api_endpoint
def update_page(slug: str, **payload):
    """Update a page by slug."""
    try:
        return update_entity("pages", slug, payload, by="slug")
    except frappe.DoesNotExistError:
        data = dict(payload or {})
        data.setdefault("slug", slug)
        data.setdefault("id", slug)
        return create_entity("pages", data), 201
