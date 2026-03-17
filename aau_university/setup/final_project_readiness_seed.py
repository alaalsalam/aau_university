# -*- coding: utf-8 -*-
from __future__ import annotations

import frappe
from frappe.utils.password import update_password


WEBSITE_SETTINGS_VALUES = {
    "site_name": "AAU University",
    "contact_email": "info@edu.yemenfrappe.com",
    "contact_phone": "+967 1 234 567",
    "show_language_picker": 1,
    "address_ar": "صنعاء، شارع الرقاص من جهة الدائري، ويمكن الوصول إلى الجامعة أيضًا من شارع الستين.",
    "map_location": "https://maps.google.com/?q=%D8%AC%D8%A7%D9%85%D8%B9%D8%A9+%D8%A7%D9%84%D8%AC%D9%8A%D9%84+%D8%A7%D9%84%D8%AC%D8%AF%D9%8A%D8%AF+%D8%B5%D9%86%D8%B9%D8%A7%D8%A1",
    "site_description_ar": "جامعة الجيل الجديد مؤسسة تعليمية حديثة في صنعاء تقدم تجربة أكاديمية تطبيقية مرتبطة باحتياجات سوق العمل والمجتمع.",
    "contact_page_badge_ar": "تواصل معنا",
    "contact_page_title_ar": "نحن هنا للإجابة عن استفساراتكم",
    "contact_page_description_ar": "يمكنكم التواصل مع جامعة الجيل الجديد للاستفسارات الأكاديمية والإدارية والشراكات عبر القنوات الرسمية الموضحة في هذه الصفحة.",
    "contact_form_title_ar": "أرسل رسالتك",
    "contact_social_title_ar": "القنوات الرسمية للجامعة",
}

TRANSLATIONS = {
    "مرحباً بكم في جامعة الجيل الجديد": "Welcome to New Generation University",
    "جامعة الجيل الجديد": "New Generation University",
    "نحو تعليم نوعي ومستقبل واعد": "Toward quality education and a promising future",
    "جامعة حديثة تسعى لإعداد خريجين مؤهلين علمياً ومهنياً، وتوفير بيئة تعليمية محفزة تدعم الإبداع والتميز وخدمة المجتمع.": "A modern university dedicated to preparing scientifically and professionally qualified graduates within a motivating environment that supports creativity, excellence, and community service.",
    "عن الجامعة": "About the University",
    "بيئة تعليمية متكاملة": "An integrated learning environment",
    "تواصل معنا": "Contact Us",
    "الحياة الجامعية": "Campus Life",
    "مشاريع التخرج": "Graduation Projects",
    "كلياتنا": "Our Colleges",
    "الأخبار": "News",
    "الفعاليات": "Events",
    "الأسئلة المتكررة": "Frequently Asked Questions",
    "لقطات من جامعتنا": "A glimpse into our university",
    "تعرف علينا": "Get to know us",
    "عن جامعة الجيل الجديد": "About New Generation University",
    "الرؤية": "Vision",
    "الرسالة": "Mission",
    "الأهداف": "Goals",
    "القيم": "Values",
    "كلمة رئيس الجامعة": "President's Message",
    "الفريق الإداري": "Leadership Team",
    "نحن هنا للإجابة عن استفساراتكم": "We are here to answer your questions",
    "يمكنكم التواصل مع جامعة الجيل الجديد للاستفسارات الأكاديمية والإدارية والشراكات عبر القنوات الرسمية الموضحة في هذه الصفحة.": "You can contact New Generation University for academic, administrative, and partnership inquiries through the official channels listed on this page.",
    "أرسل رسالتك": "Send your message",
    "القنوات الرسمية للجامعة": "Official university channels",
    "صنعاء، شارع الرقاص من جهة الدائري، ويمكن الوصول إلى الجامعة أيضًا من شارع الستين.": "Sana'a, Al-Raqas Street from the Ring Road side, with additional access from Al-Sitteen Street.",
    "جامعة الجيل الجديد مؤسسة تعليمية حديثة في صنعاء تقدم تجربة أكاديمية تطبيقية مرتبطة باحتياجات سوق العمل والمجتمع.": "New Generation University is a modern educational institution in Sana'a offering an applied academic experience aligned with labor market and community needs.",
    "كلية الطب البشري والصيدليه": "College of Human Medicine and Pharmacy",
    "كلية العلوم الطبية والصحية": "College of Medical and Health Sciences",
    "كلية الهندسة وتكنولوجيا المعلومات": "College of Engineering and Information Technology",
    "كلية العلوم الإدارية والإنسانية": "College of Administrative and Humanitarian Sciences",
}

FACULTY_FIXTURES = [
    {
        "full_name": "د. دينا مدحت",
        "academic_title": "أستاذ مساعد",
        "college_slug": "medicine",
        "biography": "عضو هيئة تدريس في المسارات الطبية، تركز على التعليم السريري وبناء جاهزية الطلبة للتطبيق العملي في المستشفيات التعليمية.",
    },
    {
        "full_name": "أ.د. أحمد علي",
        "academic_title": "أستاذ مشارك",
        "college_slug": "health-sciences",
        "biography": "أكاديمي في العلوم الصحية يعمل على تطوير المقررات وربطها بالمهارات المهنية ومتطلبات سوق العمل الصحي.",
    },
    {
        "full_name": "د. سامر الحكيمي",
        "academic_title": "أستاذ مساعد",
        "college_slug": "engineering-it",
        "biography": "متخصص في هندسة البرمجيات والتحول الرقمي، ويهتم بالمشاريع التطبيقية وربط الطلبة ببيئات الابتكار وريادة الأعمال.",
    },
    {
        "full_name": "د. هناء القباطي",
        "academic_title": "محاضر",
        "college_slug": "business-humanities",
        "biography": "تعمل في مجالات الإدارة والعلوم الإنسانية مع اهتمام خاص بتنمية المهارات القيادية والتواصل المؤسسي لدى الطلبة.",
    },
]

TEST_ACCOUNT_FIXTURES = [
    {
        "kind": "content_manager",
        "email": "content.manager@edu.yemenfrappe.com",
        "first_name": "AAU",
        "full_name": "AAU Content Manager",
        "user_type": "System User",
        "roles": ["Desk User", "Website Manager", "Workspace Manager", "AAU Content Manager"],
        "password": "AauCmsManager@2026!",
    },
    {
        "kind": "student",
        "student": "EDU-STU-2023-00016",
        "email": "basem@mail.com",
        "first_name": "باسم",
        "full_name": "باسم فتحي السيد",
        "user_type": "Website User",
        "roles": ["Student"],
        "password": "AauStudent@2026!",
    },
    {
        "kind": "student",
        "student": "EDU-STU-2023-00018",
        "email": "ziad@mail.com",
        "first_name": "Ziad",
        "full_name": "Ziad Kareem Ahmed",
        "user_type": "Website User",
        "roles": ["Student"],
        "password": "AauStudent2@2026!",
    },
    {
        "kind": "doctor",
        "instructor": "دينا مدحت",
        "email": "doctor-da286f@edu.yemenfrappe.com",
        "first_name": "دينا",
        "full_name": "دينا مدحت",
        "user_type": "Website User",
        "roles": ["Instructor"],
        "password": "AauDoctor@2026!",
    },
    {
        "kind": "doctor",
        "instructor": "Ahmed Ali",
        "email": "doctor-ahmed-ali-192ac3@edu.yemenfrappe.com",
        "first_name": "Ahmed",
        "full_name": "Ahmed Ali",
        "user_type": "Website User",
        "roles": ["Instructor"],
        "password": "AauDoctor2@2026!",
    },
]


def run() -> dict:
    summary = {
        "website_settings": _seed_website_settings(),
        "translations": _seed_translations(),
        "faculty": _seed_faculty_members(),
        "accounts": _seed_test_accounts(),
    }
    frappe.db.commit()
    return summary


def _seed_website_settings() -> dict:
    settings = frappe.get_single("Website Settings")
    changed = []
    for fieldname, value in WEBSITE_SETTINGS_VALUES.items():
        if settings.get(fieldname) != value:
            settings.set(fieldname, value)
            changed.append(fieldname)
    if changed:
        settings.save(ignore_permissions=True)
    return {"updated_fields": changed, "count": len(changed)}


def _seed_translations() -> dict:
    created = 0
    updated = 0
    for source_text, translated_text in TRANSLATIONS.items():
        existing_name = frappe.db.get_value(
            "Translation",
            {"language": "en", "source_text": source_text},
            "name",
        )
        if existing_name:
            doc = frappe.get_doc("Translation", existing_name)
            if doc.translated_text != translated_text:
                doc.translated_text = translated_text
                doc.save(ignore_permissions=True)
                updated += 1
            continue

        doc = frappe.get_doc(
            {
                "doctype": "Translation",
                "language": "en",
                "source_text": source_text,
                "translated_text": translated_text,
            }
        )
        doc.insert(ignore_permissions=True)
        created += 1

    return {"created": created, "updated": updated, "total": len(TRANSLATIONS)}


def _seed_faculty_members() -> dict:
    colleges = {
        row.get("slug"): row.get("name")
        for row in frappe.get_all(
            "Colleges",
            fields=["name", "slug"],
            filters={"is_active": 1},
            ignore_permissions=True,
            limit_page_length=100,
        )
        if row.get("slug")
    }
    created = 0
    updated = 0

    for row in FACULTY_FIXTURES:
        payload = {
            "doctype": "Faculty Members",
            "full_name": row["full_name"],
            "academic_title": row["academic_title"],
            "linked_college": colleges.get(row["college_slug"]),
            "biography": row["biography"],
            "photo": "/assets/aau_university/about-campus.jpg",
            "is_active": 1,
        }
        existing_name = frappe.db.get_value("Faculty Members", {"full_name": row["full_name"]}, "name")
        if existing_name:
            doc = frappe.get_doc("Faculty Members", existing_name)
            has_changes = False
            for key, value in payload.items():
                if key == "doctype":
                    continue
                if doc.get(key) != value:
                    doc.set(key, value)
                    has_changes = True
            if has_changes:
                doc.save(ignore_permissions=True)
                updated += 1
            continue

        frappe.get_doc(payload).insert(ignore_permissions=True)
        created += 1

    total = frappe.db.count("Faculty Members", {"is_active": 1})
    return {"created": created, "updated": updated, "active_total": total}


def _seed_test_accounts() -> dict:
    provisioned = []
    for row in TEST_ACCOUNT_FIXTURES:
        email = row["email"]
        user_doc = _ensure_user(
            email=email,
            first_name=row["first_name"],
            full_name=row["full_name"],
            user_type=row["user_type"],
            roles=row["roles"],
            password=row["password"],
        )

        if row["kind"] == "student":
            _link_student_account(row["student"], email)
        elif row["kind"] == "doctor":
            _link_instructor_account(row["instructor"], email)

        provisioned.append(
            {
                "kind": row["kind"],
                "email": email,
                "password": row["password"],
                "roles": row["roles"],
                "status": "active" if user_doc.enabled else "inactive",
            }
        )

    return {"items": provisioned, "count": len(provisioned)}


def _ensure_user(
    *,
    email: str,
    first_name: str,
    full_name: str,
    user_type: str,
    roles: list[str],
    password: str,
):
    if frappe.db.exists("User", email):
        user = frappe.get_doc("User", email)
    else:
        user = frappe.get_doc(
            {
                "doctype": "User",
                "email": email,
                "first_name": first_name,
                "full_name": full_name,
                "enabled": 1,
                "send_welcome_email": 0,
                "user_type": user_type,
            }
        )
        user.insert(ignore_permissions=True)

    changed = False
    updates = {
        "first_name": first_name,
        "full_name": full_name,
        "enabled": 1,
        "send_welcome_email": 0,
        "user_type": user_type,
    }
    for key, value in updates.items():
        if user.get(key) != value:
            user.set(key, value)
            changed = True

    existing_roles = {row.role for row in user.roles or []}
    for role in roles:
        if role not in existing_roles:
            user.append("roles", {"role": role})
            changed = True

    if changed:
        user.save(ignore_permissions=True)

    update_password(email, password)
    return user


def _link_student_account(student_name: str, email: str) -> None:
    if not frappe.db.exists("Student", student_name):
        return
    student = frappe.get_doc("Student", student_name)
    updates = {
        "user": email,
        "enabled": 1,
    }
    changed = False
    for key, value in updates.items():
        if student.get(key) != value:
            student.set(key, value)
            changed = True
    if changed:
        student.save(ignore_permissions=True)


def _link_instructor_account(instructor_name: str, email: str) -> None:
    if not frappe.db.exists("Instructor", instructor_name):
        return
    instructor = frappe.get_doc("Instructor", instructor_name)
    if instructor.get("custom_user_id") != email:
        instructor.set("custom_user_id", email)
        instructor.save(ignore_permissions=True)
