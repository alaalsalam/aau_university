# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from typing import Any

import frappe
from frappe.model.rename_doc import rename_doc
from frappe.utils import cint


ROLE_SPECS = [
    {"name": "System Manager", "desk_access": 1},
    {"name": "Workspace Manager", "desk_access": 1},
    {"name": "Website Manager", "desk_access": 1},
    {"name": "Desk User", "desk_access": 1},
    {"name": "AAU Content Manager", "desk_access": 1},
    {"name": "AAU Executive Manager", "desk_access": 1},
    {"name": "AAU Site Manager", "desk_access": 1},
    {"name": "AAU Editor", "desk_access": 1},
    {"name": "AAU Coordinator", "desk_access": 1},
    {"name": "AAU Portal User", "desk_access": 0},
    {"name": "AAU Student User", "desk_access": 0},
    {"name": "AAU Instructor User", "desk_access": 0},
]

ROLE_PROFILES = {
    "AAU Site Manager": [
        "Desk User",
        "Website Manager",
        "Workspace Manager",
        "AAU Site Manager",
        "AAU Content Manager",
    ],
    "AAU Executive Manager": [
        "Desk User",
        "Workspace Manager",
        "AAU Executive Manager",
    ],
    "AAU Editor": [
        "Desk User",
        "AAU Editor",
    ],
    "AAU Coordinator": [
        "Desk User",
        "AAU Coordinator",
    ],
    "AAU Student User": [
        "AAU Portal User",
        "Student",
        "AAU Student User",
    ],
    "AAU Instructor User": [
        "AAU Portal User",
        "Instructor",
        "AAU Instructor User",
    ],
}

DOCTYPE_ROLE_RULES = {
    "AAU Site Manager": {
            "full": [
                "User",
                "Role",
                "Role Profile",
                "Workspace",
                "Activity Log",
                "Access Log",
                "Version",
                "Translation",
            "Website Settings",
            "System Settings",
            "Data Export",
            "Home Page",
                "About University",
                "About Team Member",
                "AAU Page",
                "Contact Page Settings",
                "AAU Menu",
            "Media Library",
            "Smart Chat Settings",
            "News",
            "Events",
            "Blog Posts",
            "FAQ",
            "Projects",
            "Offers",
            "Partners",
            "Research and Publications",
            "Campus Life",
            "Centers",
            "Colleges",
            "Academic Departments",
            "Academic Programs",
            "Faculty Members",
            "Admission Requirements",
            "Contact Us Messages",
            "Email Requests",
            "Join Requests",
            "File",
        ],
    },
    "AAU Executive Manager": {
            "read_only": [
                "User",
                "Role",
                "Role Profile",
                "Activity Log",
                "Access Log",
                "Version",
                "News",
            "Events",
            "Projects",
            "Research and Publications",
            "Colleges",
            "Academic Programs",
            "Faculty Members",
            "Centers",
            "Contact Us Messages",
            "Email Requests",
            "Join Requests",
            "Data Export",
        ],
    },
    "AAU Editor": {
        "full": [
            "News",
            "Events",
            "Projects",
            "Blog Posts",
            "Research and Publications",
            "Partners",
            "Offers",
            "FAQ",
            "AAU Page",
            "Media Library",
            "File",
        ],
        "read_only": [
            "AAU Menu",
            "Home Page",
            "About University",
            "Contact Page Settings",
            "Website Settings",
        ],
    },
    "AAU Coordinator": {
        "full": [
            "Centers",
            "Colleges",
            "Academic Departments",
            "Academic Programs",
            "Faculty Members",
            "Admission Requirements",
            "Campus Life",
            "About Team Member",
        ],
        "read_only": [
            "Research and Publications",
            "Media Library",
        ],
    },
}


def apply_aau_workspaces() -> dict[str, Any]:
    """Create/update AAU workspaces, metrics and navigation in one idempotent pass."""

    _ensure_module_def()
    _ensure_roles()
    _ensure_role_profiles()
    _ensure_doctype_permissions()
    _ensure_contact_page_settings()

    number_cards = _ensure_number_cards()
    charts = _ensure_dashboard_charts()

    workspaces = [
        {
            "name": "aau",
            "label": "مركز إدارة موقع الجامعة",
            "title": "AAU",
            "sequence_id": 71,
            "icon": "website",
            "indicator_color": "blue",
            "roles": [
                "System Manager",
                "Workspace Manager",
                "Website Manager",
                "AAU Content Manager",
                "AAU Site Manager",
                "AAU Editor",
                "AAU Coordinator",
            ],
            "links": [
                {"type": "Card Break", "label": "المحتوى الرئيسي", "icon": "website"},
                {"type": "Link", "label": "الصفحة الرئيسية", "link_type": "DocType", "link_to": "Home Page"},
                {"type": "Link", "label": "عن الجامعة", "link_type": "DocType", "link_to": "About University"},
                {"type": "Link", "label": "الفريق الإداري", "link_type": "DocType", "link_to": "About Team Member"},
                {"type": "Link", "label": "صفحات AAU", "link_type": "DocType", "link_to": "AAU Page"},
                {"type": "Link", "label": "تواصل معنا", "link_type": "DocType", "link_to": "Contact Page Settings"},
                {"type": "Link", "label": "إعدادات الموقع", "link_type": "DocType", "link_to": "Website Settings"},
                {"type": "Link", "label": "قوائم التنقل", "link_type": "DocType", "link_to": "AAU Menu"},
                {"type": "Link", "label": "المكتبة الإعلامية", "link_type": "DocType", "link_to": "Media Library"},
                {"type": "Card Break", "label": "التسجيل والقبول", "icon": "check"},
                {"type": "Link", "label": "متطلبات القبول", "link_type": "DocType", "link_to": "Admission Requirements"},
                {"type": "Link", "label": "طلبات الانضمام", "link_type": "DocType", "link_to": "Join Requests"},
                {"type": "Link", "label": "طلبات البريد الإلكتروني", "link_type": "DocType", "link_to": "Email Requests"},
                {"type": "Card Break", "label": "المحتوى المنشور", "icon": "file"},
                {"type": "Link", "label": "الأخبار", "link_type": "DocType", "link_to": "News"},
                {"type": "Link", "label": "الفعاليات", "link_type": "DocType", "link_to": "Events"},
                {"type": "Link", "label": "المدونة", "link_type": "DocType", "link_to": "Blog Posts"},
                {"type": "Link", "label": "الأسئلة الشائعة", "link_type": "DocType", "link_to": "FAQ"},
                {"type": "Link", "label": "المشاريع", "link_type": "DocType", "link_to": "Projects"},
                {"type": "Link", "label": "العروض", "link_type": "DocType", "link_to": "Offers"},
                {"type": "Link", "label": "الشركاء", "link_type": "DocType", "link_to": "Partners"},
                {"type": "Card Break", "label": "البحث العلمي", "icon": "education"},
                {"type": "Link", "label": "المقالات العلمية", "link_type": "DocType", "link_to": "Research and Publications"},
                {"type": "Link", "label": "المجلة العلمية", "link_type": "DocType", "link_to": "Research and Publications"},
                {"type": "Link", "label": "الحياة الجامعية", "link_type": "DocType", "link_to": "Campus Life"},
                {"type": "Card Break", "label": "المراكز والحياة الجامعية", "icon": "folder-open"},
                {"type": "Link", "label": "المراكز", "link_type": "DocType", "link_to": "Centers"},
                {"type": "Card Break", "label": "الأكاديمي والكليات", "icon": "education"},
                {"type": "Link", "label": "الكليات", "link_type": "DocType", "link_to": "Colleges"},
                {"type": "Link", "label": "الأقسام الأكاديمية", "link_type": "DocType", "link_to": "Academic Departments"},
                {"type": "Link", "label": "البرامج الأكاديمية", "link_type": "DocType", "link_to": "Academic Programs"},
                {"type": "Link", "label": "أعضاء هيئة التدريس", "link_type": "DocType", "link_to": "Faculty Members"},
                {"type": "Link", "label": "متطلبات القبول", "link_type": "DocType", "link_to": "Admission Requirements"},
                {"type": "Card Break", "label": "الطلبات", "icon": "mail"},
                {"type": "Link", "label": "رسائل التواصل", "link_type": "DocType", "link_to": "Contact Us Messages"},
                {"type": "Link", "label": "طلبات البريد الإلكتروني", "link_type": "DocType", "link_to": "Email Requests"},
                {"type": "Link", "label": "طلبات الانضمام", "link_type": "DocType", "link_to": "Join Requests"},
                {"type": "Card Break", "label": "الإدارة والنظام", "icon": "setting-gear"},
                {"type": "Link", "label": "المستخدمون", "link_type": "DocType", "link_to": "User"},
                {"type": "Link", "label": "الأدوار", "link_type": "DocType", "link_to": "Role"},
                {"type": "Link", "label": "الترجمة", "link_type": "DocType", "link_to": "Translation"},
                {"type": "Link", "label": "مساحات العمل", "link_type": "DocType", "link_to": "Workspace"},
            ],
            "shortcuts": [
                {"type": "DocType", "label": "الأخبار", "link_to": "News", "doc_view": "List"},
                {"type": "DocType", "label": "المقالات العلمية", "link_to": "Research and Publications", "doc_view": "List"},
                {"type": "DocType", "label": "المجلة العلمية", "link_to": "Research and Publications", "doc_view": "List"},
                {"type": "DocType", "label": "الفعاليات", "link_to": "Events", "doc_view": "List"},
                {"type": "DocType", "label": "الكليات", "link_to": "Colleges", "doc_view": "List"},
                {"type": "DocType", "label": "البرامج الأكاديمية", "link_to": "Academic Programs", "doc_view": "List"},
                {"type": "DocType", "label": "المراكز", "link_to": "Centers", "doc_view": "List"},
                {"type": "DocType", "label": "الحياة الجامعية", "link_to": "Campus Life", "doc_view": "List"},
                {"type": "DocType", "label": "رسائل التواصل", "link_to": "Contact Us Messages", "doc_view": "List"},
                {"type": "DocType", "label": "طلبات البريد الإلكتروني", "link_to": "Email Requests", "doc_view": "List"},
                {"type": "DocType", "label": "طلبات الانضمام", "link_to": "Join Requests", "doc_view": "List"},
                {"type": "DocType", "label": "متطلبات القبول", "link_to": "Admission Requirements", "doc_view": "List"},
                {"type": "DocType", "label": "العروض", "link_to": "Offers", "doc_view": "List"},
                {"type": "DocType", "label": "الشركاء", "link_to": "Partners", "doc_view": "List"},
                {"type": "DocType", "label": "المستخدمون", "link_to": "User", "doc_view": "List"},
            ],
            "number_cards": [
                number_cards.get("users"),
                number_cards.get("news"),
                number_cards.get("events"),
                number_cards.get("contacts"),
            ],
            "charts": [charts.get("news_trend"), charts.get("events_trend")],
        },
        {
            "name": "aau-executive-dashboard",
            "label": "لوحة المؤشرات التنفيذية",
            "title": "AAU Executive Dashboard",
            "sequence_id": 72,
            "icon": "dashboard",
            "indicator_color": "green",
            "roles": [
                "System Manager",
                "Workspace Manager",
                "AAU Executive Manager",
                "AAU Site Manager",
            ],
            "links": [
                {"type": "Card Break", "label": "المؤشرات العامة", "icon": "dashboard"},
                {"type": "Link", "label": "المستخدمون", "link_type": "DocType", "link_to": "User"},
                {"type": "Link", "label": "الطلاب", "link_type": "DocType", "link_to": "Student"},
                {"type": "Link", "label": "المدرسون", "link_type": "DocType", "link_to": "Instructor"},
                {"type": "Card Break", "label": "المحتوى العام", "icon": "website"},
                {"type": "Link", "label": "الأخبار", "link_type": "DocType", "link_to": "News"},
                {"type": "Link", "label": "الفعاليات", "link_type": "DocType", "link_to": "Events"},
                {"type": "Link", "label": "الكليات", "link_type": "DocType", "link_to": "Colleges"},
                {"type": "Link", "label": "البرامج الأكاديمية", "link_type": "DocType", "link_to": "Academic Programs"},
                {"type": "Card Break", "label": "مركز المتابعة", "icon": "list"},
                {"type": "Link", "label": "رسائل التواصل", "link_type": "DocType", "link_to": "Contact Us Messages"},
                {"type": "Link", "label": "طلبات البريد الإلكتروني", "link_type": "DocType", "link_to": "Email Requests"},
                {"type": "Link", "label": "طلبات الانضمام", "link_type": "DocType", "link_to": "Join Requests"},
            ],
            "shortcuts": [
                {"type": "DocType", "label": "تقرير المستخدمين", "link_to": "User", "doc_view": "Report Builder"},
                {"type": "DocType", "label": "تقرير الطلاب", "link_to": "Student", "doc_view": "Report Builder"},
                {"type": "DocType", "label": "تقرير المدرسين", "link_to": "Instructor", "doc_view": "Report Builder"},
                {"type": "DocType", "label": "تقرير الأخبار", "link_to": "News", "doc_view": "Report Builder"},
                {"type": "DocType", "label": "تقرير الفعاليات", "link_to": "Events", "doc_view": "Report Builder"},
            ],
            "number_cards": [
                number_cards.get("users"),
                number_cards.get("students"),
                number_cards.get("instructors"),
                number_cards.get("news"),
                number_cards.get("events"),
                number_cards.get("programs"),
            ],
            "charts": [charts.get("news_trend"), charts.get("events_trend"), charts.get("contacts_trend")],
        },
        {
            "name": "aau-content-operations",
            "label": "إدارة المحتوى والنشر",
            "title": "AAU Content Operations",
            "sequence_id": 73,
            "icon": "file",
            "indicator_color": "cyan",
            "roles": [
                "System Manager",
                "Workspace Manager",
                "Website Manager",
                "AAU Content Manager",
                "AAU Site Manager",
                "AAU Editor",
            ],
            "links": [
                {"type": "Card Break", "label": "صفحات الموقع", "icon": "website"},
                {"type": "Link", "label": "الصفحة الرئيسية", "link_type": "DocType", "link_to": "Home Page"},
                {"type": "Link", "label": "عن الجامعة", "link_type": "DocType", "link_to": "About University"},
                {"type": "Link", "label": "صفحات AAU", "link_type": "DocType", "link_to": "AAU Page"},
                {"type": "Link", "label": "تواصل معنا", "link_type": "DocType", "link_to": "Contact Page Settings"},
                {"type": "Link", "label": "قوائم التنقل", "link_type": "DocType", "link_to": "AAU Menu"},
                {"type": "Card Break", "label": "النشر", "icon": "file"},
                {"type": "Link", "label": "الأخبار", "link_type": "DocType", "link_to": "News"},
                {"type": "Link", "label": "الفعاليات", "link_type": "DocType", "link_to": "Events"},
                {"type": "Link", "label": "المدونة", "link_type": "DocType", "link_to": "Blog Posts"},
                {"type": "Link", "label": "الأسئلة الشائعة", "link_type": "DocType", "link_to": "FAQ"},
                {"type": "Card Break", "label": "الملفات والوسائط", "icon": "folder-open"},
                {"type": "Link", "label": "المكتبة الإعلامية", "link_type": "DocType", "link_to": "Media Library"},
                {"type": "Link", "label": "إعدادات الموقع", "link_type": "DocType", "link_to": "Website Settings"},
                {"type": "Link", "label": "الترجمة", "link_type": "DocType", "link_to": "Translation"},
            ],
            "shortcuts": [
                {"type": "DocType", "label": "قائمة الأخبار", "link_to": "News", "doc_view": "List"},
                {"type": "DocType", "label": "قائمة الفعاليات", "link_to": "Events", "doc_view": "List"},
                {"type": "DocType", "label": "تحليل الأخبار", "link_to": "News", "doc_view": "Report Builder"},
                {"type": "DocType", "label": "تحليل الفعاليات", "link_to": "Events", "doc_view": "Report Builder"},
            ],
            "number_cards": [
                number_cards.get("news"),
                number_cards.get("events"),
                number_cards.get("contacts"),
                number_cards.get("join_requests"),
            ],
            "charts": [charts.get("news_trend"), charts.get("events_trend")],
        },
        {
            "name": "aau-academic-operations",
            "label": "الإدارة الأكاديمية",
            "title": "AAU Academic Operations",
            "sequence_id": 74,
            "icon": "education",
            "indicator_color": "purple",
            "roles": [
                "System Manager",
                "Workspace Manager",
                "AAU Executive Manager",
                "AAU Site Manager",
                "AAU Coordinator",
            ],
            "links": [
                {"type": "Card Break", "label": "البنية الأكاديمية", "icon": "education"},
                {"type": "Link", "label": "الكليات", "link_type": "DocType", "link_to": "Colleges"},
                {"type": "Link", "label": "البرامج الأكاديمية", "link_type": "DocType", "link_to": "Academic Programs"},
                {"type": "Link", "label": "أعضاء هيئة التدريس", "link_type": "DocType", "link_to": "Faculty Members"},
                {"type": "Card Break", "label": "المستخدمون الأكاديميون", "icon": "users"},
                {"type": "Link", "label": "الطلاب", "link_type": "DocType", "link_to": "Student"},
                {"type": "Link", "label": "المدرسون", "link_type": "DocType", "link_to": "Instructor"},
            ],
            "shortcuts": [
                {"type": "DocType", "label": "تحليل الطلاب", "link_to": "Student", "doc_view": "Report Builder"},
                {"type": "DocType", "label": "تحليل المدرسين", "link_to": "Instructor", "doc_view": "Report Builder"},
                {"type": "DocType", "label": "تحليل البرامج", "link_to": "Academic Programs", "doc_view": "Report Builder"},
                {"type": "DocType", "label": "تحليل الكليات", "link_to": "Colleges", "doc_view": "Report Builder"},
            ],
            "number_cards": [
                number_cards.get("students"),
                number_cards.get("instructors"),
                number_cards.get("colleges"),
                number_cards.get("programs"),
                number_cards.get("faculty"),
            ],
            "charts": [charts.get("students_trend")],
        },
        {
            "name": "aau-control-center",
            "label": "لوحة التحكم المركزية",
            "title": "AAU Control Center",
            "sequence_id": 75,
            "icon": "setting-gear",
            "indicator_color": "orange",
            "roles": ["System Manager", "Workspace Manager", "AAU Site Manager", "AAU Executive Manager"],
            "links": [
                {"type": "Card Break", "label": "لوحة التحكم والإدارة", "icon": "setting-gear"},
                {"type": "Link", "label": "المستخدمون", "link_type": "DocType", "link_to": "User"},
                {"type": "Link", "label": "الأدوار", "link_type": "DocType", "link_to": "Role"},
                {"type": "Link", "label": "ملفات الأدوار", "link_type": "DocType", "link_to": "Role Profile"},
                {"type": "Link", "label": "مساحات العمل", "link_type": "DocType", "link_to": "Workspace"},
                {"type": "Link", "label": "إدارة الصلاحيات", "link_type": "Page", "link_to": "permission-manager"},
                {"type": "Link", "label": "سجل النشاط", "link_type": "DocType", "link_to": "Activity Log"},
                {"type": "Link", "label": "سجل الوصول", "link_type": "DocType", "link_to": "Access Log"},
                {"type": "Link", "label": "سجل التعديلات", "link_type": "DocType", "link_to": "Version"},
                {"type": "Link", "label": "الترجمة", "link_type": "DocType", "link_to": "Translation"},
                {"type": "Link", "label": "إعدادات الموقع", "link_type": "DocType", "link_to": "Website Settings"},
                {"type": "Link", "label": "تواصل معنا", "link_type": "DocType", "link_to": "Contact Page Settings"},
                {"type": "Link", "label": "إعدادات الشات الذكي", "link_type": "DocType", "link_to": "Smart Chat Settings"},
                {"type": "Link", "label": "الإعدادات العامة", "link_type": "DocType", "link_to": "System Settings"},
                {"type": "Card Break", "label": "المتابعة والنسخ والتصدير", "icon": "folder-open"},
                {"type": "Link", "label": "تصدير البيانات", "link_type": "DocType", "link_to": "Data Export"},
                {"type": "Link", "label": "النسخ الاحتياطية", "link_type": "Page", "link_to": "backups"},
                {"type": "Card Break", "label": "اعتماد ومراقبة المحتوى", "icon": "file"},
                {"type": "Link", "label": "الأخبار", "link_type": "DocType", "link_to": "News"},
                {"type": "Link", "label": "الفعاليات", "link_type": "DocType", "link_to": "Events"},
                {"type": "Link", "label": "المشاريع", "link_type": "DocType", "link_to": "Projects"},
                {"type": "Link", "label": "المدونة", "link_type": "DocType", "link_to": "Blog Posts"},
                {"type": "Link", "label": "المجلة والمقالات", "link_type": "DocType", "link_to": "Research and Publications"},
                {"type": "Link", "label": "الشركاء", "link_type": "DocType", "link_to": "Partners"},
                {"type": "Link", "label": "العروض", "link_type": "DocType", "link_to": "Offers"},
                {"type": "Link", "label": "الأسئلة الشائعة", "link_type": "DocType", "link_to": "FAQ"},
                {"type": "Card Break", "label": "التنسيق الأكاديمي والميداني", "icon": "education"},
                {"type": "Link", "label": "الكليات", "link_type": "DocType", "link_to": "Colleges"},
                {"type": "Link", "label": "المراكز", "link_type": "DocType", "link_to": "Centers"},
                {"type": "Link", "label": "الأقسام الأكاديمية", "link_type": "DocType", "link_to": "Academic Departments"},
                {"type": "Link", "label": "البرامج الأكاديمية", "link_type": "DocType", "link_to": "Academic Programs"},
                {"type": "Link", "label": "أعضاء هيئة التدريس", "link_type": "DocType", "link_to": "Faculty Members"},
                {"type": "Link", "label": "متطلبات القبول", "link_type": "DocType", "link_to": "Admission Requirements"},
                {"type": "Card Break", "label": "المراسلات والطلبات", "icon": "mail"},
                {"type": "Link", "label": "رسائل التواصل", "link_type": "DocType", "link_to": "Contact Us Messages"},
                {"type": "Link", "label": "طلبات البريد الإلكتروني", "link_type": "DocType", "link_to": "Email Requests"},
                {"type": "Link", "label": "طلبات الانضمام", "link_type": "DocType", "link_to": "Join Requests"},
            ],
            "shortcuts": [
                {"type": "DocType", "label": "لوحة المستخدمين", "link_to": "User", "doc_view": "List"},
                {"type": "DocType", "label": "مراجعة الصلاحيات", "link_to": "Role", "doc_view": "List"},
                {"type": "DocType", "label": "ملفات الأدوار", "link_to": "Role Profile", "doc_view": "List"},
                {"type": "Page", "label": "مدير الصلاحيات", "link_to": "permission-manager"},
                {"type": "DocType", "label": "سجل النشاط", "link_to": "Activity Log", "doc_view": "List"},
                {"type": "DocType", "label": "سجل التعديلات", "link_to": "Version", "doc_view": "List"},
                {"type": "DocType", "label": "مراجعة المساحات", "link_to": "Workspace", "doc_view": "List"},
                {"type": "DocType", "label": "إعدادات الشات الذكي", "link_to": "Smart Chat Settings", "doc_view": "List"},
                {"type": "DocType", "label": "تصدير البيانات", "link_to": "Data Export", "doc_view": "List"},
                {"type": "Page", "label": "النسخ الاحتياطية", "link_to": "backups"},
                {"type": "DocType", "label": "أخبار بانتظار النشر", "link_to": "News", "doc_view": "List"},
                {"type": "DocType", "label": "فعاليات بانتظار النشر", "link_to": "Events", "doc_view": "List"},
                {"type": "DocType", "label": "مشاريع بانتظار النشر", "link_to": "Projects", "doc_view": "List"},
            ],
            "number_cards": [
                number_cards.get("users"),
                number_cards.get("students"),
                number_cards.get("instructors"),
                number_cards.get("draft_news"),
                number_cards.get("draft_events"),
                number_cards.get("draft_projects"),
                number_cards.get("hidden_colleges"),
                number_cards.get("inactive_programs"),
                number_cards.get("inactive_faculty"),
                number_cards.get("contacts"),
                number_cards.get("join_requests"),
            ],
            "charts": [
                charts.get("news_trend"),
                charts.get("events_trend"),
                charts.get("projects_trend"),
                charts.get("contacts_trend"),
                charts.get("join_requests_trend"),
                charts.get("users_trend"),
            ],
        },
        {
            "name": "student-portal-operations",
            "label": "تشغيل بوابة الطالب",
            "title": "Student Portal Operations",
            "sequence_id": 76,
            "icon": "education",
            "indicator_color": "blue",
            "roles": [
                "System Manager",
                "Workspace Manager",
                "AAU Site Manager",
                "AAU Coordinator",
                "Education Manager",
                "Academics User",
            ],
            "links": [
                {"type": "Card Break", "label": "الملف والسجل الأكاديمي", "icon": "users"},
                {"type": "Link", "label": "الطلاب", "link_type": "DocType", "link_to": "Student"},
                {"type": "Link", "label": "الالتحاق بالبرامج", "link_type": "DocType", "link_to": "Program Enrollment"},
                {"type": "Card Break", "label": "المقررات والجدول", "icon": "education"},
                {"type": "Link", "label": "تسجيل المقررات", "link_type": "DocType", "link_to": "Course Enrollment"},
                {"type": "Link", "label": "المقررات", "link_type": "DocType", "link_to": "Course"},
                {"type": "Link", "label": "المجموعات الطلابية", "link_type": "DocType", "link_to": "Student Group"},
                {"type": "Link", "label": "الجداول الدراسية", "link_type": "DocType", "link_to": "Course Schedule"},
                {"type": "Card Break", "label": "الدرجات والمواد", "icon": "folder-open"},
                {"type": "Link", "label": "نتائج التقييم", "link_type": "DocType", "link_to": "Assessment Result"},
                {"type": "Link", "label": "الملفات التعليمية", "link_type": "DocType", "link_to": "File"},
                {"type": "Card Break", "label": "الاستبيانات", "icon": "small-message"},
                {"type": "Link", "label": "استبيانات البوابة", "link_type": "DocType", "link_to": "Student Portal Survey Response"},
                {"type": "Card Break", "label": "المالية", "icon": "money"},
                {"type": "Link", "label": "الرسوم", "link_type": "DocType", "link_to": "Fees"},
                {"type": "Link", "label": "دفعات التحصيل", "link_type": "DocType", "link_to": "Payment Entry"},
            ],
            "shortcuts": [
                {"type": "DocType", "label": "بيانات الطالب", "link_to": "Student", "doc_view": "List"},
                {"type": "DocType", "label": "مقررات الطالب", "link_to": "Course Enrollment", "doc_view": "List"},
                {"type": "DocType", "label": "الجدول الدراسي", "link_to": "Course Schedule", "doc_view": "List"},
                {"type": "DocType", "label": "درجات الطالب", "link_to": "Assessment Result", "doc_view": "List"},
                {"type": "DocType", "label": "مواد المقررات", "link_to": "File", "doc_view": "List"},
                {"type": "DocType", "label": "نتائج الاستبيانات", "link_to": "Student Portal Survey Response", "doc_view": "List"},
            ],
            "number_cards": [
                number_cards.get("students"),
                number_cards.get("programs"),
            ],
            "charts": [charts.get("students_trend")],
        },
        {
            "name": "doctor-portal-operations",
            "label": "تشغيل بوابة الدكتور",
            "title": "Doctor Portal Operations",
            "sequence_id": 77,
            "icon": "user",
            "indicator_color": "blue",
            "roles": [
                "System Manager",
                "Workspace Manager",
                "AAU Site Manager",
                "Education Manager",
                "Academics User",
                "Instructor",
            ],
            "links": [
                {"type": "Card Break", "label": "الملف الأكاديمي", "icon": "user"},
                {"type": "Link", "label": "المدرسون", "link_type": "DocType", "link_to": "Instructor"},
                {"type": "Link", "label": "الطلاب", "link_type": "DocType", "link_to": "Student"},
                {"type": "Card Break", "label": "المقررات والجدول", "icon": "education"},
                {"type": "Link", "label": "المقررات", "link_type": "DocType", "link_to": "Course"},
                {"type": "Link", "label": "الجداول الدراسية", "link_type": "DocType", "link_to": "Course Schedule"},
                {"type": "Card Break", "label": "الدرجات والتقييم", "icon": "folder-open"},
                {"type": "Link", "label": "نتائج التقييم", "link_type": "DocType", "link_to": "Assessment Result"},
                {"type": "Card Break", "label": "الإعلانات والرسائل", "icon": "mail"},
                {"type": "Link", "label": "الرسائل والإعلانات", "link_type": "DocType", "link_to": "Communication"},
                {"type": "Card Break", "label": "المواد التعليمية", "icon": "folder-open"},
                {"type": "Link", "label": "ملفات المواد", "link_type": "DocType", "link_to": "File"},
                {"type": "Card Break", "label": "المالية", "icon": "money"},
                {"type": "Link", "label": "دفعات التحصيل", "link_type": "DocType", "link_to": "Payment Entry"},
            ],
            "shortcuts": [
                {"type": "DocType", "label": "المدرسون", "link_to": "Instructor", "doc_view": "List"},
                {"type": "DocType", "label": "المقررات", "link_to": "Course", "doc_view": "List"},
                {"type": "DocType", "label": "الجدول الدراسي", "link_to": "Course Schedule", "doc_view": "List"},
                {"type": "DocType", "label": "درجات الطلاب", "link_to": "Assessment Result", "doc_view": "List"},
                {"type": "DocType", "label": "الرسائل والإعلانات", "link_to": "Communication", "doc_view": "List"},
                {"type": "DocType", "label": "ملفات المواد", "link_to": "File", "doc_view": "List"},
            ],
            "number_cards": [
                number_cards.get("instructors"),
                number_cards.get("students"),
                number_cards.get("programs"),
            ],
            "charts": [charts.get("students_trend")],
        },
    ]

    workspace_names = []
    for definition in workspaces:
        workspace_names.append(_upsert_workspace(definition))

    _hide_legacy_workspace("AAU Content Hub")

    frappe.db.commit()
    frappe.clear_cache()

    return {
        "ok": True,
        "workspaces": workspace_names,
        "number_cards": sorted([name for name in number_cards.values() if name]),
        "charts": sorted([name for name in charts.values() if name]),
    }


def _ensure_contact_page_settings() -> None:
    if not frappe.db.exists("DocType", "Contact Page Settings"):
        return

    source = frappe.get_single("Website Settings") if frappe.db.exists("DocType", "Website Settings") else None
    target = frappe.get_single("Contact Page Settings")

    mappings = {
        "contact_page_badge_ar": "contact_page_badge_ar",
        "contact_page_badge_en": "contact_page_badge_en",
        "contact_page_title_ar": "contact_page_title_ar",
        "contact_page_title_en": "contact_page_title_en",
        "contact_page_description_ar": "contact_page_description_ar",
        "contact_page_description_en": "contact_page_description_en",
        "contact_form_title_ar": "contact_form_title_ar",
        "contact_form_title_en": "contact_form_title_en",
        "contact_form_name_label_ar": "contact_form_name_label_ar",
        "contact_form_name_label_en": "contact_form_name_label_en",
        "contact_form_name_placeholder_ar": "contact_form_name_placeholder_ar",
        "contact_form_name_placeholder_en": "contact_form_name_placeholder_en",
        "contact_form_email_label_ar": "contact_form_email_label_ar",
        "contact_form_email_label_en": "contact_form_email_label_en",
        "contact_form_email_placeholder_ar": "contact_form_email_placeholder_ar",
        "contact_form_email_placeholder_en": "contact_form_email_placeholder_en",
        "contact_form_subject_label_ar": "contact_form_subject_label_ar",
        "contact_form_subject_label_en": "contact_form_subject_label_en",
        "contact_form_subject_placeholder_ar": "contact_form_subject_placeholder_ar",
        "contact_form_subject_placeholder_en": "contact_form_subject_placeholder_en",
        "contact_form_message_label_ar": "contact_form_message_label_ar",
        "contact_form_message_label_en": "contact_form_message_label_en",
        "contact_form_message_placeholder_ar": "contact_form_message_placeholder_ar",
        "contact_form_message_placeholder_en": "contact_form_message_placeholder_en",
        "contact_form_submit_text_ar": "contact_form_submit_text_ar",
        "contact_form_submit_text_en": "contact_form_submit_text_en",
        "contact_phone_label_ar": "contact_phone_label_ar",
        "contact_phone_label_en": "contact_phone_label_en",
        "contact_email_label_ar": "contact_email_label_ar",
        "contact_email_label_en": "contact_email_label_en",
        "contact_address_label_ar": "contact_address_label_ar",
        "contact_address_label_en": "contact_address_label_en",
        "contact_phone": "contact_phone",
        "contact_email": "contact_email",
        "address_ar": "address_ar",
        "address_en": "address_en",
        "map_location": "map_location",
        "social_section_title_ar": "social_section_title_ar",
        "social_section_title_en": "social_section_title_en",
    }

    changed = False
    for target_field, source_field in mappings.items():
        current = target.get(target_field)
        if current not in (None, ""):
            continue
        value = source.get(source_field) if source else None
        if value not in (None, ""):
            target.set(target_field, value)
            changed = True

    if changed:
        target.save(ignore_permissions=True)


def _ensure_module_def() -> None:
    if frappe.db.exists("Module Def", "AAU"):
        return
    frappe.get_doc(
        {
            "doctype": "Module Def",
            "module_name": "AAU",
            "app_name": "aau_university",
            "custom": 1,
        }
    ).insert(ignore_permissions=True)


def _ensure_roles() -> None:
    for spec in ROLE_SPECS:
        role_name = spec["name"]
        desk_access = cint(spec.get("desk_access", 1))
        if frappe.db.exists("Role", role_name):
            frappe.db.set_value("Role", role_name, "desk_access", desk_access, update_modified=False)
            continue
        frappe.get_doc({"doctype": "Role", "role_name": role_name, "desk_access": desk_access}).insert(ignore_permissions=True)


def _ensure_role_profiles() -> None:
    if not _doctype_exists("Role Profile"):
        return

    for profile_name, roles in ROLE_PROFILES.items():
        filtered_roles = [{"role": role} for role in roles if frappe.db.exists("Role", role)]
        if not filtered_roles:
            continue

        existing_name = frappe.db.exists("Role Profile", profile_name) or frappe.db.get_value(
            "Role Profile", {"role_profile": profile_name}, "name"
        )
        if existing_name:
            doc = frappe.get_doc("Role Profile", existing_name)
        else:
            doc = frappe.new_doc("Role Profile")
            doc.role_profile = profile_name

        doc.set("roles", filtered_roles)
        if doc.is_new():
            doc.insert(ignore_permissions=True)
        else:
            doc.save(ignore_permissions=True)


def _ensure_doctype_permissions() -> None:
    for role_name, config in DOCTYPE_ROLE_RULES.items():
        for doctype_name in config.get("full", []):
            _ensure_doctype_permission(doctype_name, role_name, _full_permission(role_name))
        for doctype_name in config.get("read_only", []):
            _ensure_doctype_permission(doctype_name, role_name, _read_only_permission(role_name))


def _full_permission(role_name: str) -> dict[str, Any]:
    return {
        "role": role_name,
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


def _read_only_permission(role_name: str) -> dict[str, Any]:
    return {
        "role": role_name,
        "read": 1,
        "write": 0,
        "create": 0,
        "delete": 0,
        "submit": 0,
        "cancel": 0,
        "amend": 0,
        "report": 1,
        "export": 1,
        "print": 1,
        "email": 0,
        "share": 0,
    }


def _ensure_doctype_permission(doctype_name: str, role_name: str, desired: dict[str, Any]) -> None:
    if not _doctype_exists(doctype_name) or not frappe.db.exists("Role", role_name):
        return

    doc = frappe.get_doc("DocType", doctype_name)
    existing = None
    for perm in doc.permissions or []:
        if perm.role == role_name and cint(getattr(perm, "permlevel", 0)) == 0:
            existing = perm
            break

    if existing:
        changed = False
        for key, value in desired.items():
            if getattr(existing, key, None) != value:
                setattr(existing, key, value)
                changed = True
        if changed:
            doc.save(ignore_permissions=True)
        return

    doc.append("permissions", desired)
    doc.save(ignore_permissions=True)


def _ensure_number_cards() -> dict[str, str | None]:
    specs = {
        "users": {
            "name": "AAU Total Users",
            "label": "إجمالي المستخدمين",
            "doctype": "User",
            "filters": {},
            "color": "blue",
        },
        "students": {
            "name": "AAU Active Students",
            "label": "الطلاب النشطون",
            "doctype": "Student",
            "filters": {"enabled": 1},
            "color": "green",
        },
        "instructors": {
            "name": "AAU Active Instructors",
            "label": "المدرسون النشطون",
            "doctype": "Instructor",
            "filters": {"status": "Active"},
            "color": "cyan",
        },
        "news": {
            "name": "AAU Published News",
            "label": "الأخبار المنشورة",
            "doctype": "News",
            "filters": {"is_published": 1},
            "color": "orange",
        },
        "events": {
            "name": "AAU Published Events",
            "label": "الفعاليات المنشورة",
            "doctype": "Events",
            "filters": {"is_published": 1},
            "color": "purple",
        },
        "colleges": {
            "name": "AAU Active Colleges",
            "label": "الكليات النشطة",
            "doctype": "Colleges",
            "filters": {"is_active": 1},
            "color": "blue",
        },
        "programs": {
            "name": "AAU Active Programs",
            "label": "البرامج النشطة",
            "doctype": "Academic Programs",
            "filters": {"is_active": 1},
            "color": "green",
        },
        "faculty": {
            "name": "AAU Active Faculty Members",
            "label": "أعضاء هيئة التدريس",
            "doctype": "Faculty Members",
            "filters": {"is_active": 1},
            "color": "cyan",
        },
        "contacts": {
            "name": "AAU Contact Messages",
            "label": "رسائل التواصل",
            "doctype": "Contact Us Messages",
            "filters": {},
            "color": "red",
        },
        "join_requests": {
            "name": "AAU Join Requests",
            "label": "طلبات الانضمام",
            "doctype": "Join Requests",
            "filters": {},
            "color": "yellow",
        },
        "draft_news": {
            "name": "AAU Draft News",
            "label": "الأخبار بانتظار النشر",
            "doctype": "News",
            "filters": {"is_published": 0},
            "color": "orange",
        },
        "draft_events": {
            "name": "AAU Draft Events",
            "label": "الفعاليات بانتظار النشر",
            "doctype": "Events",
            "filters": {"is_published": 0},
            "color": "purple",
        },
        "draft_projects": {
            "name": "AAU Draft Projects",
            "label": "المشاريع بانتظار النشر",
            "doctype": "Projects",
            "filters": {"is_published": 0},
            "color": "red",
        },
        "hidden_colleges": {
            "name": "AAU Hidden Colleges",
            "label": "الكليات المخفية",
            "doctype": "Colleges",
            "filters": {"is_active": 0},
            "color": "blue",
        },
        "inactive_programs": {
            "name": "AAU Inactive Programs",
            "label": "البرامج غير المفعلة",
            "doctype": "Academic Programs",
            "filters": {"is_active": 0},
            "color": "green",
        },
        "inactive_faculty": {
            "name": "AAU Inactive Faculty Members",
            "label": "أعضاء الهيئة المخفيون",
            "doctype": "Faculty Members",
            "filters": {"is_active": 0},
            "color": "cyan",
        },
    }

    result: dict[str, str | None] = {}
    for key, spec in specs.items():
        result[key] = _upsert_number_card(
            card_name=spec["name"],
            label=spec["label"],
            document_type=spec["doctype"],
            filters=spec["filters"],
            color=spec["color"],
        )

    return result


def _upsert_number_card(*, card_name: str, label: str, document_type: str, filters: dict[str, Any], color: str) -> str | None:
    if not _doctype_exists(document_type):
        return None

    filters_json = json.dumps(_sanitize_filters(document_type, filters), ensure_ascii=False)

    existing_name = frappe.db.exists("Number Card", card_name) or frappe.db.get_value(
        "Number Card", {"label": label}, "name"
    )

    payload = {
        "label": label,
        "type": "Document Type",
        "document_type": document_type,
        "function": "Count",
        "filters_json": filters_json,
        "is_public": 0,
        "show_percentage_stats": 0,
        "color": color,
    }

    if existing_name:
        doc = frappe.get_doc("Number Card", existing_name)
        doc.update(payload)
        doc.save(ignore_permissions=True)
        return doc.name

    doc = frappe.get_doc(
        {
            "doctype": "Number Card",
            "name": card_name,
            "module": "AAU",
            **payload,
        }
    ).insert(ignore_permissions=True)
    return doc.name


def _ensure_dashboard_charts() -> dict[str, str | None]:
    specs = {
        "news_trend": {
            "name": "AAU News Trend",
            "doctype": "News",
            "filters": {"is_published": 1},
            "color": "orange",
            "based_on": "creation",
        },
        "events_trend": {
            "name": "AAU Events Trend",
            "doctype": "Events",
            "filters": {"is_published": 1},
            "color": "purple",
            "based_on": "creation",
        },
        "contacts_trend": {
            "name": "AAU Contact Messages Trend",
            "doctype": "Contact Us Messages",
            "filters": {},
            "color": "red",
            "based_on": "creation",
        },
        "students_trend": {
            "name": "AAU Student Registrations Trend",
            "doctype": "Student",
            "filters": {"enabled": 1},
            "color": "green",
            "based_on": "creation",
        },
        "projects_trend": {
            "name": "AAU Projects Trend",
            "doctype": "Projects",
            "filters": {"is_published": 1},
            "color": "blue",
            "based_on": "creation",
        },
        "join_requests_trend": {
            "name": "AAU Join Requests Trend",
            "doctype": "Join Requests",
            "filters": {},
            "color": "yellow",
            "based_on": "creation",
        },
        "users_trend": {
            "name": "AAU Users Trend",
            "doctype": "User",
            "filters": {},
            "color": "cyan",
            "based_on": "creation",
        },
    }

    result: dict[str, str | None] = {}
    for key, spec in specs.items():
        result[key] = _upsert_dashboard_chart(
            chart_name=spec["name"],
            document_type=spec["doctype"],
            filters=spec["filters"],
            color=spec["color"],
            based_on=spec["based_on"],
        )

    return result


def _upsert_dashboard_chart(
    *,
    chart_name: str,
    document_type: str,
    filters: dict[str, Any],
    color: str,
    based_on: str,
) -> str | None:
    if not _doctype_exists(document_type):
        return None

    based_on_field = based_on if _field_exists(document_type, based_on) else "creation"

    sanitized_filters = _sanitize_filters(document_type, filters)
    filters_json = json.dumps(_to_dashboard_chart_filters(document_type, sanitized_filters), ensure_ascii=False)

    payload = {
        "chart_name": chart_name,
        "chart_type": "Count",
        "document_type": document_type,
        "timeseries": 1,
        "based_on": based_on_field,
        "timespan": "Last Year",
        "time_interval": "Monthly",
        "type": "Line",
        "filters_json": filters_json,
        "is_public": 0,
        "show_values_over_chart": 1,
        "color": color,
    }

    existing_name = frappe.db.exists("Dashboard Chart", chart_name) or frappe.db.get_value(
        "Dashboard Chart", {"chart_name": chart_name}, "name"
    )

    if existing_name:
        doc = frappe.get_doc("Dashboard Chart", existing_name)
        doc.update(payload)
        doc.save(ignore_permissions=True)
        return doc.name

    doc = frappe.get_doc(
        {
            "doctype": "Dashboard Chart",
            "module": "AAU",
            **payload,
        }
    ).insert(ignore_permissions=True)
    return doc.name


def _to_dashboard_chart_filters(document_type: str, filters: dict[str, Any]) -> list[list[Any]]:
    if not filters:
        return []

    normalized: list[list[Any]] = []
    for fieldname, value in filters.items():
        normalized.append([document_type, fieldname, "=", value, False])
    return normalized


def _upsert_workspace(definition: dict[str, Any]) -> str:
    payload = _prepare_workspace_payload(definition)
    name = payload["name"]

    existing_name = None
    for candidate in (
        frappe.db.exists("Workspace", name),
        frappe.db.get_value("Workspace", {"title": payload["title"]}, "name"),
        frappe.db.get_value("Workspace", {"label": payload["label"]}, "name"),
    ):
        if candidate:
            existing_name = candidate
            break

    if existing_name and existing_name != name and not frappe.db.exists("Workspace", name):
        rename_doc("Workspace", existing_name, name, force=True, ignore_permissions=True)
        existing_name = name

    if existing_name:
        doc = frappe.get_doc("Workspace", existing_name)
    else:
        doc = frappe.new_doc("Workspace")

    scalar_fields = [
        "label",
        "title",
        "module",
        "icon",
        "indicator_color",
        "public",
        "is_hidden",
        "hide_custom",
        "content",
        "for_user",
        "parent_page",
    ]

    for fieldname in scalar_fields:
        if fieldname in payload:
            doc.set(fieldname, payload[fieldname])

    doc.set("roles", payload.get("roles", []))
    doc.set("links", payload.get("links", []))
    doc.set("shortcuts", payload.get("shortcuts", []))
    doc.set("number_cards", payload.get("number_cards", []))
    doc.set("charts", payload.get("charts", []))

    if doc.is_new():
        doc.insert(ignore_permissions=True)
        if doc.name != name and not frappe.db.exists("Workspace", name):
            rename_doc("Workspace", doc.name, name, force=True, ignore_permissions=True)
            doc = frappe.get_doc("Workspace", name)
    else:
        doc.save(ignore_permissions=True)

    # label/title/module are read-only in model; enforce persisted values via DB update.
    _archive_workspace_conflicts(doc.name, payload["label"], payload["title"])
    frappe.db.set_value("Workspace", doc.name, "label", payload["label"], update_modified=False)
    frappe.db.set_value("Workspace", doc.name, "title", payload["title"], update_modified=False)
    frappe.db.set_value("Workspace", doc.name, "module", payload["module"], update_modified=False)

    # sequence_id is read-only in model; enforce ordering via direct DB update.
    if payload.get("sequence_id") is not None:
        frappe.db.set_value("Workspace", doc.name, "sequence_id", payload["sequence_id"], update_modified=False)

    return doc.name


def _archive_workspace_conflicts(current_name: str, target_label: str, target_title: str) -> None:
    """Ensure label/title unique constraints won't fail due old duplicated workspaces."""
    label_conflict = frappe.db.get_value(
        "Workspace",
        {"label": target_label, "name": ["!=", current_name]},
        "name",
    )
    if label_conflict:
        frappe.db.set_value("Workspace", label_conflict, "label", f"{target_label} (Legacy)", update_modified=False)
        frappe.db.set_value("Workspace", label_conflict, "is_hidden", 1, update_modified=False)

    title_conflict = frappe.db.get_value(
        "Workspace",
        {"title": target_title, "name": ["!=", current_name]},
        "name",
    )
    if title_conflict:
        frappe.db.set_value("Workspace", title_conflict, "title", f"{target_title} (Legacy)", update_modified=False)
        frappe.db.set_value("Workspace", title_conflict, "is_hidden", 1, update_modified=False)


def _prepare_workspace_payload(definition: dict[str, Any]) -> dict[str, Any]:
    links = _filter_links(definition.get("links", []))
    shortcuts = _filter_shortcuts(definition.get("shortcuts", []))

    number_card_items = [
        {"number_card_name": card_name, "label": ""}
        for card_name in definition.get("number_cards", [])
        if card_name and frappe.db.exists("Number Card", card_name)
    ]

    chart_items = [
        {"chart_name": chart_name, "label": ""}
        for chart_name in definition.get("charts", [])
        if chart_name and frappe.db.exists("Dashboard Chart", chart_name)
    ]

    card_names = [item["label"] for item in links if item.get("type") == "Card Break" and item.get("label")]
    shortcut_names = [item["label"] for item in shortcuts if item.get("label")]
    number_card_names = [item["number_card_name"] for item in number_card_items]
    chart_names = [item["chart_name"] for item in chart_items]

    content = _build_workspace_content(
        title=definition["label"],
        card_names=card_names,
        shortcut_names=shortcut_names,
        number_card_names=number_card_names,
        chart_names=chart_names,
    )

    return {
        "name": definition["name"],
        "label": definition["label"],
        "title": definition["title"],
        "module": "AAU",
        "icon": definition.get("icon", "folder-normal"),
        "indicator_color": definition.get("indicator_color", "blue"),
        "public": 1,
        "is_hidden": 0,
        "hide_custom": 0,
        "for_user": None,
        "parent_page": None,
        "sequence_id": definition.get("sequence_id"),
        "roles": [{"role": role} for role in _filter_roles(definition.get("roles", []))],
        "links": links,
        "shortcuts": shortcuts,
        "number_cards": number_card_items,
        "charts": chart_items,
        "content": content,
    }


def _build_workspace_content(
    *,
    title: str,
    card_names: list[str],
    shortcut_names: list[str],
    number_card_names: list[str],
    chart_names: list[str],
) -> str:
    blocks = [
        {
            "id": "aau_header",
            "type": "header",
            "data": {"text": f'<span class="h4">{title}</span>', "col": 12},
        }
    ]

    for idx, chart_name in enumerate(chart_names, start=1):
        blocks.append(
            {
                "id": f"aau_chart_{idx}",
                "type": "chart",
                "data": {"chart_name": chart_name, "col": 12 if idx == 1 else 6},
            }
        )

    for idx, number_card_name in enumerate(number_card_names, start=1):
        blocks.append(
            {
                "id": f"aau_number_{idx}",
                "type": "number_card",
                "data": {"number_card_name": number_card_name, "col": 3},
            }
        )

    if shortcut_names:
        blocks.extend(
            [
                {"id": "aau_spacer_1", "type": "spacer", "data": {"col": 12}},
                {
                    "id": "aau_shortcuts_header",
                    "type": "header",
                    "data": {"text": '<span class="h4"><b>إجراءات سريعة</b></span>', "col": 12},
                },
            ]
        )

    for idx, shortcut_name in enumerate(shortcut_names, start=1):
        blocks.append(
            {
                "id": f"aau_shortcut_{idx}",
                "type": "shortcut",
                "data": {"shortcut_name": shortcut_name, "col": 3},
            }
        )

    if card_names:
        blocks.extend(
            [
                {"id": "aau_spacer_2", "type": "spacer", "data": {"col": 12}},
                {
                    "id": "aau_cards_header",
                    "type": "header",
                    "data": {"text": '<span class="h4"><b>الإدارة التفصيلية</b></span>', "col": 12},
                },
            ]
        )

    for idx, card_name in enumerate(card_names, start=1):
        blocks.append(
            {
                "id": f"aau_card_{idx}",
                "type": "card",
                "data": {"card_name": card_name, "col": 4},
            }
        )

    return json.dumps(blocks, ensure_ascii=False)


def _filter_roles(roles: list[str]) -> list[str]:
    valid_roles = []
    for role in roles:
        if role and frappe.db.exists("Role", role):
            valid_roles.append(role)
    return valid_roles


def _filter_links(raw_links: list[dict[str, Any]]) -> list[dict[str, Any]]:
    valid_links: list[dict[str, Any]] = []
    for link in raw_links:
        link_type = link.get("link_type")
        link_to = link.get("link_to")
        row_type = link.get("type")

        if row_type == "Card Break":
            valid_links.append({"type": "Card Break", "label": link.get("label"), "icon": link.get("icon")})
            continue

        if row_type != "Link":
            continue

        if link_type == "DocType" and not _doctype_exists(link_to):
            continue
        if link_type == "Report" and not frappe.db.exists("Report", link_to):
            continue
        if link_type == "Page" and not frappe.db.exists("Page", link_to):
            continue

        valid_links.append(
            {
                "type": "Link",
                "label": link.get("label"),
                "icon": link.get("icon"),
                "link_type": link_type,
                "link_to": link_to,
            }
        )

    return valid_links


def _filter_shortcuts(raw_shortcuts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    valid_shortcuts: list[dict[str, Any]] = []
    for shortcut in raw_shortcuts:
        shortcut_type = shortcut.get("type")
        link_to = shortcut.get("link_to")

        if shortcut_type == "DocType" and not _doctype_exists(link_to):
            continue
        if shortcut_type == "Report" and not frappe.db.exists("Report", link_to):
            continue
        if shortcut_type == "Page" and not frappe.db.exists("Page", link_to):
            continue

        valid_shortcuts.append(
            {
                "type": shortcut_type,
                "label": shortcut.get("label"),
                "link_to": link_to,
                "doc_view": shortcut.get("doc_view") or "List",
                "url": shortcut.get("url"),
            }
        )

    return valid_shortcuts


def _sanitize_filters(doctype: str, filters: dict[str, Any]) -> dict[str, Any]:
    if not filters:
        return {}

    cleaned: dict[str, Any] = {}
    for fieldname, value in filters.items():
        if _field_exists(doctype, fieldname):
            cleaned[fieldname] = value

    return cleaned


def _doctype_exists(doctype_name: str | None) -> bool:
    return bool(doctype_name and frappe.db.exists("DocType", doctype_name))


def _field_exists(doctype_name: str, fieldname: str) -> bool:
    if fieldname in {"name", "creation", "modified", "owner"}:
        return True
    return bool(frappe.db.exists("DocField", {"parent": doctype_name, "fieldname": fieldname}))


def _hide_legacy_workspace(name: str) -> None:
    if not frappe.db.exists("Workspace", name):
        return
    frappe.db.set_value("Workspace", name, "is_hidden", 1, update_modified=False)
