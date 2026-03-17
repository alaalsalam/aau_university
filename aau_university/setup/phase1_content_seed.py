# -*- coding: utf-8 -*-
from __future__ import annotations

import frappe


def _upsert_by_field(doctype: str, fieldname: str, value: str, payload: dict) -> str:
    existing_name = frappe.db.get_value(doctype, {fieldname: value}, "name")
    if existing_name:
        doc = frappe.get_doc(doctype, existing_name)
        doc.update(payload)
        doc.save(ignore_permissions=True)
        return existing_name

    doc = frappe.get_doc({"doctype": doctype, fieldname: value, **payload})
    doc.insert(ignore_permissions=True)
    return doc.name


def _seed_centers() -> int:
    rows = [
        {
            "id": "clinical-skills-center",
            "title_ar": "مركز المهارات السريرية",
            "title_en": "Clinical Skills Center",
            "desc_ar": "مركز تدريبي يدعم طلاب الكليات الصحية بمحاكاة سريرية ومعامل تطبيقية تركز على الكفاءة العملية قبل التدريب الميداني.",
            "desc_en": "A training center that supports health sciences students through clinical simulation and practice labs focused on operational readiness before field training.",
            "services": "مختبرات محاكاة\nجلسات تدريب عملي\nتقييم مهارات إكلينيكية",
            "programs": "الطب البشري\nطب الأسنان\nالصيدلة",
            "image": "/assets/aau_university/hero-campus.jpg",
            "location": "الحرم الجامعي الرئيسي - مبنى العلوم الصحية",
            "phone": "+967 1 234 580",
            "email": "clinical.center@edu.yemenfrappe.com",
            "is_published": 1,
            "display_order": 1,
        },
        {
            "id": "innovation-entrepreneurship-center",
            "title_ar": "مركز الابتكار وريادة الأعمال",
            "title_en": "Innovation and Entrepreneurship Center",
            "desc_ar": "مساحة تطوير مشاريع طلابية ومبادرات ناشئة تربط التعليم الأكاديمي بالتطبيق العملي وبناء النماذج الأولية.",
            "desc_en": "A space for student projects and startups that connects academic learning with applied execution and prototyping.",
            "services": "إرشاد مشاريع\nمعسكرات ابتكار\nاحتضان مبادرات ناشئة",
            "programs": "الهندسة وتقنية المعلومات\nإدارة الأعمال\nالتسويق الرقمي",
            "image": "/assets/aau_university/hero-campus.jpg",
            "location": "مبنى الابتكار - الطابق الثاني",
            "phone": "+967 1 234 581",
            "email": "innovation@edu.yemenfrappe.com",
            "is_published": 1,
            "display_order": 2,
        },
        {
            "id": "community-service-center",
            "title_ar": "مركز خدمة المجتمع والتعليم المستمر",
            "title_en": "Community Service and Continuing Education Center",
            "desc_ar": "مركز يقدم دورات مهنية قصيرة وبرامج خدمة مجتمع وشراكات تدريبية مع الجهات المحلية وسوق العمل.",
            "desc_en": "A center providing short professional courses, community service programs, and practical training partnerships with local institutions and employers.",
            "services": "دورات قصيرة\nبرامج تطوير مهني\nشراكات تدريب مجتمعي",
            "programs": "التنمية المهنية\nالحاسب المكتبي\nمهارات الاتصال",
            "image": "/assets/aau_university/hero-campus.jpg",
            "location": "مبنى الإدارة - الدور الأرضي",
            "phone": "+967 1 234 582",
            "email": "community@edu.yemenfrappe.com",
            "is_published": 1,
            "display_order": 3,
        },
    ]

    for row in rows:
        _upsert_by_field("Centers", "id", row["id"], row)
    return len(rows)


def _seed_blog_posts() -> int:
    rows = [
        {
            "id": "student-readiness-skills",
            "slug": "student-readiness-skills",
            "title_ar": "كيف تبني الجامعة جاهزية الطالب لسوق العمل؟",
            "title_en": "How the University Builds Student Readiness for the Job Market",
            "excerpt_ar": "نظرة على التكامل بين التدريب العملي والأنشطة والمقررات الداعمة للمهارات المهنية.",
            "excerpt_en": "A look at how applied training, activities, and curriculum work together to build professional skills.",
            "content_ar": "تركز الجامعة على ربط التجربة الأكاديمية بالمهارات المطلوبة فعليًا في سوق العمل من خلال مشاريع تطبيقية، تدريب ميداني، وتطوير مهارات العرض والعمل الجماعي. كما يتم إشراك الطلاب في مبادرات ومسابقات تعزز من قدرتهم على تحويل المعرفة إلى نتائج عملية قابلة للقياس.",
            "content_en": "The university focuses on connecting the academic experience to actual labor market skills through applied projects, field training, and the development of presentation and teamwork skills. Students are also engaged in initiatives and competitions that improve their ability to turn knowledge into measurable outcomes.",
            "author_name_ar": "فريق التحرير",
            "author_name_en": "Editorial Team",
            "author_role_ar": "إدارة المحتوى الجامعي",
            "author_role_en": "University Content Office",
            "category": "student-life",
            "category_ar": "الحياة الجامعية",
            "category_en": "Student Life",
            "image": "/assets/aau_university/hero-campus.jpg",
            "published_at": "2026-03-01",
            "read_time": 4,
            "views": 120,
            "tags": "الطلبة,المهارات,التدريب",
            "is_published": 1,
            "display_order": 1,
        },
        {
            "id": "research-culture-at-aau",
            "slug": "research-culture-at-aau",
            "title_ar": "ثقافة البحث العلمي في جامعة الجيل الجديد",
            "title_en": "Research Culture at New Generation University",
            "excerpt_ar": "كيف يتم دعم الطلاب وأعضاء هيئة التدريس لإنتاج مشاريع بحثية ذات أثر عملي.",
            "excerpt_en": "How students and faculty are supported to produce research with practical impact.",
            "content_ar": "تعمل الجامعة على تعزيز ثقافة البحث العلمي عبر مبادرات تربط مشاريع التخرج بقضايا المجتمع، وتوفر إشرافًا أكاديميًا منظمًا، ومساحات لعرض المخرجات البحثية. هذا التوجه يرفع من جودة المشاريع ويزيد من ارتباطها بالاحتياجات الفعلية للمجتمع المحلي.",
            "content_en": "The university strengthens its research culture through initiatives that connect capstone projects to community issues, provide structured academic supervision, and create spaces to showcase research outputs. This approach improves project quality and increases relevance to local needs.",
            "author_name_ar": "إدارة البحث والتطوير",
            "author_name_en": "Research and Development Office",
            "author_role_ar": "قطاع التطوير الأكاديمي",
            "author_role_en": "Academic Development Division",
            "category": "research",
            "category_ar": "البحث العلمي",
            "category_en": "Research",
            "image": "/assets/aau_university/hero-campus.jpg",
            "published_at": "2026-03-05",
            "read_time": 5,
            "views": 98,
            "tags": "بحث علمي,تطوير,مشاريع",
            "is_published": 1,
            "display_order": 2,
        },
        {
            "id": "partnerships-and-community-impact",
            "slug": "partnerships-and-community-impact",
            "title_ar": "الشراكات المؤسسية وأثرها على التجربة التعليمية",
            "title_en": "Institutional Partnerships and Their Impact on Learning",
            "excerpt_ar": "أمثلة على كيف تدعم الشراكات الخارجية التدريب والتوظيف والأنشطة التطبيقية.",
            "excerpt_en": "Examples of how external partnerships support training, employability, and applied learning.",
            "content_ar": "الشراكات ليست عنصرًا تكميليًا في التجربة الجامعية، بل جزء من بنيتها التشغيلية. من خلالها تتوسع فرص التدريب، وتصبح البرامج أكثر ارتباطًا بالواقع المهني، ويتاح للطلاب الوصول إلى بيئات تطبيقية وشبكات مهنية أوسع.",
            "content_en": "Partnerships are not an optional layer in the university experience; they are part of its operational structure. They expand training opportunities, make programs more aligned with professional reality, and give students access to applied environments and wider professional networks.",
            "author_name_ar": "مكتب العلاقات المؤسسية",
            "author_name_en": "Institutional Relations Office",
            "author_role_ar": "الشراكات والتعاون",
            "author_role_en": "Partnerships and Collaboration",
            "category": "partnerships",
            "category_ar": "الشراكات",
            "category_en": "Partnerships",
            "image": "/assets/aau_university/hero-campus.jpg",
            "published_at": "2026-03-10",
            "read_time": 3,
            "views": 84,
            "tags": "شراكات,توظيف,تعاون",
            "is_published": 1,
            "display_order": 3,
        },
    ]

    for row in rows:
        _upsert_by_field("Blog Posts", "slug", row["slug"], row)
    return len(rows)


def _seed_partners() -> int:
    rows = [
        {
            "title": "مستشفى الجامعة التعليمي",
            "content": "شريك تدريبي يدعم برامج الكليات الصحية بالتدريب السريري والإشراف الميداني.",
            "image": "/assets/aau_university/hero-campus.jpg",
            "is_published": 1,
            "display_order": 1,
        },
        {
            "title": "الغرفة التجارية والصناعية",
            "content": "شريك في برامج التدريب المهني وربط الطلبة بفرص سوق العمل وريادة الأعمال.",
            "image": "/assets/aau_university/hero-campus.jpg",
            "is_published": 1,
            "display_order": 2,
        },
        {
            "title": "مركز التحول الرقمي",
            "content": "شراكة تدعم مسارات التقنية والابتكار وتطوير المهارات الرقمية التطبيقية للطلبة.",
            "image": "/assets/aau_university/hero-campus.jpg",
            "is_published": 1,
            "display_order": 3,
        },
    ]

    for row in rows:
        _upsert_by_field("Partners", "title", row["title"], row)
    return len(rows)


def _seed_offers() -> int:
    rows = [
        {
            "id": "new-intake-scholarship",
            "title_ar": "منحة التسجيل المبكر",
            "title_en": "Early Registration Scholarship",
            "desc_ar": "خصم خاص للطلبة الجدد عند استكمال التسجيل خلال فترة القبول المبكر.",
            "desc_en": "A special discount for new students who complete registration during the early admission period.",
            "details_ar": "يستفيد الطالب من خصم على الرسوم الدراسية للفصل الأول عند استكمال ملفه ودفع الرسوم خلال المدة المحددة من إدارة القبول.",
            "details_en": "Students receive a tuition discount for the first semester when they complete their file and payment within the admission office deadline.",
            "category": "admissions",
            "image": "/assets/aau_university/hero-campus.jpg",
            "valid_until": "2026-08-31",
            "target_audience_ar": "الطلبة الجدد",
            "target_audience_en": "New students",
            "benefits_ar": "خصم مالي\nأولوية في الجدولة\nاستكمال أسرع للإجراءات",
            "benefits_en": "Financial discount\nPriority scheduling\nFaster onboarding",
            "duration_ar": "حتى نهاية فترة القبول المبكر",
            "duration_en": "Until the end of the early admission period",
            "location_ar": "إدارة القبول والتسجيل",
            "location_en": "Admissions and Registration Office",
            "requirements_ar": "استكمال الوثائق\nسداد الرسوم خلال المدة\nمطابقة شروط القبول",
            "requirements_en": "Complete documentation\nFee payment within the period\nAdmission criteria fulfilled",
            "apply_link": "https://edu.yemenfrappe.com/apply",
            "is_active": 1,
            "is_published": 1,
            "display_order": 1,
        },
        {
            "id": "academic-excellence-award",
            "title_ar": "عرض التميز الأكاديمي",
            "title_en": "Academic Excellence Offer",
            "desc_ar": "امتيازات خاصة للطلبة المتفوقين في المعدل الأكاديمي والتحصيل النوعي.",
            "desc_en": "Special benefits for students with high academic achievement and quality performance.",
            "details_ar": "يشمل العرض مزايا أكاديمية ودعمًا في الأنشطة النوعية للطلبة المتفوقين وفق معايير الاعتماد الداخلي.",
            "details_en": "The offer includes academic benefits and support for high-performing students based on internal quality criteria.",
            "category": "students",
            "image": "/assets/aau_university/hero-campus.jpg",
            "valid_until": "2026-12-31",
            "target_audience_ar": "الطلبة المستمرون",
            "target_audience_en": "Continuing students",
            "benefits_ar": "حوافز أكاديمية\nأولوية للأنشطة النوعية\nدعم للتميز",
            "benefits_en": "Academic incentives\nPriority for quality activities\nExcellence support",
            "duration_ar": "طوال العام الأكاديمي",
            "duration_en": "Throughout the academic year",
            "location_ar": "شؤون الطلاب",
            "location_en": "Student Affairs",
            "requirements_ar": "تحقيق معدل متميز\nالالتزام الأكاديمي\nسجل انضباط جيد",
            "requirements_en": "High GPA\nAcademic commitment\nGood conduct record",
            "apply_link": "https://edu.yemenfrappe.com/app/student-dashboard",
            "is_active": 1,
            "is_published": 1,
            "display_order": 2,
        },
        {
            "id": "professional-training-package",
            "title_ar": "حزمة التدريب المهني المكثف",
            "title_en": "Professional Training Package",
            "desc_ar": "برنامج تدريبي قصير يمنح الطلبة فرصة تطوير مهارات مهنية تطبيقية قبل التخرج.",
            "desc_en": "A short training package that helps students build applied professional skills before graduation.",
            "details_ar": "تتضمن الحزمة ورشًا تطبيقية ومهارات عرض وعمل جماعي وأساسيات الجاهزية المهنية بالشراكة مع جهات تدريبية.",
            "details_en": "The package includes applied workshops, presentation skills, teamwork, and professional readiness basics in partnership with training entities.",
            "category": "training",
            "image": "/assets/aau_university/hero-campus.jpg",
            "valid_until": "2026-10-15",
            "target_audience_ar": "طلبة المستويات النهائية",
            "target_audience_en": "Final-year students",
            "benefits_ar": "ورش تطبيقية\nشهادة مشاركة\nتحسين الجاهزية المهنية",
            "benefits_en": "Applied workshops\nParticipation certificate\nImproved employability",
            "duration_ar": "6 أسابيع",
            "duration_en": "6 weeks",
            "location_ar": "مركز الابتكار وريادة الأعمال",
            "location_en": "Innovation and Entrepreneurship Center",
            "requirements_ar": "التسجيل المسبق\nالالتزام بالحضور\nالانتماء للمستويات النهائية",
            "requirements_en": "Pre-registration\nAttendance commitment\nFinal-year student status",
            "apply_link": "https://edu.yemenfrappe.com/contact",
            "is_active": 1,
            "is_published": 1,
            "display_order": 3,
        },
    ]

    for row in rows:
        _upsert_by_field("Offers", "id", row["id"], row)
    return len(rows)


def _enrich_faculty() -> int:
    member_name = frappe.db.get_value("Faculty Members", {"full_name": "نسمة"}, "name")
    if not member_name:
        return 0

    department_name = frappe.db.get_value("Academic Departments", {"department_name": "الطب البشري"}, "name")
    doc = frappe.get_doc("Faculty Members", member_name)
    doc.update(
        {
            "academic_title": "الدكتورة",
            "department": department_name or doc.get("department"),
            "biography": "عضو هيئة تدريس في المسار الطبي، تركز على تطوير مهارات الطلبة السريرية وربط التعلم النظري بالتطبيق العملي في البيئة التعليمية.",
            "photo": "/assets/aau_university/hero-campus.jpg",
            "is_active": 1,
        }
    )
    doc.save(ignore_permissions=True)
    return 1


def run() -> dict:
    summary = {
        "centers": _seed_centers(),
        "blog_posts": _seed_blog_posts(),
        "partners": _seed_partners(),
        "offers": _seed_offers(),
        "faculty_enriched": _enrich_faculty(),
    }
    frappe.db.commit()
    return summary
