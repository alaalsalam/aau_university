# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from typing import Any

import frappe
from frappe.model.rename_doc import rename_doc


CORE_ROLES = [
    "System Manager",
    "Workspace Manager",
    "Website Manager",
    "Desk User",
    "AAU Content Manager",
    "AAU Executive Manager",
    "AAU Site Manager",
]


def apply_aau_workspaces() -> dict[str, Any]:
    """Create/update AAU workspaces, metrics and navigation in one idempotent pass."""

    _ensure_module_def()
    _ensure_roles()

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
            ],
            "links": [
                {"type": "Card Break", "label": "المحتوى الرئيسي", "icon": "website"},
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
                {"type": "Card Break", "label": "الأكاديمي", "icon": "education"},
                {"type": "Link", "label": "الكليات", "link_type": "DocType", "link_to": "Colleges"},
                {"type": "Link", "label": "البرامج الأكاديمية", "link_type": "DocType", "link_to": "Academic Programs"},
                {"type": "Link", "label": "أعضاء هيئة التدريس", "link_type": "DocType", "link_to": "Faculty Members"},
                {"type": "Card Break", "label": "الطلبات", "icon": "mail"},
                {"type": "Link", "label": "رسائل التواصل", "link_type": "DocType", "link_to": "Contact Us Messages"},
                {"type": "Link", "label": "طلبات الانضمام", "link_type": "DocType", "link_to": "Join Requests"},
                {"type": "Card Break", "label": "الإدارة", "icon": "setting-gear"},
                {"type": "Link", "label": "المستخدمون", "link_type": "DocType", "link_to": "User"},
                {"type": "Link", "label": "الأدوار", "link_type": "DocType", "link_to": "Role"},
                {"type": "Link", "label": "الترجمة", "link_type": "DocType", "link_to": "Translation"},
                {"type": "Link", "label": "مساحات العمل", "link_type": "DocType", "link_to": "Workspace"},
            ],
            "shortcuts": [
                {"type": "DocType", "label": "الأخبار", "link_to": "News", "doc_view": "List"},
                {"type": "DocType", "label": "الفعاليات", "link_to": "Events", "doc_view": "List"},
                {"type": "DocType", "label": "رسائل التواصل", "link_to": "Contact Us Messages", "doc_view": "List"},
                {"type": "DocType", "label": "طلبات الانضمام", "link_to": "Join Requests", "doc_view": "List"},
                {"type": "DocType", "label": "المستخدمون", "link_to": "User", "doc_view": "List"},
                {"type": "DocType", "label": "تقارير الطلاب", "link_to": "Student", "doc_view": "Report Builder"},
                {"type": "DocType", "label": "تقارير المدرسين", "link_to": "Instructor", "doc_view": "Report Builder"},
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
            ],
            "links": [
                {"type": "Card Break", "label": "صفحات الموقع", "icon": "website"},
                {"type": "Link", "label": "الصفحة الرئيسية", "link_type": "DocType", "link_to": "Home Page"},
                {"type": "Link", "label": "عن الجامعة", "link_type": "DocType", "link_to": "About University"},
                {"type": "Link", "label": "صفحات AAU", "link_type": "DocType", "link_to": "AAU Page"},
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
            "name": "aau-admin-control",
            "label": "مركز إدارة النظام",
            "title": "AAU Admin Control",
            "sequence_id": 75,
            "icon": "setting-gear",
            "indicator_color": "orange",
            "roles": ["System Manager", "Workspace Manager"],
            "links": [
                {"type": "Card Break", "label": "التحكم بالنظام", "icon": "setting-gear"},
                {"type": "Link", "label": "المستخدمون", "link_type": "DocType", "link_to": "User"},
                {"type": "Link", "label": "الأدوار", "link_type": "DocType", "link_to": "Role"},
                {"type": "Link", "label": "مساحات العمل", "link_type": "DocType", "link_to": "Workspace"},
                {"type": "Link", "label": "الترجمة", "link_type": "DocType", "link_to": "Translation"},
                {"type": "Link", "label": "إعدادات الموقع", "link_type": "DocType", "link_to": "Website Settings"},
                {"type": "Card Break", "label": "رقابة المحتوى", "icon": "file"},
                {"type": "Link", "label": "الأخبار", "link_type": "DocType", "link_to": "News"},
                {"type": "Link", "label": "الفعاليات", "link_type": "DocType", "link_to": "Events"},
                {"type": "Link", "label": "رسائل التواصل", "link_type": "DocType", "link_to": "Contact Us Messages"},
                {"type": "Link", "label": "طلبات الانضمام", "link_type": "DocType", "link_to": "Join Requests"},
            ],
            "shortcuts": [
                {"type": "DocType", "label": "لوحة المستخدمين", "link_to": "User", "doc_view": "List"},
                {"type": "DocType", "label": "مراجعة الصلاحيات", "link_to": "Role", "doc_view": "List"},
                {"type": "DocType", "label": "مراجعة المساحات", "link_to": "Workspace", "doc_view": "List"},
            ],
            "number_cards": [number_cards.get("users"), number_cards.get("contacts"), number_cards.get("join_requests")],
            "charts": [charts.get("contacts_trend")],
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
    for role in CORE_ROLES:
        if frappe.db.exists("Role", role):
            continue
        frappe.get_doc({"doctype": "Role", "role_name": role, "desk_access": 1}).insert(ignore_permissions=True)


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
    frappe.db.set_value("Workspace", doc.name, "label", payload["label"], update_modified=False)
    frappe.db.set_value("Workspace", doc.name, "title", payload["title"], update_modified=False)
    frappe.db.set_value("Workspace", doc.name, "module", payload["module"], update_modified=False)

    # sequence_id is read-only in model; enforce ordering via direct DB update.
    if payload.get("sequence_id") is not None:
        frappe.db.set_value("Workspace", doc.name, "sequence_id", payload["sequence_id"], update_modified=False)

    return doc.name


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
