# -*- coding: utf-8 -*-
from __future__ import annotations

import re

import frappe

LOG_PREFIX = "[AAU SCREEN AUDIT]"

MODULE_NAME = "AAU"
MODULES = [MODULE_NAME]


def run(update_existing: bool = True, dry_run: bool = False):
    """
    Audit and fix AAU planned DocTypes.
    - update_existing: create/update DocTypes and fields when True
    - dry_run: report only, no DB changes
    """
    report = _init_report()
    _log(f"START | update_existing={update_existing} dry_run={dry_run}")

    _ensure_module_defs(report, dry_run=dry_run)

    for doctype_name, spec in _doctype_specs().items():
        expected_module = MODULE_NAME
        required_fields = spec["fields"]

        if not frappe.db.exists("DocType", doctype_name):
            report["missing_doctypes"].append(doctype_name)
            if update_existing:
                if dry_run:
                    action = f"WOULD_CREATE DocType: {doctype_name}"
                    report["actions"].append(action)
                    report["would_create_count"] += 1
                    _log(action)
                else:
                    _create_doctype(doctype_name, expected_module, required_fields, report)
                    report["created_count"] += 1
                    _log(f"CREATED DocType: {doctype_name}")
            continue

        doc = frappe.get_doc("DocType", doctype_name)
        doc_changed = False

        if doc.module != expected_module:
            report["wrong_modules"].append(
                f"{doctype_name} (expected {expected_module}, found {doc.module})"
            )
            if update_existing and not dry_run:
                frappe.db.set_value("DocType", doctype_name, "module", expected_module)
                frappe.clear_cache(doctype=doctype_name)
                doc = frappe.get_doc("DocType", doctype_name)
                doc_changed = True

        field_issues, field_changes = _audit_fields(doc, required_fields)
        report["field_issues"].extend([f"{doctype_name}: {issue}" for issue in field_issues])

        if update_existing:
            if dry_run:
                if field_changes or (doc.module != expected_module):
                    action = f"WOULD_UPDATE DocType: {doctype_name}"
                    report["actions"].append(action)
                    report["would_update_count"] += 1
                    _log(action)
            else:
                if _apply_field_changes(doc, field_changes):
                    doc_changed = True

                if _ensure_field_order(doc):
                    doc_changed = True

                if _ensure_system_manager_permission(doc):
                    doc_changed = True

                if doc_changed:
                    doc.save(ignore_permissions=True)
                    frappe.db.commit()
                    action = f"UPDATED DocType: {doctype_name}"
                    report["actions"].append(action)
                    report["updated_count"] += 1
                    _log(action)
                else:
                    action = f"SKIPPED DocType: {doctype_name}"
                    report["actions"].append(action)
                    report["skipped_count"] += 1
                    _log(action)

    _print_report(report)
    _log("COMPLETED")
    return report


def _init_report() -> dict:
    return {
        "missing_doctypes": [],
        "wrong_modules": [],
        "field_issues": [],
        "actions": [],
        "created_count": 0,
        "updated_count": 0,
        "skipped_count": 0,
        "would_create_count": 0,
        "would_update_count": 0,
    }


def _doctype_specs() -> dict:
    default_fields = _default_fields()
    raw_specs = {
        "Home Page": {
            "module": MODULE_NAME,
            "fields": [
                _field("Page Title", "Data", "عنوان الصفحة الرئيسي", reqd=1),
                _field("Hero Description", "Small Text", "نص ترحيبي مختصر"),
                _field("Hero Image", "Attach Image", "صورة الهيدر"),
                _field("Is Published", "Check", "حالة النشر"),
                _field("Display Order", "Int", "ترتيب العرض"),
            ],
        },
        "About University": {
            "module": MODULE_NAME,
            "fields": [
                _field("Title", "Data", "عنوان القسم", reqd=1),
                _field("Description", "Long Text", "وصف عن الجامعة"),
                _field("Image", "Attach Image", "صورة تعريفية"),
                _field("Is Published", "Check", "حالة النشر"),
            ],
        },
        "University Vision and Mission": {
            "module": MODULE_NAME,
            "fields": [
                _field("Vision", "Long Text", "رؤية الجامعة"),
                _field("Mission", "Long Text", "رسالة الجامعة"),
                _field("Values", "Long Text", "القيم المؤسسية"),
                _field("Is Published", "Check", "حالة النشر"),
            ],
        },
        "University Administration": {
            "module": MODULE_NAME,
            "fields": [
                _field("Name", "Data", "اسم المسؤول/الإداري", reqd=1, fieldname="administrator_name"),
                _field("Position", "Data", "المنصب الإداري", reqd=1),
                _field("Biography", "Long Text", "نبذة تعريفية"),
                _field("Photo", "Attach Image", "الصورة"),
                _field("Display Order", "Int", "ترتيب العرض"),
                _field("Is Active", "Check", "حالة التفعيل"),
            ],
        },
        "News": {
            "module": MODULE_NAME,
            "fields": [
                _field("Title", "Data", "عنوان الخبر", reqd=1),
                _field("Summary", "Small Text", "ملخص الخبر"),
                _field("Content", "Long Text", "محتوى الخبر"),
                _field("Featured Image", "Attach Image", "الصورة الرئيسية"),
                _field("Publish Date", "Date", "تاريخ النشر"),
                _field("Is Published", "Check", "منشور"),
                _field("Display Order", "Int", "ترتيب العرض"),
            ],
        },
        "Events": {
            "module": MODULE_NAME,
            "fields": [
                _field("Event Title", "Data", "عنوان الفعالية", reqd=1),
                _field("Description", "Long Text", "وصف الفعالية"),
                _field("Event Date", "Date", "تاريخ الفعالية"),
                _field("Location", "Data", "الموقع"),
                _field("Image", "Attach Image", "الصورة"),
                _field("Is Published", "Check", "منشور"),
                _field("Display Order", "Int", "ترتيب العرض"),
            ],
        },
        "Announcements": {"module": MODULE_NAME, "fields": default_fields},
        "University Centers": {"module": MODULE_NAME, "fields": default_fields},
        "Centers": {
            "module": MODULE_NAME,
            "fields": [
                _field("ID", "Data", "المعرف الفريد", fieldname="id"),
                _field("Title Ar", "Data", "عنوان المركز بالعربية", reqd=1),
                _field("Title En", "Data", "عنوان المركز بالإنجليزية"),
                _field("Desc Ar", "Long Text", "وصف المركز بالعربية"),
                _field("Desc En", "Long Text", "وصف المركز بالإنجليزية"),
                _field("Services", "Long Text", "الخدمات المقدمة"),
                _field("Programs", "Long Text", "البرامج التابعة"),
                _field("Image", "Attach Image", "صورة المركز"),
                _field("Location", "Data", "الموقع"),
                _field("Phone", "Data", "رقم الهاتف"),
                _field("Email", "Data", "البريد الإلكتروني"),
                _field("Is Published", "Check", "منشور"),
                _field("Display Order", "Int", "ترتيب العرض"),
            ],
        },
        "Center Services": {"module": MODULE_NAME, "fields": default_fields},
        "Partners": {"module": MODULE_NAME, "fields": default_fields},
        "Offers": {
            "module": MODULE_NAME,
            "fields": [
                _field("ID", "Data", "المعرف الفريد", fieldname="id"),
                _field("Title Ar", "Data", "عنوان العرض بالعربية", reqd=1),
                _field("Title En", "Data", "عنوان العرض بالإنجليزية"),
                _field("Desc Ar", "Long Text", "وصف مختصر بالعربية"),
                _field("Desc En", "Long Text", "وصف مختصر بالإنجليزية"),
                _field("Details Ar", "Long Text", "تفاصيل العرض بالعربية"),
                _field("Details En", "Long Text", "تفاصيل العرض بالإنجليزية"),
                _field("Category", "Data", "فئة العرض"),
                _field("Image", "Attach Image", "صورة العرض"),
                _field("Valid Until", "Date", "صالح حتى"),
                _field("Target Audience Ar", "Long Text", "الفئة المستهدفة بالعربية"),
                _field("Target Audience En", "Long Text", "الفئة المستهدفة بالإنجليزية"),
                _field("Benefits Ar", "Long Text", "المزايا بالعربية"),
                _field("Benefits En", "Long Text", "المزايا بالإنجليزية"),
                _field("Duration Ar", "Data", "المدة بالعربية"),
                _field("Duration En", "Data", "المدة بالإنجليزية"),
                _field("Location Ar", "Data", "الموقع بالعربية"),
                _field("Location En", "Data", "الموقع بالإنجليزية"),
                _field("Requirements Ar", "Long Text", "المتطلبات بالعربية"),
                _field("Requirements En", "Long Text", "المتطلبات بالإنجليزية"),
                _field("Apply Link", "Data", "رابط التقديم"),
                _field("Is Active", "Check", "مفعل"),
                _field("Is Published", "Check", "منشور"),
                _field("Display Order", "Int", "ترتيب العرض"),
            ],
        },
        "Testimonials": {"module": MODULE_NAME, "fields": default_fields},
        "Colleges": {
            "module": MODULE_NAME,
            "fields": [
                _field("College Name", "Data", "اسم الكلية", reqd=1),
                _field("Description", "Long Text", "وصف الكلية"),
                _field("Dean Name", "Data", "اسم العميد"),
                _field("Image", "Attach Image", "صورة الكلية"),
                _field("Is Active", "Check", "حالة التفعيل"),
                _field("Display Order", "Int", "ترتيب العرض"),
            ],
        },
        "Academic Departments": {
            "module": MODULE_NAME,
            "fields": [
                _field("Department Name", "Data", "اسم القسم", reqd=1),
                _field("College", "Link", "الكلية التابعة", reqd=1, options="Colleges"),
                _field("Description", "Long Text", "وصف القسم"),
                _field("Is Active", "Check", "حالة التفعيل"),
            ],
        },
        "Academic Programs": {
            "module": MODULE_NAME,
            "fields": [
                _field("Program Name", "Data", "اسم البرنامج", reqd=1),
                _field("College", "Link", "الكلية التابعة", reqd=1, options="Colleges"),
                _field(
                    "Degree Type",
                    "Select",
                    "نوع الدرجة العلمية",
                    options="Diploma\nBachelor\nMaster\nPhD",
                ),
                _field("Description", "Long Text", "وصف البرنامج"),
                _field("Duration", "Data", "مدة الدراسة"),
                _field("Is Active", "Check", "مفعل"),
            ],
        },
        "Study Plans": {
            "module": MODULE_NAME,
            "fields": [
                _field("Plan Name", "Data", "اسم الخطة", reqd=1),
                _field("Academic Program", "Link", "البرنامج الأكاديمي", reqd=1, options="Academic Programs"),
                _field("Total Credits", "Int", "مجموع الساعات"),
                _field("Description", "Long Text", "وصف الخطة"),
                _field("Is Active", "Check", "مفعل"),
            ],
        },
        "Study Plan Courses": {
            "module": MODULE_NAME,
            "fields": [
                _field("Study Plan", "Link", "الخطة الدراسية", reqd=1, options="Study Plans"),
                _field("Course Name", "Data", "اسم المقرر", reqd=1),
                _field("Course Code", "Data", "رمز المقرر"),
                _field("Credit Hours", "Int", "عدد الساعات"),
                _field(
                    "Semester",
                    "Select",
                    "الفصل الدراسي",
                    options="1\n2\n3\n4\n5\n6\n7\n8",
                ),
                _field("Is Mandatory", "Check", "مقرر إجباري"),
                _field("Display Order", "Int", "ترتيب العرض"),
            ],
        },
        "Faculty Members": {
            "module": MODULE_NAME,
            "fields": [
                _field("Full Name", "Data", "الاسم الكامل", reqd=1),
                _field("Academic Title", "Data", "اللقب الأكاديمي"),
                _field("Department", "Link", "القسم", options="Academic Departments"),
                _field("Biography", "Long Text", "نبذة/سيرة"),
                _field("Photo", "Attach Image", "الصورة"),
                _field("Is Active", "Check", "مفعل"),
            ],
        },
        "Admission Requirements": {"module": MODULE_NAME, "fields": default_fields},
        "Registration Guide": {"module": MODULE_NAME, "fields": default_fields},
        "Research and Publications": {"module": MODULE_NAME, "fields": default_fields},
        "Student Activities": {"module": MODULE_NAME, "fields": default_fields},
        "Campus Life": {"module": MODULE_NAME, "fields": default_fields},
        "Contact Us Messages": {
            "module": MODULE_NAME,
            "fields": [
                _field("ID", "Data", "المعرف الفريد", reqd=1, fieldname="id"),
                _field("Name", "Data", "اسم المرسل", reqd=1, fieldname="sender_name"),
                _field("Email", "Data", "البريد الإلكتروني", reqd=1),
                _field("Phone", "Data", "رقم الهاتف"),
                _field("Subject", "Data", "عنوان الرسالة", reqd=1),
                _field("Message", "Long Text", "نص الرسالة", reqd=1),
                _field("Status", "Select", "حالة الرسالة", reqd=1, options="new\nread\nreplied\narchived"),
                _field("Replied At", "Datetime", "تاريخ الرد"),
                _field("Created At", "Datetime", "تاريخ الإرسال", reqd=1),
            ],
        },
        "Join Requests": {
            "module": MODULE_NAME,
            "fields": [
                _field("Title", "Data", "عنوان داخلي"),
                _field("ID", "Data", "المعرف الفريد", reqd=1, fieldname="id"),
                _field("Type", "Select", "نوع الطلب", reqd=1, options="student\nemployee"),
                _field("Name", "Data", "الاسم الكامل", reqd=1, fieldname="full_name"),
                _field("Email", "Data", "البريد الإلكتروني", reqd=1),
                _field("Phone", "Data", "رقم الهاتف", reqd=1),
                _field("Specialty", "Data", "التخصص", reqd=1),
                _field("Experience", "Long Text", "الخبرة"),
                _field("Cv File", "Attach", "السيرة الذاتية"),
                _field("Message", "Long Text", "رسالة إضافية"),
                _field(
                    "Status",
                    "Select",
                    "حالة الطلب",
                    reqd=1,
                    options="pending\nreviewed\naccepted\nrejected",
                ),
                _field("Reviewed At", "Datetime", "تاريخ المراجعة"),
                _field("Created At", "Datetime", "تاريخ الإرسال", reqd=1),
            ],
        },
        "FAQ": {
            "module": MODULE_NAME,
            "fields": [
                _field("Title", "Data", "عنوان داخلي"),
                _field("ID", "Data", "المعرف الفريد", fieldname="id"),
                _field("Question Ar", "Data", "السؤال بالعربية", reqd=1),
                _field("Question En", "Data", "السؤال بالإنجليزية"),
                _field("Answer Ar", "Long Text", "الإجابة بالعربية", reqd=1),
                _field("Answer En", "Long Text", "الإجابة بالإنجليزية"),
                _field("Category", "Data", "التصنيف"),
                _field("Is Published", "Check", "منشور"),
                _field("Display Order", "Int", "ترتيب العرض"),
            ],
        },
        "Team Members": {
            "module": MODULE_NAME,
            "fields": [
                _field("ID", "Data", "المعرف الفريد", fieldname="id"),
                _field("Name Ar", "Data", "الاسم بالعربية", reqd=1),
                _field("Name En", "Data", "الاسم بالإنجليزية"),
                _field("Position Ar", "Data", "المسمى الوظيفي بالعربية"),
                _field("Position En", "Data", "المسمى الوظيفي بالإنجليزية"),
                _field("Bio Ar", "Long Text", "نبذة بالعربية"),
                _field("Bio En", "Long Text", "نبذة بالإنجليزية"),
                _field("Image", "Attach Image", "الصورة الشخصية"),
                _field("Email", "Data", "البريد الإلكتروني"),
                _field("Phone", "Data", "رقم الهاتف"),
                _field("Is Published", "Check", "منشور"),
                _field("Display Order", "Int", "ترتيب العرض"),
            ],
        },
        "Projects": {
            "module": MODULE_NAME,
            "fields": [
                _field("ID", "Data", "المعرف الفريد", fieldname="id"),
                _field("Slug", "Data", "الرابط المختصر", reqd=1),
                _field("Title Ar", "Data", "عنوان المشروع بالعربية", reqd=1),
                _field("Title En", "Data", "عنوان المشروع بالإنجليزية"),
                _field("Desc Ar", "Long Text", "وصف مختصر بالعربية"),
                _field("Desc En", "Long Text", "وصف مختصر بالإنجليزية"),
                _field("Details Ar", "Long Text", "تفاصيل المشروع بالعربية"),
                _field("Details En", "Long Text", "تفاصيل المشروع بالإنجليزية"),
                _field("Start Date", "Date", "تاريخ البداية"),
                _field("End Date", "Date", "تاريخ النهاية"),
                _field("Year", "Int", "السنة"),
                _field("Progress", "Int", "نسبة الإنجاز"),
                _field("Status", "Select", "الحالة", options="current\ncompleted\nplanned"),
                _field("Is Published", "Check", "منشور"),
                _field("Display Order", "Int", "ترتيب العرض"),
            ],
        },
        "Blog Posts": {
            "module": MODULE_NAME,
            "fields": [
                _field("ID", "Data", "المعرف الفريد", fieldname="id"),
                _field("Slug", "Data", "الرابط المختصر", reqd=1),
                _field("Title Ar", "Data", "عنوان المقال بالعربية", reqd=1),
                _field("Title En", "Data", "عنوان المقال بالإنجليزية"),
                _field("Excerpt Ar", "Long Text", "الملخص بالعربية"),
                _field("Excerpt En", "Long Text", "الملخص بالإنجليزية"),
                _field("Content Ar", "Long Text", "محتوى المقال بالعربية"),
                _field("Content En", "Long Text", "محتوى المقال بالإنجليزية"),
                _field("Author Name Ar", "Data", "اسم الكاتب بالعربية"),
                _field("Author Name En", "Data", "اسم الكاتب بالإنجليزية"),
                _field("Author Avatar", "Attach Image", "صورة الكاتب"),
                _field("Author Role Ar", "Data", "وظيفة الكاتب بالعربية"),
                _field("Author Role En", "Data", "وظيفة الكاتب بالإنجليزية"),
                _field("Category", "Data", "الفئة"),
                _field("Category Ar", "Data", "الفئة بالعربية"),
                _field("Category En", "Data", "الفئة بالإنجليزية"),
                _field("Image", "Attach Image", "صورة المقال"),
                _field("Published At", "Date", "تاريخ النشر"),
                _field("Read Time", "Int", "مدة القراءة بالدقائق"),
                _field("Views", "Int", "عدد المشاهدات"),
                _field("Tags", "Long Text", "الوسوم"),
                _field("Is Published", "Check", "منشور"),
                _field("Display Order", "Int", "ترتيب العرض"),
            ],
        },
        "Job Opportunities": {"module": MODULE_NAME, "fields": default_fields},
        "Media Library": {
            "module": MODULE_NAME,
            "fields": [
                _field("Media Title", "Data", "عنوان الوسائط", reqd=1),
                _field("Media Type", "Select", "نوع الوسائط", options="Image\nVideo\nDocument"),
                _field("File", "Attach", "الملف"),
                _field("Description", "Small Text", "وصف"),
                _field("Is Published", "Check", "منشور"),
            ],
        },
        "Pages": {
            "module": MODULE_NAME,
            "fields": [
                _field("Page Title", "Data", "عنوان الصفحة", reqd=1),
                _field("Slug", "Data", "رابط الصفحة", reqd=1),
                _field("Content", "Long Text", "محتوى الصفحة"),
                _field("SEO Title", "Data", "عنوان SEO"),
                _field("SEO Description", "Small Text", "وصف SEO"),
                _field("Is Published", "Check", "منشور"),
            ],
        },
        "Menus": {"module": MODULE_NAME, "fields": default_fields},
        "Sliders": {"module": MODULE_NAME, "fields": default_fields},
        "Website Settings": {
            "module": MODULE_NAME,
            "fields": [
                _field("Site Name", "Data", "اسم الموقع", reqd=1),
                _field("Logo", "Attach Image", "شعار الموقع"),
                _field("Contact Email", "Data", "بريد التواصل"),
                _field("Contact Phone", "Data", "هاتف التواصل"),
                _field("Address", "Small Text", "العنوان"),
            ],
        },
    }
    specs = {}
    for raw_name, spec in raw_specs.items():
        doctype_name = sanitize_doctype_name(raw_name)
        if doctype_name in specs:
            raise frappe.ValidationError(f"Duplicate sanitized DocType name: {doctype_name}")
        normalized_spec = dict(spec)
        normalized_spec["module"] = MODULE_NAME
        normalized_spec["label"] = raw_name
        specs[doctype_name] = normalized_spec
    return specs


def sanitize_doctype_name(name: str) -> str:
    value = (name or "").replace("&", " and ")
    value = re.sub(r"[^A-Za-z0-9 _-]+", " ", value)
    value = re.sub(r"\s+", " ", value).strip()
    if not value:
        value = "AAU DocType"
    if not re.match(r"^[A-Za-z]", value):
        value = f"D {value}"
    return value


def _default_fields() -> list[dict]:
    return [
        _field("Title", "Data", "العنوان", reqd=1),
        _field("Content", "Long Text", "المحتوى"),
        _field("Image", "Attach Image", "الصورة"),
        _field("Is Published", "Check", "حالة النشر"),
        _field("Display Order", "Int", "ترتيب العرض"),
    ]


def _field(
    label: str,
    fieldtype: str,
    description: str,
    reqd: int = 0,
    options: str | None = None,
    fieldname: str | None = None,
) -> dict:
    return {
        "label": label,
        "fieldtype": fieldtype,
        "description": description,
        "reqd": int(reqd or 0),
        "options": options,
        "fieldname": fieldname or _to_fieldname(label),
    }


def _to_fieldname(label: str) -> str:
    return frappe.scrub(label)


def _ensure_module_defs(report: dict, dry_run: bool = False):
    for module_name in MODULES:
        if not frappe.db.exists("Module Def", module_name):
            report["actions"].append(f"{'WOULD_CREATE' if dry_run else 'CREATED'} Module Def: {module_name}")
            if dry_run:
                continue
            doc = frappe.get_doc(
                {
                    "doctype": "Module Def",
                    "module_name": module_name,
                    "app_name": "aau_university",
                    "custom": 1,
                }
            )
            doc.insert(ignore_permissions=True)
            frappe.db.commit()


def _create_doctype(name: str, module: str, required_fields: list[dict], report: dict):
    doctype_name = sanitize_doctype_name(name)
    fields = _with_section_break(required_fields, existing_fields=[])
    field_order = [f["fieldname"] for f in fields if f.get("fieldname")]
    doc = frappe.get_doc(
        {
            "doctype": "DocType",
            "name": doctype_name,
            "module": module,
            "custom": 1,
            "allow_rename": 1,
            "istable": 0,
            "issingle": 0,
            "track_changes": 1,
            "fields": fields,
            "permissions": [_system_manager_permission()],
        }
    )
    doc.set("field_order", field_order)
    doc.insert(ignore_permissions=True)
    frappe.db.commit()
    report["actions"].append(f"CREATED DocType: {doctype_name}")


def _audit_fields(doc, required_fields: list[dict]):
    issues = []
    changes = []
    fields = doc.fields or []

    if not any(df.fieldtype == "Section Break" for df in fields):
        issues.append("missing Section Break")
        changes.append(("add_section_break", _section_break_field()))

    for required in required_fields:
        existing = _find_field(doc, required)
        if not existing:
            issues.append(f"missing field '{required['label']}'")
            changes.append(("add_field", required))
            continue

        field_changes = {}
        if existing.label != required["label"]:
            issues.append(
                f"field '{required['label']}' label mismatch (found '{existing.label}')"
            )
            field_changes["label"] = required["label"]

        if existing.fieldtype != required["fieldtype"]:
            issues.append(
                f"field '{required['label']}' fieldtype mismatch (found '{existing.fieldtype}')"
            )
            field_changes["fieldtype"] = required["fieldtype"]

        if required.get("options") and (existing.options or "").strip() != required["options"]:
            issues.append(f"field '{required['label']}' options mismatch")
            field_changes["options"] = required["options"]

        if int(existing.reqd or 0) != int(required["reqd"]):
            issues.append(f"field '{required['label']}' reqd mismatch")
            field_changes["reqd"] = int(required["reqd"])

        if (existing.description or "").strip() != required["description"]:
            issues.append(f"field '{required['label']}' description mismatch")
            field_changes["description"] = required["description"]

        if field_changes:
            changes.append(("update_field", existing.fieldname, field_changes))

    return issues, changes


def _apply_field_changes(doc, changes) -> bool:
    changed = False
    if not changes:
        return False

    for change in changes:
        action = change[0]
        if action == "add_section_break":
            field = change[1]
            doc.append("fields", field)
            changed = True
        elif action == "add_field":
            field = change[1]
            doc.append("fields", field)
            changed = True
        elif action == "update_field":
            fieldname, updates = change[1], change[2]
            df = _get_field_by_fieldname(doc, fieldname)
            if not df:
                continue
            for key, value in updates.items():
                setattr(df, key, value)
            changed = True

    return changed


def _ensure_field_order(doc) -> bool:
    existing_order = _coerce_field_order(doc.get("field_order") or getattr(doc, "field_order", None))
    fields = doc.fields or []
    fieldnames = [df.fieldname for df in fields if getattr(df, "fieldname", None)]
    if not fieldnames:
        return False

    if not existing_order:
        doc.set("field_order", fieldnames)
        return True

    new_order = []
    seen = set()
    for fieldname in existing_order:
        if fieldname in fieldnames and fieldname not in seen:
            new_order.append(fieldname)
            seen.add(fieldname)
    for fieldname in fieldnames:
        if fieldname not in seen:
            new_order.append(fieldname)
            seen.add(fieldname)

    if new_order != existing_order:
        doc.set("field_order", new_order)
        return True

    return False


def _coerce_field_order(value) -> list[str]:
    if not value:
        return []
    if isinstance(value, (list, tuple)):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str):
        try:
            parsed = frappe.parse_json(value)
        except Exception:
            parsed = None
        if isinstance(parsed, list):
            return [str(item).strip() for item in parsed if str(item).strip()]
        return [part.strip() for part in re.split(r"[\n,]+", value) if part.strip()]
    return []



def _find_field(doc, required: dict):
    by_fieldname = _get_field_by_fieldname(doc, required["fieldname"])
    if by_fieldname:
        return by_fieldname
    for df in doc.fields or []:
        if df.label == required["label"]:
            return df
    return None


def _get_field_by_fieldname(doc, fieldname: str):
    for df in doc.fields or []:
        if df.fieldname == fieldname:
            return df
    return None


def _section_break_field() -> dict:
    return {
        "label": "Main Section",
        "fieldtype": "Section Break",
        "fieldname": "main_section",
    }


def _with_section_break(required_fields: list[dict], existing_fields: list[dict]) -> list[dict]:
    if any(f.get("fieldtype") == "Section Break" for f in existing_fields):
        return required_fields
    return [_section_break_field()] + required_fields


def _system_manager_permission() -> dict:
    return {
        "role": "System Manager",
        "read": 1,
        "write": 1,
        "create": 1,
        "delete": 1,
        "submit": 0,
        "cancel": 0,
        "amend": 0,
        "report": 1,
        "export": 1,
        "print": 1,
        "email": 1,
        "share": 1,
    }


def _ensure_system_manager_permission(doc) -> bool:
    for perm in doc.permissions or []:
        if perm.role == "System Manager":
            return False
    doc.append("permissions", _system_manager_permission())
    return True


def _print_report(report: dict):
    _log("AUDIT REPORT")
    _log(
        "SUMMARY: CREATED={created} UPDATED={updated} SKIPPED={skipped}".format(
            created=report["created_count"],
            updated=report["updated_count"],
            skipped=report["skipped_count"],
        )
    )
    if report["would_create_count"] or report["would_update_count"]:
        _log(
            "SUMMARY (DRY RUN): WOULD_CREATE={created} WOULD_UPDATE={updated}".format(
                created=report["would_create_count"],
                updated=report["would_update_count"],
            )
        )
    _log("MISSING_DOCTYPES: " + (", ".join(report["missing_doctypes"]) or "None"))
    _log("WRONG_MODULES: " + (", ".join(report["wrong_modules"]) or "None"))
    if report["field_issues"]:
        _log("FIELD_ISSUES:")
        for issue in report["field_issues"]:
            _log(f"- {issue}")
    else:
        _log("FIELD_ISSUES: None")
    if report["actions"]:
        _log("ACTIONS:")
        for action in report["actions"]:
            _log(f"- {action}")


def _log(message: str):
    frappe.logger("aau_university").info(f"{LOG_PREFIX} {message}")
    print(f"{LOG_PREFIX} {message}")
