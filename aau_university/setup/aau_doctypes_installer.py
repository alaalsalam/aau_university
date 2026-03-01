# -*- coding: utf-8 -*-
"""
AAU - DocTypes Installer

- Creates/updates AAU website-related DocTypes (screens) from an in-code spec.
- Idempotent: safe to run multiple times.
- Adds Module Def if missing.
- Adds basic permissions (System Manager full access) if missing.

How to run manually:
bench --site <site> console
>>> from aau_university.setup.aau_doctypes_installer import run
>>> run(update_existing=True)

Hook options:
- after_install = "aau_university.setup.aau_doctypes_installer.after_install"
- after_migrate = "aau_university.setup.aau_doctypes_installer.after_migrate"
"""

from __future__ import annotations

import re
import frappe


APP_NAME = "aau_university"
MODULE_NAME = "AAU"

# AAU modules (Module Def records) used in your app
AAU_MODULES = [MODULE_NAME]

# ---------------------------------------------------------------------
# Screens Spec
# Each screen = DocType name (visible label), module, fields:
# field: label, description_ar, fieldtype, options (optional), reqd (optional)
# ---------------------------------------------------------------------

SCREENS = [
    # ---------------- Content ----------------
    {
        "doctype_name": "Home Page",
        "module": MODULE_NAME,
        "fields": [
            ("Page Title", "عنوان الصفحة الرئيسي", "Data", None, 1),
            ("Hero Description", "نص ترحيبي مختصر", "Small Text", None, 0),
            ("Hero Image", "صورة الهيدر", "Attach Image", None, 0),
            ("Is Published", "حالة النشر", "Check", None, 0),
            ("Display Order", "ترتيب العرض", "Int", None, 0),
        ],
    },
    {
        "doctype_name": "About University",
        "module": MODULE_NAME,
        "fields": [
            ("Title", "عنوان القسم", "Data", None, 1),
            ("Description", "وصف عن الجامعة", "Long Text", None, 0),
            ("Image", "صورة تعريفية", "Attach Image", None, 0),
            ("Is Published", "حالة النشر", "Check", None, 0),
        ],
    },
    {
        "doctype_name": "University Vision and Mission",
        "module": MODULE_NAME,
        "fields": [
            ("Vision", "رؤية الجامعة", "Long Text", None, 0),
            ("Mission", "رسالة الجامعة", "Long Text", None, 0),
            ("Values", "القيم المؤسسية", "Long Text", None, 0),
            ("Is Published", "حالة النشر", "Check", None, 0),
        ],
    },
    {
        "doctype_name": "University Administration",
        "module": MODULE_NAME,
        "fields": [
            ("Name", "اسم المسؤول/الإداري", "Data", None, 1),
            ("Position", "المنصب الإداري", "Data", None, 1),
            ("Biography", "نبذة تعريفية", "Long Text", None, 0),
            ("Photo", "الصورة", "Attach Image", None, 0),
            ("Display Order", "ترتيب العرض", "Int", None, 0),
            ("Is Active", "حالة التفعيل", "Check", None, 0),
        ],
    },
    {
        "doctype_name": "News",
        "module": MODULE_NAME,
        "fields": [
            ("Title", "عنوان الخبر", "Data", None, 1),
            ("Summary", "ملخص الخبر", "Small Text", None, 0),
            ("Content", "محتوى الخبر", "Long Text", None, 0),
            ("Featured Image", "الصورة الرئيسية", "Attach Image", None, 0),
            ("Publish Date", "تاريخ النشر", "Date", None, 0),
            ("Is Published", "منشور", "Check", None, 0),
            ("Display Order", "ترتيب العرض", "Int", None, 0),
        ],
    },
    {
        "doctype_name": "Events",
        "module": MODULE_NAME,
        "fields": [
            ("Event Title", "عنوان الفعالية", "Data", None, 1),
            ("Description", "وصف الفعالية", "Long Text", None, 0),
            ("Event Date", "تاريخ الفعالية", "Date", None, 0),
            ("Location", "الموقع", "Data", None, 0),
            ("Image", "الصورة", "Attach Image", None, 0),
            ("Is Published", "منشور", "Check", None, 0),
            ("Display Order", "ترتيب العرض", "Int", None, 0),
        ],
    },
    {
        "doctype_name": "Announcements",
        "module": MODULE_NAME,
        "fields": [
            ("Title", "عنوان الإعلان", "Data", None, 1),
            ("Content", "محتوى الإعلان", "Long Text", None, 0),
            ("Publish Date", "تاريخ النشر", "Date", None, 0),
            ("Is Published", "منشور", "Check", None, 0),
            ("Display Order", "ترتيب العرض", "Int", None, 0),
        ],
    },
    {
        "doctype_name": "University Centers",
        "module": MODULE_NAME,
        "fields": [
            ("Center Name", "اسم المركز", "Data", None, 1),
            ("Description", "وصف المركز", "Long Text", None, 0),
            ("Image", "صورة المركز", "Attach Image", None, 0),
            ("Is Published", "منشور", "Check", None, 0),
            ("Display Order", "ترتيب العرض", "Int", None, 0),
        ],
    },
    {
        "doctype_name": "Center Services",
        "module": MODULE_NAME,
        "fields": [
            ("Service Name", "اسم الخدمة", "Data", None, 1),
            ("Center", "المركز التابع", "Link", "University Centers", 1),
            ("Description", "وصف الخدمة", "Long Text", None, 0),
            ("Is Published", "منشور", "Check", None, 0),
            ("Display Order", "ترتيب العرض", "Int", None, 0),
        ],
    },
    {
        "doctype_name": "Partners",
        "module": MODULE_NAME,
        "fields": [
            ("Partner Name", "اسم الشريك", "Data", None, 1),
            ("Website", "الموقع الإلكتروني", "Data", None, 0),
            ("Logo", "الشعار", "Attach Image", None, 0),
            ("Is Published", "منشور", "Check", None, 0),
            ("Display Order", "ترتيب العرض", "Int", None, 0),
        ],
    },
    {
        "doctype_name": "Testimonials",
        "module": MODULE_NAME,
        "fields": [
            ("Person Name", "اسم صاحب الشهادة", "Data", None, 1),
            ("Title", "الصفة/المسمى", "Data", None, 0),
            ("Content", "نص الشهادة", "Long Text", None, 1),
            ("Photo", "الصورة", "Attach Image", None, 0),
            ("Is Published", "منشور", "Check", None, 0),
            ("Display Order", "ترتيب العرض", "Int", None, 0),
        ],
    },

    # ---------------- Academic ----------------
    {
        "doctype_name": "Colleges",
        "module": MODULE_NAME,
        "fields": [
            ("College Name", "اسم الكلية", "Data", None, 1),
            ("Description", "وصف الكلية", "Long Text", None, 0),
            ("Dean Name", "اسم العميد", "Data", None, 0),
            ("Image", "صورة الكلية", "Attach Image", None, 0),
            ("Is Active", "حالة التفعيل", "Check", None, 0),
            ("Display Order", "ترتيب العرض", "Int", None, 0),
        ],
    },
    {
        "doctype_name": "Academic Departments",
        "module": MODULE_NAME,
        "fields": [
            ("Department Name", "اسم القسم", "Data", None, 1),
            ("College", "الكلية التابعة", "Link", "Colleges", 1),
            ("Description", "وصف القسم", "Long Text", None, 0),
            ("Is Active", "حالة التفعيل", "Check", None, 0),
        ],
    },
    {
        "doctype_name": "Academic Programs",
        "module": MODULE_NAME,
        "fields": [
            ("Program Name", "اسم البرنامج", "Data", None, 1),
            ("College", "الكلية التابعة", "Link", "Colleges", 1),
            ("Degree Type", "نوع الدرجة العلمية", "Select", "Diploma\nBachelor\nMaster\nPhD", 0),
            ("Description", "وصف البرنامج", "Long Text", None, 0),
            ("Duration", "مدة الدراسة", "Data", None, 0),
            ("Is Active", "مفعل", "Check", None, 0),
        ],
    },
    {
        "doctype_name": "Study Plans",
        "module": MODULE_NAME,
        "fields": [
            ("Plan Name", "اسم الخطة", "Data", None, 1),
            ("Academic Program", "البرنامج الأكاديمي", "Link", "Academic Programs", 1),
            ("Total Credits", "مجموع الساعات", "Int", None, 0),
            ("Description", "وصف الخطة", "Long Text", None, 0),
            ("Is Active", "مفعل", "Check", None, 0),
        ],
    },
    {
        "doctype_name": "Study Plan Courses",
        "module": MODULE_NAME,
        "fields": [
            ("Study Plan", "الخطة الدراسية", "Link", "Study Plans", 1),
            ("Course Name", "اسم المقرر", "Data", None, 1),
            ("Course Code", "رمز المقرر", "Data", None, 0),
            ("Credit Hours", "عدد الساعات", "Int", None, 0),
            ("Semester", "الفصل الدراسي", "Select", "1\n2\n3\n4\n5\n6\n7\n8", 0),
            ("Is Mandatory", "مقرر إجباري", "Check", None, 0),
            ("Display Order", "ترتيب العرض", "Int", None, 0),
        ],
    },
    {
        "doctype_name": "Faculty Members",
        "module": MODULE_NAME,
        "fields": [
            ("Full Name", "الاسم الكامل", "Data", None, 1),
            ("Academic Title", "اللقب الأكاديمي", "Data", None, 0),
            ("Department", "القسم", "Link", "Academic Departments", 0),
            ("Biography", "نبذة/سيرة", "Long Text", None, 0),
            ("Photo", "الصورة", "Attach Image", None, 0),
            ("Is Active", "مفعل", "Check", None, 0),
        ],
    },
    {
        "doctype_name": "Admission Requirements",
        "module": MODULE_NAME,
        "fields": [
            ("Title", "العنوان", "Data", None, 1),
            ("Content", "المحتوى", "Long Text", None, 1),
            ("Is Published", "منشور", "Check", None, 0),
        ],
    },
    {
        "doctype_name": "Registration Guide",
        "module": MODULE_NAME,
        "fields": [
            ("Title", "العنوان", "Data", None, 1),
            ("Content", "المحتوى", "Long Text", None, 1),
            ("Is Published", "منشور", "Check", None, 0),
        ],
    },
    {
        "doctype_name": "Research and Publications",
        "module": MODULE_NAME,
        "fields": [
            ("Title", "العنوان", "Data", None, 1),
            ("Authors", "المؤلفون", "Data", None, 0),
            ("Publish Date", "تاريخ النشر", "Date", None, 0),
            ("Abstract", "الملخص", "Long Text", None, 0),
            ("File", "الملف", "Attach", None, 0),
            ("Is Published", "منشور", "Check", None, 0),
        ],
    },

    # ---------------- Public ----------------
    {
        "doctype_name": "Student Activities",
        "module": MODULE_NAME,
        "fields": [
            ("Title", "عنوان النشاط", "Data", None, 1),
            ("Description", "وصف النشاط", "Long Text", None, 0),
            ("Image", "الصورة", "Attach Image", None, 0),
            ("Is Published", "منشور", "Check", None, 0),
            ("Display Order", "ترتيب العرض", "Int", None, 0),
        ],
    },
    {
        "doctype_name": "Campus Life",
        "module": MODULE_NAME,
        "fields": [
            ("Title", "العنوان", "Data", None, 1),
            ("Content", "المحتوى", "Long Text", None, 0),
            ("Image", "الصورة", "Attach Image", None, 0),
            ("Is Published", "منشور", "Check", None, 0),
        ],
    },
    {
        "doctype_name": "Contact Us Messages",
        "module": MODULE_NAME,
        "fields": [
            ("Sender Name", "اسم المرسل", "Data", None, 1),
            ("Email", "البريد الإلكتروني", "Data", None, 0),
            ("Subject", "عنوان الرسالة", "Data", None, 0),
            ("Message", "نص الرسالة", "Long Text", None, 1),
            ("Received Date", "تاريخ الاستلام", "Datetime", None, 0),
        ],
    },
    {
        "doctype_name": "Join Requests",
        "module": MODULE_NAME,
        "fields": [
            ("Full Name", "الاسم الكامل", "Data", None, 1),
            ("Email", "البريد الإلكتروني", "Data", None, 0),
            ("Phone", "رقم الهاتف", "Data", None, 0),
            ("Request Type", "نوع الطلب", "Select", "Student\nEmployee\nPartner\nOther", 0),
            ("Notes", "ملاحظات", "Long Text", None, 0),
            ("Status", "حالة الطلب", "Select", "New\nIn Review\nApproved\nRejected", 0),
        ],
    },
    {
        "doctype_name": "FAQ",
        "module": MODULE_NAME,
        "fields": [
            ("Question", "السؤال", "Data", None, 1),
            ("Answer", "الإجابة", "Long Text", None, 1),
            ("Is Published", "منشور", "Check", None, 0),
            ("Display Order", "ترتيب العرض", "Int", None, 0),
        ],
    },
    {
        "doctype_name": "Job Opportunities",
        "module": MODULE_NAME,
        "fields": [
            ("Title", "المسمى الوظيفي", "Data", None, 1),
            ("Department", "القسم", "Data", None, 0),
            ("Description", "الوصف", "Long Text", None, 0),
            ("Publish Date", "تاريخ النشر", "Date", None, 0),
            ("Is Published", "منشور", "Check", None, 0),
        ],
    },

    # ---------------- CMS ----------------
    {
        "doctype_name": "Media Library",
        "module": MODULE_NAME,
        "fields": [
            ("Media Title", "عنوان الوسائط", "Data", None, 1),
            ("Media Type", "نوع الوسائط", "Select", "Image\nVideo\nDocument", 0),
            ("File", "الملف", "Attach", None, 0),
            ("Description", "وصف", "Small Text", None, 0),
            ("Is Published", "منشور", "Check", None, 0),
        ],
    },
    {
        "doctype_name": "Pages",
        "module": MODULE_NAME,
        "fields": [
            ("Page Title", "عنوان الصفحة", "Data", None, 1),
            ("Slug", "رابط الصفحة", "Data", None, 1),
            ("Content", "محتوى الصفحة", "Long Text", None, 0),
            ("SEO Title", "عنوان SEO", "Data", None, 0),
            ("SEO Description", "وصف SEO", "Small Text", None, 0),
            ("Is Published", "منشور", "Check", None, 0),
        ],
    },
    {
        "doctype_name": "Menus",
        "module": MODULE_NAME,
        "fields": [
            ("Menu Title", "عنوان القائمة", "Data", None, 1),
            ("Is Published", "منشور", "Check", None, 0),
            ("Display Order", "ترتيب العرض", "Int", None, 0),
        ],
    },
    {
        "doctype_name": "Sliders",
        "module": MODULE_NAME,
        "fields": [
            ("Title", "العنوان", "Data", None, 0),
            ("Image", "الصورة", "Attach Image", None, 1),
            ("Link", "الرابط", "Data", None, 0),
            ("Is Published", "منشور", "Check", None, 0),
            ("Display Order", "ترتيب العرض", "Int", None, 0),
        ],
    },
    {
        "doctype_name": "Website Settings",
        "module": MODULE_NAME,
        "fields": [
            ("Site Name", "اسم الموقع", "Data", None, 1),
            ("Logo", "شعار الموقع", "Attach Image", None, 0),
            ("Contact Email", "بريد التواصل", "Data", None, 0),
            ("Contact Phone", "هاتف التواصل", "Data", None, 0),
            ("Address", "العنوان", "Small Text", None, 0),
        ],
    },
]

# ---------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------

def after_install():
    run(update_existing=True)

def after_migrate():
    # safer to update to match spec changes
    run(update_existing=True)

def run(update_existing: bool = True):
    """
    Main entry: create/update all AAU screens (DocTypes).
    """
    _ensure_modules()

    for s in SCREENS:
        _create_or_update_doctype(
            doctype_name=_sanitize_doctype_name(s["doctype_name"]),
            module=MODULE_NAME,
            fields=s["fields"],
            update_existing=update_existing,
        )

    frappe.db.commit()


# ---------------------------------------------------------------------
# Internals
# ---------------------------------------------------------------------

def _ensure_modules():
    for m in AAU_MODULES:
        if not frappe.db.exists("Module Def", m):
            frappe.get_doc({
                "doctype": "Module Def",
                "module_name": m,
                "app_name": APP_NAME,
                "custom": 1
            }).insert(ignore_permissions=True)

def _make_fieldname(label: str) -> str:
    # convert label to a safe fieldname (snake_case)
    x = (label or "").strip().lower()
    x = re.sub(r"[^a-z0-9]+", "_", x)
    x = re.sub(r"_+", "_", x).strip("_")
    if not x:
        x = "field"
    if x[0].isdigit():
        x = f"f_{x}"
    return x[:140]

def _base_permissions():
    # minimal: System Manager full access
    return [{
        "role": "System Manager",
        "read": 1, "write": 1, "create": 1, "delete": 1,
        "report": 1, "export": 1, "import": 0,
        "share": 1, "print": 1, "email": 1
    }]

def _create_or_update_doctype(doctype_name: str, module: str, fields: list, update_existing: bool):
    exists = frappe.db.exists("DocType", doctype_name)

    if exists and not update_existing:
        return

    doc_fields = []
    field_order = []

    # add a section break for clean UI
    doc_fields.append({
        "fieldname": "section_main",
        "label": "Main",
        "fieldtype": "Section Break",
        "collapsible": 0
    })
    field_order.append("section_main")

    used_fieldnames = set(["section_main"])

    for (label, desc_ar, fieldtype, options, reqd) in fields:
        fn = _make_fieldname(label)
        # ensure uniqueness
        base = fn
        i = 2
        while fn in used_fieldnames:
            fn = f"{base}_{i}"
            i += 1
        used_fieldnames.add(fn)

        df = {
            "fieldname": fn,
            "label": label,
            "fieldtype": fieldtype,
            "reqd": 1 if reqd else 0,
            "description": desc_ar or ""
        }
        if options:
            df["options"] = options

        doc_fields.append(df)
        field_order.append(fn)

    payload = {
        "doctype": "DocType",
        "name": doctype_name,
        "module": module,
        "custom": 1,
        "istable": 0,
        "issingle": 0,
        "allow_rename": 1,
        "track_changes": 1,
        "sort_field": "modified",
        "sort_order": "DESC",
        "row_format": "Dynamic",
        "fields": doc_fields,
        "field_order": field_order,
        "permissions": _base_permissions(),
    }

    if exists:
        if frappe.db.get_value("DocType", doctype_name, "module") != module:
            frappe.db.set_value("DocType", doctype_name, "module", module, update_modified=False)
            frappe.clear_cache(doctype=doctype_name)
        dt = frappe.get_doc("DocType", doctype_name)
        # overwrite key parts to match spec
        dt.module = module
        dt.custom = 1
        dt.allow_rename = 1
        dt.track_changes = 1

        dt.set("fields", [])
        for f in doc_fields:
            dt.append("fields", f)

        dt.set("field_order", field_order)
        dt.set("permissions", [])
        for p in _base_permissions():
            dt.append("permissions", p)

        dt.save(ignore_permissions=True)
    else:
        frappe.get_doc(payload).insert(ignore_permissions=True)


def _sanitize_doctype_name(name: str) -> str:
    value = (name or "").replace("&", " and ").strip()
    value = re.sub(r"[^A-Za-z0-9 _-]+", " ", value)
    value = re.sub(r"\s+", " ", value).strip()
    if not value:
        value = "AAU DocType"
    if value[0].isdigit():
        value = f"D {value}"
    return value
