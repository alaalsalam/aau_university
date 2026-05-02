# -*- coding: utf-8 -*-
from __future__ import annotations

import base64
import ast
import json
import os
import re

import frappe
from frappe.translate import get_all_translations
from frappe.utils.file_manager import save_file

from .registry import ADMIN_ROLES, SEARCH_TYPES
from .resources import (
    create_entity,
    delete_entity,
    get_entity,
    list_entities,
    update_status,
)
from .utils import ApiError, api_endpoint, ensure_uuid, now_ts, require_roles, to_camel

STUDENT_AFFAIRS_DOCUMENTS = [
    {
        "id": "student-affairs-regulations",
        "titleAr": "لائحة شؤون الطلاب",
        "titleEn": "Student Affairs Regulations",
        "href": "/docs/regulations.pdf",
        "fileComingSoon": 1,
        "displayOrder": 1,
    },
    {
        "id": "supplementary-semester",
        "titleAr": "الدوري التكميلي",
        "titleEn": "Supplementary Semester",
        "href": "/docs/supplementary.pdf",
        "fileComingSoon": 1,
        "displayOrder": 2,
    },
    {
        "id": "grievance-form",
        "titleAr": "استمارة تظلمات",
        "titleEn": "Grievance Form",
        "href": "/docs/grievance.pdf",
        "fileComingSoon": 1,
        "displayOrder": 3,
    },
    {
        "id": "general-conduct",
        "titleAr": "ضوابط وسلوكيات عامة",
        "titleEn": "General Behavior Controls",
        "href": "/docs/general_conduct.pdf",
        "fileComingSoon": 1,
        "displayOrder": 4,
    },
    {
        "id": "exam-conduct",
        "titleAr": "ضوابط وسلوكيات الامتحانات",
        "titleEn": "Exam Behavior Controls",
        "href": "/docs/exam_conduct.pdf",
        "fileComingSoon": 1,
        "displayOrder": 5,
    },
]


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
def create_email_request(**payload):
    """Create an institutional email request."""
    payload = _merge_request_payload(payload)
    payload.setdefault("status", "pending")
    payload.setdefault("created_at", now_ts())
    payload.setdefault("id", ensure_uuid(payload.get("id")))

    required_fields = ["name_ar", "name_en", "academic_id", "college", "level", "phone"]
    missing_fields = [field for field in required_fields if not str(payload.get(field) or "").strip()]
    if missing_fields:
        raise ApiError(
            "VALIDATION_ERROR",
            "Missing required email request fields",
            details={"missing": missing_fields},
            status_code=400,
        )

    allowed_fields = {"id", "name_ar", "name_en", "academic_id", "college", "level", "phone", "status", "created_at"}
    payload = frappe._dict({key: value for key, value in payload.items() if key in allowed_fields and value not in (None, "")})
    created = create_entity("email_requests", payload, public=True)
    doc_id = _as_text(created.get("id") or payload.get("id"))
    if doc_id:
        return get_entity("email_requests", doc_id, by="id", public=True), 201
    return created, 201


@frappe.whitelist()
@api_endpoint
def list_email_requests():
    """List institutional email requests."""
    require_roles(ADMIN_ROLES)
    result = list_entities("email_requests", public=False)
    return {"data": result["data"], "meta": result["meta"], "__meta__": True}


@frappe.whitelist()
@api_endpoint
def get_email_request(request_id: str):
    """Get an institutional email request by id."""
    require_roles(ADMIN_ROLES)
    return get_entity("email_requests", request_id, by="id", public=False)


@frappe.whitelist()
@api_endpoint
def update_email_request_status(request_id: str, status: str):
    """Update email request status."""
    require_roles(ADMIN_ROLES)
    return update_status("email_requests", request_id, "status", status)


@frappe.whitelist()
@api_endpoint
def delete_email_request(request_id: str):
    """Delete an institutional email request."""
    require_roles(ADMIN_ROLES)
    return delete_entity("email_requests", request_id, by="id")


@frappe.whitelist(allow_guest=True)
@api_endpoint
def create_join_request(**payload):
    """Create a join request."""
    payload = _merge_request_payload(payload)
    payload = _unwrap_wrapped_payload(payload)
    upload_payloads = _extract_join_request_uploads(payload)
    key_aliases = {
        "fullName": "full_name",
        "collegeId": "college_id",
        "collegeName": "college_name",
        "programId": "program_id",
        "programName": "program_name",
        "educationStatus": "education_status",
        "hasRequiredDocuments": "has_required_documents",
        "highSchoolDocumentName": "high_school_document_name",
        "idDocumentName": "id_document_name",
        "personalPhotoName": "personal_photo_name",
        "serialNumber": "serial_number",
        "cvFile": "cv_file",
        "reviewedAt": "reviewed_at",
        "createdAt": "created_at",
        "isPublished": "is_published",
        "displayOrder": "display_order",
    }
    for source_key, target_key in key_aliases.items():
        source_value = payload.get(source_key)
        if source_value not in (None, "") and payload.get(target_key) in (None, ""):
            payload[target_key] = source_value

    if payload.get("name") and not payload.get("full_name"):
        payload["full_name"] = payload.get("name")
    if payload.get("college") and not payload.get("college_id"):
        payload["college_id"] = payload.get("college")
    if payload.get("program") and not payload.get("program_id"):
        payload["program_id"] = payload.get("program")
    if payload.get("program") and not payload.get("specialty"):
        payload["specialty"] = payload.get("program")
    if payload.get("major") and not payload.get("specialty"):
        payload["specialty"] = payload.get("major")
    if payload.get("program_name") and not payload.get("specialty"):
        payload["specialty"] = payload.get("program_name")
    if payload.get("program_id") and not payload.get("specialty"):
        payload["specialty"] = payload.get("program_id")
    if payload.get("program") and not payload.get("program_name"):
        payload["program_name"] = payload.get("program")
    if payload.get("college") and not payload.get("college_name"):
        payload["college_name"] = payload.get("college")
    if payload.get("educationStatus") and not payload.get("education_status"):
        payload["education_status"] = payload.get("educationStatus")

    payload = _normalize_join_request_document_fields(payload, upload_payloads)

    documents = payload.get("documents")
    if isinstance(documents, dict):
        if documents.get("highSchool") and not payload.get("high_school_document_name"):
            payload["high_school_document_name"] = _extract_upload_name(documents.get("highSchool"))
        if documents.get("id") and not payload.get("id_document_name"):
            payload["id_document_name"] = _extract_upload_name(documents.get("id"))
        if documents.get("photo") and not payload.get("personal_photo_name"):
            payload["personal_photo_name"] = _extract_upload_name(documents.get("photo"))

    has_docs = all(
        [
            payload.get("high_school_document_name") or upload_payloads.get("high_school_document_name"),
            payload.get("id_document_name") or upload_payloads.get("id_document_name"),
            payload.get("personal_photo_name") or upload_payloads.get("personal_photo_name"),
        ]
    )
    if payload.get("has_required_documents") in (None, ""):
        payload["has_required_documents"] = 1 if has_docs else 0

    payload.setdefault("status", "pending")
    payload.setdefault("type", "student")
    payload.setdefault("created_at", now_ts())
    payload.setdefault("id", ensure_uuid(payload.get("id")))

    required_fields = ["full_name", "email", "phone", "specialty"]
    missing_fields = [field for field in required_fields if not str(payload.get(field) or "").strip()]
    if missing_fields:
        raise ApiError(
            "VALIDATION_ERROR",
            "Missing required join request fields",
            details={"missing": missing_fields},
            status_code=400,
        )

    # Keep this public endpoint tolerant to older frontend bundles that may still
    # send extra UI-only fields such as college/program/documents/educationStatus.
    allowed_fields = {
        "id",
        "type",
        "full_name",
        "email",
        "phone",
        "specialty",
        "college_id",
        "college_name",
        "program_id",
        "program_name",
        "education_status",
        "has_required_documents",
        "high_school_document_name",
        "id_document_name",
        "personal_photo_name",
        "serial_number",
        "message",
        "status",
        "reviewed_at",
        "created_at",
    }
    payload = frappe._dict(
        {
            key: value
            for key, value in payload.items()
            if key in allowed_fields and value not in (None, "")
        }
    )
    created = create_entity("join_requests", payload, public=True)
    docname = _as_text(created.get("docname"))
    doc_id = _as_text(created.get("id") or payload.get("id"))

    if docname:
        updates = _attach_join_request_uploads(docname, upload_payloads)
        if updates:
            for fieldname, file_url in updates.items():
                frappe.db.set_value("Join Requests", docname, fieldname, file_url, update_modified=True)
            if all(updates.get(field) for field in ("high_school_document_name", "id_document_name", "personal_photo_name")):
                frappe.db.set_value("Join Requests", docname, "has_required_documents", 1, update_modified=True)
            frappe.db.commit()

    if doc_id:
        return get_entity("join_requests", doc_id, by="id", public=True), 201
    return created, 201


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


@frappe.whitelist()
@api_endpoint
def repair_join_request_document_links(limit: int = 200):
    """Repair legacy join request document values into real file links."""
    require_roles(ADMIN_ROLES)
    fixed = 0
    scanned = 0
    rows = frappe.get_all(
        "Join Requests",
        fields=[
            "name",
            "high_school_document_name",
            "id_document_name",
            "personal_photo_name",
        ],
        order_by="modified desc",
        limit_page_length=max(1, min(int(limit or 200), 2000)),
        ignore_permissions=True,
    )
    for row in rows:
        scanned += 1
        updates = _repair_join_request_document_row(row)
        if updates:
            for fieldname, value in updates.items():
                frappe.db.set_value("Join Requests", row.get("name"), fieldname, value, update_modified=True)
            fixed += 1
    if fixed:
        frappe.db.commit()
    return {"scanned": scanned, "fixed": fixed}


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
    if "modified" not in fields:
        fields.append("modified")
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
    if "modified" not in fields:
        fields.append("modified")
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
    doctype = _first_existing_doctype(["AAU Page", "Static Page", "Pages"])
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
def list_student_affairs_documents():
    doctype = _first_existing_doctype(["Student Affairs Document"])
    items = []

    if doctype:
        meta = frappe.get_meta(doctype)
        db_fields = {
            df.fieldname
            for df in meta.fields
            if df.fieldname and df.fieldtype not in {"Section Break", "Column Break", "Tab Break", "Fold", "HTML", "Button"}
        }

        fields_to_read = [
            "name",
            "id",
            "title_ar",
            "title_en",
            "title",
            "file_url",
            "href",
            "file_coming_soon",
            "is_published",
            "display_order",
        ]
        read_fields = [field for field in fields_to_read if field in db_fields or field == "name"]
        filters = {}
        if "is_published" in db_fields and frappe.session.user == "Guest":
            filters["is_published"] = 1
        order_by = "display_order asc, modified desc" if "display_order" in db_fields else "modified desc"
        rows = frappe.get_all(doctype, filters=filters, fields=read_fields, order_by=order_by, ignore_permissions=True)

        for row in rows:
            href = _as_text(row.get("file_url") or row.get("href"))
            file_coming_soon = row.get("file_coming_soon")
            if file_coming_soon in (None, ""):
                file_coming_soon = 0 if href else 1
            items.append(
                {
                    "id": _as_text(row.get("id") or row.get("name")),
                    "titleAr": _as_text(row.get("title_ar") or row.get("title")),
                    "titleEn": _as_text(row.get("title_en") or row.get("title_ar") or row.get("title")),
                    "href": href,
                    "fileComingSoon": bool(file_coming_soon),
                    "displayOrder": int(row.get("display_order") or 0),
                }
            )

        items = [item for item in items if item.get("id") and (item.get("titleAr") or item.get("titleEn"))]

    if not items:
        items = [
            {
                "id": _as_text(item.get("id")),
                "titleAr": _as_text(item.get("titleAr")),
                "titleEn": _as_text(item.get("titleEn") or item.get("titleAr")),
                "href": _as_text(item.get("href")),
                "fileComingSoon": bool(item.get("fileComingSoon", True)),
                "displayOrder": int(item.get("displayOrder") or 0),
            }
            for item in sorted(STUDENT_AFFAIRS_DOCUMENTS, key=lambda row: int(row.get("displayOrder") or 0))
        ]

    return {
        "sectionTitleAr": "شؤون الطلاب",
        "sectionTitleEn": "Student Affairs",
        "items": items,
    }


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
        "footerBackgroundType": "footer_background_type",
        "footerBackgroundImage": "footer_background_image",
        "footerBackgroundVideo": "footer_background_video",
        "footerBackgroundOverlayOpacity": "footer_background_overlay_opacity",
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
        return _as_text(translations.get(source))

    def _choose_en(explicit_en, ar_value, default_en: str = "") -> str:
        explicit = _text(explicit_en)
        if explicit:
            return explicit
        translated = _translated(_text(ar_value))
        if translated:
            return translated
        return _text(default_en)

    hero = {
        "badgeAr": _text(row.get("hero_badge_ar"), default="مرحباً بكم في جامعة الجيل الجديد"),
        "badgeEn": _choose_en(row.get("hero_badge_en"), row.get("hero_badge_ar"), "Welcome to Al-Jeel Al-Jadeed University"),
        "titlePrimaryAr": _text(row.get("hero_title_primary_ar"), default="جامعة الجيل الجديد"),
        "titlePrimaryEn": _choose_en(row.get("hero_title_primary_en"), row.get("hero_title_primary_ar"), "Al-Jeel Al-Jadeed University"),
        "titleSecondaryAr": _text(row.get("hero_title_secondary_ar"), default="الجامعة"),
        "titleSecondaryEn": _choose_en(row.get("hero_title_secondary_en"), row.get("hero_title_secondary_ar"), "University"),
        "descriptionAr": _text(row.get("hero_description_ar")),
        "descriptionEn": _choose_en(row.get("hero_description_en"), row.get("hero_description_ar")),
        "image": _text(row.get("hero_image")),
        "backgroundType": _text(row.get("hero_background_type"), default="none"),
        "backgroundImage": _text(row.get("hero_background_image")),
        "backgroundVideo": _text(row.get("hero_background_video")),
        "backgroundOverlayOpacity": row.get("hero_background_overlay_opacity"),
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
            "labelEn": _choose_en(row.get("stats_students_label_en"), row.get("stats_students_label_ar"), "Students"),
            "icon": "GraduationCap",
        },
        {
            "key": "faculty",
            "number": str(faculty_count),
            "labelAr": _text(row.get("stats_faculty_label_ar"), default="عضو هيئة تدريس"),
            "labelEn": _choose_en(row.get("stats_faculty_label_en"), row.get("stats_faculty_label_ar"), "Faculty"),
            "icon": "Users",
        },
        {
            "key": "programs",
            "number": str(row.get("programs_count") or 0),
            "labelAr": _text(row.get("stats_programs_label_ar"), default="برنامج أكاديمي"),
            "labelEn": _choose_en(row.get("stats_programs_label_en"), row.get("stats_programs_label_ar"), "Programs"),
            "icon": "BookOpen",
        },
        {
            "key": "colleges",
            "number": str(colleges_count or 0),
            "labelAr": _text(row.get("stats_colleges_label_ar"), default="كليات متخصصة"),
            "labelEn": _choose_en(row.get("stats_colleges_label_en"), row.get("stats_colleges_label_ar"), "Colleges"),
            "icon": "Award",
        },
    ]

    about = {}

    def _section_content(prefix: str, title_ar: str, title_en: str, description_ar: str, description_en: str):
        title_value = _text(row.get(f"{prefix}_title_ar"), default=title_ar)
        description_value = _text(row.get(f"{prefix}_description_ar"), default=description_ar)
        return {
            "titleAr": title_value,
            "titleEn": _choose_en(row.get(f"{prefix}_title_en"), title_value, title_en),
            "descriptionAr": description_value,
            "descriptionEn": _choose_en(row.get(f"{prefix}_description_en"), description_value, description_en),
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
            "overlayTitleEn": _choose_en(
                row.get("video_overlay_title_en"),
                _text(row.get("video_overlay_title_ar"), default="جولة في الحرم الجامعي"),
                "Campus Virtual Tour",
            ),
            "overlayDescriptionAr": _text(
                row.get("video_overlay_description_ar"),
                default="استكشف القاعات الدراسية والمعامل المجهزة بأحدث التقنيات.",
            ),
            "overlayDescriptionEn": _choose_en(
                row.get("video_overlay_description_en"),
                _text(row.get("video_overlay_description_ar"), default="استكشف القاعات الدراسية والمعامل المجهزة بأحدث التقنيات."),
                "Explore classrooms and laboratories equipped with the latest technologies.",
            ),
            "videoFile": _text(row.get("video_file")),
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

    def _preferred_en(en_value, ar_value, fallback: str = "") -> str:
        en_text = _as_text(en_value)
        if len(en_text.strip()) >= 4:
            return en_text
        translated = _translated_text(_as_text(ar_value))
        return translated or fallback

    site_name_ar = _as_text(settings.get("site_name_ar") or settings.get("site_name") or settings.get("app_name"))
    site_name_en = _as_text(settings.get("site_name_en") or settings.get("site_name") or settings.get("app_name"))
    site_description_ar = _as_text(settings.get("site_description_ar") or settings.get("about_short"))
    address_ar = _as_text(settings.get("address_ar") or settings.get("address"))
    return {
        "siteName": _as_text(settings.get("site_name") or settings.get("app_name") or site_name_ar),
        "siteNameAr": site_name_ar,
        "siteNameEn": site_name_en,
        "siteDescriptionAr": site_description_ar,
        "siteDescriptionEn": _preferred_en(settings.get("site_description_en") or settings.get("about_short_en"), site_description_ar),
        "contactPhone": _as_text(settings.get("contact_phone") or settings.get("phone")),
        "contactEmail": _as_text(settings.get("contact_email") or settings.get("email")),
        "addressAr": address_ar,
        "addressEn": _preferred_en(settings.get("address_en"), address_ar, "Sanaa, Yemen"),
        "mapLocation": _as_text(settings.get("map_location")),
        "footerBackgroundType": _as_text(settings.get("footer_background_type"), default="none"),
        "footerBackgroundImage": _as_text(settings.get("footer_background_image")),
        "footerBackgroundVideo": _as_text(settings.get("footer_background_video")),
        "footerBackgroundOverlayOpacity": settings.get("footer_background_overlay_opacity"),
        "socialLinks": social_links,
    }


def _build_contact_page_payload() -> dict:
    settings = _get_website_settings_payload()
    contact_settings = {}
    if frappe.db.exists("DocType", "Contact Page Settings"):
        try:
            contact_settings = frappe.get_doc("Contact Page Settings", "Contact Page Settings").as_dict()
        except Exception:
            contact_settings = {}
    source = contact_settings or settings
    profile = _build_site_profile_payload()

    def _preferred_en(en_value, ar_value, fallback: str = "") -> str:
        en_text = _as_text(en_value)
        if len(en_text.strip()) >= 3:
            return en_text
        translated = _translated_text(_as_text(ar_value))
        return translated or fallback

    badge_ar = _as_text(source.get("contact_page_badge_ar"), default="تواصل معنا")
    title_ar = _as_text(source.get("contact_page_title_ar"), default="نحن هنا للإجابة على استفساراتكم")
    description_ar = _as_text(
        source.get("contact_page_description_ar"),
        default="تواصل مع جامعة الجيل الجديد للاستفسار عن القبول والبرامج الأكاديمية والخدمات الطلابية.",
    )
    form_title_ar = _as_text(source.get("contact_form_title_ar"), default="أرسل رسالة")
    social_title_ar = _as_text(source.get("social_section_title_ar"), default="تابعنا على")

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
            "titleEn": _preferred_en(source.get("contact_form_title_en"), form_title_ar, "Send a Message"),
            "nameLabelAr": _as_text(source.get("contact_form_name_label_ar"), default="الاسم"),
            "nameLabelEn": _preferred_en(source.get("contact_form_name_label_en"), source.get("contact_form_name_label_ar"), "Name"),
            "namePlaceholderAr": _as_text(source.get("contact_form_name_placeholder_ar"), default="أدخل اسمك"),
            "namePlaceholderEn": _preferred_en(source.get("contact_form_name_placeholder_en"), source.get("contact_form_name_placeholder_ar"), "Enter your name"),
            "emailLabelAr": _as_text(source.get("contact_form_email_label_ar"), default="البريد الإلكتروني"),
            "emailLabelEn": _preferred_en(source.get("contact_form_email_label_en"), source.get("contact_form_email_label_ar"), "Email"),
            "emailPlaceholderAr": _as_text(source.get("contact_form_email_placeholder_ar"), default="أدخل بريدك الإلكتروني"),
            "emailPlaceholderEn": _preferred_en(source.get("contact_form_email_placeholder_en"), source.get("contact_form_email_placeholder_ar"), "Enter your email"),
            "subjectLabelAr": _as_text(source.get("contact_form_subject_label_ar"), default="الموضوع"),
            "subjectLabelEn": _preferred_en(source.get("contact_form_subject_label_en"), source.get("contact_form_subject_label_ar"), "Subject"),
            "subjectPlaceholderAr": _as_text(source.get("contact_form_subject_placeholder_ar"), default="أدخل موضوع الرسالة"),
            "subjectPlaceholderEn": _preferred_en(source.get("contact_form_subject_placeholder_en"), source.get("contact_form_subject_placeholder_ar"), "Enter message subject"),
            "messageLabelAr": _as_text(source.get("contact_form_message_label_ar"), default="الرسالة"),
            "messageLabelEn": _preferred_en(source.get("contact_form_message_label_en"), source.get("contact_form_message_label_ar"), "Message"),
            "messagePlaceholderAr": _as_text(source.get("contact_form_message_placeholder_ar"), default="اكتب رسالتك هنا"),
            "messagePlaceholderEn": _preferred_en(source.get("contact_form_message_placeholder_en"), source.get("contact_form_message_placeholder_ar"), "Write your message here"),
            "submitTextAr": _as_text(source.get("contact_form_submit_text_ar"), default="إرسال الرسالة"),
            "submitTextEn": _preferred_en(source.get("contact_form_submit_text_en"), source.get("contact_form_submit_text_ar"), "Send Message"),
        },
        "social": {
            "titleAr": social_title_ar,
            "titleEn": _translated_text(social_title_ar, "en") or "Follow Us",
        },
        "siteProfile": {
            **profile,
            "contactPhone": _as_text(source.get("contact_phone") or settings.get("contact_phone") or settings.get("phone")),
            "contactEmail": _as_text(source.get("contact_email") or settings.get("contact_email") or settings.get("email")),
            "addressAr": _as_text(source.get("address_ar") or settings.get("address_ar") or settings.get("address")),
            "addressEn": _preferred_en(source.get("address_en"), source.get("address_ar") or settings.get("address_ar") or settings.get("address"), "Sanaa, Yemen"),
            "mapLocation": _as_text(source.get("map_location") or settings.get("map_location")),
            "phoneLabelAr": _as_text(source.get("contact_phone_label_ar"), default="الهاتف"),
            "phoneLabelEn": _preferred_en(source.get("contact_phone_label_en"), source.get("contact_phone_label_ar"), "Phone"),
            "emailLabelAr": _as_text(source.get("contact_email_label_ar"), default="البريد الإلكتروني"),
            "emailLabelEn": _preferred_en(source.get("contact_email_label_en"), source.get("contact_email_label_ar"), "Email"),
            "addressLabelAr": _as_text(source.get("contact_address_label_ar"), default="العنوان"),
            "addressLabelEn": _preferred_en(source.get("contact_address_label_en"), source.get("contact_address_label_ar"), "Address"),
        },
        "meta": {"generated_at": now_ts(), "source": "Contact Page Settings" if contact_settings else "Website Settings"},
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
        return translated or fallback

    def _choose_en(en_value, ar_value, fallback: str = "") -> str:
        en_text = _as_text(en_value)
        if en_text:
            return en_text
        translated = _translated(_as_text(ar_value), fallback)
        return translated or ""

    page_badge_ar = _as_text(row.get("page_badge_ar"), default="تعرف علينا")
    page_title_ar = _as_text(row.get("page_title_ar"), default="عن جامعة الجيل الجديد")
    page_description_ar = _as_text(row.get("page_description_ar"))
    intro_body_ar = _as_text(row.get("intro_body_ar"))

    identity = [
        {
            "key": "vision",
            "titleAr": _as_text(row.get("vision_title_ar"), default="الرؤية"),
            "titleEn": _choose_en(row.get("vision_title_en"), row.get("vision_title_ar"), "Vision"),
            "descriptionAr": _as_text(row.get("vision_description_ar")),
            "descriptionEn": _choose_en(row.get("vision_description_en"), row.get("vision_description_ar")),
        },
        {
            "key": "mission",
            "titleAr": _as_text(row.get("mission_title_ar"), default="الرسالة"),
            "titleEn": _choose_en(row.get("mission_title_en"), row.get("mission_title_ar"), "Mission"),
            "descriptionAr": _as_text(row.get("mission_description_ar")),
            "descriptionEn": _choose_en(row.get("mission_description_en"), row.get("mission_description_ar")),
        },
        {
            "key": "goals",
            "titleAr": _as_text(row.get("goals_title_ar"), default="الأهداف"),
            "titleEn": _choose_en(row.get("goals_title_en"), row.get("goals_title_ar"), "Goals"),
            "descriptionAr": _as_text(row.get("goals_description_ar")),
            "descriptionEn": _choose_en(row.get("goals_description_en"), row.get("goals_description_ar")),
        },
        {
            "key": "values",
            "titleAr": _as_text(row.get("values_title_ar"), default="القيم"),
            "titleEn": _choose_en(row.get("values_title_en"), row.get("values_title_ar"), "Values"),
            "descriptionAr": _as_text(row.get("values_description_ar")),
            "descriptionEn": _choose_en(row.get("values_description_en"), row.get("values_description_ar")),
        },
    ]

    team_groups: dict[str, list[dict]] = {}
    for member in sorted(row.get("team_members") or [], key=lambda item: int(item.get("display_order") or 0)):
        group_name_ar = _as_text(member.get("group_name_ar"), default="الفريق الإداري")
        team_groups.setdefault(group_name_ar, []).append(
            {
                "group_name_en": _as_text(member.get("group_name_en")),
                "nameAr": _as_text(member.get("full_name_ar")),
                "nameEn": _choose_en(member.get("full_name_en"), member.get("full_name_ar")),
                "roleAr": _as_text(member.get("job_title_ar")),
                "roleEn": _choose_en(member.get("job_title_en"), member.get("job_title_ar")),
                "image": _as_text(member.get("member_image")),
                "displayOrder": int(member.get("display_order") or 0),
            }
        )

    groups = [
        {
            "titleAr": group_name_ar,
            "titleEn": _choose_en((members[0] or {}).get("group_name_en") if members else "", group_name_ar),
            "members": members,
        }
        for group_name_ar, members in team_groups.items()
    ]

    return {
        "pageHeader": {
            "badgeAr": page_badge_ar,
            "badgeEn": _choose_en(row.get("page_badge_en"), page_badge_ar, "About Us"),
            "titleAr": page_title_ar,
            "titleEn": _choose_en(row.get("page_title_en"), page_title_ar, "About AJ JEEL ALJADEED UNIVERSITY"),
            "descriptionAr": page_description_ar,
            "descriptionEn": _choose_en(row.get("page_description_en"), page_description_ar),
        },
        "intro": {
            "bodyAr": intro_body_ar,
            "bodyEn": _choose_en(row.get("intro_body_en"), intro_body_ar),
            "image": _as_text(row.get("intro_image")),
        },
        "identity": identity,
        "presidentMessage": {
            "sectionTitleAr": _as_text(row.get("president_section_title_ar"), default="كلمة رئيس الجامعة"),
            "sectionTitleEn": _choose_en(row.get("president_section_title_en"), row.get("president_section_title_ar"), "President's Message"),
            "introAr": _as_text(row.get("president_message_intro_ar")),
            "introEn": _choose_en(row.get("president_message_intro_en"), row.get("president_message_intro_ar")),
            "bodyAr": _as_text(row.get("president_message_body_ar")),
            "bodyEn": _choose_en(row.get("president_message_body_en"), row.get("president_message_body_ar")),
            "closingAr": _as_text(row.get("president_message_closing_ar")),
            "closingEn": _choose_en(row.get("president_message_closing_en"), row.get("president_message_closing_ar")),
            "nameAr": _as_text(row.get("president_name_ar")),
            "nameEn": _choose_en(row.get("president_name_en"), row.get("president_name_ar")),
            "roleAr": _as_text(row.get("president_role_ar")),
            "roleEn": _choose_en(row.get("president_role_en"), row.get("president_role_ar")),
            "image": _as_text(row.get("president_image")),
        },
        "team": {
            "titleAr": _as_text(row.get("team_section_title_ar"), default="الفريق الإداري"),
            "titleEn": _choose_en(row.get("team_section_title_en"), row.get("team_section_title_ar"), "Administrative Team"),
            "descriptionAr": _as_text(row.get("team_section_description_ar")),
            "descriptionEn": _choose_en(row.get("team_section_description_en"), row.get("team_section_description_ar")),
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
        "event_title_en",
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
    desired = ["name", "title", "title_en", "content", "content_en", "image", "display_order", "is_published"]
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
        "site_name_en",
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
        "footer_background_type",
        "footer_background_image",
        "footer_background_video",
        "footer_background_overlay_opacity",
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
    elif isinstance(data_payload, dict):
        for key, value in data_payload.items():
            merged.setdefault(key, value)

    # WHY+WHAT: tolerate older frontend bundles that send wrapped payloads such as
    # {"data": {...}} or {"payload": {...}} or {"message": {...}}.
    for wrapper_key in ("data", "payload", "message"):
        wrapped = merged.get(wrapper_key)
        if isinstance(wrapped, dict):
            for key, value in wrapped.items():
                merged.setdefault(key, value)
            nested_data = wrapped.get("data")
            if isinstance(nested_data, dict):
                for key, value in nested_data.items():
                    merged.setdefault(key, value)

    return merged


def _unwrap_wrapped_payload(payload: frappe._dict) -> frappe._dict:
    """Flatten older wrapped request shapes like {'data': {...}}."""
    flattened = frappe._dict(payload or {})
    for wrapper_key in ("data", "payload", "message"):
        wrapped = flattened.get(wrapper_key)
        parsed = None
        if isinstance(wrapped, str):
            try:
                parsed = frappe.parse_json(wrapped)
            except Exception:
                parsed = None
        elif isinstance(wrapped, dict):
            parsed = wrapped

        if isinstance(parsed, dict):
            for key, value in parsed.items():
                flattened.setdefault(key, value)
            nested_data = parsed.get("data")
            if isinstance(nested_data, dict):
                for key, value in nested_data.items():
                    flattened.setdefault(key, value)
    return flattened


def _extract_upload_name(value) -> str:
    if isinstance(value, dict):
        return _as_text(value.get("name") or value.get("filename") or value.get("fileName"))
    return _as_text(value)


def _extract_join_request_uploads(payload: frappe._dict) -> dict[str, dict]:
    uploads: dict[str, dict] = {}
    documents = payload.get("documents")
    if isinstance(documents, str):
        try:
            documents = frappe.parse_json(documents)
        except Exception:
            documents = None
    if isinstance(documents, dict):
        high_school = (
            documents.get("highSchool")
            or documents.get("high_school")
            or documents.get("highSchoolDocument")
            or documents.get("highSchoolDocumentName")
        )
        id_document = (
            documents.get("id")
            or documents.get("idDocument")
            or documents.get("idDocumentName")
            or documents.get("id_document")
        )
        personal_photo = (
            documents.get("photo")
            or documents.get("personalPhoto")
            or documents.get("personalPhotoName")
            or documents.get("personal_photo")
        )
        if isinstance(high_school, dict):
            uploads["high_school_document_name"] = high_school
        if isinstance(id_document, dict):
            uploads["id_document_name"] = id_document
        if isinstance(personal_photo, dict):
            uploads["personal_photo_name"] = personal_photo

    top_level_aliases = {
        "high_school_document_name": (
            "high_school_document_name",
            "highSchoolDocumentName",
            "highSchoolDocument",
        ),
        "id_document_name": (
            "id_document_name",
            "idDocumentName",
            "idDocument",
        ),
        "personal_photo_name": (
            "personal_photo_name",
            "personalPhotoName",
            "personalPhoto",
        ),
    }
    for target_field, alias_keys in top_level_aliases.items():
        for alias_key in alias_keys:
            value = payload.get(alias_key)
            if isinstance(value, str):
                try:
                    parsed = frappe.parse_json(value)
                    if isinstance(parsed, dict):
                        value = parsed
                except Exception:
                    pass
            if isinstance(value, dict) and _as_text(value.get("content") or value.get("data") or value.get("base64")):
                uploads[target_field] = value
                break
    return uploads


def _normalize_join_request_document_fields(payload: frappe._dict, uploads: dict[str, dict]) -> frappe._dict:
    normalized = frappe._dict(payload or {})
    field_aliases = {
        "high_school_document_name": ("high_school_document_name", "highSchoolDocumentName"),
        "id_document_name": ("id_document_name", "idDocumentName"),
        "personal_photo_name": ("personal_photo_name", "personalPhotoName"),
    }
    for target_field, alias_keys in field_aliases.items():
        for alias_key in alias_keys:
            value = normalized.get(alias_key)
            if isinstance(value, str):
                try:
                    parsed = frappe.parse_json(value)
                    if isinstance(parsed, dict):
                        value = parsed
                except Exception:
                    pass
            if isinstance(value, dict):
                normalized[target_field] = _extract_upload_name(value)
            elif value not in (None, "") and normalized.get(target_field) in (None, ""):
                normalized[target_field] = _as_text(value)
        upload = (uploads or {}).get(target_field)
        if isinstance(upload, dict) and not normalized.get(target_field):
            normalized[target_field] = _extract_upload_name(upload)
    return normalized


def _decode_upload_content(raw_content: str) -> bytes:
    content = _as_text(raw_content)
    if not content:
        raise ApiError("VALIDATION_ERROR", "Uploaded file content is empty", status_code=400)

    if content.startswith("data:"):
        parts = content.split(",", 1)
        if len(parts) != 2:
            raise ApiError("VALIDATION_ERROR", "Invalid data URL payload", status_code=400)
        content = parts[1]

    try:
        return base64.b64decode(content)
    except Exception as exc:
        raise ApiError("VALIDATION_ERROR", "Invalid uploaded file encoding", status_code=400) from exc


def _attach_join_request_uploads(docname: str, uploads: dict[str, dict]) -> dict[str, str]:
    updates: dict[str, str] = {}
    for fieldname, upload in (uploads or {}).items():
        if not isinstance(upload, dict):
            continue

        filename = _as_text(upload.get("name") or upload.get("filename") or upload.get("fileName"), default=f"{fieldname}.bin")
        raw_content = _as_text(upload.get("content") or upload.get("data") or upload.get("base64"))
        if not raw_content:
            continue

        content = _decode_upload_content(raw_content)
        file_doc = save_file(
            fname=filename,
            content=content,
            dt="Join Requests",
            dn=docname,
            is_private=1,
            decode=False,
            df=fieldname,
        )
        file_url = _as_text(getattr(file_doc, "file_url", None) or (file_doc.get("file_url") if isinstance(file_doc, dict) else ""))
        if file_url:
            updates[fieldname] = file_url

    return updates


def _repair_join_request_document_row(row: dict) -> dict[str, str]:
    updates: dict[str, str] = {}
    field_aliases = {
        "high_school_document_name": "high_school_document_name",
        "id_document_name": "id_document_name",
        "personal_photo_name": "personal_photo_name",
    }
    for fieldname in field_aliases:
        raw_value = row.get(fieldname)
        text_value = _as_text(raw_value)
        if not text_value:
            continue
        if text_value.startswith("/private/files/") or text_value.startswith("/files/"):
            continue

        parsed_upload = _parse_upload_dict(raw_value)
        if isinstance(parsed_upload, dict):
            try:
                repaired = _attach_join_request_uploads(row.get("name"), {fieldname: parsed_upload}).get(fieldname)
            except Exception:
                repaired = ""
            if repaired:
                updates[fieldname] = repaired
                continue

        guessed_private = f"/private/files/{text_value}"
        guessed_public = f"/files/{text_value}"
        file_url = ""
        if frappe.db.exists("File", {"file_url": guessed_private}):
            file_url = guessed_private
        elif frappe.db.exists("File", {"file_url": guessed_public}):
            file_url = guessed_public
        elif frappe.db.exists("File", {"file_name": text_value, "attached_to_name": row.get("name")}):
            existing_url = frappe.db.get_value(
                "File",
                {"file_name": text_value, "attached_to_name": row.get("name")},
                "file_url",
            )
            file_url = _as_text(existing_url)
        else:
            private_path = frappe.get_site_path("private", "files", text_value)
            public_path = frappe.get_site_path("public", "files", text_value)
            if os.path.exists(private_path):
                file_url = guessed_private
            elif os.path.exists(public_path):
                file_url = guessed_public
        if file_url:
            updates[fieldname] = file_url

    if updates and all(
        [
            updates.get("high_school_document_name") or _as_text(row.get("high_school_document_name")).startswith("/"),
            updates.get("id_document_name") or _as_text(row.get("id_document_name")).startswith("/"),
            updates.get("personal_photo_name") or _as_text(row.get("personal_photo_name")).startswith("/"),
        ]
    ):
        updates["has_required_documents"] = 1
    return updates


def _parse_upload_dict(value):
    if isinstance(value, dict):
        return value
    text = _as_text(value)
    if not text:
        return None
    try:
        parsed = frappe.parse_json(text)
        if isinstance(parsed, dict):
            return parsed
    except Exception:
        pass
    try:
        parsed = ast.literal_eval(text)
        if isinstance(parsed, dict):
            return parsed
    except Exception:
        return None
    return None


def _as_text(value, default: str = "") -> str:
    if value is None:
        return default
    if isinstance(value, str):
        cleaned = value.strip()
        return cleaned if cleaned else default
    return str(value).strip() or default


def _contains_arabic(value: str) -> bool:
    return bool(re.search(r"[\u0600-\u06FF]", _as_text(value)))


def _preferred_ar_text(primary_value, fallback_value) -> str:
    primary = _as_text(primary_value)
    fallback = _as_text(fallback_value)
    if _contains_arabic(fallback):
        return fallback
    return primary or fallback


def _serialize_news_item(row: dict) -> dict:
    slug = _as_text(row.get("slug")) or _slugify_news_value(
        row.get("title_en") or row.get("title") or row.get("title_ar")
    )
    title_ar = _as_text(row.get("title") or row.get("title_ar"))
    title_en = _as_text(row.get("title_en") or _translated_text(title_ar) or row.get("title") or row.get("title_ar") or title_ar)
    description_ar = _as_text(row.get("summary") or row.get("description_ar"))
    description_en = _as_text(
        row.get("description_en") or _translated_text(description_ar) or row.get("summary") or row.get("description_ar") or description_ar
    )
    content_ar = _as_text(row.get("content") or row.get("content_ar"))
    content_en = _as_text(
        row.get("content_en") or _translated_text(content_ar) or row.get("content") or row.get("content_ar") or content_ar
    )
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
    title_en = _as_text(row.get("title_en"), default=_translated_text(title_ar))
    content_en = _as_text(row.get("content_en"), default=_translated_text(content_ar))
    slug = _as_text(row.get("name")) or _slugify_news_value(title_ar)
    return {
        "id": slug,
        "slug": slug,
        "titleAr": title_ar,
        "titleEn": title_en,
        "descriptionAr": content_ar,
        "descriptionEn": content_en,
        "contentAr": content_ar,
        "contentEn": content_en,
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
        "image": _as_text(row.get("image")),
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
    return _as_text(translations.get(source))


def _slugify_news_value(value: str | None) -> str:
    if not value:
        return ""
    slug = re.sub(r"[^\w\s-]", "", str(value).strip().lower())
    slug = re.sub(r"[-\s]+", "-", slug)
    return slug.strip("-")


def _serialize_event_item(row: dict) -> dict:
    slug = _as_text(row.get("slug")) or _slugify_news_value(
        row.get("event_title_en")
        or row.get("title_en")
        or row.get("title_ar")
        or row.get("event_title")
        or row.get("title")
    )
    title_ar = _as_text(row.get("title_ar") or row.get("title") or row.get("event_title"))
    title_en = _as_text(row.get("event_title_en") or row.get("title_en"))
    description_ar = _preferred_ar_text(row.get("description_ar"), row.get("description"))
    description_en = _as_text(row.get("description_en"))
    content_ar = _as_text(row.get("content_ar") or row.get("content") or description_ar)
    content_en = _as_text(row.get("content_en"))
    date = row.get("date") or row.get("event_date")
    end_date = row.get("end_date")
    location_ar = _as_text(row.get("location_ar") or row.get("location"))
    location_en = _as_text(row.get("location_en"))
    organizer_ar = _as_text(row.get("organizer_ar") or row.get("organizer"))
    organizer_en = _as_text(row.get("organizer_en"))
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
    programs_count = len(programs)
    departments_count = _count_college_departments(row, programs)
    faculty_count = _count_college_faculty(row)
    slug = row.get("slug") or _slugify_news_value(
        row.get("name_en")
        or row.get("name_ar")
        or row.get("college_name")
        or row.get("name")
    )
    name_ar = _as_text(row.get("name_ar") or row.get("college_name") or row.get("name"))
    name_en = _as_text(row.get("name_en") or _translated_text(name_ar) or row.get("college_name") or row.get("name") or name_ar)
    description_ar = _preferred_ar_text(row.get("description_ar"), row.get("description"))
    description_en = _as_text(row.get("description_en") or _translated_text(description_ar) or row.get("description") or description_ar)
    vision_ar = _as_text(row.get("vision_ar"))
    mission_ar = _as_text(row.get("mission_ar"))
    goals_ar = _as_text(row.get("goals_ar"))
    quality_ar = _as_text(row.get("quality_ar"))
    values_ar = _as_text(row.get("values_ar"))
    strategy_ar = _as_text(row.get("strategy_ar"))
    dean_name_ar = _as_text(row.get("dean_name_ar") or row.get("dean_name"))
    dean_name_en = _as_text(row.get("dean_name_en"))
    department_head_name_ar = _as_text(row.get("department_head_name"))
    department_head_name_en = _as_text(row.get("department_head_name_en"))
    college_news = _list_college_news(row)

    return {
        "id": row.get("id") or slug or row.get("name"),
        "slug": slug,
        "updatedAt": _as_text(row.get("modified")),
        "nameAr": name_ar,
        "nameEn": name_en,
        "deanName": dean_name_ar,
        "deanNameEn": dean_name_en,
        "deanImage": _as_text(row.get("dean_image")),
        "departmentHeadName": department_head_name_ar,
        "departmentHeadNameEn": department_head_name_en,
        "departmentHeadImage": _as_text(row.get("department_head_image")),
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
        "icon": _as_text(row.get("icon")),
        "image": _as_text(row.get("image")),
        "backgroundImage": _as_text(row.get("background_image") or row.get("image")),
        "programs": programs,
        "programsCount": programs_count,
        "departmentsCount": departments_count,
        "facultyCount": faculty_count,
        "news": college_news,
    }

def _list_college_news(college_row: dict) -> list[dict]:
    doctype = _first_existing_doctype(["News"])
    if not doctype:
        return []

    available = _selectable_fields(doctype)
    has_college_link = "college" in available

    college_docname = _as_text(college_row.get("name"))

    fields = [
        field
        for field in [
            "name",
            "slug",
            "title",
            "title_ar",
            "title_en",
            "summary",
            "summary_en",
            "description_ar",
            "description_en",
            "date",
            "publish_date",
            "featured_image",
            "image",
            "is_published",
            "display_order",
            "college",
        ]
        if field in available
    ]

    filters = {}
    if has_college_link and college_docname:
        filters["college"] = college_docname
    if "is_published" in available:
        filters["is_published"] = 1

    order_by = "date desc, publish_date desc, modified desc"
    if "display_order" in available:
        order_by = "display_order asc, date desc, publish_date desc, modified desc"

    rows = frappe.get_all(
        doctype,
        filters=filters,
        fields=fields,
        order_by=order_by,
        limit_page_length=6,
        ignore_permissions=True,
    )

    # Fallback: keep college section populated with latest published news
    # when no direct college mapping exists yet.
    if not rows:
        fallback_filters = {}
        if "is_published" in available:
            fallback_filters["is_published"] = 1
        rows = frappe.get_all(
            doctype,
            filters=fallback_filters,
            fields=fields,
            order_by=order_by,
            limit_page_length=3,
            ignore_permissions=True,
        )

    items = []
    for row in rows:
        title_ar = _as_text(row.get("title") or row.get("title_ar"))
        title_en = _as_text(row.get("title_en") or _translated_text(title_ar))
        desc_ar = _as_text(row.get("summary") or row.get("description_ar"))
        desc_en = _as_text(row.get("summary_en") or row.get("description_en") or _translated_text(desc_ar))
        slug = _as_text(row.get("slug")) or _slugify_news_value(title_en or title_ar or row.get("name"))
        date_value = row.get("date") or row.get("publish_date")
        image_value = _as_text(row.get("featured_image") or row.get("image"))
        items.append(
            {
                "id": row.get("name") or slug,
                "slug": slug,
                "titleAr": title_ar,
                "titleEn": title_en,
                "descAr": desc_ar,
                "descEn": desc_en,
                "date": str(date_value)[:10] if date_value else "",
                "image": image_value,
            }
        )
    return items


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
        "study_years_en",
        "duration",
        "duration_en",
        "description",
        "description_ar",
        "description_en",
        "objectives_ar",
        "objectives_en",
        "career_prospects_ar",
        "career_prospects_en",
        "application_steps_ar",
        "application_steps_en",
        "why_program_ar",
        "why_program_en",
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
        objectives_ar = _split_text_lines(program.get("objectives_ar"))
        objectives_en = _split_text_lines(program.get("objectives_en"))
        career_ar = _split_text_lines(program.get("career_prospects_ar"))
        career_en = _split_text_lines(program.get("career_prospects_en"))
        application_steps_ar = _split_text_lines(program.get("application_steps_ar"))
        application_steps_en = _split_text_lines(program.get("application_steps_en"))
        why_program_ar = _split_text_lines(program.get("why_program_ar"))
        why_program_en = _split_text_lines(program.get("why_program_en"))
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
                "studyYearsEn": str(program.get("study_years_en") or program.get("duration_en") or program.get("study_years") or program.get("duration") or ""),
                "degreeType": _as_text(program.get("degree_type")),
                "image": program.get("image"),
                "updatedAt": _as_text(program.get("modified")),
                "descriptionAr": program.get("description_ar") or program.get("description") or "",
                "descriptionEn": program.get("description_en") or _translated_text(program.get("description_ar") or "") or program.get("description") or "",
                "objectives": _merge_program_objectives(objectives_ar, objectives_en),
                "studyPlan": [],
                "careerProspectsAr": career_ar,
                "careerProspectsEn": _ensure_parallel_text_list(career_ar, career_en),
                "applicationStepsAr": application_steps_ar,
                "applicationStepsEn": _ensure_parallel_text_list(application_steps_ar, application_steps_en),
                "whyProgramAr": why_program_ar,
                "whyProgramEn": _ensure_parallel_text_list(why_program_ar, why_program_en),
                "facultyMembers": _get_program_faculty_members(program),
            }
        )
    cache[college_key] = programs
    return programs


def _split_text_lines(value) -> list[str]:
    text = _as_text(value)
    if not text:
        return []
    normalized = re.sub(r"[;,،]+", "\n", text)
    return [line.strip() for line in normalized.splitlines() if line.strip()]


def _merge_program_objectives(objectives_ar: list[str], objectives_en: list[str]) -> list[dict]:
    size = max(len(objectives_ar), len(objectives_en))
    result = []
    for index in range(size):
        text_ar = objectives_ar[index] if index < len(objectives_ar) else ""
        text_en = objectives_en[index] if index < len(objectives_en) else ""
        if not text_en and text_ar:
            text_en = _translated_text(text_ar)
        if not text_ar and text_en:
            text_ar = text_en
        if not text_ar and not text_en:
            continue
        result.append(
            {
                "id": f"objective-{index + 1}",
                "textAr": text_ar,
                "textEn": text_en,
            }
        )
    return result


def _ensure_parallel_text_list(primary: list[str], secondary: list[str]) -> list[str]:
    if secondary:
        return secondary
    return [_translated_text(item) for item in primary]


def _get_program_faculty_members(program_row: dict) -> list[dict]:
    doctype = _first_existing_doctype(["Faculty Members"])
    if not doctype:
        return []

    available = _selectable_fields(doctype)
    if "linked_program" not in available:
        return []

    fields = [
        field
        for field in [
            "name",
            "full_name",
            "full_name_en",
            "academic_title",
            "academic_title_en",
            "department",
            "biography",
            "biography_en",
            "photo",
            "is_active",
            "linked_program",
        ]
        if field in available
    ]
    if not fields:
        return []

    filters = {"linked_program": program_row.get("name")}
    if "is_active" in available:
        filters["is_active"] = 1

    rows = frappe.get_all(
        doctype,
        filters=filters,
        fields=fields,
        order_by="modified desc",
        ignore_permissions=True,
        limit_page_length=24,
    )

    items = []
    for row in rows:
        name_ar = _as_text(row.get("full_name"))
        degree_ar = _as_text(row.get("academic_title"))
        department_ar = _as_text(row.get("department"))
        items.append(
            {
                "id": _as_text(row.get("name")),
                "nameAr": name_ar,
                "nameEn": _as_text(row.get("full_name_en") or _translated_text(name_ar)),
                "titleAr": degree_ar,
                "titleEn": _as_text(row.get("academic_title_en") or _translated_text(degree_ar)),
                "specializationAr": department_ar,
                "specializationEn": _translated_text(department_ar),
                "email": "",
                "image": _as_text(row.get("photo")),
            }
        )
    return items


def _count_college_departments(college_row: dict, programs: list[dict]) -> int:
    doctype = _first_existing_doctype(["Academic Departments"])
    if doctype:
        available = _selectable_fields(doctype)
        if "college" in available:
            fields = [field for field in ["name", "college", "is_active"] if field in available]
            filters = {}
            if "is_active" in available:
                filters["is_active"] = 1

            aliases = _college_aliases(college_row)
            rows = frappe.get_all(
                doctype,
                fields=fields,
                filters=filters,
                ignore_permissions=True,
                limit_page_length=0,
            )
            matched = {row.get("name") for row in rows if _as_text(row.get("college")) in aliases and row.get("name")}
            if matched:
                return len(matched)

    department_values = {
        _as_text((program or {}).get("departmentAr"))
        for program in (programs or [])
        if _as_text((program or {}).get("departmentAr"))
    }
    if department_values:
        return len(department_values)
    return len(programs or [])


def _count_college_faculty(college_row: dict) -> int:
    faculty_doctype = _first_existing_doctype(["Faculty Members"])
    dept_doctype = _first_existing_doctype(["Academic Departments"])
    if not faculty_doctype or not dept_doctype:
        return 0

    dept_available = _selectable_fields(dept_doctype)
    faculty_available = _selectable_fields(faculty_doctype)
    if "college" not in dept_available or "department" not in faculty_available:
        return 0

    dept_filters = {}
    if "is_active" in dept_available:
        dept_filters["is_active"] = 1
    dept_fields = [field for field in ["name", "college"] if field in dept_available]

    aliases = _college_aliases(college_row)
    dept_rows = frappe.get_all(
        dept_doctype,
        fields=dept_fields,
        filters=dept_filters,
        ignore_permissions=True,
        limit_page_length=0,
    )
    department_names = [row.get("name") for row in dept_rows if _as_text(row.get("college")) in aliases and row.get("name")]
    if not department_names:
        return 0

    faculty_filters = {"department": ["in", department_names]}
    if "is_active" in faculty_available:
        faculty_filters["is_active"] = 1
    return frappe.db.count(faculty_doctype, filters=faculty_filters)


def _college_aliases(college_row: dict) -> set[str]:
    aliases = set()
    for value in [
        college_row.get("name"),
        college_row.get("id"),
        college_row.get("slug"),
        college_row.get("college_name"),
        college_row.get("name_ar"),
        college_row.get("name_en"),
    ]:
        text = _as_text(value)
        if text:
            aliases.add(text)
    return aliases


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
    title_ar = row.get("title_ar") or row.get("page_title") or ""
    content_ar = row.get("content_ar") or row.get("content") or ""
    return {
        "slug": row.get("slug"),
        "titleAr": title_ar,
        "titleEn": row.get("title_en") or _translated_text(title_ar) or title_ar,
        "contentAr": content_ar,
        "contentEn": row.get("content_en") or _translated_text(content_ar) or content_ar,
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
