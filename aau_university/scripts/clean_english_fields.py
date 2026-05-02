from __future__ import annotations

import re
import frappe


ARABIC_RE = re.compile(r"[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF]")


def _has_arabic(value: str) -> bool:
    return bool(ARABIC_RE.search(value or ""))


def _safe_fields(doctype: str, fields: list[str]) -> list[str]:
    meta = frappe.get_meta(doctype)
    return [field for field in fields if field == "name" or meta.has_field(field)]


def _clear_if_arabic(doctype: str, name: str, field: str, value, changes: list[tuple[str, str, str]]) -> None:
    if value is None:
        return
    if isinstance(value, str) and value == "":
        return
    if _has_arabic(str(value)):
        frappe.db.set_value(doctype, name, field, "")
        changes.append((doctype, name, field))


def run() -> None:
    changes: list[tuple[str, str, str]] = []

    if frappe.db.exists("DocType", "About University"):
        doc = frappe.get_doc("About University", "About University")
        single_fields = _safe_fields(
            "About University",
            [
                "page_badge_en",
                "page_title_en",
                "page_description_en",
                "intro_body_en",
                "vision_title_en",
                "vision_description_en",
                "mission_title_en",
                "mission_description_en",
                "goals_title_en",
                "goals_description_en",
                "values_title_en",
                "values_description_en",
                "president_section_title_en",
                "president_message_intro_en",
                "president_message_body_en",
                "president_message_closing_en",
                "president_name_en",
                "president_role_en",
                "team_section_title_en",
                "team_section_description_en",
            ],
        )
        for field in single_fields:
            value = doc.get(field)
            if value and _has_arabic(value):
                frappe.db.set_value("About University", "About University", field, "")
                changes.append(("About University", "About University", field))

        if doc.get("team_members"):
            for row in doc.get("team_members"):
                for field in ("group_name_en", "full_name_en", "job_title_en"):
                    value = row.get(field)
                    if value and _has_arabic(value):
                        frappe.db.set_value("About Team Member", row.name, field, "")
                        changes.append(("About Team Member", row.name, field))

    if frappe.db.exists("DocType", "Campus Life"):
        for row in frappe.get_all("Campus Life", fields=_safe_fields("Campus Life", ["name", "title_en", "content_en"])):
            _clear_if_arabic("Campus Life", row.name, "title_en", row.get("title_en"), changes)
            _clear_if_arabic("Campus Life", row.name, "content_en", row.get("content_en"), changes)

    if frappe.db.exists("DocType", "Research and Publications"):
        for row in frappe.get_all(
            "Research and Publications",
            fields=_safe_fields("Research and Publications", ["name", "title_en", "content_en"]),
        ):
            _clear_if_arabic("Research and Publications", row.name, "title_en", row.get("title_en"), changes)
            _clear_if_arabic("Research and Publications", row.name, "content_en", row.get("content_en"), changes)

    if frappe.db.exists("DocType", "Centers"):
        for row in frappe.get_all(
            "Centers",
            fields=_safe_fields("Centers", ["name", "title_en", "desc_en", "location_en", "services_en", "programs_en"]),
        ):
            _clear_if_arabic("Centers", row.name, "title_en", row.get("title_en"), changes)
            _clear_if_arabic("Centers", row.name, "desc_en", row.get("desc_en"), changes)
            _clear_if_arabic("Centers", row.name, "location_en", row.get("location_en"), changes)
            _clear_if_arabic("Centers", row.name, "services_en", row.get("services_en"), changes)
            _clear_if_arabic("Centers", row.name, "programs_en", row.get("programs_en"), changes)

    if frappe.db.exists("DocType", "Academic Programs"):
        for row in frappe.get_all(
            "Academic Programs",
            fields=_safe_fields(
                "Academic Programs",
                ["name", "name_en", "description_en", "department_en", "study_years_en", "high_school_type_en", "duration_en"],
            ),
        ):
            _clear_if_arabic("Academic Programs", row.name, "name_en", row.get("name_en"), changes)
            _clear_if_arabic("Academic Programs", row.name, "description_en", row.get("description_en"), changes)
            _clear_if_arabic("Academic Programs", row.name, "department_en", row.get("department_en"), changes)
            _clear_if_arabic("Academic Programs", row.name, "study_years_en", row.get("study_years_en"), changes)
            _clear_if_arabic("Academic Programs", row.name, "high_school_type_en", row.get("high_school_type_en"), changes)
            _clear_if_arabic("Academic Programs", row.name, "duration_en", row.get("duration_en"), changes)

    if frappe.db.exists("DocType", "Faculty Members"):
        for row in frappe.get_all(
            "Faculty Members",
            fields=_safe_fields(
                "Faculty Members",
                ["name", "full_name_en", "academic_title_en", "biography_en"],
            ),
        ):
            _clear_if_arabic("Faculty Members", row.name, "full_name_en", row.get("full_name_en"), changes)
            _clear_if_arabic("Faculty Members", row.name, "academic_title_en", row.get("academic_title_en"), changes)
            _clear_if_arabic("Faculty Members", row.name, "biography_en", row.get("biography_en"), changes)

    if frappe.db.exists("DocType", "Home Page"):
        doc = frappe.get_doc("Home Page", "Home Page")
        home_fields = _safe_fields(
            "Home Page",
            [
                "hero_badge_en",
                "hero_title_primary_en",
                "hero_title_secondary_en",
                "hero_description_en",
                "stats_students_label_en",
                "stats_faculty_label_en",
                "stats_programs_label_en",
                "stats_colleges_label_en",
                "campus_life_title_en",
                "campus_life_description_en",
                "events_title_en",
                "events_description_en",
                "news_title_en",
                "news_description_en",
            ],
        )
        for field in home_fields:
            value = doc.get(field)
            if value and _has_arabic(value):
                frappe.db.set_value("Home Page", "Home Page", field, "")
                changes.append(("Home Page", "Home Page", field))

    if frappe.db.exists("DocType", "Website Settings"):
        doc = frappe.get_doc("Website Settings", "Website Settings")
        settings_fields = _safe_fields(
            "Website Settings",
            [
                "address_en",
                "contact_page_badge_en",
                "contact_page_title_en",
                "contact_page_description_en",
                "contact_form_title_en",
                "social_section_title_en",
                "site_description_en",
                "about_short_en",
            ],
        )
        for field in settings_fields:
            value = doc.get(field)
            if value and _has_arabic(value):
                frappe.db.set_value("Website Settings", "Website Settings", field, "")
                changes.append(("Website Settings", "Website Settings", field))

    frappe.db.commit()

    from collections import Counter

    counts = Counter(item[0] for item in changes)
    print("cleared_fields", len(changes))
    print("by_doctype", dict(counts))
