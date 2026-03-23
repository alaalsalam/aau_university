# -*- coding: utf-8 -*-
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import frappe


PROTECTED_USERS = {
    "Administrator",
    "Guest",
    "demo@example.com",
}


@dataclass
class SeedResult:
    deleted_students: int = 0
    deleted_instructors: int = 0
    deleted_faculty: int = 0
    deleted_users: int = 0
    created_students: int = 0
    created_instructors: int = 0
    created_faculty: int = 0
    created_users: int = 0


def reset_people_data() -> dict[str, Any]:
    """Remove old student/teacher data and seed realistic AAU demo data."""

    _ensure_roles(["Student", "Instructor"]) 

    result = SeedResult()

    linked_users = _collect_linked_users()

    # 1) purge old academic people records
    result.deleted_students = _delete_all_docs("Student")
    result.deleted_instructors = _delete_all_docs("Instructor")
    if frappe.db.exists("DocType", "Faculty Members"):
        result.deleted_faculty = _delete_all_docs("Faculty Members")

    # 2) remove old linked users (except protected/system users)
    result.deleted_users = _delete_linked_users(linked_users)

    # 3) seed canonical data
    colleges = _get_colleges()
    departments = _seed_departments(colleges)

    instructor_rows = _seed_instructors(departments)
    result.created_instructors = len(instructor_rows)
    result.created_users += len(instructor_rows)

    student_rows = _seed_students()
    result.created_students = len(student_rows)
    result.created_users += len(student_rows)

    faculty_created = _seed_faculty(instructor_rows, colleges)
    result.created_faculty = faculty_created

    frappe.db.commit()
    frappe.clear_cache()

    return {
        "ok": True,
        "stats": result.__dict__,
        "final_counts": {
            "Student": frappe.db.count("Student"),
            "Instructor": frappe.db.count("Instructor"),
            "Faculty Members": frappe.db.count("Faculty Members") if frappe.db.exists("DocType", "Faculty Members") else 0,
        },
    }


def _ensure_roles(role_names: list[str]) -> None:
    for role in role_names:
        if not frappe.db.exists("Role", role):
            frappe.get_doc({"doctype": "Role", "role_name": role, "desk_access": 0}).insert(ignore_permissions=True)


def _collect_linked_users() -> set[str]:
    users: set[str] = set()
    if frappe.db.exists("DocType", "Student"):
        for row in frappe.get_all("Student", fields=["user", "student_email_id"]):
            if row.get("user"):
                users.add(row["user"])
            if row.get("student_email_id"):
                users.add(row["student_email_id"])
    if frappe.db.exists("DocType", "Instructor"):
        for row in frappe.get_all("Instructor", fields=["custom_user_id"]):
            if row.get("custom_user_id"):
                users.add(row["custom_user_id"])
    return {u for u in users if u and u not in PROTECTED_USERS}


def _delete_all_docs(doctype_name: str) -> int:
    if not frappe.db.exists("DocType", doctype_name):
        return 0

    names = frappe.get_all(doctype_name, pluck="name", limit_page_length=100000)
    deleted = 0
    for name in names:
        try:
            frappe.delete_doc(doctype_name, name, ignore_permissions=True, force=True)
            deleted += 1
        except Exception:
            # Fallback hard delete for corrupted legacy rows
            frappe.db.delete(doctype_name, {"name": name})
            deleted += 1
    return deleted


def _delete_linked_users(user_emails: set[str]) -> int:
    deleted = 0
    for email in sorted(user_emails):
        if email in PROTECTED_USERS:
            continue
        if not frappe.db.exists("User", email):
            continue
        # Do not remove privileged accounts
        roles = set(frappe.get_roles(email))
        if "System Manager" in roles:
            continue
        try:
            frappe.delete_doc("User", email, ignore_permissions=True, force=True)
            deleted += 1
        except Exception:
            pass
    return deleted


def _seed_departments(colleges: list[str]) -> list[str]:
    if not frappe.db.exists("DocType", "Academic Departments"):
        return []

    names = [
        "علوم الحاسوب",
        "نظم المعلومات",
        "المحاسبة",
        "اللغة الإنجليزية",
        "الطب البشري",
        "طب الأسنان",
    ]
    out: list[str] = []
    for dep in names:
        existing = frappe.db.get_value("Academic Departments", {"department_name": dep}, "name")
        if existing:
            out.append(existing)
            continue
        payload = {
            "doctype": "Academic Departments",
            "department_name": dep,
            "description": f"قسم {dep}",
            "is_active": 1,
        }
        if colleges:
            payload["college"] = colleges[len(out) % len(colleges)]

        doc = frappe.get_doc(
            {
                **payload,
            }
        ).insert(ignore_permissions=True)
        out.append(doc.name)
    return out


def _get_colleges() -> list[str]:
    if not frappe.db.exists("DocType", "Colleges"):
        return []
    rows = frappe.get_all(
        "Colleges",
        fields=["name"],
        filters={"is_active": 1},
        order_by="display_order asc, name asc",
        limit_page_length=100000,
    )
    if not rows:
        rows = frappe.get_all("Colleges", fields=["name"], order_by="name asc", limit_page_length=100000)
    return [r.name for r in rows]


def _create_user(email: str, full_name: str, role: str) -> None:
    if frappe.db.exists("User", email):
        user = frappe.get_doc("User", email)
    else:
        user = frappe.new_doc("User")
        user.email = email

    user.first_name = full_name.split(" ")[0]
    user.full_name = full_name
    user.enabled = 1
    user.send_welcome_email = 0
    user.user_type = "System User"
    user.new_password = "AAU@12345"
    if user.is_new():
        user.insert(ignore_permissions=True)
    else:
        user.save(ignore_permissions=True)

    if not frappe.db.exists("Has Role", {"parent": email, "parenttype": "User", "role": role}):
        user.append("roles", {"role": role})
        user.save(ignore_permissions=True)


def _seed_instructors(departments: list[str]) -> list[dict[str, str]]:
    if not frappe.db.exists("DocType", "Instructor"):
        return []

    instructors = [
        "د. أحمد العنسي",
        "د. سارة الشامي",
        "د. مازن الكبسي",
        "د. ندى المتوكل",
        "د. حسام القباطي",
        "د. ريم العريقي",
        "د. باسم العلفي",
        "د. هدى الجائفي",
    ]

    rows: list[dict[str, str]] = []
    for idx, name in enumerate(instructors, start=1):
        email = f"instructor{idx:02d}@aau.edu.ye"
        _create_user(email, name, "Instructor")

        doc = frappe.get_doc(
            {
                "doctype": "Instructor",
                "instructor_name": name,
                "status": "Active",
                # Instructor.department links ERPNext Department doctype, keep it empty unless mapped explicitly.
                "department": None,
                "custom_user_id": email,
            }
        ).insert(ignore_permissions=True)
        rows.append({"name": doc.name, "full_name": name, "email": email})
    return rows


def _seed_students() -> list[str]:
    if not frappe.db.exists("DocType", "Student"):
        return []

    student_names = [
        "محمد السريحي",
        "ليان الظاهري",
        "عبدالله الغزالي",
        "هديل النعيمي",
        "مروان السقاف",
        "رنا الديلمي",
        "يزن الشرعبي",
        "أفنان الحسني",
        "عمر البخيتي",
        "شهد العامري",
        "خالد المقبلي",
        "رحمة السقاف",
        "صهيب الحكيمي",
        "سلمى المقرمي",
        "قيس الحداد",
        "آية الطيب",
        "ماجد الكاف",
        "نرمين العريقي",
        "زياد السنباني",
        "إسراء الجرموزي",
        "أنس الحيمي",
        "ميار الآنسي",
        "رامي الفقيه",
        "دينا الورد",
    ]

    created: list[str] = []
    branch_name = _get_default_branch()
    for idx, full_name in enumerate(student_names, start=1):
        email = f"student{idx:03d}@aau.edu.ye"
        _create_user(email, full_name, "Student")

        first_name, *rest = full_name.split(" ")
        last_name = rest[-1] if rest else first_name
        doc = frappe.new_doc("Student")
        doc.first_name = first_name
        doc.last_name = last_name
        doc.student_name = full_name
        doc.full_name = full_name
        doc.student_email_id = email
        doc.user = email
        doc.enabled = 1
        doc.student_status = "Enabled"
        doc.joining_date = frappe.utils.nowdate()
        doc.mobile = f"770{idx:06d}"[:9]
        if branch_name and frappe.db.has_column("Student", "custom_branch"):
            doc.custom_branch = branch_name
        # Student.program links Education Program doctype; keep empty to avoid invalid legacy links.
        doc.insert(ignore_permissions=True)
        created.append(doc.name)

    return created


def _seed_faculty(instructor_rows: list[dict[str, str]], colleges: list[str]) -> int:
    if not frappe.db.exists("DocType", "Faculty Members"):
        return 0

    created = 0
    titles = ["أستاذ مساعد", "محاضر", "أستاذ مشارك", "معيد"]
    for idx, row in enumerate(instructor_rows, start=1):
        doc = frappe.get_doc(
            {
                "doctype": "Faculty Members",
                "full_name": row["full_name"],
                "academic_title": titles[(idx - 1) % len(titles)],
                "department": "",
                "biography": f"عضو هيئة تدريس بخبرة أكاديمية وتطبيقية في تخصص {idx}.",
                "is_active": 1,
                "linked_college": colleges[(idx - 1) % len(colleges)] if colleges else None,
            }
        ).insert(ignore_permissions=True)
        created += 1
    return created


def _get_default_branch() -> str | None:
    if not frappe.db.exists("DocType", "Branch"):
        return None
    return frappe.db.get_value("Branch", {}, "name") or None
