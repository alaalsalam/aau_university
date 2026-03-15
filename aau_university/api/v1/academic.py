# -*- coding: utf-8 -*-
from __future__ import annotations

import frappe
from frappe.translate import get_all_translations
from frappe.utils import cint

from .resources import (
    create_entity,
    delete_entity,
    get_entity,
    list_entities,
    update_entity,
)
from .utils import ApiError, api_endpoint


@frappe.whitelist(allow_guest=True)
@api_endpoint
def list_colleges():
    """List colleges."""
    result = list_entities("colleges", search_fields=["name_ar", "name_en"], public=True)
    normalized = []
    for item in result["data"]:
        row = _normalize_public_college_row(_enrich_college_payload(item))
        if row:
            normalized.append(row)

    result["data"] = _deduplicate_public_colleges(normalized)
    result["meta"]["total"] = len(result["data"])
    result["meta"]["totalPages"] = 1
    return {"data": result["data"], "meta": result["meta"], "__meta__": True}


@frappe.whitelist(allow_guest=True)
@api_endpoint
def get_college(slug: str):
    """Get a college by slug."""
    try:
        return _normalize_public_college_row(_enrich_college_payload(get_entity("colleges", slug, by="slug", public=True)))
    except frappe.DoesNotExistError:
        for row in _iter_public_college_candidates():
            if row.get("slug") == slug:
                return row
        raise


@frappe.whitelist(allow_guest=True)
@api_endpoint
def list_college_programs(college_id: str):
    """List programs for a college."""
    doctype = "Academic Programs"
    if not frappe.db.exists("DocType", doctype):
        return {"data": [], "meta": {"page": 1, "limit": 20, "total": 0, "totalPages": 0}, "__meta__": True}

    college_docname = _resolve_college_docname(college_id)
    meta = frappe.get_meta(doctype)
    available_fields = {
        df.fieldname
        for df in meta.fields
        if df.fieldname and df.fieldtype not in {"Section Break", "Column Break", "Tab Break", "Fold", "HTML", "Button"}
    }
    desired = [
        "name",
        "program_name",
        "degree_type",
        "description",
        "duration",
        "is_active",
        "college",
    ]
    fields = [field for field in desired if field == "name" or field in available_fields]
    filters = {"college": college_docname}
    if "is_active" in available_fields:
        filters["is_active"] = 1

    rows = frappe.get_all(
        doctype,
        fields=fields,
        filters=filters,
        order_by="modified desc",
        ignore_permissions=True,
    )
    data = [_serialize_program_row(row) for row in rows]
    return {
        "data": data,
        "meta": {"page": 1, "limit": len(data) or 20, "total": len(data), "totalPages": 1 if data else 0},
        "__meta__": True,
    }


@frappe.whitelist(allow_guest=True)
@api_endpoint
def list_college_faculty(college_id: str):
    """List faculty members for a college."""
    college_docname = _resolve_college_docname(college_id)
    items = _list_faculty_payload(include_inactive=False, college_name=college_docname)
    return {
        "data": items,
        "meta": {"page": 1, "limit": len(items) or 20, "total": len(items), "totalPages": 1 if items else 0},
        "__meta__": True,
    }


@frappe.whitelist(allow_guest=True)
@api_endpoint
def list_programs():
    """List academic programs."""
    result = list_entities(
        "academic_programs",
        search_fields=["name_ar", "name_en", "description_ar", "description_en"],
        public=True,
    )
    return {"data": result["data"], "meta": result["meta"], "__meta__": True}


@frappe.whitelist(allow_guest=True)
@api_endpoint
def list_departments():
    """List academic departments."""
    if not frappe.db.exists("DocType", "Academic Departments"):
        return {"data": [], "meta": {"page": 1, "limit": 20, "total": 0, "totalPages": 0}, "__meta__": True}

    rows = frappe.get_all(
        "Academic Departments",
        fields=["name", "department_name", "college", "is_active"],
        filters={"is_active": 1},
        order_by="modified desc",
        ignore_permissions=True,
        limit_page_length=0,
    )
    data = []
    for row in rows:
        college_docname = _as_text(row.get("college"))
        data.append(
            {
                "id": row.get("name"),
                "nameAr": _as_text(row.get("department_name")),
                "nameEn": _translated_text(_as_text(row.get("department_name"))),
                "college": college_docname,
                "collegeLabel": _resolve_college_label(college_docname),
            }
        )
    return {
        "data": data,
        "meta": {"page": 1, "limit": len(data) or 20, "total": len(data), "totalPages": 1 if data else 0},
        "__meta__": True,
    }


@frappe.whitelist(allow_guest=True)
@api_endpoint
def get_program(program_id: str):
    """Get a program by id."""
    return get_entity("academic_programs", program_id, by="id", public=True)


@frappe.whitelist()
@api_endpoint
def create_college(**payload):
    """Create a college."""
    return create_entity("colleges", payload), 201


@frappe.whitelist()
@api_endpoint
def update_college(college_id: str, **payload):
    """Update a college."""
    return update_entity("colleges", college_id, payload, by="id")


@frappe.whitelist()
@api_endpoint
def delete_college(college_id: str):
    """Delete a college."""
    return delete_entity("colleges", college_id, by="id")


@frappe.whitelist()
@api_endpoint
def create_program(**payload):
    """Create a program."""
    return create_entity("academic_programs", payload), 201


@frappe.whitelist()
@api_endpoint
def update_program(program_id: str, **payload):
    """Update a program."""
    return update_entity("academic_programs", program_id, payload, by="id")


@frappe.whitelist()
@api_endpoint
def delete_program(program_id: str):
    """Delete a program."""
    return delete_entity("academic_programs", program_id, by="id")


@frappe.whitelist(allow_guest=True)
@api_endpoint
def list_program_objectives(program_id: str):
    """List objectives for a program."""
    frappe.form_dict["program_id"] = program_id
    result = list_entities("program_objectives", public=True)
    return {"data": result["data"], "meta": result["meta"], "__meta__": True}


@frappe.whitelist()
@api_endpoint
def create_program_objective(**payload):
    """Create a program objective."""
    return create_entity("program_objectives", payload), 201


@frappe.whitelist()
@api_endpoint
def update_program_objective(objective_id: str, **payload):
    """Update a program objective."""
    return update_entity("program_objectives", objective_id, payload, by="id")


@frappe.whitelist()
@api_endpoint
def delete_program_objective(objective_id: str):
    """Delete a program objective."""
    return delete_entity("program_objectives", objective_id, by="id")


@frappe.whitelist(allow_guest=True)
@api_endpoint
def list_faculty():
    """List faculty members."""
    return {"data": _list_faculty_payload(), "meta": _faculty_meta(), "__meta__": True}


@frappe.whitelist(allow_guest=True)
@api_endpoint
def get_faculty(member_id: str):
    """Get a faculty member by id."""
    return _get_faculty_payload(member_id)


@frappe.whitelist(allow_guest=True)
@api_endpoint
def search_faculty(q: str):
    """Search faculty members."""
    frappe.form_dict["q"] = q
    return {"data": _list_faculty_payload(), "meta": _faculty_meta(), "__meta__": True}


@frappe.whitelist(allow_guest=True)
@api_endpoint
def filter_faculty(**filters):
    """Filter faculty members."""
    frappe.form_dict.update(filters)
    return {"data": _list_faculty_payload(), "meta": _faculty_meta(), "__meta__": True}


@frappe.whitelist(allow_guest=True)
@api_endpoint
def list_faculty_colleges():
    """List distinct faculty colleges."""
    values = []
    for item in _list_faculty_payload(include_inactive=True):
        label_ar = item.get("collegeAr") or item.get("departmentAr")
        if not label_ar:
            continue
        values.append(
            {
                "labelAr": label_ar,
                "labelEn": item.get("collegeEn") or item.get("departmentEn") or label_ar,
            }
        )
    return _unique_label_rows(values)


@frappe.whitelist(allow_guest=True)
@api_endpoint
def list_faculty_degrees():
    """List distinct faculty degrees."""
    values = []
    for item in _list_faculty_payload(include_inactive=True):
        label_ar = item.get("degreeAr")
        if not label_ar:
            continue
        values.append({"labelAr": label_ar, "labelEn": item.get("degreeEn") or label_ar})
    return _unique_label_rows(values)


@frappe.whitelist(allow_guest=True)
@api_endpoint
def list_faculty_specializations():
    """List distinct faculty specializations."""
    values = []
    for item in _list_faculty_payload(include_inactive=True):
        label_ar = item.get("specializationAr")
        if not label_ar:
            continue
        values.append({"labelAr": label_ar, "labelEn": item.get("specializationEn") or label_ar})
    return _unique_label_rows(values)


@frappe.whitelist()
@api_endpoint
def create_faculty(**payload):
    """Create a faculty member."""
    doc = frappe.get_doc(_normalize_faculty_payload(payload))
    doc.insert(ignore_permissions=True)
    return _serialize_faculty_row(doc), 201


@frappe.whitelist()
@api_endpoint
def update_faculty(member_id: str, **payload):
    """Update a faculty member."""
    if not frappe.db.exists("Faculty Members", member_id):
        raise frappe.DoesNotExistError
    doc = frappe.get_doc("Faculty Members", member_id)
    doc.update(_normalize_faculty_payload(payload, is_update=True))
    doc.save(ignore_permissions=True)
    return _serialize_faculty_row(doc)


@frappe.whitelist()
@api_endpoint
def delete_faculty(member_id: str):
    """Delete a faculty member."""
    return delete_entity("faculty_members", member_id, by="name")


@frappe.whitelist(allow_guest=True)
@api_endpoint
def list_program_faculty(program_id: str):
    """List faculty for a program."""
    frappe.form_dict["program_id"] = program_id
    result = list_entities("program_faculty", public=True)
    return {"data": result["data"], "meta": result["meta"], "__meta__": True}


@frappe.whitelist()
@api_endpoint
def create_program_faculty(**payload):
    """Create a program faculty entry."""
    return create_entity("program_faculty", payload), 201


@frappe.whitelist()
@api_endpoint
def update_program_faculty(program_faculty_id: str, **payload):
    """Update a program faculty entry."""
    return update_entity("program_faculty", program_faculty_id, payload, by="id")


@frappe.whitelist()
@api_endpoint
def delete_program_faculty(program_faculty_id: str):
    """Delete a program faculty entry."""
    return delete_entity("program_faculty", program_faculty_id, by="id")


@frappe.whitelist(allow_guest=True)
@api_endpoint
def get_college_dean(college_id: str):
    """Get dean for a college."""
    frappe.form_dict["college_id"] = college_id
    result = list_entities("college_deans", public=True)
    return result["data"][0] if result["data"] else None


def _enrich_college_payload(payload: dict) -> dict:
    if not payload:
        return payload

    row = dict(payload)
    docname = row.get("docname")
    if not docname:
        college_id = row.get("id")
        slug = row.get("slug")
        if college_id and frappe.db.exists("Colleges", college_id):
            docname = college_id
        elif college_id:
            resolved = frappe.db.get_value("Colleges", {"id": college_id}, "name")
            docname = resolved or docname
        if not docname and slug:
            resolved = frappe.db.get_value("Colleges", {"slug": slug}, "name")
            docname = resolved or docname

    if not docname:
        return row

    extra = frappe.db.get_value(
        "Colleges",
        docname,
        ["college_name", "dean_name"],
        as_dict=True,
    ) or {}

    college_name = extra.get("college_name")
    dean_name = extra.get("dean_name")
    if college_name and not row.get("collegeName"):
        row["collegeName"] = college_name
    if dean_name and not row.get("deanName"):
        row["deanName"] = dean_name
    return row


def _public_college_slug(source: str | None) -> str:
    if not source:
        return ""
    return frappe.scrub(source).replace("_", "-").strip("-")


def _normalize_public_college_row(payload: dict | None) -> dict | None:
    if not payload:
        return None

    row = dict(payload)
    name_ar = (row.get("nameAr") or "").strip()
    name_en = (row.get("nameEn") or "").strip()
    college_name = (row.get("collegeName") or "").strip()
    display_name = name_ar or name_en or college_name
    is_active = cint(row.get("isActive"))

    if not is_active or not display_name:
        return None

    slug = (row.get("slug") or "").strip() or _public_college_slug(display_name)
    if not slug:
        return None

    row["slug"] = slug
    row["id"] = row.get("id") or row.get("docname") or slug
    if not row.get("collegeName"):
        row["collegeName"] = college_name or name_ar or name_en
    if not row.get("nameAr"):
        row["nameAr"] = name_ar or college_name or name_en
    if not row.get("nameEn"):
        row["nameEn"] = name_en or college_name or name_ar
    row["isActive"] = 1
    row["displayOrder"] = cint(row.get("displayOrder"))
    return row


def _college_rank(row: dict) -> tuple[int, int, int]:
    return (
        cint(not bool(row.get("slug"))),
        cint(not bool(row.get("nameAr") and row.get("nameEn"))),
        cint(row.get("displayOrder") or 9999),
    )


def _deduplicate_public_colleges(rows: list[dict]) -> list[dict]:
    by_slug: dict[str, dict] = {}
    for row in rows:
        slug = row.get("slug")
        if not slug:
            continue
        current = by_slug.get(slug)
        if not current or _college_rank(row) < _college_rank(current):
            by_slug[slug] = row

    return sorted(by_slug.values(), key=lambda row: (cint(row.get("displayOrder") or 9999), row.get("slug") or ""))


def _iter_public_college_candidates() -> list[dict]:
    result = list_entities("colleges", search_fields=["name_ar", "name_en"], public=True)
    normalized = []
    for item in result["data"]:
        row = _normalize_public_college_row(_enrich_college_payload(item))
        if row:
            normalized.append(row)
    return _deduplicate_public_colleges(normalized)


def _resolve_college_docname(college_id: str) -> str:
    if frappe.db.exists("Colleges", college_id):
        return college_id

    for filters in ({"slug": college_id}, {"id": college_id}, {"name_ar": college_id}, {"name_en": college_id}, {"college_name": college_id}):
        resolved = frappe.db.get_value("Colleges", filters, "name")
        if resolved:
            return resolved

    raise frappe.DoesNotExistError(f"College {college_id} not found")


def _serialize_program_row(row: dict) -> dict:
    description = row.get("description") or ""
    return {
        "id": row.get("name"),
        "programName": row.get("program_name") or "",
        "nameAr": row.get("program_name") or "",
        "nameEn": row.get("program_name") or "",
        "degreeType": row.get("degree_type"),
        "description": description,
        "descriptionAr": description,
        "descriptionEn": description,
        "duration": row.get("duration") or "",
        "studyYears": row.get("duration") or "",
        "isActive": cint(row.get("is_active")),
        "college": row.get("college"),
    }


def _list_faculty_payload(include_inactive: bool = False, college_name: str | None = None) -> list[dict]:
    filters: dict[str, object] = {}
    meta = frappe.get_meta("Faculty Members")
    if not include_inactive and meta.get_field("is_active"):
        filters["is_active"] = 1

    q = _faculty_request_value("q")
    degree = _faculty_request_value("degree")
    department = (
        _faculty_request_value("department")
        or _faculty_request_value("college")
        or _faculty_request_value("specialization")
    )

    rows = frappe.get_all(
        "Faculty Members",
        filters=filters,
        fields=["name", "full_name", "academic_title", "department", "linked_college", "biography", "photo", "is_active"],
        order_by="modified desc",
        ignore_permissions=True,
        limit_page_length=0,
    )

    items = [_serialize_faculty_row(row) for row in rows]

    if degree:
        normalized = degree.casefold()
        items = [
            item
            for item in items
            if (item.get("degreeAr") or "").casefold() == normalized
            or (item.get("degreeEn") or "").casefold() == normalized
        ]

    if department:
        normalized = department.casefold()
        items = [
            item
            for item in items
            if (item.get("departmentAr") or "").casefold() == normalized
            or (item.get("departmentEn") or "").casefold() == normalized
            or (item.get("collegeAr") or "").casefold() == normalized
            or (item.get("collegeEn") or "").casefold() == normalized
            or (item.get("specializationAr") or "").casefold() == normalized
            or (item.get("specializationEn") or "").casefold() == normalized
        ]

    if college_name:
        items = [item for item in items if _faculty_matches_college(item, college_name)]

    if q:
        needle = q.casefold()
        items = [
            item
            for item in items
            if needle in (item.get("nameAr") or "").casefold()
            or needle in (item.get("nameEn") or "").casefold()
            or needle in (item.get("degreeAr") or "").casefold()
            or needle in (item.get("degreeEn") or "").casefold()
            or needle in (item.get("departmentAr") or "").casefold()
            or needle in (item.get("departmentEn") or "").casefold()
            or needle in (item.get("bioAr") or "").casefold()
            or needle in (item.get("bioEn") or "").casefold()
        ]

    page = max(int(frappe.form_dict.get("page") or 1), 1)
    limit = max(int(frappe.form_dict.get("limit") or frappe.form_dict.get("page_size") or 20), 1)
    offset = (page - 1) * limit
    paged = items[offset : offset + limit]
    frappe.flags.aau_faculty_meta = {
        "page": page,
        "limit": limit,
        "total": len(items),
        "totalPages": (len(items) + limit - 1) // limit if limit else 1,
    }
    return paged


def _faculty_meta() -> dict:
    return getattr(frappe.flags, "aau_faculty_meta", {"page": 1, "limit": 20, "total": 0, "totalPages": 0})


def _get_faculty_payload(member_id: str) -> dict:
    if not frappe.db.exists("Faculty Members", member_id):
        raise frappe.DoesNotExistError
    row = frappe.get_doc("Faculty Members", member_id)
    if getattr(row, "is_active", 1) in (0, "0", False):
        raise frappe.DoesNotExistError
    return _serialize_faculty_row(row)


def _serialize_faculty_row(row) -> dict:
    full_name = _as_text(_doc_value(row, "full_name"))
    academic_title = _as_text(_doc_value(row, "academic_title"))
    biography = _as_text(_doc_value(row, "biography"))
    department_link = _as_text(_doc_value(row, "department"))
    linked_college = _as_text(_doc_value(row, "linked_college"))
    department_name, department_college_name = _resolve_department_names(department_link)
    college_name = linked_college or department_college_name
    college_label = _resolve_college_label(college_name)
    department_ar = department_name or department_link
    department_en = _translated_text(department_ar)
    college_ar = college_label or department_ar
    college_en = _translated_text(college_ar)

    return {
        "id": _doc_value(row, "name"),
        "nameAr": full_name,
        "nameEn": _translated_text(full_name),
        "degreeAr": academic_title,
        "degreeEn": _translated_text(academic_title),
        "specializationAr": department_ar,
        "specializationEn": department_en,
        "collegeAr": college_ar,
        "collegeEn": college_en,
        "linkedCollege": college_name,
        "departmentAr": department_ar,
        "departmentEn": department_en,
        "email": _as_text(_doc_value(row, "email")),
        "phone": _as_text(_doc_value(row, "phone")),
        "bioAr": biography,
        "bioEn": _translated_text(biography),
        "image": _as_text(_doc_value(row, "photo") or _doc_value(row, "image")),
        "officeHoursAr": _as_text(_doc_value(row, "office_hours")),
        "officeHoursEn": _translated_text(_as_text(_doc_value(row, "office_hours"))),
        "researchInterestsAr": [],
        "researchInterestsEn": [],
        "publications": [],
        "courses": [],
        "education": [],
        "experience": [],
    }


def _normalize_faculty_payload(payload: dict, is_update: bool = False) -> dict:
    name_ar = _payload_value(payload, "nameAr", "name_ar", "full_name")
    degree_ar = _payload_value(payload, "degreeAr", "degree_ar", "academic_title")
    department = _payload_value(payload, "departmentAr", "department_ar", "department", "specializationAr", "specialization_ar", "collegeAr", "college_ar")
    linked_college = _payload_value(payload, "linkedCollege", "linked_college")
    biography = _payload_value(payload, "bioAr", "bio_ar", "biography")
    photo = _payload_value(payload, "image", "photo")
    is_active = payload.get("is_active")
    if is_active is None:
        is_active = payload.get("isActive")

    normalized = {}
    if not is_update:
        normalized["doctype"] = "Faculty Members"
    if name_ar:
        normalized["full_name"] = name_ar
    if degree_ar:
        normalized["academic_title"] = degree_ar
    if department:
        normalized["department"] = department
    if linked_college:
        normalized["linked_college"] = _resolve_college_docname(linked_college)
    if biography:
        normalized["biography"] = biography
    if photo:
        normalized["photo"] = photo
    if is_active is not None:
        normalized["is_active"] = 1 if str(is_active).lower() in {"1", "true", "yes"} else 0

    if not is_update and not normalized.get("full_name"):
        raise ApiError("VALIDATION_ERROR", "Faculty full name is required", status_code=400)
    return normalized


def _resolve_department_names(department_name: str) -> tuple[str, str]:
    if not department_name or not frappe.db.exists("DocType", "Academic Departments"):
        return "", ""
    if not frappe.db.exists("Academic Departments", department_name):
        return department_name, ""
    row = frappe.db.get_value(
        "Academic Departments",
        department_name,
        ["department_name", "college"],
        as_dict=True,
    ) or {}
    return _as_text(row.get("department_name"), default=department_name), _as_text(row.get("college"))


def _resolve_college_label(college_name: str) -> str:
    if not college_name or not frappe.db.exists("DocType", "Colleges"):
        return ""

    try:
        college_docname = _resolve_college_docname(college_name)
    except frappe.DoesNotExistError:
        return college_name

    row = frappe.db.get_value(
        "Colleges",
        college_docname,
        ["name_ar", "college_name", "name_en"],
        as_dict=True,
    ) or {}
    return _as_text(row.get("name_ar") or row.get("college_name") or row.get("name_en"), default=college_name)


def _resolve_college_identity(college_name: str) -> tuple[str, str]:
    if not college_name:
        return "", ""
    try:
        college_docname = _resolve_college_docname(college_name)
    except frappe.DoesNotExistError:
        return "", _public_college_slug(college_name)
    row = frappe.db.get_value(
        "Colleges",
        college_docname,
        ["name_ar", "college_name", "name_en", "slug"],
        as_dict=True,
    ) or {}
    label = _as_text(row.get("name_ar") or row.get("college_name") or row.get("name_en"), default=college_docname)
    slug = _as_text(row.get("slug")) or _public_college_slug(label)
    return label, slug


def _faculty_matches_college(item: dict, college_name: str) -> bool:
    linked_college = _as_text(item.get("linkedCollege"))
    if not linked_college:
        return False

    if linked_college == college_name:
        return True

    target_label, target_slug = _resolve_college_identity(college_name)
    linked_label, linked_slug = _resolve_college_identity(linked_college)
    return bool(target_slug and linked_slug and target_slug == linked_slug) or bool(target_label and linked_label and target_label == linked_label)


def _translated_text(value: str, lang: str = "en") -> str:
    source = _as_text(value)
    if not source:
        return ""
    translations = get_all_translations(lang) or {}
    return _as_text(translations.get(source), default=source)


def _doc_value(row, fieldname: str):
    if isinstance(row, dict):
        return row.get(fieldname)
    return row.get(fieldname)


def _as_text(value, default: str = "") -> str:
    if value is None:
        return default
    if isinstance(value, str):
        value = value.strip()
        return value or default
    return str(value).strip() or default


def _payload_value(payload: dict, *keys: str) -> str:
    for key in keys:
        value = payload.get(key)
        if value is not None and str(value).strip():
            return str(value).strip()
    return ""


def _faculty_request_value(*keys: str) -> str:
    for key in keys:
        value = frappe.form_dict.get(key)
        if value is not None and str(value).strip():
            return str(value).strip()
    return ""


def _unique_label_rows(values: list[dict]) -> list[dict]:
    seen = set()
    rows = []
    for value in values:
        key = (value.get("labelAr") or "", value.get("labelEn") or "")
        if key in seen:
            continue
        seen.add(key)
        rows.append(value)
    return rows


@frappe.whitelist()
@api_endpoint
def update_college_dean(dean_id: str, **payload):
    """Update a college dean."""
    return update_entity("college_deans", dean_id, payload, by="id")
