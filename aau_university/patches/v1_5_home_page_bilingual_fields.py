# -*- coding: utf-8 -*-
from __future__ import annotations

import frappe

LOG_PREFIX = "[AAU HOME BILINGUAL]"


BACKFILL_PAIRS = [
    ("hero_title", "hero_title_primary_ar"),
    ("hero_title", "hero_title_primary_en"),
    ("hero_description", "hero_description_ar"),
    ("hero_description", "hero_description_en"),
    ("hero_subtitle", "hero_title_secondary_ar"),
    ("hero_subtitle", "hero_title_secondary_en"),
    ("hero_cta_text", "hero_apply_text_ar"),
    ("hero_cta_text", "hero_apply_text_en"),
    ("about_title", "about_title_ar"),
    ("about_title", "about_title_en"),
    ("about_description", "about_description_ar"),
    ("about_description", "about_description_en"),
    ("footer_text", "footer_text_ar"),
    ("footer_text", "footer_text_en"),
    ("page_title", "page_title_ar"),
    ("page_title", "page_title_en"),
]


def execute():
    logger = frappe.logger("aau_university")
    logger.info(f"{LOG_PREFIX} START")

    try:
        if not frappe.db.exists("DocType", "Home Page"):
            logger.info(f"{LOG_PREFIX} Home Page doctype missing, skip")
            return

        frappe.reload_doc("aau", "doctype", "home_page")
        _backfill_from_legacy_fields()
        frappe.clear_cache(doctype="Home Page")
        frappe.db.commit()
        logger.info(f"{LOG_PREFIX} DONE")
    except Exception:
        logger.error(f"{LOG_PREFIX} FAILED\n{frappe.get_traceback()}")
        raise


def _backfill_from_legacy_fields():
    columns = set(frappe.get_meta("Home Page").get_valid_columns() or [])
    for source_field, target_field in BACKFILL_PAIRS:
        if source_field not in columns or target_field not in columns:
            continue
        frappe.db.sql(
            f"""
            UPDATE `tabHome Page`
            SET `{target_field}` = COALESCE(NULLIF(`{target_field}`, ''), `{source_field}`)
            WHERE COALESCE(NULLIF(`{target_field}`, ''), '') = ''
              AND COALESCE(NULLIF(`{source_field}`, ''), '') != ''
            """
        )

    # Reasonable bilingual defaults for hero actions if empty
    defaults = {
        "hero_badge_ar": "مرحباً بكم في جامعة الجيل الجديد",
        "hero_badge_en": "Welcome to AJ JEEL ALJADEED UNIVERSITY",
        "hero_apply_text_ar": "التقديم الآن",
        "hero_apply_text_en": "Apply Now",
        "hero_explore_text_ar": "استكشف الكليات",
        "hero_explore_text_en": "Explore Colleges",
        "hero_discover_text_ar": "اكتشف المزيد",
        "hero_discover_text_en": "Discover More",
        "hero_explore_link": "/colleges",
    }
    for fieldname, value in defaults.items():
        if fieldname not in columns:
            continue
        frappe.db.sql(
            f"""
            UPDATE `tabHome Page`
            SET `{fieldname}` = %s
            WHERE COALESCE(NULLIF(`{fieldname}`, ''), '') = ''
            """,
            (value,),
        )
