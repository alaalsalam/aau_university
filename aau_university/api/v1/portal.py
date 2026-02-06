# -*- coding: utf-8 -*-
from __future__ import annotations

import frappe

from .utils import ApiError, api_endpoint, require_auth


def _require_doctype(doctype: str):
    if not frappe.db.exists("DocType", doctype):
        raise ApiError("NOT_IMPLEMENTED", f"{doctype} doctype not configured", status_code=501)


def _get_user_email() -> str:
    require_auth()
    user = frappe.get_doc("User", frappe.session.user)
    return user.email


@frappe.whitelist()
@api_endpoint
def get_doctor_profile():
    """Get doctor profile (mapped to Faculty Members by email)."""
    _require_doctype("Faculty Members")
    email = _get_user_email()
    row = frappe.get_all(
        "Faculty Members",
        filters={"email": email},
        fields=["name", "id"],
        limit=1,
        ignore_permissions=True,
    )
    if not row:
        raise ApiError("NOT_FOUND", "Doctor profile not found", status_code=404)
    doc = frappe.get_doc("Faculty Members", row[0]["name"])
    return {
        "id": doc.id,
        "nameAr": doc.name_ar,
        "nameEn": doc.name_en,
        "degreeAr": doc.degree_ar,
        "degreeEn": doc.degree_en,
        "specializationAr": doc.specialization_ar,
        "specializationEn": doc.specialization_en,
        "collegeAr": doc.college_ar,
        "collegeEn": doc.college_en,
        "departmentAr": doc.department_ar,
        "departmentEn": doc.department_en,
        "email": doc.email,
        "phone": doc.phone,
        "officeHoursAr": getattr(doc, "office_hours_ar", None),
        "officeHoursEn": getattr(doc, "office_hours_en", None),
        "bioAr": doc.bio_ar,
        "bioEn": doc.bio_en,
        "image": doc.image,
    }


@frappe.whitelist()
@api_endpoint
def update_doctor_profile(**payload):
    """Update doctor profile (mapped to Faculty Members by email)."""
    _require_doctype("Faculty Members")
    email = _get_user_email()
    row = frappe.get_all(
        "Faculty Members",
        filters={"email": email},
        fields=["name"],
        limit=1,
        ignore_permissions=True,
    )
    if not row:
        raise ApiError("NOT_FOUND", "Doctor profile not found", status_code=404)
    doc = frappe.get_doc("Faculty Members", row[0]["name"])
    for key in [
        "name_ar",
        "name_en",
        "degree_ar",
        "degree_en",
        "specialization_ar",
        "specialization_en",
        "college_ar",
        "college_en",
        "department_ar",
        "department_en",
        "phone",
        "bio_ar",
        "bio_en",
        "image",
    ]:
        if key in payload:
            doc.set(key, payload[key])
    doc.save(ignore_permissions=True)
    return get_doctor_profile()


@frappe.whitelist()
@api_endpoint
def list_doctor_courses():
    """List courses for doctor (not configured)."""
    _require_doctype("Course")
    return []


@frappe.whitelist()
@api_endpoint
def list_doctor_students(courseId: str | None = None):
    """List doctor students (not configured)."""
    _require_doctype("Student")
    return []


@frappe.whitelist()
@api_endpoint
def update_doctor_student_grades(student_id: str, **payload):
    """Update doctor student grades (not configured)."""
    _require_doctype("Student")
    return {"updated": True}


@frappe.whitelist()
@api_endpoint
def list_doctor_schedule():
    """List doctor schedule (not configured)."""
    _require_doctype("Course Schedule")
    return []


@frappe.whitelist()
@api_endpoint
def get_doctor_finance():
    """Get doctor finance (not configured)."""
    raise ApiError("NOT_IMPLEMENTED", "Finance data not configured", status_code=501)


@frappe.whitelist()
@api_endpoint
def list_doctor_notifications():
    """List doctor notifications (not configured)."""
    raise ApiError("NOT_IMPLEMENTED", "Notifications not configured", status_code=501)


@frappe.whitelist()
@api_endpoint
def mark_doctor_notification_read(notification_id: str):
    """Mark doctor notification as read."""
    raise ApiError("NOT_IMPLEMENTED", "Notifications not configured", status_code=501)


@frappe.whitelist()
@api_endpoint
def list_doctor_messages():
    """List doctor messages (not configured)."""
    raise ApiError("NOT_IMPLEMENTED", "Messages not configured", status_code=501)


@frappe.whitelist()
@api_endpoint
def mark_doctor_message_read(message_id: str):
    """Mark doctor message as read."""
    raise ApiError("NOT_IMPLEMENTED", "Messages not configured", status_code=501)


@frappe.whitelist()
@api_endpoint
def list_doctor_materials(courseId: str | None = None):
    """List doctor materials (not configured)."""
    raise ApiError("NOT_IMPLEMENTED", "Materials not configured", status_code=501)


@frappe.whitelist()
@api_endpoint
def upload_doctor_material(**payload):
    """Upload doctor material (not configured)."""
    raise ApiError("NOT_IMPLEMENTED", "Materials not configured", status_code=501)


@frappe.whitelist()
@api_endpoint
def delete_doctor_material(material_id: str):
    """Delete doctor material (not configured)."""
    raise ApiError("NOT_IMPLEMENTED", "Materials not configured", status_code=501)


@frappe.whitelist()
@api_endpoint
def get_student_profile():
    """Get student profile (uses Student doctype if available)."""
    _require_doctype("Student")
    email = _get_user_email()
    row = frappe.get_all(
        "Student",
        filters={"student_email_id": email},
        fields=["name"],
        limit=1,
        ignore_permissions=True,
    )
    if not row:
        raise ApiError("NOT_FOUND", "Student profile not found", status_code=404)
    doc = frappe.get_doc("Student", row[0]["name"])
    return {
        "id": doc.name,
        "academicNumber": doc.student_email_id,
        "nameAr": doc.student_name,
        "nameEn": doc.student_name,
        "emailPersonal": doc.personal_email or doc.student_email_id,
        "emailUniversity": doc.student_email_id,
        "phone": doc.student_mobile_number,
        "collegeAr": doc.college,
        "collegeEn": doc.college,
        "departmentAr": doc.department,
        "departmentEn": doc.department,
        "specializationAr": doc.program,
        "specializationEn": doc.program,
        "levelAr": doc.student_group,
        "levelEn": doc.student_group,
        "status": "active" if doc.enabled else "inactive",
        "gpa": None,
        "totalCredits": None,
        "completedCredits": None,
        "admissionDate": doc.admission_date,
        "expectedGraduation": None,
        "advisorAr": None,
        "advisorEn": None,
        "image": doc.image,
    }


@frappe.whitelist()
@api_endpoint
def update_student_profile(**payload):
    """Update student profile."""
    _require_doctype("Student")
    email = _get_user_email()
    row = frappe.get_all(
        "Student",
        filters={"student_email_id": email},
        fields=["name"],
        limit=1,
        ignore_permissions=True,
    )
    if not row:
        raise ApiError("NOT_FOUND", "Student profile not found", status_code=404)
    doc = frappe.get_doc("Student", row[0]["name"])
    for key in ["student_name", "student_mobile_number", "personal_email", "image"]:
        if key in payload:
            doc.set(key, payload[key])
    doc.save(ignore_permissions=True)
    return get_student_profile()


@frappe.whitelist()
@api_endpoint
def list_student_courses():
    """List student courses (not configured)."""
    _require_doctype("Student")
    return []


@frappe.whitelist()
@api_endpoint
def list_student_schedule():
    """List student schedule (not configured)."""
    _require_doctype("Student")
    return []


@frappe.whitelist()
@api_endpoint
def list_student_grades(semester: str | None = None):
    """List student grades (not configured)."""
    _require_doctype("Student")
    return []


@frappe.whitelist()
@api_endpoint
def get_student_finance():
    """Get student finance (not configured)."""
    raise ApiError("NOT_IMPLEMENTED", "Finance data not configured", status_code=501)


@frappe.whitelist()
@api_endpoint
def list_student_materials(courseId: str | None = None):
    """List student materials (not configured)."""
    raise ApiError("NOT_IMPLEMENTED", "Materials not configured", status_code=501)


@frappe.whitelist()
@api_endpoint
def list_student_notifications():
    """List student notifications (not configured)."""
    raise ApiError("NOT_IMPLEMENTED", "Notifications not configured", status_code=501)


@frappe.whitelist()
@api_endpoint
def mark_student_notification_read(notification_id: str):
    """Mark student notification as read."""
    raise ApiError("NOT_IMPLEMENTED", "Notifications not configured", status_code=501)


@frappe.whitelist()
@api_endpoint
def list_conversations():
    """List conversations (not configured)."""
    raise ApiError("NOT_IMPLEMENTED", "Messages not configured", status_code=501)


@frappe.whitelist()
@api_endpoint
def get_conversation(conversation_id: str):
    """Get conversation messages (not configured)."""
    raise ApiError("NOT_IMPLEMENTED", "Messages not configured", status_code=501)


@frappe.whitelist()
@api_endpoint
def send_message(**payload):
    """Send a message (not configured)."""
    raise ApiError("NOT_IMPLEMENTED", "Messages not configured", status_code=501)


@frappe.whitelist()
@api_endpoint
def mark_conversation_read(conversation_id: str):
    """Mark conversation as read (not configured)."""
    raise ApiError("NOT_IMPLEMENTED", "Messages not configured", status_code=501)


@frappe.whitelist()
@api_endpoint
def unread_message_count():
    """Get unread message count (not configured)."""
    raise ApiError("NOT_IMPLEMENTED", "Messages not configured", status_code=501)
