# -*- coding: utf-8 -*-
from __future__ import annotations

import frappe
from frappe.utils import add_days, nowdate


def seed_home(site: str | None = None):
    # WHY+WHAT: provide immediate smoke-test content after deploy by creating minimal Home Page, News, Events, Colleges, and FAQ records if missing.
    connected_here = _connect_if_needed(site)
    try:
        summary = {
            "home_page": _seed_home_page(),
            "news": _seed_news(),
            "events": _seed_events(),
            "colleges": _seed_colleges(),
            "faqs": _seed_faqs(),
        }
        frappe.db.commit()
        return {"ok": True, "data": summary}
    finally:
        if connected_here:
            frappe.destroy()


def _connect_if_needed(site: str | None) -> bool:
    if not site or getattr(frappe.local, "site", None):
        return False
    frappe.init(site=site)
    frappe.connect()
    return True


def _first_existing_doctype(candidates: list[str]) -> str | None:
    for doctype in candidates:
        if frappe.db.exists("DocType", doctype):
            return doctype
    return None


def _seed_home_page() -> dict:
    doctype = _first_existing_doctype(["Home Page"])
    if not doctype:
        return {"doctype": None, "created": 0, "skipped": 1}

    payload = {
        "page_title": "AAU University Home",
        "hero_title": "Welcome to AAU University",
        "hero_subtitle": "Academic excellence and practical learning.",
        "hero_description": "Discover programs, events, and student opportunities.",
        "about_title": "About AAU University",
        "about_description": "AAU provides quality education for future leaders.",
        "is_published": 1,
    }
    created = _insert_if_missing(doctype, payload, unique_fields=["page_title"])
    return {"doctype": doctype, "created": int(created), "skipped": int(not created)}


def _seed_news() -> dict:
    doctype = _first_existing_doctype(["News"])
    if not doctype:
        return {"doctype": None, "created": 0, "skipped": 2}

    rows = [
        {
            "slug": "welcome-semester-2026",
            "title": "Welcome Semester 2026",
            "summary": "AAU starts the new semester with orientation activities.",
            "content": "AAU University welcomes students with orientation sessions and campus tours.",
            "publish_date": nowdate(),
            "is_published": 1,
            "display_order": 1,
            "title_ar": "انطلاق الفصل الدراسي 2026",
            "title_en": "Welcome Semester 2026",
            "description_ar": "تبدأ الجامعة الفصل الجديد بأنشطة تعريفية.",
            "description_en": "AAU starts the new semester with orientation activities.",
            "content_ar": "تستقبل الجامعة الطلاب بفعاليات تعريفية وجولات داخل الحرم.",
            "content_en": "AAU welcomes students with orientation sessions and campus tours.",
            "date": nowdate(),
            "is_featured": 1,
        },
        {
            "slug": "aau-library-hours",
            "title": "Library Extended Hours",
            "summary": "Main library now opens extended evening hours.",
            "content": "The university library is now open until 9 PM on weekdays.",
            "publish_date": add_days(nowdate(), -1),
            "is_published": 1,
            "display_order": 2,
            "title_ar": "تمديد ساعات عمل المكتبة",
            "title_en": "Library Extended Hours",
            "description_ar": "المكتبة الرئيسية أصبحت تعمل لفترة مسائية أطول.",
            "description_en": "Main library now opens extended evening hours.",
            "content_ar": "المكتبة الجامعية تعمل حتى الساعة 9 مساءً خلال أيام الأسبوع.",
            "content_en": "The university library is now open until 9 PM on weekdays.",
            "date": add_days(nowdate(), -1),
        },
    ]
    return _seed_many(doctype, rows, unique_fields=["slug", "title", "title_en", "title_ar"])


def _seed_events() -> dict:
    doctype = _first_existing_doctype(["Events", "Event"])
    if not doctype:
        return {"doctype": None, "created": 0, "skipped": 2}

    rows = [
        {
            "slug": "orientation-day-2026",
            "title": "Orientation Day 2026",
            "description": "Orientation for new students.",
            "date": add_days(nowdate(), 5),
            "is_published": 1,
            "display_order": 1,
            "title_ar": "اليوم التعريفي 2026",
            "title_en": "Orientation Day 2026",
            "description_ar": "فعالية تعريفية للطلاب المستجدين.",
            "description_en": "Orientation event for new students.",
            "location_ar": "القاعة الرئيسية",
            "location_en": "Main Hall",
            "organizer_ar": "شؤون الطلاب",
            "organizer_en": "Student Affairs",
            "category": "academic",
            "status": "upcoming",
        },
        {
            "slug": "career-day-2026",
            "title": "Career Day 2026",
            "description": "Employers meet final-year students.",
            "date": add_days(nowdate(), 12),
            "is_published": 1,
            "display_order": 2,
            "title_ar": "يوم المهن 2026",
            "title_en": "Career Day 2026",
            "description_ar": "لقاء بين الشركات وطلاب السنة النهائية.",
            "description_en": "Employers meet final-year students.",
            "location_ar": "مركز الفعاليات",
            "location_en": "Events Center",
            "organizer_ar": "مكتب الخريجين",
            "organizer_en": "Alumni Office",
            "category": "academic",
            "status": "upcoming",
        },
    ]
    return _seed_many(doctype, rows, unique_fields=["slug", "title", "title_en", "title_ar"])


def _seed_colleges() -> dict:
    doctype = _first_existing_doctype(["Colleges", "College"])
    if not doctype:
        return {"doctype": None, "created": 0, "skipped": 2}

    rows = [
        {
            "slug": "medicine",
            "college_name": "College of Human Medicine",
            "description": "Programs focused on clinical and medical sciences.",
            "dean_name": "Dr. Ahmed Ali",
            "is_active": 1,
            "display_order": 1,
            "name_ar": "كلية الطب البشري",
            "name_en": "College of Human Medicine",
            "description_ar": "برامج أكاديمية في العلوم الطبية والسريرية.",
            "description_en": "Programs focused on clinical and medical sciences.",
        },
        {
            "slug": "engineering-it",
            "college_name": "College of Engineering and IT",
            "description": "Modern engineering and information technology tracks.",
            "dean_name": "Dr. Salma Hassan",
            "is_active": 1,
            "display_order": 2,
            "name_ar": "كلية الهندسة وتقنية المعلومات",
            "name_en": "College of Engineering and IT",
            "description_ar": "مسارات حديثة في الهندسة وتقنية المعلومات.",
            "description_en": "Modern engineering and information technology tracks.",
        },
    ]
    return _seed_many(doctype, rows, unique_fields=["slug", "college_name", "name_en", "name_ar"])


def _seed_faqs() -> dict:
    doctype = _first_existing_doctype(["FAQs", "FAQ"])
    if not doctype:
        return {"doctype": None, "created": 0, "skipped": 2}

    rows = [
        {
            "question": "How can I apply to AAU?",
            "answer": "Apply through admissions office or the online portal.",
            "category": "admission",
            "is_published": 1,
            "display_order": 1,
            "question_ar": "كيف يمكنني التقديم في الجامعة؟",
            "question_en": "How can I apply to AAU?",
            "answer_ar": "يمكنك التقديم عبر مكتب القبول أو البوابة الإلكترونية.",
            "answer_en": "Apply through admissions office or the online portal.",
        },
        {
            "question": "Does AAU offer scholarships?",
            "answer": "Yes, merit and need-based scholarships are available.",
            "category": "scholarship",
            "is_published": 1,
            "display_order": 2,
            "question_ar": "هل توفر الجامعة منحًا دراسية؟",
            "question_en": "Does AAU offer scholarships?",
            "answer_ar": "نعم، تتوفر منح دراسية تفوقية ودعم حسب الحالة.",
            "answer_en": "Yes, merit and need-based scholarships are available.",
        },
    ]
    return _seed_many(doctype, rows, unique_fields=["question", "question_en", "question_ar"])


def _seed_many(doctype: str, rows: list[dict], unique_fields: list[str]) -> dict:
    created = 0
    skipped = 0
    for row in rows:
        if _insert_if_missing(doctype, row, unique_fields):
            created += 1
        else:
            skipped += 1
    return {"doctype": doctype, "created": created, "skipped": skipped}


def _insert_if_missing(doctype: str, payload: dict, unique_fields: list[str]) -> bool:
    meta = frappe.get_meta(doctype)
    allowed_fields = {df.fieldname for df in meta.fields if df.fieldname}
    values = _normalize_values(payload, allowed_fields)

    filters = {
        field: values[field]
        for field in unique_fields
        if field in values and values.get(field) not in (None, "")
    }
    if filters and frappe.db.exists(doctype, filters):
        return False

    doc = frappe.get_doc({"doctype": doctype, **values})
    doc.insert(ignore_permissions=True)
    return True


def _normalize_values(payload: dict, allowed_fields: set[str]) -> dict:
    values = {key: value for key, value in payload.items() if key in allowed_fields}

    if "event_title" in allowed_fields and "event_title" not in values:
        values["event_title"] = payload.get("event_title") or payload.get("title") or payload.get("title_en")
    if "event_date" in allowed_fields and "event_date" not in values:
        values["event_date"] = payload.get("event_date") or payload.get("date") or payload.get("publish_date")
    if "location" in allowed_fields and "location" not in values:
        values["location"] = payload.get("location") or payload.get("location_en") or payload.get("location_ar")

    if "title" in allowed_fields and "title" not in values:
        values["title"] = payload.get("title") or payload.get("event_title") or payload.get("question")
    if "content" in allowed_fields and "content" not in values:
        values["content"] = payload.get("content") or payload.get("description") or payload.get("answer")
    if "publish_date" in allowed_fields and "publish_date" not in values:
        values["publish_date"] = payload.get("publish_date") or payload.get("date")

    return {key: value for key, value in values.items() if value not in (None, "")}
