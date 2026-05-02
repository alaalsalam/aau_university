from __future__ import annotations

import frappe


def _template_for_program(name_text: str) -> dict[str, str]:
    key = (name_text or "").lower()

    if any(token in key for token in ["medicine", "طب", "surgery", "جراحة"]):
        return {
            "objectives_ar": "تأهيل كفاءات طبية قادرة على التشخيص والعلاج بكفاءة.\nتنمية المهارات السريرية والتواصل المهني مع المرضى.\nتعزيز البحث العلمي والأخلاقيات الطبية.",
            "objectives_en": "Prepare competent physicians capable of accurate diagnosis and effective treatment.\nDevelop strong clinical and professional communication skills.\nStrengthen medical research and professional ethics.",
            "career_ar": "طبيب امتياز\nطبيب عام\nباحث طبي",
            "career_en": "Intern Physician\nGeneral Practitioner\nMedical Researcher",
        }

    if any(token in key for token in ["dental", "أسنان", "oral"]):
        return {
            "objectives_ar": "إعداد أطباء أسنان ذوي كفاءة علمية وعملية عالية.\nإتقان مهارات التشخيص والعلاج الوقائي والتجميلي.\nتعزيز المسؤولية المهنية وخدمة المجتمع.",
            "objectives_en": "Prepare dentists with strong academic and practical competence.\nMaster diagnostic, preventive, and restorative treatment skills.\nPromote professional responsibility and community service.",
            "career_ar": "طبيب أسنان عام\nطبيب أسنان تجميلي\nأخصائي صحة فم",
            "career_en": "General Dentist\nCosmetic Dentist\nOral Health Specialist",
        }

    if any(token in key for token in ["pharmacy", "صيد"]):
        return {
            "objectives_ar": "تأهيل صيادلة قادرين على تقديم رعاية دوائية آمنة.\nتنمية مهارات التحليل الدوائي ومتابعة العلاجات.\nتعزيز البحث في العلوم الصيدلانية.",
            "objectives_en": "Prepare pharmacists to deliver safe pharmaceutical care.\nDevelop medication analysis and therapeutic follow-up skills.\nEnhance research in pharmaceutical sciences.",
            "career_ar": "صيدلي سريري\nصيدلي مجتمع\nمندوب علمي دوائي",
            "career_en": "Clinical Pharmacist\nCommunity Pharmacist\nMedical Representative",
        }

    if any(token in key for token in ["artificial intelligence", "ai", "ذكاء"]):
        return {
            "objectives_ar": "إكساب الطلبة أساسيات الذكاء الاصطناعي وتعلم الآلة.\nتطوير القدرة على بناء حلول ذكية تخدم القطاعات المختلفة.\nتعزيز مهارات تحليل البيانات واتخاذ القرار.",
            "objectives_en": "Provide students with AI and machine learning foundations.\nDevelop the ability to build intelligent solutions for multiple sectors.\nStrengthen data analysis and decision-making skills.",
            "career_ar": "مهندس ذكاء اصطناعي\nعالم بيانات\nمهندس تعلم آلة",
            "career_en": "AI Engineer\nData Scientist\nMachine Learning Engineer",
        }

    if any(token in key for token in ["information technology", "it", "تقنية"]):
        return {
            "objectives_ar": "تأهيل مختصين في تطوير وتشغيل الأنظمة التقنية.\nتنمية مهارات الشبكات وأمن المعلومات والبنية التحتية.\nرفع كفاءة الطلبة في إدارة المشاريع التقنية.",
            "objectives_en": "Prepare specialists in developing and operating IT systems.\nDevelop networking, cybersecurity, and infrastructure skills.\nImprove students' capability in managing technology projects.",
            "career_ar": "مهندس نظم\nأخصائي شبكات\nأخصائي دعم تقني",
            "career_en": "Systems Engineer\nNetwork Specialist\nTechnical Support Specialist",
        }

    if any(token in key for token in ["business", "إدارة", "management"]):
        return {
            "objectives_ar": "تطوير القدرات الإدارية والتحليلية لدى الطلبة.\nتعزيز مهارات التخطيط واتخاذ القرار في بيئة الأعمال.\nإعداد كوادر قادرة على قيادة فرق العمل بكفاءة.",
            "objectives_en": "Develop students' managerial and analytical capabilities.\nEnhance planning and decision-making skills in business environments.\nPrepare graduates capable of leading teams effectively.",
            "career_ar": "مدير مشاريع\nمحلل أعمال\nمسؤول موارد بشرية",
            "career_en": "Project Manager\nBusiness Analyst\nHR Officer",
        }

    return {
        "objectives_ar": "تنمية المعرفة التخصصية والمهارات العملية للطلبة.\nتعزيز التفكير النقدي وحل المشكلات.\nإعداد خريجين مؤهلين لسوق العمل.",
        "objectives_en": "Develop students' domain knowledge and practical skills.\nStrengthen critical thinking and problem-solving abilities.\nPrepare graduates ready for the labor market.",
        "career_ar": "وظائف تخصصية في القطاعين العام والخاص\nمساعد باحث\nمطور مهني",
        "career_en": "Specialized roles in public and private sectors\nResearch Assistant\nProfessional Practitioner",
    }


def run() -> dict[str, int]:
    programs = frappe.get_all(
        "Academic Programs",
        fields=["name", "program_name", "name_ar", "name_en", "college", "objectives_ar", "objectives_en", "career_prospects_ar", "career_prospects_en"],
        limit_page_length=0,
        ignore_permissions=True,
    )

    updated_programs = 0
    for row in programs:
        source_name = row.get("name_ar") or row.get("name_en") or row.get("program_name") or ""
        template = _template_for_program(source_name)

        updates = {}
        if not (row.get("objectives_ar") or "").strip():
            updates["objectives_ar"] = template["objectives_ar"]
        if not (row.get("objectives_en") or "").strip():
            updates["objectives_en"] = template["objectives_en"]
        if not (row.get("career_prospects_ar") or "").strip():
            updates["career_prospects_ar"] = template["career_ar"]
        if not (row.get("career_prospects_en") or "").strip():
            updates["career_prospects_en"] = template["career_en"]

        if updates:
            frappe.db.set_value("Academic Programs", row["name"], updates, update_modified=False)
            updated_programs += 1

    faculties = frappe.get_all(
        "Faculty Members",
        fields=["name", "linked_college", "linked_program"],
        filters={"is_active": 1},
        limit_page_length=0,
        ignore_permissions=True,
    )

    programs_by_college: dict[str, list[str]] = {}
    for row in programs:
        college = row.get("college")
        if not college:
            continue
        programs_by_college.setdefault(college, []).append(row.get("name"))

    linked_faculty = 0
    cycle_index: dict[str, int] = {}
    for faculty in faculties:
        if faculty.get("linked_program"):
            continue
        college = faculty.get("linked_college")
        if not college:
            continue
        choices = programs_by_college.get(college) or []
        if not choices:
            continue
        idx = cycle_index.get(college, 0)
        selected_program = choices[idx % len(choices)]
        cycle_index[college] = idx + 1
        frappe.db.set_value("Faculty Members", faculty["name"], "linked_program", selected_program, update_modified=False)
        linked_faculty += 1

    frappe.db.commit()
    return {
        "updated_programs": updated_programs,
        "linked_faculty": linked_faculty,
        "programs_total": len(programs),
    }
