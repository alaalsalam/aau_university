# -*- coding: utf-8 -*-
from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime
from decimal import Decimal
from typing import Any

import frappe
from frappe.utils.file_manager import save_file

from .utils import ApiError, api_endpoint, require_auth


DAY_AR = {
    "Monday": "الاثنين",
    "Tuesday": "الثلاثاء",
    "Wednesday": "الأربعاء",
    "Thursday": "الخميس",
    "Friday": "الجمعة",
    "Saturday": "السبت",
    "Sunday": "الأحد",
}

GRADE_POINTS = {
    "A+": 4.0,
    "A": 4.0,
    "A-": 3.7,
    "B+": 3.3,
    "B": 3.0,
    "B-": 2.7,
    "C+": 2.3,
    "C": 2.0,
    "C-": 1.7,
    "D+": 1.3,
    "D": 1.0,
    "F": 0.0,
    "O": 0.0,
}

ELEVATED_PORTAL_ROLES = {"System Manager", "Administrator", "Education Manager", "AAU Admin", "AUU Admin"}
DOCTOR_PORTAL_ROLES = {"Instructor"} | ELEVATED_PORTAL_ROLES
ANNOUNCEMENT_SUBJECT_PREFIX = "[AAU-ANNOUNCEMENT]"


def _require_doctype(doctype: str):
    if not frappe.db.exists("DocType", doctype):
        raise ApiError("NOT_IMPLEMENTED", f"{doctype} doctype not configured", status_code=501)


def _normalize(value: Any) -> str:
    return str(value or "").strip().lower()


def _clean(value: Any) -> str:
    return str(value or "").strip()


def _to_float(value: Any) -> float:
    if value in (None, ""):
        return 0.0
    try:
        if isinstance(value, Decimal):
            return float(value)
        return float(value)
    except Exception:
        return 0.0


def _to_int(value: Any) -> int:
    return int(round(_to_float(value)))


def _iso(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    text = _clean(value)
    if not text:
        return None
    return text


def _time_hhmm(value: Any) -> str:
    text = _clean(value)
    if not text:
        return ""
    return text[:5]


def _range_label(from_time: Any, to_time: Any) -> str:
    start = _time_hhmm(from_time)
    end = _time_hhmm(to_time)
    if start and end:
        return f"{start} - {end}"
    return start or end or ""


def _day_labels(schedule_date: Any) -> tuple[str, str]:
    if not schedule_date:
        return "", ""
    if isinstance(schedule_date, str):
        try:
            day_obj = datetime.strptime(schedule_date[:10], "%Y-%m-%d").date()
        except Exception:
            return "", ""
    else:
        day_obj = schedule_date
    day_en = day_obj.strftime("%A")
    return DAY_AR.get(day_en, day_en), day_en


def _file_size_label(size_bytes: Any) -> str:
    size = _to_float(size_bytes)
    if size <= 0:
        return "0 B"
    units = ["B", "KB", "MB", "GB"]
    idx = 0
    while size >= 1024 and idx < len(units) - 1:
        size /= 1024
        idx += 1
    if idx == 0:
        return f"{int(size)} {units[idx]}"
    return f"{size:.1f} {units[idx]}"


def _split_csv(value: Any) -> list[str]:
    text = _clean(value)
    if not text:
        return []
    return [segment.strip() for segment in text.split(",") if segment.strip()]


def _user_identity() -> dict[str, Any]:
    require_auth()
    user = frappe.session.user
    user_doc = frappe.get_doc("User", user)
    email = _clean(getattr(user_doc, "email", None) or user)
    roles = set(frappe.get_roles(user))
    identifiers = {
        _normalize(user),
        _normalize(email),
        _normalize(getattr(user_doc, "full_name", None)),
        _normalize((email.split("@", 1)[0] if "@" in email else email)),
    }
    identifiers.discard("")
    return {
        "user": user,
        "email": email,
        "full_name": _clean(getattr(user_doc, "full_name", None) or user),
        "roles": roles,
        "identifiers": identifiers,
    }


def _require_doctor_access() -> dict[str, Any]:
    identity = _user_identity()
    if not identity["roles"].intersection(DOCTOR_PORTAL_ROLES):
        raise ApiError("FORBIDDEN", "Doctor access required", status_code=403)
    return identity


def _instructor_user_link_field() -> str | None:
    if not frappe.db.exists("DocType", "Instructor"):
        return None
    meta = frappe.get_meta("Instructor")
    valid_columns = set(meta.get_valid_columns())
    for fieldname in ("custom_user_id", "user_id", "user", "custom_user"):
        if fieldname in valid_columns:
            return fieldname
    return None


def _employee_user_map(employee_ids: set[str]) -> dict[str, str]:
    cleaned = {_clean(emp) for emp in employee_ids if _clean(emp)}
    if not cleaned or not frappe.db.exists("DocType", "Employee"):
        return {}
    rows = frappe.get_all(
        "Employee",
        filters={"name": ["in", list(cleaned)]},
        fields=["name", "user_id"],
        ignore_permissions=True,
        limit_page_length=0,
    )
    mapped = {}
    for row in rows:
        employee_name = _clean(row.get("name"))
        user_id = _clean(row.get("user_id"))
        if employee_name and user_id:
            mapped[employee_name] = user_id
    return mapped


def _student_fields() -> list[str]:
    meta = frappe.get_meta("Student")
    wanted = [
        "name",
        "user",
        "student_email_id",
        "student_name",
        "student_mobile_number",
        "personal_email",
        "program",
        "enabled",
        "custom_status",
        "admission_date",
        "student_group",
        "student_batch_name",
        "image",
        "photo",
    ]
    valid = set(meta.get_valid_columns())
    return [field for field in wanted if field in valid]


def _find_student_by_current_user(required: bool = True) -> dict | None:
    _require_doctype("Student")
    identity = _user_identity()
    fields = _student_fields()
    where = []
    params: list[Any] = []

    if "user" in fields:
        where.append("lower(ifnull(user, '')) = %s")
        params.append(_normalize(identity["user"]))

    if "student_email_id" in fields:
        where.append("lower(ifnull(student_email_id, '')) = %s")
        params.append(_normalize(identity["email"]))
        where.append("lower(ifnull(student_email_id, '')) = %s")
        params.append(_normalize(identity["user"]))

    if "name" in fields:
        where.append("lower(name) = %s")
        params.append(_normalize(identity["user"]))

    if not where:
        if required:
            raise ApiError("NOT_IMPLEMENTED", "Student lookup fields are missing", status_code=501)
        return None

    sql = f"""
        select {', '.join(fields)}
        from `tabStudent`
        where {' or '.join(where)}
        order by modified desc
        limit 1
    """
    rows = frappe.db.sql(sql, tuple(params), as_dict=True)
    if rows:
        return rows[0]

    if required:
        raise ApiError("NOT_FOUND", "Student profile not found", status_code=404)
    return None


def _student_identifiers(student_row: dict | None) -> set[str]:
    if not student_row:
        return set()
    values = {
        _normalize(student_row.get("name")),
        _normalize(student_row.get("user")),
        _normalize(student_row.get("student_email_id")),
        _normalize(student_row.get("student_name")),
    }
    values.discard("")
    return values


def _find_student_by_identifier(identifier: str) -> dict | None:
    if not identifier:
        return None
    fields = _student_fields()
    needle = _normalize(identifier)
    where = ["lower(name) = %s"]
    params: list[Any] = [needle]
    if "user" in fields:
        where.append("lower(ifnull(user, '')) = %s")
        params.append(needle)
    if "student_email_id" in fields:
        where.append("lower(ifnull(student_email_id, '')) = %s")
        params.append(needle)

    sql = f"""
        select {', '.join(fields)}
        from `tabStudent`
        where {' or '.join(where)}
        order by modified desc
        limit 1
    """
    rows = frappe.db.sql(sql, tuple(params), as_dict=True)
    return rows[0] if rows else None


def _course_name_map(courses: set[str]) -> dict[str, str]:
    if not courses:
        return {}
    _require_doctype("Course")
    rows = frappe.get_all(
        "Course",
        filters={"name": ["in", list(courses)]},
        fields=["name", "course_name"],
        ignore_permissions=True,
        limit_page_length=0,
    )
    mapped = {row["name"]: _clean(row.get("course_name") or row["name"]) for row in rows}
    for course in courses:
        mapped.setdefault(course, course)
    return mapped


def _resolve_doctor_context() -> dict[str, Any]:
    identity = _user_identity()
    all_scope = bool(identity["roles"].intersection(ELEVATED_PORTAL_ROLES))
    instructors: list[dict] = []
    link_field = _instructor_user_link_field()
    if frappe.db.exists("DocType", "Instructor"):
        fields = ["name", "instructor_name", "employee", "department", "image"]
        if link_field and link_field not in fields:
            fields.append(link_field)
        instructors = frappe.get_all(
            "Instructor",
            fields=fields,
            ignore_permissions=True,
            limit_page_length=0,
        )

    employee_to_user = _employee_user_map({_clean(row.get("employee")) for row in instructors if row.get("employee")})
    explicit_matches = []
    name_fallback_matches = []
    for row in instructors:
        keys = set()
        if link_field:
            keys.add(_normalize(row.get(link_field)))
        employee_name = _clean(row.get("employee"))
        if employee_name and employee_name in employee_to_user:
            keys.add(_normalize(employee_to_user[employee_name]))
        keys.discard("")
        if keys.intersection(identity["identifiers"]):
            explicit_matches.append(row)

        names = {
            _normalize(row.get("name")),
            _normalize(row.get("instructor_name")),
        }
        names.discard("")
        if names.intersection(identity["identifiers"]):
            name_fallback_matches.append(row)

    matches = explicit_matches
    matched_by = "explicit"
    if not matches and "Instructor" in identity["roles"] and len(name_fallback_matches) == 1:
        matches = name_fallback_matches
        matched_by = "name_fallback"

    return {
        "identity": identity,
        "all_scope": all_scope,
        "matched_instructors": matches,
        "instructors": instructors,
        "matched_by": matched_by if matches else "",
        "instructor_user_link_field": link_field,
        "employee_to_user": employee_to_user,
    }


def _ensure_doctor_context(require_mapping: bool = True) -> dict[str, Any]:
    _require_doctor_access()
    ctx = _resolve_doctor_context()
    if not require_mapping or ctx["all_scope"] or ctx["matched_instructors"]:
        return ctx
    raise ApiError(
        "FORBIDDEN",
        "Doctor account is not linked to an Instructor profile",
        status_code=403,
        details={
            "hint": "Set Instructor.custom_user_id or Instructor.employee -> Employee.user_id for this account"
        },
    )


def _doctor_schedule_rows(course_id: str | None = None) -> list[dict]:
    _require_doctype("Course Schedule")
    ctx = _ensure_doctor_context(require_mapping=True)
    rows = frappe.get_all(
        "Course Schedule",
        fields=[
            "name",
            "course",
            "student_group",
            "schedule_date",
            "from_time",
            "to_time",
            "room",
            "instructor",
            "instructor_name",
            "title",
        ],
        order_by="schedule_date desc, from_time asc",
        ignore_permissions=True,
        limit_page_length=0,
    )

    if not ctx["all_scope"]:
        matched = ctx["matched_instructors"]
        if not matched:
            return []
        allowed_names = {
            _normalize(item.get("name")) for item in matched
        } | {
            _normalize(item.get("instructor_name")) for item in matched
        }
        filtered = []
        for row in rows:
            instructor_keys = {
                _normalize(row.get("instructor")),
                _normalize(row.get("instructor_name")),
            }
            if instructor_keys.intersection(allowed_names):
                filtered.append(row)
        rows = filtered

    if course_id:
        course_key = _normalize(course_id)
        rows = [row for row in rows if _normalize(row.get("course")) == course_key]

    return rows


def _student_group_members(groups: set[str]) -> list[dict]:
    if not groups:
        return []
    _require_doctype("Student Group Student")
    rows = frappe.get_all(
        "Student Group Student",
        filters={"parent": ["in", list(groups)]},
        fields=["parent", "student", "student_name", "active"],
        ignore_permissions=True,
        limit_page_length=0,
    )
    return [row for row in rows if int(row.get("active") or 0) == 1]


def _assessment_for_student_course(student_ids: set[str], course: str) -> tuple[dict | None, list[dict]]:
    if not student_ids or not frappe.db.exists("DocType", "Assessment Result"):
        return None, []

    rows = frappe.get_all(
        "Assessment Result",
        filters={"student": ["in", list(student_ids)], "course": course},
        fields=[
            "name",
            "student",
            "course",
            "academic_term",
            "academic_year",
            "total_score",
            "maximum_score",
            "grade",
            "modified",
        ],
        order_by="modified desc",
        ignore_permissions=True,
        limit_page_length=1,
    )
    if not rows:
        return None, []

    result = rows[0]
    details: list[dict] = []
    if frappe.db.exists("DocType", "Assessment Result Detail"):
        details = frappe.get_all(
            "Assessment Result Detail",
            filters={"parent": result["name"]},
            fields=["idx", "assessment_criteria", "score", "maximum_score", "grade"],
            order_by="idx asc",
            ignore_permissions=True,
            limit_page_length=0,
        )
    return result, details


def _attendance_percent(student_ids: set[str], schedule_names: set[str]) -> int:
    if not student_ids or not schedule_names or not frappe.db.exists("DocType", "Student Attendance"):
        return 0
    rows = frappe.get_all(
        "Student Attendance",
        filters={"student": ["in", list(student_ids)], "course_schedule": ["in", list(schedule_names)]},
        fields=["status"],
        ignore_permissions=True,
        limit_page_length=0,
    )
    total = len(rows)
    if total == 0:
        return 0
    present = sum(1 for row in rows if _normalize(row.get("status")) == "present")
    return int(round((present / total) * 100))


def _course_material_type(file_name: str) -> str:
    ext = _clean(file_name).split(".")[-1].lower() if "." in _clean(file_name) else ""
    if ext in {"mp4", "mov", "avi", "mkv", "webm"}:
        return "video"
    if ext in {"doc", "docx", "ppt", "pptx", "pdf"}:
        return "lecture"
    if ext in {"xls", "xlsx", "csv"}:
        return "assignment"
    if ext in {"zip", "rar"}:
        return "resource"
    return "resource"


def _serialize_material(file_row: dict, course_id: str | None = None) -> dict:
    file_name = _clean(file_row.get("file_name"))
    return {
        "id": file_row.get("name"),
        "courseId": course_id or _clean(file_row.get("attached_to_name")),
        "titleAr": file_name,
        "titleEn": file_name,
        "descriptionAr": "",
        "descriptionEn": "",
        "type": _course_material_type(file_name),
        "fileName": file_name,
        "fileSize": _file_size_label(file_row.get("file_size")),
        "uploadDate": _iso(file_row.get("creation")),
        "downloadCount": 0,
        "fileUrl": file_row.get("file_url"),
    }


def _announcement_subject(course_id: str) -> str:
    return f"{ANNOUNCEMENT_SUBJECT_PREFIX} {course_id}"


def _is_doctor_announcement_row(row: dict | None) -> bool:
    if not row:
        return False
    return _clean(row.get("reference_doctype")) == "Course" and _clean(row.get("subject")).startswith(
        ANNOUNCEMENT_SUBJECT_PREFIX
    )


def _serialize_doctor_announcement(row: dict) -> dict:
    body = _clean(row.get("content"))
    if not body:
        body = _clean(row.get("subject")).replace(ANNOUNCEMENT_SUBJECT_PREFIX, "", 1).strip()
    return {
        "id": _clean(row.get("name")),
        "courseId": _clean(row.get("reference_name")),
        "textAr": body,
        "textEn": body,
        "createdAt": _iso(row.get("communication_date") or row.get("creation")),
        "createdBy": _clean(row.get("sender")),
    }


def _student_user_targets_for_course(course_id: str) -> set[str]:
    course = _clean(course_id)
    if not course:
        return set()
    if not (
        frappe.db.exists("DocType", "Course Schedule")
        and frappe.db.exists("DocType", "Student Group Student")
        and frappe.db.exists("DocType", "Student")
    ):
        return set()

    schedule_rows = frappe.get_all(
        "Course Schedule",
        filters={"course": course},
        fields=["student_group"],
        ignore_permissions=True,
        limit_page_length=0,
    )
    groups = {_clean(row.get("student_group")) for row in schedule_rows if row.get("student_group")}
    if not groups:
        return set()

    member_rows = frappe.get_all(
        "Student Group Student",
        filters={"parent": ["in", list(groups)]},
        fields=["student", "active"],
        ignore_permissions=True,
        limit_page_length=0,
    )
    student_ids = {
        _clean(row.get("student"))
        for row in member_rows
        if row.get("student") and (row.get("active") in (None, "", 1, "1", True))
    }
    if not student_ids:
        return set()

    student_rows = frappe.get_all(
        "Student",
        filters={"name": ["in", list(student_ids)]},
        fields=["name", "user", "student_email_id"],
        ignore_permissions=True,
        limit_page_length=0,
    )
    targets = set()
    for row in student_rows:
        for candidate in (_clean(row.get("user")), _clean(row.get("student_email_id"))):
            if candidate and frappe.db.exists("User", candidate):
                targets.add(candidate)
    return targets


def _create_student_announcement_notifications(course_id: str, text: str, sender: str, communication_name: str) -> int:
    if not frappe.db.exists("DocType", "Notification Log"):
        return 0

    targets = _student_user_targets_for_course(course_id)
    if not targets:
        return 0

    created = 0
    subject = f"Announcement: {course_id}"
    for user in sorted(targets):
        exists = frappe.db.exists(
            "Notification Log",
            {
                "for_user": user,
                "document_type": "Communication",
                "document_name": communication_name,
            },
        )
        if exists:
            continue
        doc = frappe.get_doc(
            {
                "doctype": "Notification Log",
                "for_user": user,
                "subject": subject,
                "type": "Alert",
                "email_content": text,
                "document_type": "Communication",
                "document_name": communication_name,
                "from_user": sender,
            }
        )
        doc.insert(ignore_permissions=True)
        created += 1
    return created


def _notification_type(value: str) -> str:
    text = _normalize(value)
    if "grade" in text or "تقييم" in text or "درجة" in text:
        return "grade"
    if "payment" in text or "رسوم" in text or "مال" in text:
        return "payment"
    if "course" in text or "مقرر" in text:
        return "course"
    if "alert" in text or "تحذير" in text:
        return "alert"
    if "reminder" in text or "تذكير" in text:
        return "reminder"
    if "announcement" in text or "share" in text or "اعلان" in text:
        return "announcement"
    return "system"


def _notifications_for_current_user(student_row: dict | None = None) -> list[dict]:
    identity = _user_identity()
    notifications: list[dict] = []

    if frappe.db.exists("DocType", "Notification Log"):
        filters = {"for_user": ["in", [identity["user"], identity["email"]]]}
        rows = frappe.get_all(
            "Notification Log",
            filters=filters,
            fields=["name", "subject", "type", "document_type", "document_name", "from_user", "creation", "read"],
            order_by="creation desc",
            ignore_permissions=True,
            limit_page_length=100,
        )
        for row in rows:
            kind = _notification_type(row.get("type") or row.get("subject"))
            notifications.append(
                {
                    "id": f"NLOG::{row['name']}",
                    "titleAr": _clean(row.get("subject")) or "إشعار",
                    "titleEn": _clean(row.get("subject")) or "Notification",
                    "messageAr": _clean(row.get("subject")) or "",
                    "messageEn": _clean(row.get("subject")) or "",
                    "type": kind,
                    "senderAr": _clean(row.get("from_user")) or "System",
                    "senderEn": _clean(row.get("from_user")) or "System",
                    "senderType": "admin" if row.get("from_user") else "system",
                    "date": _iso(row.get("creation")),
                    "isRead": bool(int(row.get("read") or 0)),
                }
            )

    if frappe.db.exists("DocType", "ToDo"):
        todo_rows = frappe.get_all(
            "ToDo",
            filters={"allocated_to": ["in", [identity["user"], identity["email"]]]},
            fields=["name", "description", "status", "priority", "date", "modified", "reference_type", "reference_name"],
            order_by="modified desc",
            ignore_permissions=True,
            limit_page_length=100,
        )
        student_name = _clean(student_row.get("name")) if student_row else ""
        for row in todo_rows:
            if student_name and _clean(row.get("reference_type")) == "Student":
                if _clean(row.get("reference_name")) != student_name:
                    continue
            kind = _notification_type(row.get("priority") or row.get("description"))
            status = _normalize(row.get("status"))
            notifications.append(
                {
                    "id": f"TODO::{row['name']}",
                    "titleAr": "مهمة",
                    "titleEn": "Task",
                    "messageAr": _clean(row.get("description")),
                    "messageEn": _clean(row.get("description")),
                    "type": kind,
                    "senderAr": "النظام",
                    "senderEn": "System",
                    "senderType": "system",
                    "date": _iso(row.get("date") or row.get("modified")),
                    "isRead": status in {"closed", "cancelled", "completed"},
                }
            )

    notifications.sort(key=lambda item: item.get("date") or "", reverse=True)
    return notifications


def _mark_notification(notification_id: str) -> dict:
    if notification_id.startswith("NLOG::"):
        name = notification_id.split("::", 1)[1]
        if frappe.db.exists("Notification Log", name):
            frappe.db.set_value("Notification Log", name, "read", 1, update_modified=False)
            frappe.db.commit()
        return {"id": notification_id, "isRead": True}

    if notification_id.startswith("TODO::"):
        name = notification_id.split("::", 1)[1]
        if frappe.db.exists("ToDo", name):
            frappe.db.set_value("ToDo", name, "status", "Closed", update_modified=False)
            frappe.db.commit()
        return {"id": notification_id, "isRead": True}

    raise ApiError("NOT_FOUND", "Notification not found", status_code=404)


def _current_message_identities() -> set[str]:
    identity = _user_identity()
    ids = {
        _normalize(identity["user"]),
        _normalize(identity["email"]),
    }
    ids.discard("")
    return ids


def _query_messages_for_current_user() -> list[dict]:
    ids = sorted(_current_message_identities())
    if not ids:
        return []

    sender_placeholders = ",".join(["%s"] * len(ids))
    where_parts = [f"lower(ifnull(sender, '')) in ({sender_placeholders})"]
    params: list[Any] = list(ids)

    for identifier in ids:
        where_parts.append("lower(ifnull(recipients, '')) like %s")
        params.append(f"%{identifier}%")

    sql = f"""
        select
            name, sender, recipients, subject, content,
            communication_date, creation, reference_doctype, reference_name,
            read_by_recipient, has_attachment
        from `tabCommunication`
        where ({' or '.join(where_parts)})
        order by communication_date desc, creation desc
        limit 500
    """
    return frappe.db.sql(sql, tuple(params), as_dict=True)


def _student_user_ids(student_row: dict | None) -> set[str]:
    if not student_row:
        return set()
    return {
        _normalize(student_row.get("user")),
        _normalize(student_row.get("student_email_id")),
        _normalize(student_row.get("name")),
    } - {""}


def _conversation_id(student_id: str, doctor_id: str) -> str:
    return f"student::{student_id}::doctor::{doctor_id}"


def _parse_conversation_id(conversation_id: str) -> tuple[str, str]:
    parts = (conversation_id or "").split("::")
    if len(parts) != 4 or parts[0] != "student" or parts[2] != "doctor":
        raise ApiError("VALIDATION_ERROR", "Invalid conversation id", status_code=400)
    student_id = parts[1].strip()
    doctor_id = parts[3].strip()
    if not student_id or not doctor_id:
        raise ApiError("VALIDATION_ERROR", "Invalid conversation id", status_code=400)
    return student_id, doctor_id


def _ensure_conversation_access(student_row: dict, doctor_id: str) -> dict[str, Any]:
    identity = _user_identity()
    current_ids = _current_message_identities()
    student_ids = _student_user_ids(student_row)
    student_name = _normalize(student_row.get("name"))
    doctor_identity = _normalize(doctor_id)
    is_admin = bool(identity["roles"].intersection(ELEVATED_PORTAL_ROLES))

    is_student_participant = bool(current_ids.intersection(student_ids) or (student_name and student_name in current_ids))
    is_doctor_participant = False
    if doctor_identity and doctor_identity in current_ids:
        if is_admin:
            is_doctor_participant = True
        else:
            _ensure_doctor_context(require_mapping=True)
            is_doctor_participant = True

    if not (is_admin or is_student_participant or is_doctor_participant):
        raise ApiError("FORBIDDEN", "Not allowed to access this conversation", status_code=403)

    return {
        "identity": identity,
        "current_ids": current_ids,
        "student_ids": student_ids,
        "doctor_identity": doctor_identity,
        "is_admin": is_admin,
        "is_student_participant": is_student_participant,
        "is_doctor_participant": is_doctor_participant,
    }


def _counterpart_from_message(message_row: dict, current_ids: set[str]) -> str:
    sender = _normalize(message_row.get("sender"))
    recipients = [_normalize(v) for v in _split_csv(message_row.get("recipients"))]
    if sender and sender not in current_ids:
        return sender
    for recipient in recipients:
        if recipient and recipient not in current_ids:
            return recipient
    return sender or (recipients[0] if recipients else "")


def _resolve_user_display(identifier: str) -> tuple[str, str]:
    if not identifier:
        return "", ""
    user = frappe.db.get_value("User", {"name": identifier}, ["full_name", "email"], as_dict=True)
    if not user:
        user = frappe.db.get_value("User", {"email": identifier}, ["name", "full_name", "email"], as_dict=True)
    if not user:
        return identifier, identifier
    full = _clean(user.get("full_name") or user.get("name") or user.get("email"))
    return full, _clean(user.get("email") or user.get("name"))


def _serialize_chat_message(row: dict, conversation_id: str, doctor_identity: str, student_ids: set[str]) -> dict:
    sender = _normalize(row.get("sender"))
    sender_type = "doctor" if sender == _normalize(doctor_identity) else "student"
    if sender_type == "doctor" and sender in student_ids:
        sender_type = "student"
    sender_name, _ = _resolve_user_display(sender)
    return {
        "id": row.get("name"),
        "conversationId": conversation_id,
        "senderId": sender,
        "senderType": sender_type,
        "senderName": sender_name or sender,
        "text": _clean(row.get("content")),
        "createdAt": _iso(row.get("communication_date") or row.get("creation")),
        "isRead": bool(int(row.get("read_by_recipient") or 0)),
    }


def _payment_method_labels(method: str) -> tuple[str, str]:
    method_clean = _clean(method)
    normalized = _normalize(method_clean)
    mapping = {
        "cash": ("نقد", "Cash"),
        "bank transfer": ("حوالة بنكية", "Bank Transfer"),
        "bank": ("حوالة بنكية", "Bank Transfer"),
        "card": ("بطاقة", "Card"),
        "check": ("شيك", "Check"),
        "نقد": ("نقد", "Cash"),
        "شيك": ("شيك", "Check"),
        "حوالة مصرفية": ("حوالة بنكية", "Bank Transfer"),
    }
    if normalized in mapping:
        return mapping[normalized]
    return method_clean or "دفع", method_clean or "Payment"


@frappe.whitelist()
@api_endpoint
def get_doctor_profile():
    """Get doctor profile from Instructor doctype (with Faculty Members fallback)."""
    ctx = _ensure_doctor_context(require_mapping=True)
    identity = ctx["identity"]

    if frappe.db.exists("DocType", "Instructor"):
        if ctx["matched_instructors"]:
            instructor = ctx["matched_instructors"][0]
            name = _clean(instructor.get("instructor_name") or instructor.get("name") or identity["full_name"])
            return {
                "id": _clean(instructor.get("name") or identity["user"]),
                "nameAr": name,
                "nameEn": name,
                "degreeAr": "",
                "degreeEn": "",
                "specializationAr": "",
                "specializationEn": "",
                "collegeAr": _clean(instructor.get("department")),
                "collegeEn": _clean(instructor.get("department")),
                "departmentAr": _clean(instructor.get("department")),
                "departmentEn": _clean(instructor.get("department")),
                "email": identity["email"],
                "phone": "",
                "officeHoursAr": "",
                "officeHoursEn": "",
                "bioAr": "",
                "bioEn": "",
                "image": instructor.get("image"),
            }

    if frappe.db.exists("DocType", "Faculty Members"):
        rows = frappe.get_all(
            "Faculty Members",
            filters={"full_name": identity["full_name"]},
            fields=["name", "full_name", "academic_title", "department", "biography", "photo", "is_active"],
            ignore_permissions=True,
            limit_page_length=1,
        )
        if rows:
            row = rows[0]
            return {
                "id": _clean(row.get("name") or identity["user"]),
                "nameAr": _clean(row.get("full_name") or identity["full_name"]),
                "nameEn": _clean(row.get("full_name") or identity["full_name"]),
                "degreeAr": _clean(row.get("academic_title")),
                "degreeEn": _clean(row.get("academic_title")),
                "specializationAr": "",
                "specializationEn": "",
                "collegeAr": _clean(row.get("department")),
                "collegeEn": _clean(row.get("department")),
                "departmentAr": _clean(row.get("department")),
                "departmentEn": _clean(row.get("department")),
                "email": identity["email"],
                "phone": "",
                "officeHoursAr": "",
                "officeHoursEn": "",
                "bioAr": _clean(row.get("biography")),
                "bioEn": _clean(row.get("biography")),
                "image": row.get("photo"),
            }

    return {
        "id": identity["user"],
        "nameAr": identity["full_name"],
        "nameEn": identity["full_name"],
        "degreeAr": "",
        "degreeEn": "",
        "specializationAr": "",
        "specializationEn": "",
        "collegeAr": "",
        "collegeEn": "",
        "departmentAr": "",
        "departmentEn": "",
        "email": identity["email"],
        "phone": "",
        "officeHoursAr": "",
        "officeHoursEn": "",
        "bioAr": "",
        "bioEn": "",
        "image": None,
    }


@frappe.whitelist()
@api_endpoint
def update_doctor_profile(**payload):
    """Update doctor profile fields on User and Instructor when available."""
    ctx = _ensure_doctor_context(require_mapping=True)
    identity = ctx["identity"]
    user_doc = frappe.get_doc("User", identity["user"])

    if payload.get("email"):
        user_doc.email = payload.get("email")
    if payload.get("nameAr") or payload.get("nameEn"):
        user_doc.full_name = payload.get("nameAr") or payload.get("nameEn")
    user_doc.save(ignore_permissions=True)

    if frappe.db.exists("DocType", "Instructor") and ctx["matched_instructors"]:
        instructor_doc = frappe.get_doc("Instructor", ctx["matched_instructors"][0]["name"])
        if payload.get("nameAr") or payload.get("nameEn"):
            instructor_doc.instructor_name = payload.get("nameAr") or payload.get("nameEn")
        if payload.get("image"):
            instructor_doc.image = payload.get("image")
        link_field = ctx.get("instructor_user_link_field")
        if link_field and not _clean(instructor_doc.get(link_field)):
            instructor_doc.set(link_field, identity["user"])
        instructor_doc.save(ignore_permissions=True)

    frappe.db.commit()
    return get_doctor_profile()


@frappe.whitelist()
@api_endpoint
def list_doctor_courses():
    """List courses assigned to current doctor from Course Schedule."""
    rows = _doctor_schedule_rows()
    grouped: dict[str, dict] = {}

    groups_by_course: dict[str, set[str]] = defaultdict(set)
    schedule_signatures: dict[str, list[str]] = defaultdict(list)
    for row in rows:
        course = _clean(row.get("course"))
        if not course:
            continue
        if row.get("student_group"):
            groups_by_course[course].add(_clean(row.get("student_group")))
        day_ar, day_en = _day_labels(row.get("schedule_date"))
        time_range = _range_label(row.get("from_time"), row.get("to_time"))
        signature = f"{day_ar} {time_range}".strip() if day_ar else time_range
        if signature and signature not in schedule_signatures[course]:
            schedule_signatures[course].append(signature)

    student_counts: dict[str, int] = {}
    for course, groups in groups_by_course.items():
        members = _student_group_members(groups)
        student_counts[course] = len({_clean(member.get("student")) for member in members if member.get("student")})

    course_names = _course_name_map(set(groups_by_course.keys()) | {_clean(r.get("course")) for r in rows if r.get("course")})

    for row in rows:
        course = _clean(row.get("course"))
        if not course:
            continue
        if course in grouped:
            continue
        semester = ""
        if row.get("schedule_date"):
            schedule_date = _iso(row.get("schedule_date")) or ""
            semester = schedule_date[:4] if schedule_date else ""
        grouped[course] = {
            "id": course,
            "code": course,
            "nameAr": course_names.get(course, course),
            "nameEn": course_names.get(course, course),
            "creditHours": 0,
            "semester": semester,
            "studentsCount": student_counts.get(course, 0),
            "scheduleAr": " | ".join(schedule_signatures.get(course, [])[:3]),
            "scheduleEn": " | ".join(schedule_signatures.get(course, [])[:3]),
            "classroom": _clean(row.get("room")),
        }

    return list(grouped.values())


@frappe.whitelist()
@api_endpoint
def list_doctor_students(courseId: str | None = None):
    """List students for doctor filtered by course when provided."""
    schedule_rows = _doctor_schedule_rows(course_id=courseId)
    if not schedule_rows:
        return []

    groups = {_clean(row.get("student_group")) for row in schedule_rows if row.get("student_group")}
    members = _student_group_members(groups)

    schedule_names_by_course: dict[str, set[str]] = defaultdict(set)
    for row in schedule_rows:
        course = _clean(row.get("course"))
        if course and row.get("name"):
            schedule_names_by_course[course].add(_clean(row.get("name")))

    course_name_map = _course_name_map({_clean(row.get("course")) for row in schedule_rows if row.get("course")})

    output = []
    seen: set[tuple[str, str]] = set()
    for member in members:
        raw_student = _clean(member.get("student"))
        student_row = _find_student_by_identifier(raw_student) or _find_student_by_identifier(member.get("student_name"))
        if not student_row:
            continue

        student_keys = _student_identifiers(student_row) | {raw_student, _normalize(member.get("student_name"))}
        student_name = _clean(student_row.get("student_name") or member.get("student_name") or raw_student)

        for course, schedule_names in schedule_names_by_course.items():
            key = (_clean(student_row.get("name")) or raw_student, course)
            if key in seen:
                continue
            seen.add(key)

            result, details = _assessment_for_student_course(student_keys, course)
            total_score = _to_float(result.get("total_score")) if result else 0.0

            midterm = 0.0
            final = 0.0
            if len(details) >= 2:
                midterm = _to_float(details[0].get("score"))
                final = _to_float(details[1].get("score"))
            elif len(details) == 1:
                final = _to_float(details[0].get("score"))
            else:
                final = total_score

            output.append(
                {
                    "id": _clean(student_row.get("name") or raw_student),
                    "nameAr": student_name,
                    "nameEn": student_name,
                    "academicNumber": _clean(student_row.get("student_email_id") or student_row.get("name") or raw_student),
                    "courseId": course,
                    "courseCode": course,
                    "attendance": _attendance_percent(student_keys, schedule_names),
                    "midterm": round(midterm, 2),
                    "final": round(final, 2),
                    "total": round(total_score, 2),
                }
            )

    output.sort(key=lambda item: (item.get("courseCode") or "", item.get("nameEn") or ""))
    return output


@frappe.whitelist()
@api_endpoint
def update_doctor_student_grades(student_id: str, **payload):
    """Create/update Assessment Result for student and course."""
    ctx = _ensure_doctor_context(require_mapping=True)
    _require_doctype("Assessment Result")

    student_row = _find_student_by_identifier(student_id)
    if not student_row:
        raise ApiError("NOT_FOUND", "Student not found", status_code=404)

    course = _clean(payload.get("courseId") or payload.get("course_code") or payload.get("course"))
    if not course:
        raise ApiError("VALIDATION_ERROR", "courseId is required", status_code=400)

    if not ctx["all_scope"] and not _doctor_schedule_rows(course_id=course):
        raise ApiError("FORBIDDEN", "Course is not assigned to current doctor", status_code=403)

    total = _to_float(payload.get("total"))
    if total <= 0:
        midterm = _to_float(payload.get("midterm"))
        final = _to_float(payload.get("final"))
        coursework = _to_float(payload.get("coursework"))
        total = midterm + final + coursework

    grade = _clean(payload.get("grade"))
    if not grade:
        grade = "A" if total >= 90 else "B" if total >= 80 else "C" if total >= 70 else "D" if total >= 60 else "F"

    student_name = _clean(student_row.get("student_name") or student_row.get("name"))
    student_keys = list(_student_identifiers(student_row))

    existing = frappe.get_all(
        "Assessment Result",
        filters={"student": ["in", student_keys], "course": course},
        fields=["name"],
        order_by="modified desc",
        ignore_permissions=True,
        limit_page_length=1,
    )

    if existing:
        doc = frappe.get_doc("Assessment Result", existing[0]["name"])
    else:
        doc = frappe.get_doc({"doctype": "Assessment Result"})

    doc.student = _clean(student_row.get("name"))
    doc.student_name = student_name
    doc.course = course
    doc.total_score = total
    doc.maximum_score = max(_to_float(getattr(doc, "maximum_score", 0)) or 0, 100)
    doc.grade = grade
    if not getattr(doc, "academic_year", None):
        doc.academic_year = _clean(payload.get("academic_year"))
    if not getattr(doc, "academic_term", None):
        doc.academic_term = _clean(payload.get("academic_term"))

    if doc.get("name"):
        doc.save(ignore_permissions=True)
    else:
        doc.insert(ignore_permissions=True)

    frappe.db.commit()
    return {"updated": True, "assessmentResult": doc.name, "total": total, "grade": grade}


@frappe.whitelist()
@api_endpoint
def list_doctor_schedule():
    """List doctor schedule items from Course Schedule."""
    rows = _doctor_schedule_rows()
    course_names = _course_name_map({_clean(row.get("course")) for row in rows if row.get("course")})

    items = []
    for row in rows:
        course = _clean(row.get("course"))
        if not course:
            continue
        day_ar, day_en = _day_labels(row.get("schedule_date"))
        item_type = "lecture"
        room_norm = _normalize(row.get("room"))
        if "lab" in room_norm or "مختبر" in room_norm:
            item_type = "lab"

        items.append(
            {
                "id": row.get("name"),
                "dayAr": day_ar,
                "dayEn": day_en,
                "time": _range_label(row.get("from_time"), row.get("to_time")),
                "courseCode": course,
                "courseNameAr": course_names.get(course, course),
                "courseNameEn": course_names.get(course, course),
                "classroom": _clean(row.get("room")),
                "type": item_type,
            }
        )
    return items


@frappe.whitelist()
@api_endpoint
def get_doctor_finance():
    """Return doctor finance summary from Payment Entry when employee mapping exists."""
    ctx = _ensure_doctor_context(require_mapping=True)
    _require_doctype("Payment Entry")

    employee = ""
    if ctx["matched_instructors"]:
        employee = _clean(ctx["matched_instructors"][0].get("employee"))

    if not employee:
        return {
            "baseSalary": 0,
            "allowances": {
                "housingAr": "بدل سكن",
                "housingEn": "Housing Allowance",
                "housingAmount": 0,
                "transportAr": "بدل نقل",
                "transportEn": "Transport Allowance",
                "transportAmount": 0,
                "otherAr": "بدلات أخرى",
                "otherEn": "Other Allowances",
                "otherAmount": 0,
                "total": 0,
            },
            "deductions": {
                "taxAr": "ضريبة",
                "taxEn": "Tax",
                "taxAmount": 0,
                "insuranceAr": "تأمين",
                "insuranceEn": "Insurance",
                "insuranceAmount": 0,
                "otherAr": "خصومات أخرى",
                "otherEn": "Other Deductions",
                "otherAmount": 0,
                "total": 0,
            },
            "netSalary": 0,
            "paymentHistory": [],
        }

    payments = frappe.get_all(
        "Payment Entry",
        filters={"party_type": "Employee", "party": employee, "docstatus": 1},
        fields=["name", "posting_date", "paid_amount", "received_amount", "status"],
        order_by="posting_date desc",
        ignore_permissions=True,
        limit_page_length=50,
    )

    history = []
    monthly_values = []
    for row in payments[:12]:
        amount = max(_to_float(row.get("received_amount")), _to_float(row.get("paid_amount")))
        monthly_values.append(amount)
        posting_date = row.get("posting_date")
        month_ar, month_en = "", ""
        if posting_date:
            if isinstance(posting_date, str):
                try:
                    dt = datetime.strptime(posting_date[:10], "%Y-%m-%d")
                except Exception:
                    dt = None
            else:
                dt = datetime.combine(posting_date, datetime.min.time())
            if dt:
                month_en = dt.strftime("%B %Y")
                month_ar = month_en

        history.append(
            {
                "id": row.get("name"),
                "monthAr": month_ar,
                "monthEn": month_en,
                "baseSalary": amount,
                "allowances": 0,
                "deductions": 0,
                "netSalary": amount,
                "status": "paid" if _normalize(row.get("status")) in {"submitted", "paid"} else "pending",
                "paidDate": _iso(posting_date),
            }
        )

    base_salary = round(sum(monthly_values) / len(monthly_values), 2) if monthly_values else 0
    return {
        "baseSalary": base_salary,
        "allowances": {
            "housingAr": "بدل سكن",
            "housingEn": "Housing Allowance",
            "housingAmount": 0,
            "transportAr": "بدل نقل",
            "transportEn": "Transport Allowance",
            "transportAmount": 0,
            "otherAr": "بدلات أخرى",
            "otherEn": "Other Allowances",
            "otherAmount": 0,
            "total": 0,
        },
        "deductions": {
            "taxAr": "ضريبة",
            "taxEn": "Tax",
            "taxAmount": 0,
            "insuranceAr": "تأمين",
            "insuranceEn": "Insurance",
            "insuranceAmount": 0,
            "otherAr": "خصومات أخرى",
            "otherEn": "Other Deductions",
            "otherAmount": 0,
            "total": 0,
        },
        "netSalary": base_salary,
        "paymentHistory": history,
    }


@frappe.whitelist()
@api_endpoint
def list_doctor_notifications():
    """List doctor notifications from Notification Log and ToDo."""
    _ensure_doctor_context(require_mapping=False)
    return _notifications_for_current_user()


@frappe.whitelist()
@api_endpoint
def mark_doctor_notification_read(notification_id: str):
    """Mark doctor notification as read."""
    _ensure_doctor_context(require_mapping=False)
    return _mark_notification(notification_id)


@frappe.whitelist()
@api_endpoint
def list_doctor_messages():
    """List doctor messages from Communication."""
    _ensure_doctor_context(require_mapping=False)
    current_ids = _current_message_identities()
    rows = _query_messages_for_current_user()
    out = []
    for row in rows:
        counterpart = _counterpart_from_message(row, current_ids)
        if not counterpart:
            continue
        student_id = _clean(row.get("reference_name"))
        student_row = _find_student_by_identifier(student_id) if student_id else None
        student_name = _clean((student_row or {}).get("student_name") or student_id)
        out.append(
            {
                "id": row.get("name"),
                "studentId": _clean((student_row or {}).get("name") or student_id),
                "studentNameAr": student_name,
                "studentNameEn": student_name,
                "studentAcademicNumber": _clean((student_row or {}).get("student_email_id") or (student_row or {}).get("name") or student_id),
                "subjectAr": _clean(row.get("subject")) or "رسالة",
                "subjectEn": _clean(row.get("subject")) or "Message",
                "messageAr": _clean(row.get("content")),
                "messageEn": _clean(row.get("content")),
                "date": _iso(row.get("communication_date") or row.get("creation")),
                "isRead": bool(int(row.get("read_by_recipient") or 0)),
                "courseCode": "",
            }
        )
    return out


@frappe.whitelist()
@api_endpoint
def mark_doctor_message_read(message_id: str):
    """Mark doctor message as read."""
    if not frappe.db.exists("Communication", message_id):
        raise ApiError("NOT_FOUND", "Message not found", status_code=404)
    current_ids = sorted(_current_message_identities())
    if not current_ids:
        raise ApiError("FORBIDDEN", "Not allowed to update this message", status_code=403)
    where = " or ".join(["lower(ifnull(recipients, '')) like %s" for _ in current_ids])
    params: list[Any] = [f"%{identifier}%" for identifier in current_ids]
    can_access = frappe.db.sql(
        f"select name from `tabCommunication` where name = %s and ({where}) limit 1",
        tuple([message_id, *params]),
        as_dict=True,
    )
    if not can_access:
        raise ApiError("FORBIDDEN", "Not allowed to update this message", status_code=403)
    frappe.db.set_value("Communication", message_id, "read_by_recipient", 1, update_modified=False)
    frappe.db.commit()
    return {"id": message_id, "isRead": True}


@frappe.whitelist()
@api_endpoint
def list_doctor_announcements(courseId: str | None = None):
    """List doctor-authored course announcements."""
    ctx = _ensure_doctor_context(require_mapping=True)
    _require_doctype("Communication")

    selected_course = _clean(courseId or frappe.form_dict.get("courseId"))
    filters: dict[str, Any] = {"reference_doctype": "Course"}
    if selected_course:
        if not ctx["all_scope"] and not _doctor_schedule_rows(course_id=selected_course):
            raise ApiError("FORBIDDEN", "Course is not assigned to current doctor", status_code=403)
        filters["reference_name"] = selected_course
    elif not ctx["all_scope"]:
        allowed_courses = {_clean(row.get("course")) for row in _doctor_schedule_rows() if row.get("course")}
        if not allowed_courses:
            return []
        filters["reference_name"] = ["in", sorted(allowed_courses)]

    rows = frappe.get_all(
        "Communication",
        filters=filters,
        fields=["name", "subject", "content", "sender", "reference_doctype", "reference_name", "communication_date", "creation"],
        order_by="creation desc",
        ignore_permissions=True,
        limit_page_length=500,
    )
    current_ids = _current_message_identities()
    out = []
    for row in rows:
        if not _is_doctor_announcement_row(row):
            continue
        if _normalize(row.get("sender")) not in current_ids:
            continue
        out.append(_serialize_doctor_announcement(row))
    return out


@frappe.whitelist()
@api_endpoint
def create_doctor_announcement(**payload):
    """Create a course announcement authored by current doctor."""
    ctx = _ensure_doctor_context(require_mapping=True)
    _require_doctype("Communication")

    course_id = _clean(payload.get("courseId") or frappe.form_dict.get("courseId"))
    text = _clean(payload.get("text") or payload.get("message") or frappe.form_dict.get("text"))
    if not course_id:
        raise ApiError("VALIDATION_ERROR", "courseId is required", status_code=400)
    if not text:
        raise ApiError("VALIDATION_ERROR", "text is required", status_code=400)
    if len(text) > 5000:
        raise ApiError("VALIDATION_ERROR", "text length must be <= 5000", status_code=400)

    if not ctx["all_scope"] and not _doctor_schedule_rows(course_id=course_id):
        raise ApiError("FORBIDDEN", "Course is not assigned to current doctor", status_code=403)

    sender = _clean(frappe.session.user)
    announcement = frappe.get_doc(
        {
            "doctype": "Communication",
            "communication_type": "Communication",
            "communication_medium": "Other",
            "sent_or_received": "Sent",
            "sender": sender,
            "subject": _announcement_subject(course_id),
            "content": text,
            "reference_doctype": "Course",
            "reference_name": course_id,
            "read_by_recipient": 0,
        }
    )
    announcement.insert(ignore_permissions=True)
    _create_student_announcement_notifications(
        course_id=course_id,
        text=text,
        sender=sender,
        communication_name=announcement.name,
    )
    frappe.db.commit()
    return _serialize_doctor_announcement(announcement.as_dict())


@frappe.whitelist()
@api_endpoint
def delete_doctor_announcement(announcement_id: str):
    """Delete a doctor-authored course announcement."""
    ctx = _ensure_doctor_context(require_mapping=True)
    if not frappe.db.exists("Communication", announcement_id):
        raise ApiError("NOT_FOUND", "Announcement not found", status_code=404)

    row = frappe.db.get_value(
        "Communication",
        announcement_id,
        ["name", "subject", "sender", "reference_doctype", "reference_name"],
        as_dict=True,
    ) or {}
    if not _is_doctor_announcement_row(row):
        raise ApiError("NOT_FOUND", "Announcement not found", status_code=404)

    course_id = _clean(row.get("reference_name"))
    if course_id and not ctx["all_scope"] and not _doctor_schedule_rows(course_id=course_id):
        raise ApiError("FORBIDDEN", "Course is not assigned to current doctor", status_code=403)

    current_ids = _current_message_identities()
    if not ctx["all_scope"] and _normalize(row.get("sender")) not in current_ids:
        raise ApiError("FORBIDDEN", "Not allowed to delete this announcement", status_code=403)

    frappe.delete_doc("Communication", announcement_id, ignore_permissions=True, force=1)
    frappe.db.commit()
    return {"deleted": True}


@frappe.whitelist()
@api_endpoint
def list_doctor_materials(courseId: str | None = None):
    """List doctor materials from File attached to Course/Instructor."""
    ctx = _ensure_doctor_context(require_mapping=True)
    _require_doctype("File")
    schedule_rows = _doctor_schedule_rows(course_id=courseId)
    courses = {_clean(row.get("course")) for row in schedule_rows if row.get("course")}

    instructor_names = {_clean(item.get("name")) for item in ctx["matched_instructors"] if item.get("name")}

    materials = []
    if courses:
        course_files = frappe.get_all(
            "File",
            filters={"attached_to_doctype": "Course", "attached_to_name": ["in", list(courses)]},
            fields=["name", "file_name", "file_url", "file_size", "creation", "attached_to_name"],
            order_by="creation desc",
            ignore_permissions=True,
            limit_page_length=200,
        )
        for row in course_files:
            materials.append(_serialize_material(row, course_id=_clean(row.get("attached_to_name"))))

    if instructor_names:
        instructor_files = frappe.get_all(
            "File",
            filters={"attached_to_doctype": "Instructor", "attached_to_name": ["in", list(instructor_names)]},
            fields=["name", "file_name", "file_url", "file_size", "creation", "attached_to_name"],
            order_by="creation desc",
            ignore_permissions=True,
            limit_page_length=200,
        )
        for row in instructor_files:
            materials.append(_serialize_material(row, course_id=courseId or ""))

    if courseId:
        target = _normalize(courseId)
        materials = [item for item in materials if _normalize(item.get("courseId")) == target]

    seen = set()
    deduped = []
    for item in materials:
        item_id = item.get("id")
        if item_id in seen:
            continue
        seen.add(item_id)
        deduped.append(item)
    return deduped


@frappe.whitelist()
@api_endpoint
def upload_doctor_material(**payload):
    """Upload doctor material and attach to Course or Instructor."""
    ctx = _ensure_doctor_context(require_mapping=True)
    _require_doctype("File")
    if not frappe.request or not frappe.request.files:
        raise ApiError("VALIDATION_ERROR", "No file uploaded", status_code=400)

    course_id = _clean(payload.get("courseId") or frappe.form_dict.get("courseId"))
    attached_doctype = "Course" if course_id else "Instructor"
    attached_name = course_id

    if course_id and not ctx["all_scope"] and not _doctor_schedule_rows(course_id=course_id):
        raise ApiError("FORBIDDEN", "Course is not assigned to current doctor", status_code=403)

    if not attached_name:
        if not ctx["matched_instructors"]:
            raise ApiError("VALIDATION_ERROR", "No instructor mapping found for current user", status_code=400)
        attached_name = _clean(ctx["matched_instructors"][0].get("name"))

    fileobj = next(iter(frappe.request.files.values()))
    saved = save_file(
        fileobj.filename,
        fileobj.stream.read(),
        attached_to_doctype=attached_doctype,
        attached_to_name=attached_name,
        is_private=0,
    )
    return _serialize_material(saved.as_dict(), course_id=course_id or attached_name)


@frappe.whitelist()
@api_endpoint
def delete_doctor_material(material_id: str):
    """Delete doctor material file."""
    if not frappe.db.exists("File", material_id):
        raise ApiError("NOT_FOUND", "Material not found", status_code=404)
    ctx = _ensure_doctor_context(require_mapping=True)
    file_row = frappe.db.get_value(
        "File",
        material_id,
        ["attached_to_doctype", "attached_to_name"],
        as_dict=True,
    ) or {}
    if not ctx["all_scope"]:
        attached_doctype = _clean(file_row.get("attached_to_doctype"))
        attached_name = _clean(file_row.get("attached_to_name"))
        allowed_instructors = {_clean(item.get("name")) for item in ctx["matched_instructors"] if item.get("name")}
        allowed_courses = {_clean(row.get("course")) for row in _doctor_schedule_rows() if row.get("course")}
        allowed = False
        if attached_doctype == "Instructor" and attached_name in allowed_instructors:
            allowed = True
        if attached_doctype == "Course" and attached_name in allowed_courses:
            allowed = True
        if not allowed:
            raise ApiError("FORBIDDEN", "Not allowed to delete this material", status_code=403)
    frappe.delete_doc("File", material_id, ignore_permissions=True, force=1)
    frappe.db.commit()
    return {"deleted": True}


@frappe.whitelist()
@api_endpoint
def get_student_profile():
    """Get student profile from Student doctype."""
    student = _find_student_by_current_user(required=True)

    status = "active"
    student_status = _normalize(student.get("custom_status") or student.get("status"))
    if "suspend" in student_status or "inactive" in student_status:
        status = "suspended"
    elif "graduat" in student_status:
        status = "graduated"

    return {
        "id": _clean(student.get("name")),
        "academicNumber": _clean(student.get("student_email_id") or student.get("name")),
        "nameAr": _clean(student.get("student_name") or student.get("name")),
        "nameEn": _clean(student.get("student_name") or student.get("name")),
        "emailPersonal": _clean(student.get("personal_email") or student.get("student_email_id")),
        "emailUniversity": _clean(student.get("student_email_id")),
        "phone": _clean(student.get("student_mobile_number")),
        "collegeAr": _clean(student.get("program")),
        "collegeEn": _clean(student.get("program")),
        "departmentAr": _clean(student.get("student_group") or student.get("student_batch_name")),
        "departmentEn": _clean(student.get("student_group") or student.get("student_batch_name")),
        "specializationAr": _clean(student.get("program")),
        "specializationEn": _clean(student.get("program")),
        "levelAr": _clean(student.get("student_group") or student.get("student_batch_name")),
        "levelEn": _clean(student.get("student_group") or student.get("student_batch_name")),
        "status": status,
        "gpa": 0,
        "totalCredits": 0,
        "completedCredits": 0,
        "admissionDate": _iso(student.get("admission_date")) or _iso(student.get("creation")) or "",
        "expectedGraduation": "",
        "advisorAr": "",
        "advisorEn": "",
        "image": student.get("image") or student.get("photo"),
    }


@frappe.whitelist()
@api_endpoint
def update_student_profile(**payload):
    """Update student profile fields."""
    student = _find_student_by_current_user(required=True)
    doc = frappe.get_doc("Student", student["name"])

    if payload.get("nameAr") or payload.get("nameEn"):
        doc.student_name = payload.get("nameAr") or payload.get("nameEn")
    if payload.get("phone"):
        doc.student_mobile_number = payload.get("phone")
    if payload.get("emailPersonal"):
        doc.personal_email = payload.get("emailPersonal")
    if payload.get("image"):
        if hasattr(doc, "image"):
            doc.image = payload.get("image")
        elif hasattr(doc, "photo"):
            doc.photo = payload.get("image")

    doc.save(ignore_permissions=True)
    frappe.db.commit()
    return get_student_profile()


def _student_course_rows(student: dict) -> tuple[list[dict], dict[str, str], set[str]]:
    student_ids = list(_student_identifiers(student) | {_normalize(student.get("name"))})

    enrollment_rows = []
    if frappe.db.exists("DocType", "Course Enrollment"):
        enrollment_rows = frappe.get_all(
            "Course Enrollment",
            filters={"student": ["in", student_ids]},
            fields=["name", "course", "program", "enrollment_date"],
            order_by="modified desc",
            ignore_permissions=True,
            limit_page_length=0,
        )

    program_courses = []
    program_semester_map: dict[str, str] = {}
    if frappe.db.exists("DocType", "Program Enrollment") and frappe.db.exists("DocType", "Program Enrollment Course"):
        programs = frappe.get_all(
            "Program Enrollment",
            filters={"student": ["in", student_ids]},
            fields=["name", "program", "academic_term", "academic_year"],
            order_by="modified desc",
            ignore_permissions=True,
            limit_page_length=0,
        )
        program_ids = [row["name"] for row in programs]
        for row in programs:
            semester = " / ".join([_clean(row.get("academic_year")), _clean(row.get("academic_term"))]).strip(" /")
            program_semester_map[row["name"]] = semester

        if program_ids:
            program_courses = frappe.get_all(
                "Program Enrollment Course",
                filters={"parent": ["in", program_ids]},
                fields=["parent", "course", "course_name"],
                ignore_permissions=True,
                limit_page_length=0,
            )

    combined = []
    for row in enrollment_rows:
        combined.append(
            {
                "course": _clean(row.get("course")),
                "semester": _clean(row.get("program")),
                "enrollment_date": _iso(row.get("enrollment_date")),
            }
        )

    for row in program_courses:
        combined.append(
            {
                "course": _clean(row.get("course")),
                "course_name": _clean(row.get("course_name")),
                "semester": _clean(program_semester_map.get(row.get("parent"))),
                "enrollment_date": None,
            }
        )

    course_codes = {item["course"] for item in combined if item.get("course")}
    course_names = _course_name_map(course_codes)
    return combined, course_names, course_codes


@frappe.whitelist()
@api_endpoint
def list_student_courses():
    """List student enrolled courses from Course Enrollment/Program Enrollment."""
    student = _find_student_by_current_user(required=True)
    combined, course_names, course_codes = _student_course_rows(student)

    student_groups = set()
    if frappe.db.exists("DocType", "Student Group Student"):
        member_rows = frappe.get_all(
            "Student Group Student",
            filters={"student": ["in", list(_student_identifiers(student) | {_normalize(student.get('name'))})]},
            fields=["parent"],
            ignore_permissions=True,
            limit_page_length=0,
        )
        student_groups = {_clean(row.get("parent")) for row in member_rows if row.get("parent")}

    schedule_rows = []
    if student_groups and frappe.db.exists("DocType", "Course Schedule"):
        schedule_rows = frappe.get_all(
            "Course Schedule",
            filters={"student_group": ["in", list(student_groups)]},
            fields=["course", "instructor_name", "room", "schedule_date", "from_time", "to_time"],
            order_by="schedule_date desc",
            ignore_permissions=True,
            limit_page_length=0,
        )

    schedule_by_course: dict[str, list[dict]] = defaultdict(list)
    for row in schedule_rows:
        course = _clean(row.get("course"))
        if course:
            schedule_by_course[course].append(row)

    assessment_courses = set()
    if frappe.db.exists("DocType", "Assessment Result"):
        assessment_rows = frappe.get_all(
            "Assessment Result",
            filters={"student": ["in", list(_student_identifiers(student) | {_normalize(student.get('name'))})]},
            fields=["course"],
            ignore_permissions=True,
            limit_page_length=0,
        )
        assessment_courses = {_clean(row.get("course")) for row in assessment_rows if row.get("course")}

    output = []
    seen = set()
    for item in combined:
        course = _clean(item.get("course"))
        if not course or course in seen:
            continue
        seen.add(course)

        schedules = schedule_by_course.get(course, [])
        first_schedule = schedules[0] if schedules else {}
        signatures = []
        for row in schedules[:3]:
            day_ar, day_en = _day_labels(row.get("schedule_date"))
            label = f"{day_ar} {_range_label(row.get('from_time'), row.get('to_time'))}".strip()
            if label and label not in signatures:
                signatures.append(label)

        status = "current"
        if course in assessment_courses:
            status = "completed"
        elif schedules:
            latest_date = schedules[0].get("schedule_date")
            if latest_date and latest_date > datetime.utcnow().date():
                status = "upcoming"

        output.append(
            {
                "id": course,
                "code": course,
                "nameAr": item.get("course_name") or course_names.get(course, course),
                "nameEn": item.get("course_name") or course_names.get(course, course),
                "creditHours": 0,
                "doctorAr": _clean(first_schedule.get("instructor_name")),
                "doctorEn": _clean(first_schedule.get("instructor_name")),
                "classroom": _clean(first_schedule.get("room")),
                "scheduleAr": " | ".join(signatures),
                "scheduleEn": " | ".join(signatures),
                "semester": _clean(item.get("semester")),
                "status": status,
            }
        )

    output.sort(key=lambda row: row.get("code") or "")
    return output


@frappe.whitelist()
@api_endpoint
def list_student_schedule():
    """List student schedule items from Course Schedule by student groups."""
    student = _find_student_by_current_user(required=True)

    if not frappe.db.exists("DocType", "Student Group Student") or not frappe.db.exists("DocType", "Course Schedule"):
        return []

    student_ids = list(_student_identifiers(student) | {_normalize(student.get("name"))})
    group_rows = frappe.get_all(
        "Student Group Student",
        filters={"student": ["in", student_ids]},
        fields=["parent"],
        ignore_permissions=True,
        limit_page_length=0,
    )
    groups = {_clean(row.get("parent")) for row in group_rows if row.get("parent")}
    if not groups:
        return []

    schedules = frappe.get_all(
        "Course Schedule",
        filters={"student_group": ["in", list(groups)]},
        fields=["name", "course", "schedule_date", "from_time", "to_time", "room", "instructor_name"],
        order_by="schedule_date desc, from_time asc",
        ignore_permissions=True,
        limit_page_length=0,
    )

    course_names = _course_name_map({_clean(row.get("course")) for row in schedules if row.get("course")})
    output = []
    for row in schedules:
        day_ar, day_en = _day_labels(row.get("schedule_date"))
        room_norm = _normalize(row.get("room"))
        entry_type = "lab" if "lab" in room_norm or "مختبر" in room_norm else "lecture"
        course = _clean(row.get("course"))
        output.append(
            {
                "id": row.get("name"),
                "dayAr": day_ar,
                "dayEn": day_en,
                "time": _range_label(row.get("from_time"), row.get("to_time")),
                "courseCode": course,
                "courseNameAr": course_names.get(course, course),
                "courseNameEn": course_names.get(course, course),
                "doctorAr": _clean(row.get("instructor_name")),
                "doctorEn": _clean(row.get("instructor_name")),
                "classroom": _clean(row.get("room")),
                "type": entry_type,
            }
        )
    return output


@frappe.whitelist()
@api_endpoint
def list_student_grades(semester: str | None = None):
    """List student grades from Assessment Result (+ details)."""
    _require_doctype("Assessment Result")
    student = _find_student_by_current_user(required=True)
    student_ids = list(_student_identifiers(student) | {_normalize(student.get("name"))})

    filters: dict[str, Any] = {"student": ["in", student_ids]}
    rows = frappe.get_all(
        "Assessment Result",
        filters=filters,
        fields=[
            "name",
            "course",
            "academic_term",
            "academic_year",
            "total_score",
            "maximum_score",
            "grade",
            "student",
            "modified",
        ],
        order_by="modified desc",
        ignore_permissions=True,
        limit_page_length=0,
    )

    if semester:
        semester_norm = _normalize(semester)
        rows = [
            row
            for row in rows
            if semester_norm in _normalize(row.get("academic_term"))
            or semester_norm in _normalize(row.get("academic_year"))
            or semester_norm in _normalize(f"{row.get('academic_year')} {row.get('academic_term')}")
        ]

    course_names = _course_name_map({_clean(row.get("course")) for row in rows if row.get("course")})

    # Build course schedule map for attendance by course.
    course_schedule_ids_by_course: dict[str, set[str]] = defaultdict(set)
    if frappe.db.exists("DocType", "Student Group Student") and frappe.db.exists("DocType", "Course Schedule"):
        groups = frappe.get_all(
            "Student Group Student",
            filters={"student": ["in", student_ids]},
            fields=["parent"],
            ignore_permissions=True,
            limit_page_length=0,
        )
        group_names = {_clean(row.get("parent")) for row in groups if row.get("parent")}
        if group_names:
            schedules = frappe.get_all(
                "Course Schedule",
                filters={"student_group": ["in", list(group_names)]},
                fields=["name", "course"],
                ignore_permissions=True,
                limit_page_length=0,
            )
            for schedule in schedules:
                course = _clean(schedule.get("course"))
                name = _clean(schedule.get("name"))
                if course and name:
                    course_schedule_ids_by_course[course].add(name)

    output = []
    for row in rows:
        detail_rows = []
        if frappe.db.exists("DocType", "Assessment Result Detail"):
            detail_rows = frappe.get_all(
                "Assessment Result Detail",
                filters={"parent": row["name"]},
                fields=["idx", "score", "maximum_score"],
                order_by="idx asc",
                ignore_permissions=True,
                limit_page_length=0,
            )

        coursework = 0.0
        midterm = 0.0
        final = 0.0
        if len(detail_rows) >= 3:
            coursework = _to_float(detail_rows[0].get("score"))
            midterm = _to_float(detail_rows[1].get("score"))
            final = _to_float(detail_rows[2].get("score"))
        elif len(detail_rows) == 2:
            midterm = _to_float(detail_rows[0].get("score"))
            final = _to_float(detail_rows[1].get("score"))
        elif len(detail_rows) == 1:
            final = _to_float(detail_rows[0].get("score"))
        else:
            final = _to_float(row.get("total_score"))

        course = _clean(row.get("course"))
        attendance = _attendance_percent(set(student_ids), course_schedule_ids_by_course.get(course, set()))

        semester_value = " / ".join([_clean(row.get("academic_year")), _clean(row.get("academic_term"))]).strip(" /")
        grade = _clean(row.get("grade"))
        total_score = _to_float(row.get("total_score"))
        status = "in_progress"
        if grade:
            status = "pass" if GRADE_POINTS.get(grade, 0) > 0 else "fail"

        output.append(
            {
                "id": row.get("name"),
                "courseId": course,
                "courseCode": course,
                "courseNameAr": course_names.get(course, course),
                "courseNameEn": course_names.get(course, course),
                "creditHours": 0,
                "semester": semester_value,
                "semesterAr": semester_value,
                "semesterEn": semester_value,
                "attendance": attendance,
                "coursework": round(coursework, 2),
                "midterm": round(midterm, 2),
                "final": round(final, 2),
                "total": round(total_score, 2),
                "grade": grade,
                "points": GRADE_POINTS.get(grade, 0.0),
                "status": status,
            }
        )

    return output


@frappe.whitelist()
@api_endpoint
def get_student_finance():
    """Get student finance summary from Fees/Sales Invoice/Payment Entry."""
    student = _find_student_by_current_user(required=True)
    student_ids = list(_student_identifiers(student) | {_normalize(student.get("name"))})

    fees_rows = []
    if frappe.db.exists("DocType", "Fees"):
        fees_rows = frappe.get_all(
            "Fees",
            filters={"student": ["in", student_ids]},
            fields=[
                "name",
                "grand_total",
                "outstanding_amount",
                "posting_date",
                "due_date",
                "academic_term",
                "academic_year",
                "docstatus",
            ],
            order_by="posting_date desc",
            ignore_permissions=True,
            limit_page_length=0,
        )

    invoice_rows = []
    if frappe.db.exists("DocType", "Sales Invoice"):
        invoice_rows = frappe.get_all(
            "Sales Invoice",
            filters={"student": ["in", student_ids]},
            fields=["name", "grand_total", "outstanding_amount", "posting_date", "due_date", "status", "docstatus"],
            order_by="posting_date desc",
            ignore_permissions=True,
            limit_page_length=0,
        )

    payments = []
    if frappe.db.exists("DocType", "Payment Entry"):
        payments = frappe.get_all(
            "Payment Entry",
            filters={"party_type": "Student", "party": ["in", student_ids], "docstatus": 1},
            fields=["name", "party", "paid_amount", "received_amount", "posting_date", "mode_of_payment"],
            order_by="posting_date desc",
            ignore_permissions=True,
            limit_page_length=0,
        )

    total_fees = sum(_to_float(row.get("grand_total")) for row in fees_rows) + sum(
        _to_float(row.get("grand_total")) for row in invoice_rows
    )
    total_remaining = sum(_to_float(row.get("outstanding_amount")) for row in fees_rows) + sum(
        _to_float(row.get("outstanding_amount")) for row in invoice_rows
    )
    total_paid = sum(max(_to_float(row.get("paid_amount")), _to_float(row.get("received_amount"))) for row in payments)
    if total_paid <= 0:
        total_paid = max(total_fees - total_remaining, 0)

    installments = []
    for idx, row in enumerate(fees_rows, start=1):
        total_amount = _to_float(row.get("grand_total"))
        remaining = _to_float(row.get("outstanding_amount"))
        paid = max(total_amount - remaining, 0)
        due_date = row.get("due_date")
        status = "pending"
        if remaining <= 0:
            status = "paid"
        elif paid > 0:
            status = "partial"
        elif due_date and due_date < datetime.utcnow().date():
            status = "overdue"

        semester = " / ".join([_clean(row.get("academic_year")), _clean(row.get("academic_term"))]).strip(" /")
        installments.append(
            {
                "id": row.get("name"),
                "installmentNumber": idx,
                "amountTotal": round(total_amount, 2),
                "amountPaid": round(paid, 2),
                "amountRemaining": round(remaining, 2),
                "dueDate": _iso(due_date),
                "paidDate": _iso(row.get("posting_date")) if status == "paid" else None,
                "status": status,
                "semester": semester,
            }
        )

    payment_items = []
    for row in payments:
        amount = max(_to_float(row.get("paid_amount")), _to_float(row.get("received_amount")))
        method_ar, method_en = _payment_method_labels(row.get("mode_of_payment"))
        payment_items.append(
            {
                "id": row.get("name"),
                "receiptNumber": row.get("name"),
                "amount": round(amount, 2),
                "date": _iso(row.get("posting_date")),
                "method": "cash",
                "methodAr": method_ar,
                "methodEn": method_en,
                "descriptionAr": "دفعة رسوم دراسية",
                "descriptionEn": "Tuition fee payment",
                "installmentId": None,
            }
        )

    return {
        "totalFees": round(total_fees, 2),
        "totalPaid": round(total_paid, 2),
        "totalRemaining": round(max(total_remaining, 0), 2),
        "discountAmount": 0,
        "discountType": None,
        "installments": installments,
        "payments": payment_items,
    }


@frappe.whitelist()
@api_endpoint
def list_student_materials(courseId: str | None = None):
    """List student materials from course attachments and student attachments."""
    _require_doctype("File")
    student = _find_student_by_current_user(required=True)
    _, _, course_codes = _student_course_rows(student)

    files: list[dict] = []
    if course_codes:
        course_files = frappe.get_all(
            "File",
            filters={"attached_to_doctype": "Course", "attached_to_name": ["in", list(course_codes)]},
            fields=["name", "file_name", "file_url", "file_size", "creation", "attached_to_name"],
            order_by="creation desc",
            ignore_permissions=True,
            limit_page_length=500,
        )
        for row in course_files:
            files.append(_serialize_material(row, course_id=_clean(row.get("attached_to_name"))))

    student_name = _clean(student.get("name"))
    if student_name:
        student_files = frappe.get_all(
            "File",
            filters={"attached_to_doctype": "Student", "attached_to_name": student_name},
            fields=["name", "file_name", "file_url", "file_size", "creation", "attached_to_name"],
            order_by="creation desc",
            ignore_permissions=True,
            limit_page_length=100,
        )
        for row in student_files:
            files.append(_serialize_material(row, course_id=courseId or ""))

    output = []
    for item in files:
        output.append(
            {
                "id": item["id"],
                "courseId": item.get("courseId") or "",
                "courseCode": item.get("courseId") or "",
                "titleAr": item.get("titleAr"),
                "titleEn": item.get("titleEn"),
                "descriptionAr": item.get("descriptionAr"),
                "descriptionEn": item.get("descriptionEn"),
                "type": item.get("type") if item.get("type") in {"lecture", "assignment", "resource", "video", "exam"} else "resource",
                "fileName": item.get("fileName"),
                "fileSize": item.get("fileSize"),
                "uploadDate": item.get("uploadDate"),
                "downloadCount": item.get("downloadCount", 0),
                "fileUrl": item.get("fileUrl"),
            }
        )

    if courseId:
        course_key = _normalize(courseId)
        output = [row for row in output if _normalize(row.get("courseId")) == course_key]

    seen = set()
    deduped = []
    for row in output:
        if row["id"] in seen:
            continue
        seen.add(row["id"])
        deduped.append(row)
    return deduped


@frappe.whitelist()
@api_endpoint
def list_student_announcements(courseId: str | None = None):
    """List course announcements visible to the current student."""
    _require_doctype("Communication")
    student = _find_student_by_current_user(required=True)
    _, _, course_codes = _student_course_rows(student)
    allowed_courses = {_clean(code) for code in course_codes if _clean(code)}
    if not allowed_courses:
        return []

    selected_course = _clean(courseId or frappe.form_dict.get("courseId"))
    if selected_course:
        if selected_course not in allowed_courses:
            raise ApiError("FORBIDDEN", "Course is not assigned to current student", status_code=403)
        allowed_courses = {selected_course}

    rows = frappe.get_all(
        "Communication",
        filters={"reference_doctype": "Course", "reference_name": ["in", sorted(allowed_courses)]},
        fields=["name", "subject", "content", "sender", "reference_doctype", "reference_name", "communication_date", "creation"],
        order_by="creation desc",
        ignore_permissions=True,
        limit_page_length=500,
    )
    output = []
    for row in rows:
        if not _is_doctor_announcement_row(row):
            continue
        output.append(_serialize_doctor_announcement(row))
    return output


@frappe.whitelist()
@api_endpoint
def list_student_notifications():
    """List student notifications from Notification Log and ToDo."""
    student = _find_student_by_current_user(required=True)
    notifications = _notifications_for_current_user(student_row=student)

    output = []
    for item in notifications:
        output.append(
            {
                "id": item["id"],
                "titleAr": item["titleAr"],
                "titleEn": item["titleEn"],
                "messageAr": item["messageAr"],
                "messageEn": item["messageEn"],
                "type": item["type"] if item["type"] in {"announcement", "grade", "payment", "course", "system"} else "system",
                "date": item["date"],
                "isRead": item["isRead"],
            }
        )
    return output


@frappe.whitelist()
@api_endpoint
def mark_student_notification_read(notification_id: str):
    """Mark student notification as read."""
    return _mark_notification(notification_id)


@frappe.whitelist()
@api_endpoint
def list_conversations():
    """List chat conversations for current student/doctor from Communication."""
    identity = _user_identity()
    current_ids = _current_message_identities()
    student_row = _find_student_by_current_user(required=False)
    view = _normalize(frappe.form_dict.get("view"))
    has_doctor_role = bool(identity["roles"].intersection(DOCTOR_PORTAL_ROLES))
    is_student_view = False
    if view == "student":
        if not student_row:
            raise ApiError("NOT_FOUND", "Student profile not found", status_code=404)
        is_student_view = True
    elif view == "doctor":
        _ensure_doctor_context(require_mapping=True)
    elif student_row and not has_doctor_role:
        is_student_view = True
    elif has_doctor_role:
        _ensure_doctor_context(require_mapping=True)
    elif student_row:
        is_student_view = True
    else:
        raise ApiError("FORBIDDEN", "No conversation access for current account", status_code=403)

    rows = _query_messages_for_current_user()
    grouped: dict[str, dict] = {}

    for row in rows:
        reference_student = _clean(row.get("reference_name"))
        if not reference_student:
            continue

        student_ref = _find_student_by_identifier(reference_student)
        if not student_ref:
            continue

        student_ref_name = _clean(student_ref.get("name"))
        student_ref_user_ids = _student_user_ids(student_ref)
        recipients = {_normalize(value) for value in _split_csv(row.get("recipients"))}
        unread = 1 if recipients.intersection(current_ids) and not int(row.get("read_by_recipient") or 0) else 0

        if is_student_view:
            if not current_ids.intersection(student_ref_user_ids) and _normalize(student_ref_name) not in current_ids:
                continue
            counterpart = _counterpart_from_message(row, current_ids)
            if not counterpart:
                continue
            doctor_id = counterpart
            conv_id = _conversation_id(student_ref_name, doctor_id)
            doctor_name, doctor_email = _resolve_user_display(doctor_id)
            key = conv_id
            existing = grouped.get(key)
            if not existing:
                grouped[key] = {
                    "id": conv_id,
                    "studentId": student_ref_name,
                    "studentName": _clean(student_ref.get("student_name") or student_ref_name),
                    "studentAcademicNumber": _clean(student_ref.get("student_email_id") or student_ref_name),
                    "doctorId": doctor_id,
                    "doctorName": doctor_name,
                    "doctorEmail": doctor_email,
                    "lastMessage": _clean(row.get("content")),
                    "lastMessageDate": _iso(row.get("communication_date") or row.get("creation")),
                    "unreadCount": unread,
                }
            else:
                existing["unreadCount"] += unread
            continue

        doctor_id = identity["email"] or identity["user"]
        conv_id = _conversation_id(student_ref_name, doctor_id)
        key = conv_id
        existing = grouped.get(key)
        if not existing:
            grouped[key] = {
                "id": conv_id,
                "studentId": student_ref_name,
                "studentName": _clean(student_ref.get("student_name") or student_ref_name),
                "studentAcademicNumber": _clean(student_ref.get("student_email_id") or student_ref_name),
                "doctorId": doctor_id,
                "doctorName": identity["full_name"],
                "doctorEmail": identity["email"],
                "lastMessage": _clean(row.get("content")),
                "lastMessageDate": _iso(row.get("communication_date") or row.get("creation")),
                "unreadCount": unread,
            }
        else:
            existing["unreadCount"] += unread

    conversations = list(grouped.values())
    conversations.sort(key=lambda row: row.get("lastMessageDate") or "", reverse=True)
    return conversations


@frappe.whitelist()
@api_endpoint
def get_conversation(conversation_id: str):
    """Get chat messages in a conversation."""
    student_id, doctor_id = _parse_conversation_id(conversation_id)

    student_row = _find_student_by_identifier(student_id)
    if not student_row:
        raise ApiError("NOT_FOUND", "Conversation student not found", status_code=404)

    access = _ensure_conversation_access(student_row, doctor_id)
    doctor_identity = access["doctor_identity"]
    student_ids = access["student_ids"]

    rows = frappe.get_all(
        "Communication",
        filters={"reference_doctype": "Student", "reference_name": student_row["name"]},
        fields=[
            "name",
            "sender",
            "recipients",
            "content",
            "communication_date",
            "creation",
            "read_by_recipient",
        ],
        order_by="communication_date asc, creation asc",
        ignore_permissions=True,
        limit_page_length=500,
    )

    messages = []
    for row in rows:
        sender = _normalize(row.get("sender"))
        recipients = {_normalize(value) for value in _split_csv(row.get("recipients"))}
        if sender not in ({doctor_identity} | student_ids) and not recipients.intersection({doctor_identity} | student_ids):
            continue
        messages.append(_serialize_chat_message(row, conversation_id, doctor_identity, student_ids))

    return messages


@frappe.whitelist()
@api_endpoint
def send_message(**payload):
    """Send chat message and store it in Communication."""
    identity = _user_identity()
    text = _clean(payload.get("text"))
    conversation_id = _clean(payload.get("conversationId"))
    if not text:
        raise ApiError("VALIDATION_ERROR", "text is required", status_code=400)
    if not conversation_id:
        raise ApiError("VALIDATION_ERROR", "conversationId is required", status_code=400)

    student_id, doctor_id = _parse_conversation_id(conversation_id)
    student_row = _find_student_by_identifier(student_id)
    if not student_row:
        raise ApiError("NOT_FOUND", "Student not found for conversation", status_code=404)

    access = _ensure_conversation_access(student_row, doctor_id)
    student_ids = access["student_ids"]
    doctor_identity = access["doctor_identity"]
    current_ids = access["current_ids"]

    sender_type = _clean(payload.get("senderType"))
    if sender_type == "student":
        if not access["is_student_participant"]:
            raise ApiError("FORBIDDEN", "Current user is not the student of this conversation", status_code=403)
        recipient = doctor_id
    elif sender_type == "doctor":
        _ensure_doctor_context(require_mapping=True)
        if doctor_identity not in current_ids and not access["is_admin"]:
            raise ApiError("FORBIDDEN", "Current user is not the doctor of this conversation", status_code=403)
        recipient = student_row.get("user") or student_row.get("student_email_id") or student_row.get("name")
    else:
        raise ApiError("VALIDATION_ERROR", "senderType must be student or doctor", status_code=400)

    sender = identity["email"] or identity["user"]
    subject = f"Portal Conversation {student_row.get('name')}"

    doc = frappe.get_doc(
        {
            "doctype": "Communication",
            "subject": subject,
            "communication_medium": "Chat",
            "communication_type": "Communication",
            "sender": sender,
            "recipients": recipient,
            "content": text,
            "reference_doctype": "Student",
            "reference_name": student_row.get("name"),
            "read_by_recipient": 0,
            "sent_or_received": "Sent",
            "status": "Linked",
        }
    )
    doc.insert(ignore_permissions=True)
    frappe.db.commit()

    return {
        "id": doc.name,
        "conversationId": conversation_id,
        "senderId": sender,
        "senderType": sender_type,
        "senderName": _clean(payload.get("senderName")) or identity["full_name"],
        "text": text,
        "createdAt": _iso(doc.creation),
        "isRead": False,
    }


@frappe.whitelist()
@api_endpoint
def mark_conversation_read(conversation_id: str):
    """Mark all received messages in a conversation as read for current user."""
    student_id, doctor_id = _parse_conversation_id(conversation_id)
    student_row = _find_student_by_identifier(student_id)
    if not student_row:
        raise ApiError("NOT_FOUND", "Conversation student not found", status_code=404)

    access = _ensure_conversation_access(student_row, doctor_id)
    current_ids = access["current_ids"]
    recipient_filters = []
    params: list[Any] = []
    for identifier in sorted(current_ids):
        recipient_filters.append("lower(ifnull(recipients, '')) like %s")
        params.append(f"%{identifier}%")

    if not recipient_filters:
        return {"updated": 0}

    sql = f"""
        update `tabCommunication`
        set read_by_recipient = 1
        where reference_doctype = 'Student'
          and reference_name = %s
          and ({' or '.join(recipient_filters)})
          and ifnull(read_by_recipient, 0) = 0
    """
    frappe.db.sql(sql, tuple([student_row["name"], *params]))
    frappe.db.commit()
    return {"updated": True}


@frappe.whitelist()
@api_endpoint
def unread_message_count():
    """Count unread messages for current user from Communication recipients."""
    ids = sorted(_current_message_identities())
    if not ids:
        return {"count": 0}

    where = []
    params: list[Any] = []
    for identifier in ids:
        where.append("lower(ifnull(recipients, '')) like %s")
        params.append(f"%{identifier}%")

    sql = f"""
        select count(*) as total
        from `tabCommunication`
        where ({' or '.join(where)})
          and ifnull(read_by_recipient, 0) = 0
    """
    row = frappe.db.sql(sql, tuple(params), as_dict=True)
    return {"count": int((row[0] or {}).get("total") or 0) if row else 0}
