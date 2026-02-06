# -*- coding: utf-8 -*-
from __future__ import annotations

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
                    report["actions"].append(f"WOULD_CREATE DocType: {doctype_name}")
                    report["would_create_count"] += 1
                else:
                    _create_doctype(doctype_name, expected_module, required_fields, report)
                    report["created_count"] += 1
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
                    report["actions"].append(f"WOULD_UPDATE DocType: {doctype_name}")
                    report["would_update_count"] += 1
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
                    report["actions"].append(f"UPDATED DocType: {doctype_name}")
                    report["updated_count"] += 1
                else:
                    report["actions"].append(f"SKIPPED DocType: {doctype_name}")
                    report["skipped_count"] += 1

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
    specs = {
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
        "University Vision & Mission": {
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
        "Center Services": {"module": MODULE_NAME, "fields": default_fields},
        "Partners": {"module": MODULE_NAME, "fields": default_fields},
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
        "Research & Publications": {"module": MODULE_NAME, "fields": default_fields},
        "Student Activities": {"module": MODULE_NAME, "fields": default_fields},
        "Campus Life": {"module": MODULE_NAME, "fields": default_fields},
        "Contact Us Messages": {
            "module": MODULE_NAME,
            "fields": [
                _field("Sender Name", "Data", "اسم المرسل", reqd=1),
                _field("Email", "Data", "البريد الإلكتروني"),
                _field("Subject", "Data", "عنوان الرسالة"),
                _field("Message", "Long Text", "نص الرسالة", reqd=1),
                _field("Received Date", "Datetime", "تاريخ الاستلام"),
            ],
        },
        "Join Requests": {"module": MODULE_NAME, "fields": default_fields},
        "FAQ": {"module": MODULE_NAME, "fields": default_fields},
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
    for spec in specs.values():
        spec["module"] = MODULE_NAME
    return specs


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
    fields = _with_section_break(required_fields, existing_fields=[])
    doc = frappe.get_doc(
        {
            "doctype": "DocType",
            "name": name,
            "module": module,
            "custom": 1,
            "allow_rename": 1,
            "istable": 0,
            "issingle": 0,
            "track_changes": 1,
            "fields": fields,
            "field_order": [f["fieldname"] for f in fields],
            "permissions": [_system_manager_permission()],
        }
    )
    doc.insert(ignore_permissions=True)
    frappe.db.commit()
    report["actions"].append(f"CREATED DocType: {name}")


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
    existing_order = getattr(doc, "field_order", None) or []
    fields = doc.fields or []
    fieldnames = [df.fieldname for df in fields if getattr(df, "fieldname", None)]
    if not fieldnames:
        return False

    if not existing_order:
        doc.field_order = fieldnames
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
        doc.field_order = new_order
        return True

    return False



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
