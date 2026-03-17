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


def _normalize_doctype(
    name: str,
    labels: dict[str, str],
    hidden_fields: set[str],
    field_order: list[str] | None = None,
) -> None:
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
        "Blog Posts",
        labels={
            "main_section": "بيانات المقال",
            "id": "المعرف",
            "slug": "الرابط المختصر",
            "title_ar": "عنوان المقال",
            "excerpt_ar": "الملخص",
            "content_ar": "المحتوى",
            "author_name_ar": "اسم الكاتب",
            "author_avatar": "صورة الكاتب",
            "author_role_ar": "صفة الكاتب",
            "category": "معرف الفئة",
            "category_ar": "اسم الفئة",
            "image": "صورة المقال",
            "published_at": "تاريخ النشر",
            "read_time": "وقت القراءة",
            "views": "عدد المشاهدات",
            "tags": "الوسوم",
            "is_published": "منشور",
            "display_order": "ترتيب العرض",
        },
        hidden_fields={
            "title_en",
            "excerpt_en",
            "content_en",
            "author_name_en",
            "author_role_en",
            "category_en",
        },
        field_order=[
            "main_section",
            "id",
            "slug",
            "title_ar",
            "title_en",
            "excerpt_ar",
            "excerpt_en",
            "content_ar",
            "content_en",
            "author_name_ar",
            "author_name_en",
            "author_avatar",
            "author_role_ar",
            "author_role_en",
            "category",
            "category_ar",
            "category_en",
            "image",
            "published_at",
            "read_time",
            "views",
            "tags",
            "is_published",
            "display_order",
        ],
    )

    _normalize_doctype(
        "Faculty Members",
        labels={
            "main_section": "بيانات عضو هيئة التدريس",
            "full_name": "الاسم الكامل",
            "academic_title": "اللقب الأكاديمي",
            "linked_college": "الكلية المرتبطة",
            "department": "القسم الأكاديمي",
            "biography": "النبذة التعريفية",
            "photo": "الصورة الشخصية",
            "is_active": "مفعل",
        },
        hidden_fields=set(),
        field_order=[
            "main_section",
            "full_name",
            "academic_title",
            "linked_college",
            "department",
            "biography",
            "photo",
            "is_active",
        ],
    )

    frappe.db.commit()
