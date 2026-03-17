# -*- coding: utf-8 -*-
from __future__ import annotations

import frappe
from frappe.utils import cint


def _ensure_role_perm(doc, role: str) -> None:
    for perm in doc.get("permissions") or []:
        if perm.role == role and cint(perm.permlevel or 0) == 0:
            perm.read = 1
            perm.write = 1
            perm.create = 1
            perm.delete = 1
            perm.report = 1
            perm.print = 1
            perm.email = 1
            perm.export = 1
            perm.share = 1
            return

    doc.append(
        "permissions",
        {
            "role": role,
            "permlevel": 0,
            "read": 1,
            "write": 1,
            "create": 1,
            "delete": 1,
            "report": 1,
            "print": 1,
            "email": 1,
            "export": 1,
            "share": 1,
        },
    )


def _normalize_doctype(name: str, labels: dict[str, str], hidden_fields: set[str], field_order: list[str] | None = None) -> None:
    if not frappe.db.exists("DocType", name):
        return

    doc = frappe.get_doc("DocType", name)

    for field in doc.get("fields") or []:
        if field.fieldname in labels:
            field.label = labels[field.fieldname]
        if field.fieldname in hidden_fields:
            field.hidden = 1

    _ensure_role_perm(doc, "AAU Content Manager")

    if field_order:
        existing = [df.fieldname for df in doc.get("fields") or [] if df.fieldname]
        normalized_order = [item for item in field_order if item in existing]
        normalized_order.extend([item for item in existing if item not in normalized_order])
        doc.set("field_order", normalized_order)

    doc.save(ignore_permissions=True)


def execute():
    _normalize_doctype(
        "Events",
        labels={
            "main_section": "بيانات الفعالية",
            "event_title": "عنوان الفعالية",
            "description": "وصف الفعالية",
            "event_date": "تاريخ الفعالية",
            "location": "الموقع",
            "image": "صورة الفعالية",
            "is_published": "منشور",
            "display_order": "ترتيب العرض",
        },
        hidden_fields=set(),
        field_order=[
            "main_section",
            "event_title",
            "description",
            "event_date",
            "location",
            "image",
            "is_published",
            "display_order",
        ],
    )

    _normalize_doctype(
        "Centers",
        labels={
            "main_section": "بيانات المركز",
            "id": "المعرف",
            "title_ar": "اسم المركز",
            "desc_ar": "وصف المركز",
            "services": "الخدمات",
            "programs": "البرامج المرتبطة",
            "image": "صورة المركز",
            "location": "الموقع",
            "phone": "رقم الهاتف",
            "email": "البريد الإلكتروني",
            "is_published": "منشور",
            "display_order": "ترتيب العرض",
        },
        hidden_fields={"title_en", "desc_en"},
        field_order=[
            "main_section",
            "id",
            "title_ar",
            "title_en",
            "desc_ar",
            "desc_en",
            "services",
            "programs",
            "image",
            "location",
            "phone",
            "email",
            "is_published",
            "display_order",
        ],
    )

    _normalize_doctype(
        "Offers",
        labels={
            "main_section": "بيانات العرض",
            "id": "المعرف",
            "title_ar": "عنوان العرض",
            "desc_ar": "الوصف المختصر",
            "details_ar": "تفاصيل العرض",
            "category": "الفئة",
            "image": "صورة العرض",
            "valid_until": "صالح حتى",
            "target_audience_ar": "الفئة المستهدفة",
            "benefits_ar": "المزايا",
            "duration_ar": "المدة",
            "location_ar": "الموقع",
            "requirements_ar": "الشروط والمتطلبات",
            "apply_link": "رابط التقديم",
            "is_active": "مفعل",
            "is_published": "منشور",
            "display_order": "ترتيب العرض",
        },
        hidden_fields={
            "title_en",
            "desc_en",
            "details_en",
            "target_audience_en",
            "benefits_en",
            "duration_en",
            "location_en",
            "requirements_en",
        },
        field_order=[
            "main_section",
            "id",
            "title_ar",
            "title_en",
            "desc_ar",
            "desc_en",
            "details_ar",
            "details_en",
            "category",
            "image",
            "valid_until",
            "target_audience_ar",
            "target_audience_en",
            "benefits_ar",
            "benefits_en",
            "duration_ar",
            "duration_en",
            "location_ar",
            "location_en",
            "requirements_ar",
            "requirements_en",
            "apply_link",
            "is_active",
            "is_published",
            "display_order",
        ],
    )

    frappe.db.commit()
