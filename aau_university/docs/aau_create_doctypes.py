# -*- coding: utf-8 -*-
"""
AAU - Create all DocTypes (Screens) from DATABASE_SCHEMA_AND_API.md

Project: AAU
Stage: MVP implementation
Objective: إنشاء جميع الشاشات (DocTypes) + الحقول بالكامل من ملف التوثيق
          مع وصف عربي لكل حقل، وتوزيع DocTypes على Modules الصحيحة:
          Content / Academic / Public / CMS (داخل تطبيق aau)

Source of truth:
- /mnt/data/DATABASE_SCHEMA_AND_API.md

How to run:
1) bench --site <yoursite> console
2) Execute:
   import aau_create_doctypes as m
   m.create_all()

Notes:
- السكربت "Idempotent": إذا كان الـ DocType موجودًا سيتم تخطيه (لن يعيد إنشاءه).
- حقول TEXT[] يتم تحويلها إلى Child Table تلقائيًا.
- حقول FK (xxx_id) تُحوّل إلى Link عندما يمكن استنتاج الهدف.
- حقول created_at / updated_at / id تُنشأ كحقول Read Only (للمطابقة مع الوثيقة).
"""

import re
import frappe

MD_PATH = "/mnt/data/DATABASE_SCHEMA_AND_API.md"
APP_NAME = "aau"

# -----------------------------
# 1) Mapping: Table Name -> DocType Label (Screen Name)
# -----------------------------
TABLE_TO_DOCTYPE = {
    "colleges": "Colleges",
    "college_deans": "College Deans",
    "academic_programs": "Academic Programs",
    "program_objectives": "Program Objectives",
    "study_plans": "Study Plans",
    "study_plan_courses": "Study Plan Courses",
    "faculty_members": "Faculty Members",
    "program_faculty": "Program Faculty",
    "news": "News",
    "events": "Events",
    "centers": "Centers",
    "center_services": "Center Services",
    "center_programs": "Center Programs",
    "partners": "Partners",
    "offers": "Offers",
    "faqs": "FAQs",
    "team_members": "Team Members",
    "projects": "Projects",
    "campus_life": "Campus Life",
    "blog_posts": "Blog Posts",
    "pages": "Pages",
    "media": "Media Library",
    "settings": "Website Settings",
    "contact_messages": "Contact Messages",
    "join_requests": "Join Requests",
}

# -----------------------------
# 2) Module assignment (as per your app setup)
# -----------------------------
TABLE_TO_MODULE = {t: "Content" for t in TABLE_TO_DOCTYPE.keys()}

# CMS
for t in ("settings", "pages", "media"):
    TABLE_TO_MODULE[t] = "CMS"

# Public (user submitted forms)
for t in ("contact_messages", "join_requests"):
    TABLE_TO_MODULE[t] = "Public"

# Academic (content but academically structured)
for t in ("academic_programs", "program_objectives", "study_plans", "study_plan_courses", "program_faculty"):
    TABLE_TO_MODULE[t] = "Academic"

# -----------------------------
# Helpers
# -----------------------------
def _to_fieldname(s: str) -> str:
    s = (s or "").strip().lower()
    s = re.sub(r"[^a-z0-9_]+", "_", s)
    s = re.sub(r"_+", "_", s).strip("_")
    if not s:
        s = "field"
    if s[0].isdigit():
        s = f"f_{s}"
    return s

def _title_label_from_field(field: str) -> str:
    # Human-readable label (English Title Case); description will be Arabic from md
    return (field or "").replace("_", " ").strip().title()

def _ensure_module_def(module_name: str):
    # Optional helper to ensure Module Def exists (helps Desk organization)
    if not frappe.db.exists("Module Def", module_name):
        doc = frappe.get_doc({
            "doctype": "Module Def",
            "module_name": module_name,
            "app_name": APP_NAME,
            "custom": 1
        })
        doc.insert(ignore_permissions=True)

def _parse_md_tables(md_text: str):
    """
    Parse the documentation markdown into:
    [
      {
        "table_name": "colleges",
        "fields": [
          {"field":"id","type":"UUID","desc":"المعرف الفريد","reqd":True},
          ...
        ]
      }, ...
    ]
    """
    # Blocks begin with: ## ... (table_name)
    header_pat = re.compile(r"^##\s+.*?\(([^)]+)\)\s*$", re.MULTILINE)
    headers = list(header_pat.finditer(md_text))

    results = []
    for i, h in enumerate(headers):
        table_name = h.group(1).strip()
        start = h.end()
        end = headers[i + 1].start() if i + 1 < len(headers) else len(md_text)
        block = md_text[start:end]

        # We only care about tables we mapped
        if table_name not in TABLE_TO_DOCTYPE:
            continue

        lines = [ln.rstrip() for ln in block.splitlines()]
        table_lines = []
        in_table = False

        # Find the first fields table after "### الحقول:"
        for ln in lines:
            if ln.strip().startswith("| الحقل"):
                in_table = True
                continue
            if in_table:
                if not ln.strip().startswith("|"):
                    break
                if re.match(r"^\|\s*-+\s*\|", ln.strip()):
                    continue
                table_lines.append(ln)

        fields = []
        for ln in table_lines:
            cols = [c.strip() for c in ln.strip().strip("|").split("|")]
            if len(cols) < 4:
                continue
            field, ftype, desc, reqd = cols[0], cols[1], cols[2], cols[3]
            fields.append({
                "field": field.strip(),
                "type": ftype.strip(),
                "desc": desc.strip(),
                "reqd": ("✅" in reqd)
            })

        if fields:
            results.append({"table_name": table_name, "fields": fields})

    return results

def _extract_enum_options(type_str: str, desc: str):
    # Extract options from parentheses: (a/b/c) or (a,b,c)
    combined = f"{type_str} {desc}"
    m = re.search(r"\(([^)]+)\)", combined)
    if not m:
        return ""
    raw = m.group(1).strip()
    parts = re.split(r"\s*/\s*|\s*,\s*|\s*\|\s*", raw)
    parts = [p.strip() for p in parts if p.strip()]
    return "\n".join(parts)

def _guess_link_target(field_name: str):
    """
    FK convention in doc: xxx_id
    We attempt to map to known DocTypes.
    """
    if not field_name.endswith("_id"):
        return None
    base = field_name[:-3]

    # explicit guesses for this schema
    if base == "college":
        return "Colleges"
    if base == "program":
        return "Academic Programs"
    if base == "study_plan":
        return "Study Plans"
    if base == "center":
        return "Centers"

    # plural fallback
    plural = base + "s"
    if plural in TABLE_TO_DOCTYPE:
        return TABLE_TO_DOCTYPE[plural]
    return None

def _map_fieldtype(field: str, type_str: str, desc: str):
    t = (type_str or "").upper().strip()

    # Arrays
    if "[]" in t:
        return ("TABLE", "")

    # FK
    if "UUID" in t and field.endswith("_id"):
        target = _guess_link_target(field)
        if target:
            return ("LINK", target)

    if "UUID" in t:
        return ("DATA", "")

    if "VARCHAR" in t:
        return ("DATA", "")

    if t == "TEXT":
        return ("LONG_TEXT", "")

    if "DECIMAL" in t or t in ("FLOAT", "DOUBLE"):
        return ("FLOAT", "")

    if "INTEGER" in t or t in ("INT",):
        return ("INT", "")

    if "BOOLEAN" in t:
        return ("CHECK", "")

    if t == "DATE":
        return ("DATE", "")

    if "TIMESTAMP" in t or t == "DATETIME":
        return ("DATETIME", "")

    if "ENUM" in t:
        return ("SELECT", _extract_enum_options(t, desc))

    return ("DATA", "")

def _ensure_child_table(parent_table: str, array_field: str, array_desc_ar: str):
    """
    Create a child table DocType for TEXT[] fields.

    We keep it generic and bilingual:
    - text_ar
    - text_en
    - order_index
    """
    parent_dt = TABLE_TO_DOCTYPE[parent_table]
    child_dt = f"{parent_dt} {array_field.replace('_', ' ').title()}"

    if frappe.db.exists("DocType", child_dt):
        return child_dt

    module_name = TABLE_TO_MODULE.get(parent_table, "AAU")
    _ensure_module_def(module_name)

    fields = [
        {
            "fieldname": "text_ar",
            "fieldtype": "Data",
            "label": "النص بالعربي",
            "description": "القيمة باللغة العربية"
        },
        {
            "fieldname": "text_en",
            "fieldtype": "Data",
            "label": "النص بالإنجليزي",
            "description": "القيمة باللغة الإنجليزية"
        },
        {
            "fieldname": "order_index",
            "fieldtype": "Int",
            "label": "ترتيب العرض",
            "description": "ترتيب ظهور العنصر"
        }
    ]

    dt = frappe.get_doc({
        "doctype": "DocType",
        "name": child_dt,
        "module": module_name,
        "custom": 1,
        "istable": 1,
        "allow_rename": 0,
        "fields": fields,
        "permissions": [
            {
                "role": "System Manager",
                "read": 1, "write": 1, "create": 1, "delete": 1,
                "report": 1, "export": 1, "print": 1, "email": 1, "share": 1
            }
        ],
    })
    dt.insert(ignore_permissions=True)
    frappe.db.commit()
    return child_dt

def _build_doctype(table_name: str, field_rows: list):
    dt_name = TABLE_TO_DOCTYPE[table_name]
    module_name = TABLE_TO_MODULE.get(table_name, "AAU")
    _ensure_module_def(module_name)

    if frappe.db.exists("DocType", dt_name):
        print(f"SKIP (exists): {dt_name}")
        return

    fields = []
    field_order = []

    # Section break
    fields.append({
        "fieldname": "section_main",
        "fieldtype": "Section Break",
        "label": "البيانات الأساسية"
    })
    field_order.append("section_main")

    # Map fields in the same order as documentation
    for r in field_rows:
        raw = r["field"]
        type_str = r["type"]
        desc_ar = r["desc"] or "—"
        reqd = 1 if r["reqd"] else 0

        f_fieldname = _to_fieldname(raw)
        label = _title_label_from_field(raw)

        mapped, opt = _map_fieldtype(raw, type_str, desc_ar)

        # Arrays -> Child Table
        if mapped == "TABLE":
            child_dt = _ensure_child_table(table_name, raw, desc_ar)
            fields.append({
                "fieldname": f_fieldname,
                "fieldtype": "Table",
                "label": label,
                "description": desc_ar,
                "options": child_dt,
                "reqd": reqd
            })
            field_order.append(f_fieldname)
            continue

        # Link
        if mapped == "LINK":
            fields.append({
                "fieldname": f_fieldname,
                "fieldtype": "Link",
                "label": label,
                "description": desc_ar,
                "options": opt,
                "reqd": reqd
            })
            field_order.append(f_fieldname)
            continue

        # Select
        if mapped == "SELECT":
            fields.append({
                "fieldname": f_fieldname,
                "fieldtype": "Select",
                "label": label,
                "description": desc_ar,
                "options": opt,
                "reqd": reqd
            })
            field_order.append(f_fieldname)
            continue

        # Primitive
        ft_map = {
            "DATA": "Data",
            "LONG_TEXT": "Long Text",
            "FLOAT": "Float",
            "INT": "Int",
            "CHECK": "Check",
            "DATE": "Date",
            "DATETIME": "Datetime",
        }
        fieldtype = ft_map.get(mapped, "Data")

        field_doc = {
            "fieldname": f_fieldname,
            "fieldtype": fieldtype,
            "label": label,
            "description": desc_ar,
            "reqd": reqd
        }

        # Rules
        if raw == "slug":
            field_doc["unique"] = 1
            field_doc["reqd"] = 1

        if raw in ("created_at", "updated_at", "id"):
            field_doc["read_only"] = 1

        # is_active / is_published fields should be required as per doc
        if raw in ("is_active", "is_published"):
            field_doc["fieldtype"] = "Check"
            field_doc["reqd"] = reqd

        fields.append(field_doc)
        field_order.append(f_fieldname)

    # Create DocType
    dt = frappe.get_doc({
        "doctype": "DocType",
        "name": dt_name,
        "module": module_name,
        "custom": 1,
        "allow_rename": 1,
        "engine": "InnoDB",
        "track_changes": 1,
        "field_order": field_order,
        "fields": fields,
        "permissions": [
            {
                "role": "System Manager",
                "read": 1, "write": 1, "create": 1, "delete": 1,
                "report": 1, "export": 1, "print": 1, "email": 1, "share": 1
            }
        ],
        "sort_field": "modified",
        "sort_order": "DESC",
        "row_format": "Dynamic",
        "grid_page_length": 50,
        "rows_threshold_for_grid_search": 20
    })
    dt.insert(ignore_permissions=True)
    frappe.db.commit()
    print(f"CREATED: {dt_name}  |  module={module_name}")

def _load_md():
    return frappe.read_file(MD_PATH)

def _validate_parsed(parsed):
    parsed_names = {x["table_name"] for x in parsed}
    missing = [t for t in TABLE_TO_DOCTYPE.keys() if t not in parsed_names]
    if missing:
        msg = "لم يتم العثور على الجداول التالية داخل ملف التوثيق:\n- " + "\n- ".join(missing)
        raise RuntimeError(msg)

# -----------------------------
# Public API
# -----------------------------
def create_all():
    """
    Main entry: create all DocTypes from the MD file.
    """
    md = _load_md()
    parsed = _parse_md_tables(md)
    _validate_parsed(parsed)

    # Ensure your modules exist
    for m in ("Content", "Academic", "Public", "CMS", "AAU"):
        _ensure_module_def(m)

    # Create in a deterministic order (as the md file is ordered)
    for item in parsed:
        _build_doctype(item["table_name"], item["fields"])

    print("DONE ✅  تم إنشاء جميع الشاشات بنجاح")

