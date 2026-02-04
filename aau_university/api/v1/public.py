# -*- coding: utf-8 -*-
from __future__ import annotations

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
    return {
        "news": _list_home_section("news", limit=4, filters={"is_published": 1}),
        "events": _list_home_section("events", limit=4, filters={"is_published": 1}),
        "colleges": _list_home_section("colleges", limit=6, filters={"is_active": 1}),
        "faqs": _list_home_section("faqs", limit=6, filters={"is_published": 1}),
        "meta": {
            "generated_at": now_ts(),
            "source": _home_source(),
        },
    }


def _list_home_section(entity_key: str, limit: int, filters: dict | None = None) -> list[dict]:
    candidates = {
        "news": ["News"],
        "events": ["Events", "Event"],
        "colleges": ["Colleges", "College"],
        "faqs": ["FAQs", "FAQ"],
    }.get(entity_key, [])
    return _list_home_doctype(candidates=candidates, limit=limit, filters=filters)


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
