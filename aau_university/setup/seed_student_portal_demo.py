# -*- coding: utf-8 -*-
from __future__ import annotations

from datetime import date
from typing import Any

import frappe
from frappe.model.naming import make_autoname
from frappe.utils import nowdate
from frappe.utils.file_manager import save_file


STUDENT_NAME = "EDU-STU-2026-00024"
ACADEMIC_YEAR = "2025"
ACADEMIC_TERM = "الفصل الدراسي الأول - 2025"
GROUP_NAME = "AAU-PORTAL-DEMO-2025-24"
GRADE_SCALE = "التقدير"
ASSESSMENT_CRITERION = "المعيار الاول"

COURSE_BLUEPRINTS = [
    {
        "course_name": "مقدمة في تقنية المعلومات",
        "description": "مدخل عملي لأساسيات الحاسوب، الأنظمة، وأخلاقيات استخدام التقنية.",
        "instructor": "د. أحمد العنسي",
        "room": "HTL-ROOM-2023-00002",
        "schedules": [
            {"date": "2025-04-06", "from_time": "09:00:00", "to_time": "10:30:00"},
            {"date": "2025-04-08", "from_time": "09:00:00", "to_time": "10:30:00"},
        ],
        "grade": {"total_score": 91, "maximum_score": 100, "grade": "A"},
        "materials": [
            ("خطة المقرر.txt", "خطة المقرر: مقدمة في تقنية المعلومات\nالأسبوع 1: مدخل إلى الأنظمة.\nالأسبوع 2: مكونات الحاسوب."),
            ("واجب 1.txt", "واجب قصير: قارن بين أنظمة التشغيل المكتبية والخوادم."),
        ],
    },
    {
        "course_name": "أساسيات البرمجة",
        "description": "مفاهيم البرمجة الهيكلية، المتغيرات، الشروط، والحلقات مع تطبيقات عملية.",
        "instructor": "د. سارة الشامي",
        "room": "HTL-ROOM-2023-00003",
        "schedules": [
            {"date": "2025-04-07", "from_time": "11:00:00", "to_time": "12:30:00"},
            {"date": "2025-04-09", "from_time": "11:00:00", "to_time": "12:30:00"},
        ],
        "grade": {"total_score": 84, "maximum_score": 100, "grade": "B+"},
        "materials": [
            ("المحاضرة الأولى.txt", "المحاضرة الأولى: المتغيرات وأنواع البيانات.\nتمارين تطبيقية على Python."),
        ],
    },
    {
        "course_name": "مبادئ قواعد البيانات",
        "description": "تصميم الجداول والعلاقات واستعلامات SQL الأساسية مع تطبيقات على قواعد البيانات.",
        "instructor": "د. مازن الكبسي",
        "room": "HTL-ROOM-2023-00004",
        "schedules": [
            {"date": "2025-04-10", "from_time": "08:30:00", "to_time": "10:00:00"},
            {"date": "2025-04-12", "from_time": "08:30:00", "to_time": "10:00:00"},
        ],
        "grade": {"total_score": 88, "maximum_score": 100, "grade": "A-"},
        "materials": [
            ("مختبر SQL.txt", "تجربة مختبر: إنشاء قاعدة بيانات بسيطة وإنشاء ثلاث جداول مرتبطة."),
        ],
    },
]


def seed_student_portal_demo(student_name: str = STUDENT_NAME) -> dict[str, Any]:
    _ensure_dependencies()

    student = frappe.get_doc("Student", student_name)
    program_name = student.program or "دورة it"
    if not frappe.db.exists("Program", program_name):
        raise frappe.ValidationError(f"Program not found: {program_name}")

    course_names = [_ensure_course(course_spec) for course_spec in COURSE_BLUEPRINTS]
    program_enrollment = _ensure_program_enrollment(student, program_name, course_names)
    course_enrollments = _ensure_course_enrollments(student, program_enrollment, course_names)
    student_group = _ensure_student_group(student, program_name)
    schedules = _ensure_course_schedules(student_group, course_names)
    assessment_results = _ensure_assessment_results(student, program_name, student_group, course_names)
    material_files = _ensure_course_materials(course_names)

    frappe.db.commit()
    frappe.clear_cache()

    return {
        "ok": True,
        "student": student.name,
        "program": program_name,
        "program_enrollment": program_enrollment,
        "course_count": len(course_names),
        "course_enrollments": course_enrollments,
        "student_group": student_group,
        "schedule_count": len(schedules),
        "assessment_results": assessment_results,
        "materials_count": len(material_files),
    }


def inspect_student_portal_demo(student_name: str = STUDENT_NAME) -> dict[str, Any]:
    return {
        "student": student_name,
        "program_enrollments": frappe.db.count(
            "Program Enrollment",
            {"student": student_name, "academic_year": ACADEMIC_YEAR, "academic_term": ACADEMIC_TERM},
        ),
        "course_enrollments": frappe.db.count("Course Enrollment", {"student": student_name}),
        "group_links": frappe.db.count("Student Group Student", {"student": student_name}),
        "schedules": frappe.db.count("Course Schedule", {"student_group": GROUP_NAME}),
        "results": frappe.db.count("Assessment Result", {"student": student_name}),
        "materials": frappe.db.count("File", {"attached_to_doctype": "Course", "attached_to_name": ["in", [spec["course_name"] for spec in COURSE_BLUEPRINTS]]}),
    }


def _ensure_dependencies() -> None:
    required = ["Student", "Program", "Course", "Program Enrollment", "Course Enrollment", "Student Group", "Course Schedule", "Instructor", "Room", "File"]
    for doctype in required:
        if not frappe.db.exists("DocType", doctype):
            raise frappe.ValidationError(f"Required DocType is missing: {doctype}")


def _ensure_course(course_spec: dict[str, Any]) -> str:
    existing = frappe.db.get_value("Course", {"course_name": course_spec["course_name"]}, "name")
    if existing:
        if course_spec.get("description") and frappe.db.has_column("Course", "description"):
            frappe.db.set_value("Course", existing, "description", course_spec["description"], update_modified=False)
        return existing

    doc = frappe.get_doc(
        {
            "doctype": "Course",
            "course_name": course_spec["course_name"],
            "description": course_spec.get("description"),
            "default_grading_scale": GRADE_SCALE if frappe.db.exists("Grading Scale", GRADE_SCALE) else None,
        }
    )
    doc.insert(ignore_permissions=True)
    return doc.name


def _ensure_program_enrollment(student, program_name: str, course_names: list[str]) -> str:
    existing = frappe.db.get_value(
        "Program Enrollment",
        {
            "student": student.name,
            "program": program_name,
            "academic_year": ACADEMIC_YEAR,
            "academic_term": ACADEMIC_TERM,
        },
        "name",
    )
    if existing:
        doc = frappe.get_doc("Program Enrollment", existing)
        current_courses = {row.course for row in doc.courses}
        for course_name in course_names:
            if course_name not in current_courses:
                doc.append("courses", {"course": course_name, "course_name": course_name})
        doc.save(ignore_permissions=True)
        return doc.name

    doc = frappe.get_doc(
        {
            "doctype": "Program Enrollment",
            "student": student.name,
            "student_name": student.student_name,
            "program": program_name,
            "academic_year": ACADEMIC_YEAR,
            "academic_term": ACADEMIC_TERM,
            "enrollment_date": nowdate(),
            "courses": [{"course": name, "course_name": name} for name in course_names],
        }
    )
    doc.insert(ignore_permissions=True)
    return doc.name


def _ensure_course_enrollments(student, program_enrollment: str, course_names: list[str]) -> list[str]:
    out: list[str] = []
    for course_name in course_names:
        existing = frappe.db.get_value(
            "Course Enrollment",
            {"student": student.name, "course": course_name, "program_enrollment": program_enrollment},
            "name",
        )
        if existing:
            out.append(existing)
            continue
        doc = frappe.get_doc(
            {
                "doctype": "Course Enrollment",
                "program_enrollment": program_enrollment,
                "student": student.name,
                "course": course_name,
                "enrollment_date": nowdate(),
            }
        )
        doc.insert(ignore_permissions=True)
        out.append(doc.name)
    return out


def _ensure_student_group(student, program_name: str) -> str:
    if frappe.db.exists("Student Group", GROUP_NAME):
        doc = frappe.get_doc("Student Group", GROUP_NAME)
    else:
        doc = frappe.get_doc(
            {
                "doctype": "Student Group",
                "academic_year": ACADEMIC_YEAR,
                "academic_term": ACADEMIC_TERM,
                "group_based_on": "Activity",
                "student_group_name": GROUP_NAME,
                "program": program_name,
                "max_strength": 30,
            }
        )

    student_names = {row.student for row in doc.students}
    if student.name not in student_names:
        doc.append(
            "students",
            {"student": student.name, "student_name": student.student_name, "group_roll_number": 1, "active": 1},
        )

    if COURSE_BLUEPRINTS and hasattr(doc, "instructors"):
        instructor_names = {row.instructor for row in doc.instructors}
        for course_spec in COURSE_BLUEPRINTS:
            instructor = course_spec["instructor"]
            if instructor and frappe.db.exists("Instructor", instructor) and instructor not in instructor_names:
                doc.append("instructors", {"instructor": instructor, "instructor_name": instructor})
                instructor_names.add(instructor)

    if doc.is_new():
        doc.insert(ignore_permissions=True)
    else:
        doc.save(ignore_permissions=True)
    return doc.name


def _ensure_course_schedules(student_group: str, course_names: list[str]) -> list[str]:
    created_or_found: list[str] = []
    blueprint_map = {spec["course_name"]: spec for spec in COURSE_BLUEPRINTS}
    for course_name in course_names:
        spec = blueprint_map[course_name]
        for slot in spec["schedules"]:
            existing = frappe.db.get_value(
                "Course Schedule",
                {
                    "student_group": student_group,
                    "course": course_name,
                    "schedule_date": slot["date"],
                    "from_time": slot["from_time"],
                    "to_time": slot["to_time"],
                },
                "name",
            )
            if existing:
                created_or_found.append(existing)
                continue
            doc = frappe.get_doc(
                {
                    "doctype": "Course Schedule",
                    "name": make_autoname("EDU-CSH-.YYYY.-.#####"),
                    "naming_series": "EDU-CSH-.YYYY.-",
                    "student_group": student_group,
                    "instructor": spec["instructor"],
                    "instructor_name": spec["instructor"],
                    "course": course_name,
                    "schedule_date": slot["date"],
                    "room": spec["room"],
                    "from_time": slot["from_time"],
                    "to_time": slot["to_time"],
                    "class_schedule_color": "amber",
                    "title": f"{course_name} by {spec['instructor']}",
                    "color": "#FCF3CF",
                }
            )
            # Bypass custom overlap hooks in this environment; the student portal only reads these rows.
            doc.db_insert(ignore_if_duplicate=True)
            created_or_found.append(doc.name)
    return created_or_found


def _ensure_assessment_results(student, program_name: str, student_group: str, course_names: list[str]) -> list[str]:
    out: list[str] = []
    criterion = ASSESSMENT_CRITERION if frappe.db.exists("Assessment Criteria", ASSESSMENT_CRITERION) else None
    for course_name in course_names:
        spec = next(item for item in COURSE_BLUEPRINTS if item["course_name"] == course_name)
        existing = frappe.db.get_value(
            "Assessment Result",
            {
                "student": student.name,
                "course": course_name,
                "academic_year": ACADEMIC_YEAR,
                "academic_term": ACADEMIC_TERM,
            },
            "name",
        )
        if existing:
            out.append(existing)
            continue

        grade_spec = spec["grade"]
        doc = frappe.get_doc(
            {
                "doctype": "Assessment Result",
                "name": make_autoname("EDU-RES-.YYYY.-.#####"),
                "student": student.name,
                "student_name": student.student_name,
                "student_group": student_group,
                "program": program_name,
                "course": course_name,
                "academic_year": ACADEMIC_YEAR,
                "academic_term": ACADEMIC_TERM,
                "grading_scale": GRADE_SCALE if frappe.db.exists("Grading Scale", GRADE_SCALE) else None,
                "maximum_score": grade_spec["maximum_score"],
                "total_score": grade_spec["total_score"],
                "grade": grade_spec["grade"],
                "comment": "بيانات تجريبية لعرض الدرجات في بوابة الطالب.",
            }
        )
        detail_rows = [
            {"score": round(grade_spec["total_score"] * 0.2, 2), "maximum_score": 20},
            {"score": round(grade_spec["total_score"] * 0.3, 2), "maximum_score": 30},
            {"score": round(grade_spec["total_score"] * 0.5, 2), "maximum_score": 50},
        ]
        if criterion:
            doc.details = [
                {"assessment_criteria": criterion, "score": row["score"], "maximum_score": row["maximum_score"], "grade": grade_spec["grade"]}
                for row in detail_rows
            ]
        else:
            doc.details = []

        # Use db_insert to bypass Assessment Plan validation; the portal only reads these rows.
        doc.db_insert(ignore_if_duplicate=True)
        for idx, row in enumerate(detail_rows, start=1):
            child = frappe.get_doc(
                {
                    "doctype": "Assessment Result Detail",
                    "parent": doc.name,
                    "parenttype": "Assessment Result",
                    "parentfield": "details",
                    "idx": idx,
                    "assessment_criteria": criterion,
                    "score": row["score"],
                    "maximum_score": row["maximum_score"],
                    "grade": grade_spec["grade"],
                }
            )
            child.db_insert(ignore_if_duplicate=False)
        out.append(doc.name)
    return out


def _ensure_course_materials(course_names: list[str]) -> list[str]:
    file_urls: list[str] = []
    for course_name in course_names:
        spec = next(item for item in COURSE_BLUEPRINTS if item["course_name"] == course_name)
        existing_files = set(
            frappe.get_all(
                "File",
                filters={"attached_to_doctype": "Course", "attached_to_name": course_name},
                pluck="file_name",
                ignore_permissions=True,
            )
        )
        for file_name, content in spec.get("materials", []):
            if file_name in existing_files:
                continue
            saved = save_file(
                file_name,
                content.encode("utf-8"),
                "Course",
                course_name,
                is_private=0,
            )
            file_urls.append(saved.file_url)
    return file_urls
