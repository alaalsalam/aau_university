# -*- coding: utf-8 -*-
from __future__ import annotations

import frappe

LOG_PREFIX = "[AAU ABOUT CMS]"

DEFAULTS = {
    "page_badge_ar": "تعرف علينا",
    "page_title_ar": "عن جامعة الجيل الجديد",
    "page_description_ar": "تعرف على رؤية الجامعة ورسالتها وأهدافها والقيم التي تقود مسيرتها.",
    "intro_body_ar": "جامعة الجيل الجديد تأسست سنة 2022م، وتقع وسط العاصمة صنعاء في شارع الرقاص من جهة الدائري ويمكن الوصول إليها أيضا من شارع الستين. تضم الجامعة أربع كليات هي كلية الطب البشري، وكلية العلوم الطبية والصحية، وكلية الهندسة وتكنولوجيا المعلومات، وكلية العلوم الإدارية والإنسانية.",
    "intro_image": "/assets/aau_university/about-campus.jpg",
    "vision_title_ar": "الرؤية",
    "vision_description_ar": "مؤسسة تعليمية رائدة وطنيا ومتميزة إقليميا وفاعلة في بناء مجتمع المعرفة.",
    "mission_title_ar": "الرسالة",
    "mission_description_ar": "إعداد خريجين يتمتعون بالكفاءة العلمية والمهنية والتعلم مدى الحياة، من خلال خبرة تعليمية رائدة وبيئة علمية وتعليمية داعمة وبرامج أكاديمية نوعية مبتكرة تلبي متطلبات سوق العمل وتسهم في خدمة المجتمع وتعزيز التنمية المستدامة.",
    "goals_title_ar": "الأهداف",
    "goals_description_ar": "تحقيق التميز الأكاديمي والبحثي، وتعزيز الشراكة المجتمعية، وتوفير بيئة تعليمية محفزة، وتنمية الموارد البشرية والمادية للجامعة.",
    "values_title_ar": "القيم",
    "values_description_ar": "الريادة والتعلم المستمر، الابتكار والإبداع، المسؤولية والشفافية، والعمل بروح الفريق.",
    "president_section_title_ar": "كلمة رئيس الجامعة",
    "president_message_intro_ar": "بسم الله الرحمن الرحيم، الحمد لله رب العالمين، والصلاة والسلام على خاتم الأنبياء والمرسلين.",
    "president_message_body_ar": "يسرني أن أرحب بطلابنا وطالباتنا الذين يتطلعون للانضمام إلى أسرة الجامعة، ونؤكد التزام الجامعة بتقديم تعليم نوعي وبيئة جامعية تشجع على الإبداع والريادة والتميز.",
    "president_message_closing_ar": "ختاما، نثق بأنكم ستكونون على قدر المسؤولية في تمثيل الجامعة وتحقيق رؤيتها وبناء مستقبل مشرق لكم ولوطنكم.",
    "president_name_ar": "أ.د/ همدان الشامي",
    "president_role_ar": "رئيس الجامعة",
    "president_image": "/assets/aau_university/about-campus.jpg",
    "team_section_title_ar": "الفريق الإداري",
    "team_section_description_ar": "نخبة من الكفاءات الأكاديمية والإدارية التي تقود مسيرة الجامعة نحو التميز والحداثة.",
}

DEFAULT_TEAM = [
    {"group_name_ar": "القيادة العليا", "full_name_ar": "أ.د/ همدان الشامي", "job_title_ar": "رئيس الجامعة", "member_image": "/assets/aau_university/about-campus.jpg", "display_order": 1},
    {"group_name_ar": "القيادة العليا", "full_name_ar": "أ.د. محمد العلفي", "job_title_ar": "نائب رئيس الجامعة للشؤون الأكاديمية", "member_image": "", "display_order": 2},
    {"group_name_ar": "القيادة العليا", "full_name_ar": "د. خالد سيف", "job_title_ar": "الأمين العام للجامعة", "member_image": "", "display_order": 3},
    {"group_name_ar": "القيادة العليا", "full_name_ar": "د. سارة المنصور", "job_title_ar": "نائب رئيس الجامعة للدراسات العليا", "member_image": "", "display_order": 4},
    {"group_name_ar": "مدراء الإدارات العامة", "full_name_ar": "م. ياسر القاضي", "job_title_ar": "مدير الشؤون المالية", "member_image": "", "display_order": 10},
    {"group_name_ar": "مدراء الإدارات العامة", "full_name_ar": "د. علي عبده", "job_title_ar": "مسجل عام الجامعة", "member_image": "", "display_order": 11},
    {"group_name_ar": "مدراء الإدارات العامة", "full_name_ar": "أ. منى الراعي", "job_title_ar": "مدير شؤون الموظفين", "member_image": "", "display_order": 12},
    {"group_name_ar": "مدراء الإدارات العامة", "full_name_ar": "أ. سامي محمد", "job_title_ar": "مدير النظم والمعلومات", "member_image": "", "display_order": 13},
]


def execute():
    logger = frappe.logger("aau_university")
    logger.info(f"{LOG_PREFIX} START")
    try:
        _migrate_to_single()
        frappe.clear_cache(doctype="About University")
        frappe.db.commit()
        logger.info(f"{LOG_PREFIX} DONE")
    except Exception:
        logger.error(f"{LOG_PREFIX} FAILED\n{frappe.get_traceback()}")
        raise


def _migrate_to_single():
    meta = frappe.get_meta("About University")
    source_row = {}
    if not meta.issingle:
        rows = frappe.get_all(
            "About University",
            fields=["name", "title", "description", "image", "is_published"],
            order_by="modified desc",
            limit_page_length=1,
            ignore_permissions=True,
        )
        if rows:
            source_row = rows[0]

    for fieldname, value in DEFAULTS.items():
        current = frappe.db.get_single_value("About University", fieldname)
        if current not in (None, ""):
            continue
        if fieldname == "page_title_ar" and source_row.get("title"):
            value = source_row.get("title")
        elif fieldname == "intro_body_ar" and source_row.get("description"):
            value = source_row.get("description")
        elif fieldname == "intro_image" and source_row.get("image"):
            value = source_row.get("image")
        frappe.db.set_single_value("About University", fieldname, value)

    current_rows = frappe.get_all(
        "About Team Member",
        fields=["name"],
        filters={"parenttype": "About University", "parent": "About University", "parentfield": "team_members"},
        ignore_permissions=True,
    )
    if not current_rows:
        doc = frappe.get_doc("About University", "About University")
        doc.set("team_members", [])
        for row in DEFAULT_TEAM:
            doc.append("team_members", row)
        doc.save(ignore_permissions=True)
