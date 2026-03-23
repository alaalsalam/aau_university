# -*- coding: utf-8 -*-
from __future__ import annotations

import json

import frappe


def apply_aau_workspaces() -> dict:
    main_workspace = _upsert_workspace(
        payload={
            "name": "aau",
            "label": "مركز إدارة موقع الجامعة",
            "title": "AAU",
            "module": "AAU",
            "icon": "website",
            "indicator_color": "blue",
            "public": 0,
            "is_hidden": 0,
            "hide_custom": 0,
            "content": json.dumps(
                [
                    {
                        "id": "aau_workspace_header",
                        "type": "header",
                        "data": {"text": "<span class=\"h4\">مركز إدارة موقع الجامعة (AAU)</span>", "col": 12},
                    },
                    {"id": "aau_card_site_content", "type": "card", "data": {"card_name": "المحتوى الأساسي للموقع", "col": 3}},
                    {"id": "aau_card_published", "type": "card", "data": {"card_name": "المحتوى المنشور", "col": 3}},
                    {"id": "aau_card_academic", "type": "card", "data": {"card_name": "المحتوى الأكاديمي", "col": 3}},
                    {"id": "aau_card_admin", "type": "card", "data": {"card_name": "الإدارة", "col": 3}},
                    {"id": "aau_card_requests", "type": "card", "data": {"card_name": "الطلبات والتفاعل", "col": 12}},
                ],
                ensure_ascii=False,
            ),
            "roles": [
                {"role": "AAU Content Manager"},
                {"role": "System Manager"},
                {"role": "Workspace Manager"},
                {"role": "Website Manager"},
            ],
            "links": [
                {"type": "Card Break", "label": "المحتوى الأساسي للموقع", "icon": "website"},
                {"type": "Link", "label": "الصفحة الرئيسية", "link_type": "DocType", "link_to": "Home Page"},
                {"type": "Link", "label": "عن الجامعة", "link_type": "DocType", "link_to": "About University"},
                {"type": "Link", "label": "صفحات AAU", "link_type": "DocType", "link_to": "AAU Page"},
                {"type": "Link", "label": "إعدادات الموقع", "link_type": "DocType", "link_to": "Website Settings"},
                {"type": "Link", "label": "قوائم التنقل", "link_type": "DocType", "link_to": "AAU Menu"},
                {"type": "Link", "label": "المكتبة الإعلامية", "link_type": "DocType", "link_to": "Media Library"},
                {"type": "Card Break", "label": "المحتوى المنشور", "icon": "file"},
                {"type": "Link", "label": "الأخبار", "link_type": "DocType", "link_to": "News"},
                {"type": "Link", "label": "الفعاليات", "link_type": "DocType", "link_to": "Events"},
                {"type": "Link", "label": "المدونة", "link_type": "DocType", "link_to": "Blog Posts"},
                {"type": "Link", "label": "الأسئلة الشائعة", "link_type": "DocType", "link_to": "FAQ"},
                {"type": "Link", "label": "المشاريع", "link_type": "DocType", "link_to": "Projects"},
                {"type": "Link", "label": "الحياة الجامعية", "link_type": "DocType", "link_to": "Campus Life"},
                {"type": "Link", "label": "المراكز", "link_type": "DocType", "link_to": "Centers"},
                {"type": "Link", "label": "العروض", "link_type": "DocType", "link_to": "Offers"},
                {"type": "Link", "label": "الشركاء", "link_type": "DocType", "link_to": "Partners"},
                {"type": "Card Break", "label": "المحتوى الأكاديمي", "icon": "education"},
                {"type": "Link", "label": "الكليات", "link_type": "DocType", "link_to": "Colleges"},
                {"type": "Link", "label": "البرامج الأكاديمية", "link_type": "DocType", "link_to": "Academic Programs"},
                {"type": "Link", "label": "أعضاء هيئة التدريس", "link_type": "DocType", "link_to": "Faculty Members"},
                {"type": "Card Break", "label": "الطلبات والتفاعل", "icon": "mail"},
                {"type": "Link", "label": "رسائل التواصل", "link_type": "DocType", "link_to": "Contact Us Messages"},
                {"type": "Link", "label": "طلبات الانضمام", "link_type": "DocType", "link_to": "Join Requests"},
                {"type": "Card Break", "label": "الإدارة", "icon": "setting-gear"},
                {"type": "Link", "label": "المستخدمون", "link_type": "DocType", "link_to": "User"},
                {"type": "Link", "label": "الأدوار", "link_type": "DocType", "link_to": "Role"},
                {"type": "Link", "label": "الترجمة", "link_type": "DocType", "link_to": "Translation"},
                {"type": "Link", "label": "مساحات العمل", "link_type": "DocType", "link_to": "Workspace"},
            ],
        }
    )

    admin_workspace = _upsert_workspace(
        payload={
            "name": "aau-admin-control",
            "label": "مركز إدارة النظام",
            "title": "AAU Admin Control",
            "module": "AAU",
            "icon": "setting-gear",
            "indicator_color": "orange",
            "public": 0,
            "is_hidden": 0,
            "hide_custom": 0,
            "content": json.dumps(
                [
                    {"id": "aau_admin_header", "type": "header", "data": {"text": "<span class=\"h4\">AAU Admin Control</span>", "col": 12}},
                    {"id": "aau_admin_card_access", "type": "card", "data": {"card_name": "إدارة المستخدمين والصلاحيات", "col": 6}},
                    {"id": "aau_admin_card_content", "type": "card", "data": {"card_name": "إدارة المحتوى", "col": 6}},
                ],
                ensure_ascii=False,
            ),
            "roles": [
                {"role": "System Manager"},
                {"role": "Workspace Manager"},
            ],
            "links": [
                {"type": "Card Break", "label": "إدارة المستخدمين والصلاحيات", "icon": "users"},
                {"type": "Link", "label": "المستخدمون", "link_type": "DocType", "link_to": "User"},
                {"type": "Link", "label": "الأدوار", "link_type": "DocType", "link_to": "Role"},
                {"type": "Link", "label": "مساحات العمل", "link_type": "DocType", "link_to": "Workspace"},
                {"type": "Link", "label": "الترجمة", "link_type": "DocType", "link_to": "Translation"},
                {"type": "Link", "label": "إعدادات الموقع", "link_type": "DocType", "link_to": "Website Settings"},
                {"type": "Card Break", "label": "إدارة المحتوى", "icon": "file"},
                {"type": "Link", "label": "الأخبار", "link_type": "DocType", "link_to": "News"},
                {"type": "Link", "label": "الفعاليات", "link_type": "DocType", "link_to": "Events"},
                {"type": "Link", "label": "المدونة", "link_type": "DocType", "link_to": "Blog Posts"},
                {"type": "Link", "label": "الصفحة الرئيسية", "link_type": "DocType", "link_to": "Home Page"},
                {"type": "Link", "label": "عن الجامعة", "link_type": "DocType", "link_to": "About University"},
            ],
        }
    )

    frappe.db.commit()
    frappe.db.set_value("Workspace", "aau", "label", "مركز إدارة موقع الجامعة", update_modified=False)
    frappe.db.set_value("Workspace", "aau", "title", "AAU", update_modified=False)
    frappe.clear_cache()
    return {
        "main_workspace": main_workspace,
        "admin_workspace": admin_workspace,
    }


def _upsert_workspace(*, payload: dict) -> str:
    workspace_name = payload["name"]
    update_payload = dict(payload)
    if frappe.db.exists("Workspace", workspace_name):
        doc = frappe.get_doc("Workspace", workspace_name)
        doc.update(update_payload)
        doc.save(ignore_permissions=True)
        return doc.name

    existing_by_title = frappe.db.get_value("Workspace", {"title": payload.get("title")}, "name")
    if existing_by_title:
        doc = frappe.get_doc("Workspace", existing_by_title)
        update_payload.pop("name", None)
        doc.update(update_payload)
        doc.save(ignore_permissions=True)
        return doc.name

    frappe.get_doc({"doctype": "Workspace", **update_payload}).insert(ignore_permissions=True)
    return workspace_name
