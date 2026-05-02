# -*- coding: utf-8 -*-
from __future__ import annotations

import frappe
import re
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
        "id",
        "program_name",
        "name_ar",
        "name_en",
        "degree_type",
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
        "department_ar",
        "department_en",
        "admission_rate",
        "high_school_type",
        "high_school_type_en",
        "study_years",
        "image",
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
        ["college_name", "dean_name_ar", "dean_name"],
        as_dict=True,
    ) or {}

    college_name = extra.get("college_name")
    dean_name = extra.get("dean_name_ar") or extra.get("dean_name")
    if college_name and not row.get("collegeName"):
        row["collegeName"] = college_name
    if dean_name and not row.get("deanName"):
        row["deanName"] = dean_name
    return row


def _public_college_slug(source: str | None) -> str:
    if not source:
        return ""
    return frappe.scrub(source).replace("_", "-").strip("-")


def _canonical_public_college_slug(payload: dict) -> str:
    row = payload or {}
    slug = _as_text(row.get("slug"))
    name_ar = _as_text(row.get("nameAr") or row.get("collegeName"))
    name_en = _as_text(row.get("nameEn"))
    icon = _as_text(row.get("icon")).lower()
    haystack = f"{name_ar} {name_en}".lower()

    if slug in {"medicine", "health-sciences", "engineering-it", "business-humanities"}:
        return slug

    if icon == "stethoscope" or "الطب البشري" in haystack or "human medicine" in haystack:
        return "medicine"
    if icon == "heart" or "العلوم الطبية" in haystack or "health sciences" in haystack or "medical and health sciences" in haystack:
        return "health-sciences"
    if icon == "settings" or "الهندسة" in haystack or "engineering" in haystack or "technology" in haystack or "تكنولوجيا المعلومات" in haystack:
        return "engineering-it"
    if icon == "briefcase" or "العلوم الإدارية" in haystack or "administrative" in haystack or "humanitarian" in haystack:
        return "business-humanities"

    return slug or _public_college_slug(name_ar or name_en)


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

    slug = _canonical_public_college_slug(row) or _public_college_slug(display_name)
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

    meta = frappe.get_meta("Colleges")
    available_fields = {
        df.fieldname
        for df in meta.fields
        if df.fieldname and df.fieldtype not in {"Section Break", "Column Break", "Tab Break", "Fold", "HTML", "Button"}
    }

    for fieldname in ("slug", "id", "name_ar", "name_en", "college_name"):
        if fieldname not in available_fields:
            continue
        filters = {fieldname: college_id}
        resolved = frappe.db.get_value("Colleges", filters, "name")
        if resolved:
            return resolved

    raise frappe.DoesNotExistError(f"College {college_id} not found")


def _serialize_program_row(row: dict) -> dict:
    name_ar = row.get("name_ar") or row.get("program_name") or ""
    name_en = row.get("name_en") or ""
    description = row.get("description") or ""
    description_ar = row.get("description_ar") or description
    description_en = row.get("description_en") or ""
    objectives_ar = _split_text_lines(row.get("objectives_ar"))
    objectives_en = _split_text_lines(row.get("objectives_en"))
    career_ar = _split_text_lines(row.get("career_prospects_ar"))
    career_en = _split_text_lines(row.get("career_prospects_en"))
    application_steps_ar = _split_text_lines(row.get("application_steps_ar"))
    application_steps_en = _split_text_lines(row.get("application_steps_en"))
    why_program_ar = _split_text_lines(row.get("why_program_ar"))
    why_program_en = _split_text_lines(row.get("why_program_en"))
    return {
        "id": row.get("id") or row.get("name"),
        "programName": row.get("program_name") or "",
        "nameAr": name_ar,
        "nameEn": name_en,
        "degreeType": row.get("degree_type"),
        "description": description,
        "descriptionAr": description_ar,
        "descriptionEn": description_en,
        "departmentAr": row.get("department_ar") or "",
        "departmentEn": row.get("department_en") or "",
        "admissionRate": cint(row.get("admission_rate") or 0),
        "highSchoolType": row.get("high_school_type") or "علمي",
        "highSchoolTypeEn": row.get("high_school_type_en") or "",
        "image": row.get("image") or "",
        "duration": row.get("duration") or row.get("study_years") or "",
        "studyYears": row.get("study_years") or row.get("duration") or "",
        "studyYearsEn": row.get("study_years_en") or row.get("duration_en") or row.get("study_years") or row.get("duration") or "",
        "isActive": cint(row.get("is_active")),
        "college": row.get("college"),
        "updatedAt": _as_text(row.get("modified")),
        "objectives": _merge_program_objectives(objectives_ar, objectives_en),
        "careerProspectsAr": career_ar,
        "careerProspectsEn": career_en or [_translated_text(item) for item in career_ar],
        "applicationStepsAr": application_steps_ar,
        "applicationStepsEn": application_steps_en or [_translated_text(item) for item in application_steps_ar],
        "whyProgramAr": why_program_ar,
        "whyProgramEn": why_program_en or [_translated_text(item) for item in why_program_ar],
        "facultyMembers": _list_program_faculty_members(_as_text(row.get("name"))),
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
        fields=[
            "name",
            "full_name",
            "full_name_en",
            "academic_title",
            "academic_title_en",
            "department",
            "linked_college",
            "linked_program",
            "biography",
            "biography_en",
            "photo",
            "is_active",
        ],
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
    full_name_en = _as_text(_doc_value(row, "full_name_en"))
    academic_title = _as_text(_doc_value(row, "academic_title"))
    academic_title_en = _as_text(_doc_value(row, "academic_title_en"))
    biography = _as_text(_doc_value(row, "biography"))
    biography_en = _as_text(_doc_value(row, "biography_en"))
    department_link = _as_text(_doc_value(row, "department"))
    linked_college = _as_text(_doc_value(row, "linked_college"))
    linked_program = _as_text(_doc_value(row, "linked_program"))
    department_name, department_college_name = _resolve_department_names(department_link)
    college_name = linked_college or department_college_name
    college_label = _resolve_college_label(college_name)
    department_ar = department_name or department_link
    department_en = _translated_text(department_ar)
    college_ar = college_label or department_ar
    college_en = _translated_text(college_ar)

    research_interests_ar = [
        item.strip()
        for item in _as_text(_doc_value(row, "research_interests_ar")).replace("\r", "").split("\n")
        if item.strip()
    ]
    research_interests_en = [
        item.strip()
        for item in _as_text(_doc_value(row, "research_interests_en")).replace("\r", "").split("\n")
        if item.strip()
    ]
    publications = []
    for item in (_doc_value(row, "publications") or []):
        publications.append(
            {
                "id": _as_text(getattr(item, "name", "") or item.get("name")),
                "titleAr": _as_text(getattr(item, "title_ar", "") or item.get("title_ar")),
                "titleEn": _as_text(getattr(item, "title_en", "") or item.get("title_en")) or _translated_text(_as_text(getattr(item, "title_ar", "") or item.get("title_ar"))),
                "journal": _as_text(getattr(item, "journal", "") or item.get("journal")),
                "year": _as_text(getattr(item, "year", "") or item.get("year")),
                "link": _as_text(getattr(item, "link", "") or item.get("link")),
            }
        )
    courses = []
    for item in (_doc_value(row, "courses") or []):
        courses.append(
            {
                "id": _as_text(getattr(item, "name", "") or item.get("name")),
                "code": _as_text(getattr(item, "code", "") or item.get("code")),
                "nameAr": _as_text(getattr(item, "name_ar", "") or item.get("name_ar")),
                "nameEn": _as_text(getattr(item, "name_en", "") or item.get("name_en")) or _translated_text(_as_text(getattr(item, "name_ar", "") or item.get("name_ar"))),
                "semester": _as_text(getattr(item, "semester", "") or item.get("semester")),
            }
        )
    education = []
    for item in (_doc_value(row, "education") or []):
        education.append(
            {
                "id": _as_text(getattr(item, "name", "") or item.get("name")),
                "degreeAr": _as_text(getattr(item, "degree_ar", "") or item.get("degree_ar")),
                "degreeEn": _as_text(getattr(item, "degree_en", "") or item.get("degree_en")) or _translated_text(_as_text(getattr(item, "degree_ar", "") or item.get("degree_ar"))),
                "institutionAr": _as_text(getattr(item, "institution_ar", "") or item.get("institution_ar")),
                "institutionEn": _as_text(getattr(item, "institution_en", "") or item.get("institution_en")) or _translated_text(_as_text(getattr(item, "institution_ar", "") or item.get("institution_ar"))),
                "year": _as_text(getattr(item, "year", "") or item.get("year")),
            }
        )
    experience = []
    for item in (_doc_value(row, "experience") or []):
        experience.append(
            {
                "id": _as_text(getattr(item, "name", "") or item.get("name")),
                "positionAr": _as_text(getattr(item, "position_ar", "") or item.get("position_ar")),
                "positionEn": _as_text(getattr(item, "position_en", "") or item.get("position_en")) or _translated_text(_as_text(getattr(item, "position_ar", "") or item.get("position_ar"))),
                "organizationAr": _as_text(getattr(item, "organization_ar", "") or item.get("organization_ar")),
                "organizationEn": _as_text(getattr(item, "organization_en", "") or item.get("organization_en")) or _translated_text(_as_text(getattr(item, "organization_ar", "") or item.get("organization_ar"))),
                "periodAr": _as_text(getattr(item, "period_ar", "") or item.get("period_ar")),
                "periodEn": _as_text(getattr(item, "period_en", "") or item.get("period_en")) or _translated_text(_as_text(getattr(item, "period_ar", "") or item.get("period_ar"))),
            }
        )

    return {
        "id": _doc_value(row, "name"),
        "nameAr": full_name,
        "nameEn": full_name_en or _translated_text(full_name),
        "degreeAr": academic_title,
        "degreeEn": academic_title_en or _translated_text(academic_title),
        "specializationAr": department_ar,
        "specializationEn": department_en,
        "collegeAr": college_ar,
        "collegeEn": college_en,
        "linkedCollege": college_name,
        "linkedProgram": linked_program,
        "departmentAr": department_ar,
        "departmentEn": department_en,
        "email": _as_text(_doc_value(row, "email")),
        "phone": _as_text(_doc_value(row, "phone")),
        "bioAr": biography,
        "bioEn": biography_en or _translated_text(biography),
        "image": _as_text(_doc_value(row, "photo") or _doc_value(row, "image")),
        "officeHoursAr": _as_text(_doc_value(row, "office_hours")),
        "officeHoursEn": _as_text(_doc_value(row, "office_hours_en")) or _translated_text(_as_text(_doc_value(row, "office_hours"))),
        "researchInterestsAr": research_interests_ar,
        "researchInterestsEn": research_interests_en or [_translated_text(item) for item in research_interests_ar if _translated_text(item)],
        "publications": publications,
        "courses": courses,
        "education": education,
        "experience": experience,
    }


def _normalize_faculty_payload(payload: dict, is_update: bool = False) -> dict:
    name_ar = _payload_value(payload, "nameAr", "name_ar", "full_name")
    name_en = _payload_value(payload, "nameEn", "name_en", "full_name_en")
    degree_ar = _payload_value(payload, "degreeAr", "degree_ar", "academic_title")
    degree_en = _payload_value(payload, "degreeEn", "degree_en", "academic_title_en")
    department = _payload_value(payload, "departmentAr", "department_ar", "department", "specializationAr", "specialization_ar", "collegeAr", "college_ar")
    linked_college = _payload_value(payload, "linkedCollege", "linked_college")
    linked_program = _payload_value(payload, "linkedProgram", "linked_program")
    biography = _payload_value(payload, "bioAr", "bio_ar", "biography")
    biography_en = _payload_value(payload, "bioEn", "bio_en", "biography_en")
    email = _payload_value(payload, "email")
    phone = _payload_value(payload, "phone")
    office_hours = _payload_value(payload, "officeHoursAr", "office_hours")
    office_hours_en = _payload_value(payload, "officeHoursEn", "office_hours_en")
    research_interests_ar = payload.get("researchInterestsAr") or payload.get("research_interests_ar")
    research_interests_en = payload.get("researchInterestsEn") or payload.get("research_interests_en")
    publications = payload.get("publications")
    courses = payload.get("courses")
    education = payload.get("education")
    experience = payload.get("experience")
    photo = _payload_value(payload, "image", "photo")
    is_active = payload.get("is_active")
    if is_active is None:
        is_active = payload.get("isActive")

    normalized = {}
    if not is_update:
        normalized["doctype"] = "Faculty Members"
    if _payload_has_any_key(payload, "nameAr", "name_ar", "full_name"):
        normalized["full_name"] = name_ar
    if _payload_has_any_key(payload, "nameEn", "name_en", "full_name_en"):
        normalized["full_name_en"] = name_en
    if _payload_has_any_key(payload, "degreeAr", "degree_ar", "academic_title"):
        normalized["academic_title"] = degree_ar
    if _payload_has_any_key(payload, "degreeEn", "degree_en", "academic_title_en"):
        normalized["academic_title_en"] = degree_en
    if _payload_has_any_key(payload, "departmentAr", "department_ar", "department", "specializationAr", "specialization_ar", "collegeAr", "college_ar"):
        normalized["department"] = department
    if _payload_has_any_key(payload, "linkedCollege", "linked_college"):
        normalized["linked_college"] = _resolve_college_docname(linked_college)
    if _payload_has_any_key(payload, "linkedProgram", "linked_program"):
        normalized["linked_program"] = linked_program
    if _payload_has_any_key(payload, "bioAr", "bio_ar", "biography"):
        normalized["biography"] = biography
    if _payload_has_any_key(payload, "bioEn", "bio_en", "biography_en"):
        normalized["biography_en"] = biography_en
    if _payload_has_any_key(payload, "email"):
        normalized["email"] = email
    if _payload_has_any_key(payload, "phone"):
        normalized["phone"] = phone
    if _payload_has_any_key(payload, "officeHoursAr", "office_hours"):
        normalized["office_hours"] = office_hours
    if _payload_has_any_key(payload, "officeHoursEn", "office_hours_en"):
        normalized["office_hours_en"] = office_hours_en
    if research_interests_ar is not None:
        normalized["research_interests_ar"] = "\n".join(
            [str(item).strip() for item in (research_interests_ar if isinstance(research_interests_ar, list) else str(research_interests_ar).split("\n")) if str(item).strip()]
        )
    if research_interests_en is not None:
        normalized["research_interests_en"] = "\n".join(
            [str(item).strip() for item in (research_interests_en if isinstance(research_interests_en, list) else str(research_interests_en).split("\n")) if str(item).strip()]
        )
    if isinstance(publications, list):
        normalized["publications"] = [
            {
                "doctype": "Faculty Publication",
                "title_ar": _payload_value(item, "titleAr", "title_ar"),
                "title_en": _payload_value(item, "titleEn", "title_en"),
                "journal": _payload_value(item, "journal"),
                "year": _payload_value(item, "year"),
                "link": _payload_value(item, "link"),
            }
            for item in publications
        ]
    if isinstance(courses, list):
        normalized["courses"] = [
            {
                "doctype": "Faculty Course",
                "code": _payload_value(item, "code"),
                "name_ar": _payload_value(item, "nameAr", "name_ar"),
                "name_en": _payload_value(item, "nameEn", "name_en"),
                "semester": _payload_value(item, "semester"),
            }
            for item in courses
        ]
    if isinstance(education, list):
        normalized["education"] = [
            {
                "doctype": "Faculty Education",
                "degree_ar": _payload_value(item, "degreeAr", "degree_ar"),
                "degree_en": _payload_value(item, "degreeEn", "degree_en"),
                "institution_ar": _payload_value(item, "institutionAr", "institution_ar"),
                "institution_en": _payload_value(item, "institutionEn", "institution_en"),
                "year": _payload_value(item, "year"),
            }
            for item in education
        ]
    if isinstance(experience, list):
        normalized["experience"] = [
            {
                "doctype": "Faculty Experience",
                "position_ar": _payload_value(item, "positionAr", "position_ar"),
                "position_en": _payload_value(item, "positionEn", "position_en"),
                "organization_ar": _payload_value(item, "organizationAr", "organization_ar"),
                "organization_en": _payload_value(item, "organizationEn", "organization_en"),
                "period_ar": _payload_value(item, "periodAr", "period_ar"),
                "period_en": _payload_value(item, "periodEn", "period_en"),
            }
            for item in experience
        ]
    if _payload_has_any_key(payload, "image", "photo"):
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
        result.append({"id": f"objective-{index + 1}", "textAr": text_ar, "textEn": text_en})
    return result


def _list_program_faculty_members(program_docname: str) -> list[dict]:
    if not program_docname:
        return []
    if not frappe.db.exists("DocType", "Faculty Members"):
        return []

    meta = frappe.get_meta("Faculty Members")
    if not meta.get_field("linked_program"):
        return []

    filters = {"linked_program": program_docname}
    if meta.get_field("is_active"):
        filters["is_active"] = 1

    rows = frappe.get_all(
        "Faculty Members",
        filters=filters,
        fields=[
            "name",
            "full_name",
            "full_name_en",
            "academic_title",
            "academic_title_en",
            "department",
            "photo",
        ],
        order_by="modified desc",
        ignore_permissions=True,
        limit_page_length=24,
    )

    items = []
    for row in rows:
        name_ar = _as_text(row.get("full_name"))
        name_en = _as_text(row.get("full_name_en") or _translated_text(name_ar))
        title_ar = _as_text(row.get("academic_title"))
        title_en = _as_text(row.get("academic_title_en") or _translated_text(title_ar))
        spec_ar = _as_text(row.get("department"))
        items.append(
            {
                "id": _as_text(row.get("name")),
                "nameAr": name_ar,
                "nameEn": name_en,
                "titleAr": title_ar,
                "titleEn": title_en,
                "specializationAr": spec_ar,
                "specializationEn": _translated_text(spec_ar),
                "image": _as_text(row.get("photo")),
            }
        )
    return items


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


def _payload_has_any_key(payload: dict, *keys: str) -> bool:
    return any(key in payload for key in keys)


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
