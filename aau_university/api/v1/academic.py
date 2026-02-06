# -*- coding: utf-8 -*-
from __future__ import annotations

import frappe

from .resources import (
    create_entity,
    delete_entity,
    get_entity,
    list_entities,
    update_entity,
)
from .utils import api_endpoint


@frappe.whitelist(allow_guest=True)
@api_endpoint
def list_colleges():
    """List colleges."""
    result = list_entities("colleges", search_fields=["name_ar", "name_en"], public=True)
    return {"data": result["data"], "meta": result["meta"], "__meta__": True}


@frappe.whitelist(allow_guest=True)
@api_endpoint
def get_college(slug: str):
    """Get a college by slug."""
    return get_entity("colleges", slug, by="slug", public=True)


@frappe.whitelist(allow_guest=True)
@api_endpoint
def list_college_programs(college_id: str):
    """List programs for a college."""
    frappe.form_dict["college_id"] = college_id
    result = list_entities("academic_programs", public=True)
    return {"data": result["data"], "meta": result["meta"], "__meta__": True}


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
    result = list_entities(
        "faculty_members",
        search_fields=["name_ar", "name_en", "specialization_ar", "specialization_en"],
        public=True,
    )
    return {"data": result["data"], "meta": result["meta"], "__meta__": True}


@frappe.whitelist(allow_guest=True)
@api_endpoint
def get_faculty(member_id: str):
    """Get a faculty member by id."""
    return get_entity("faculty_members", member_id, by="id", public=True)


@frappe.whitelist(allow_guest=True)
@api_endpoint
def search_faculty(q: str):
    """Search faculty members."""
    frappe.form_dict["q"] = q
    result = list_entities(
        "faculty_members",
        search_fields=["name_ar", "name_en", "specialization_ar", "specialization_en"],
        public=True,
    )
    return {"data": result["data"], "meta": result["meta"], "__meta__": True}


@frappe.whitelist(allow_guest=True)
@api_endpoint
def filter_faculty(**filters):
    """Filter faculty members."""
    frappe.form_dict.update(filters)
    result = list_entities("faculty_members", public=True)
    return {"data": result["data"], "meta": result["meta"], "__meta__": True}


@frappe.whitelist(allow_guest=True)
@api_endpoint
def list_faculty_colleges():
    """List distinct faculty colleges."""
    rows = frappe.get_all(
        "Faculty Members",
        fields=["college_ar", "college_en"],
        distinct=True,
        ignore_permissions=True,
    )
    return rows


@frappe.whitelist(allow_guest=True)
@api_endpoint
def list_faculty_degrees():
    """List distinct faculty degrees."""
    rows = frappe.get_all(
        "Faculty Members",
        fields=["degree_ar", "degree_en"],
        distinct=True,
        ignore_permissions=True,
    )
    return rows


@frappe.whitelist(allow_guest=True)
@api_endpoint
def list_faculty_specializations():
    """List distinct faculty specializations."""
    rows = frappe.get_all(
        "Faculty Members",
        fields=["specialization_ar", "specialization_en"],
        distinct=True,
        ignore_permissions=True,
    )
    return rows


@frappe.whitelist()
@api_endpoint
def create_faculty(**payload):
    """Create a faculty member."""
    return create_entity("faculty_members", payload), 201


@frappe.whitelist()
@api_endpoint
def update_faculty(member_id: str, **payload):
    """Update a faculty member."""
    return update_entity("faculty_members", member_id, payload, by="id")


@frappe.whitelist()
@api_endpoint
def delete_faculty(member_id: str):
    """Delete a faculty member."""
    return delete_entity("faculty_members", member_id, by="id")


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


@frappe.whitelist()
@api_endpoint
def update_college_dean(dean_id: str, **payload):
    """Update a college dean."""
    return update_entity("college_deans", dean_id, payload, by="id")
