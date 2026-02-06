# 📊 توثيق قاعدة البيانات وواجهات API
# Database Schema and API Documentation

هذا الملف يحتوي على جميع الجداول والحقول وال APIs المطلوبة للموقع ليكون تفاعلي بالكامل.

---

## 🏛️ جدول 1: الكليات (colleges)

### الحقول:
| الحقل | النوع | الوصف | مطلوب |
|-------|------|-------|-------|
| id | UUID | المعرف الفريد | ✅ |
| slug | VARCHAR(100) | الرابط الفريد للكلية | ✅ |
| name_ar | VARCHAR(255) | اسم الكلية بالعربي | ✅ |
| name_en | VARCHAR(255) | اسم الكلية بالإنجليزي | ✅ |
| description_ar | TEXT | وصف الكلية بالعربي | ✅ |
| description_en | TEXT | وصف الكلية بالإنجليزي | ✅ |
| vision_ar | TEXT | رؤية الكلية بالعربي | ✅ |
| vision_en | TEXT | رؤية الكلية بالإنجليزي | ✅ |
| mission_ar | TEXT | رسالة الكلية بالعربي | ✅ |
| mission_en | TEXT | رسالة الكلية بالإنجليزي | ✅ |
| admission_requirements_ar | TEXT | متطلبات القبول بالعربي | ✅ |
| admission_requirements_en | TEXT | متطلبات القبول بالإنجليزي | ✅ |
| icon | VARCHAR(100) | اسم الأيقونة | ❌ |
| image | VARCHAR(500) | رابط صورة الكلية | ❌ |
| order_index | INTEGER | ترتيب العرض | ❌ |
| is_active | BOOLEAN | حالة النشر | ✅ |
| created_at | TIMESTAMP | تاريخ الإنشاء | ✅ |
| updated_at | TIMESTAMP | تاريخ التحديث | ✅ |

### API Endpoints:
```
GET    /api/colleges                    - جلب جميع الكليات
GET    /api/colleges/:slug              - جلب كلية واحدة
POST   /api/colleges                    - إنشاء كلية جديدة
PUT    /api/colleges/:id                - تحديث كلية
DELETE /api/colleges/:id                - حذف كلية
```

---

## 👔 جدول 2: عمداء الكليات (college_deans)

### الحقول:
| الحقل | النوع | الوصف | مطلوب |
|-------|------|-------|-------|
| id | UUID | المعرف الفريد | ✅ |
| college_id | UUID | معرف الكلية (FK) | ✅ |
| name_ar | VARCHAR(255) | الاسم بالعربي | ✅ |
| name_en | VARCHAR(255) | الاسم بالإنجليزي | ✅ |
| title_ar | VARCHAR(255) | اللقب بالعربي | ✅ |
| title_en | VARCHAR(255) | اللقب بالإنجليزي | ✅ |
| image | VARCHAR(500) | صورة العميد | ✅ |
| email | VARCHAR(255) | البريد الإلكتروني | ❌ |
| phone | VARCHAR(50) | رقم الهاتف | ❌ |
| bio_ar | TEXT | السيرة الذاتية بالعربي | ❌ |
| bio_en | TEXT | السيرة الذاتية بالإنجليزي | ❌ |
| message_ar | TEXT | كلمة العميد بالعربي | ❌ |
| message_en | TEXT | كلمة العميد بالإنجليزي | ❌ |
| is_active | BOOLEAN | حالة النشر | ✅ |
| created_at | TIMESTAMP | تاريخ الإنشاء | ✅ |

### API Endpoints:
```
GET    /api/colleges/:id/dean           - جلب عميد كلية معينة
PUT    /api/college-deans/:id           - تحديث بيانات العميد
```

---

## 📚 جدول 3: البرامج الأكاديمية (academic_programs)

### الحقول:
| الحقل | النوع | الوصف | مطلوب |
|-------|------|-------|-------|
| id | UUID | المعرف الفريد | ✅ |
| college_id | UUID | معرف الكلية (FK) | ✅ |
| name_ar | VARCHAR(255) | اسم البرنامج بالعربي | ✅ |
| name_en | VARCHAR(255) | اسم البرنامج بالإنجليزي | ✅ |
| department_ar | VARCHAR(255) | القسم بالعربي | ✅ |
| department_en | VARCHAR(255) | القسم بالإنجليزي | ✅ |
| admission_rate | DECIMAL(5,2) | نسبة القبول | ✅ |
| high_school_type | ENUM | نوع الثانوية (علمي/ادبي/مختلط) | ✅ |
| study_years | VARCHAR(50) | سنوات الدراسة | ✅ |
| image | VARCHAR(500) | صورة البرنامج | ❌ |
| description_ar | TEXT | وصف البرنامج بالعربي | ❌ |
| description_en | TEXT | وصف البرنامج بالإنجليزي | ❌ |
| career_prospects_ar | TEXT[] | فرص العمل بالعربي (مصفوفة) | ❌ |
| career_prospects_en | TEXT[] | فرص العمل بالإنجليزي (مصفوفة) | ❌ |
| order_index | INTEGER | ترتيب العرض | ❌ |
| is_active | BOOLEAN | حالة النشر | ✅ |
| created_at | TIMESTAMP | تاريخ الإنشاء | ✅ |
| updated_at | TIMESTAMP | تاريخ التحديث | ✅ |

### API Endpoints:
```
GET    /api/programs                    - جلب جميع البرامج
GET    /api/colleges/:id/programs       - جلب برامج كلية معينة
GET    /api/programs/:id                - جلب برنامج واحد
POST   /api/programs                    - إنشاء برنامج جديد
PUT    /api/programs/:id                - تحديث برنامج
DELETE /api/programs/:id                - حذف برنامج
```

---

## 🎯 جدول 4: أهداف البرامج (program_objectives)

### الحقول:
| الحقل | النوع | الوصف | مطلوب |
|-------|------|-------|-------|
| id | UUID | المعرف الفريد | ✅ |
| program_id | UUID | معرف البرنامج (FK) | ✅ |
| text_ar | TEXT | الهدف بالعربي | ✅ |
| text_en | TEXT | الهدف بالإنجليزي | ✅ |
| order_index | INTEGER | ترتيب العرض | ❌ |

### API Endpoints:
```
GET    /api/programs/:id/objectives     - جلب أهداف برنامج معين
POST   /api/program-objectives          - إضافة هدف جديد
PUT    /api/program-objectives/:id      - تحديث هدف
DELETE /api/program-objectives/:id      - حذف هدف
```

---

## 📖 جدول 5: الخطة الدراسية (study_plans)

### الحقول:
| الحقل | النوع | الوصف | مطلوب |
|-------|------|-------|-------|
| id | UUID | المعرف الفريد | ✅ |
| program_id | UUID | معرف البرنامج (FK) | ✅ |
| year_ar | VARCHAR(50) | السنة بالعربي | ✅ |
| year_en | VARCHAR(50) | السنة بالإنجليزي | ✅ |
| semester_ar | VARCHAR(50) | الفصل بالعربي | ✅ |
| semester_en | VARCHAR(50) | الفصل بالإنجليزي | ✅ |
| order_index | INTEGER | ترتيب العرض | ❌ |

---

## 📘 جدول 6: مقررات الخطة الدراسية (study_plan_courses)

### الحقول:
| الحقل | النوع | الوصف | مطلوب |
|-------|------|-------|-------|
| id | UUID | المعرف الفريد | ✅ |
| study_plan_id | UUID | معرف الخطة (FK) | ✅ |
| name_ar | VARCHAR(255) | اسم المقرر بالعربي | ✅ |
| name_en | VARCHAR(255) | اسم المقرر بالإنجليزي | ✅ |
| credit_hours | INTEGER | الساعات المعتمدة | ✅ |

---

## 👨‍🏫 جدول 7: أعضاء هيئة التدريس (faculty_members)

### الحقول:
| الحقل | النوع | الوصف | مطلوب |
|-------|------|-------|-------|
| id | UUID | المعرف الفريد | ✅ |
| name_ar | VARCHAR(255) | الاسم بالعربي | ✅ |
| name_en | VARCHAR(255) | الاسم بالإنجليزي | ✅ |
| degree_ar | VARCHAR(255) | الدرجة العلمية بالعربي | ✅ |
| degree_en | VARCHAR(255) | الدرجة العلمية بالإنجليزي | ✅ |
| specialization_ar | VARCHAR(255) | التخصص بالعربي | ✅ |
| specialization_en | VARCHAR(255) | التخصص بالإنجليزي | ✅ |
| college_ar | VARCHAR(255) | الكلية بالعربي | ✅ |
| college_en | VARCHAR(255) | الكلية بالإنجليزي | ✅ |
| department_ar | VARCHAR(255) | القسم بالعربي | ❌ |
| department_en | VARCHAR(255) | القسم بالإنجليزي | ❌ |
| email | VARCHAR(255) | البريد الإلكتروني | ❌ |
| phone | VARCHAR(50) | رقم الهاتف | ❌ |
| bio_ar | TEXT | السيرة الذاتية بالعربي | ❌ |
| bio_en | TEXT | السيرة الذاتية بالإنجليزي | ❌ |
| image | VARCHAR(500) | صورة العضو | ❌ |
| order_index | INTEGER | ترتيب العرض | ❌ |
| is_active | BOOLEAN | حالة النشر | ✅ |
| created_at | TIMESTAMP | تاريخ الإنشاء | ✅ |
| updated_at | TIMESTAMP | تاريخ التحديث | ✅ |

### API Endpoints:
```
GET    /api/faculty                     - جلب جميع الأعضاء
GET    /api/faculty/:id                 - جلب عضو واحد
GET    /api/colleges/:id/faculty        - جلب أعضاء كلية معينة
POST   /api/faculty                     - إنشاء عضو جديد
PUT    /api/faculty/:id                 - تحديث عضو
DELETE /api/faculty/:id                 - حذف عضو
```

---

## 👨‍🏫 جدول 8: أعضاء هيئة التدريس للبرامج (program_faculty)

### الحقول:
| الحقل | النوع | الوصف | مطلوب |
|-------|------|-------|-------|
| id | UUID | المعرف الفريد | ✅ |
| program_id | UUID | معرف البرنامج (FK) | ✅ |
| name_ar | VARCHAR(255) | الاسم بالعربي | ✅ |
| name_en | VARCHAR(255) | الاسم بالإنجليزي | ✅ |
| title_ar | VARCHAR(255) | اللقب بالعربي | ✅ |
| title_en | VARCHAR(255) | اللقب بالإنجليزي | ✅ |
| image | VARCHAR(500) | الصورة | ❌ |
| email | VARCHAR(255) | البريد الإلكتروني | ❌ |
| specialization_ar | VARCHAR(255) | التخصص بالعربي | ❌ |
| specialization_en | VARCHAR(255) | التخصص بالإنجليزي | ❌ |

### API Endpoints:
```
GET    /api/programs/:id/faculty        - جلب أعضاء برنامج معين
POST   /api/program-faculty             - إضافة عضو لبرنامج
PUT    /api/program-faculty/:id         - تحديث عضو
DELETE /api/program-faculty/:id         - حذف عضو
```

---

## 📰 جدول 9: الأخبار (news)

### الحقول:
| الحقل | النوع | الوصف | مطلوب |
|-------|------|-------|-------|
| id | UUID | المعرف الفريد | ✅ |
| slug | VARCHAR(255) | الرابط الفريد | ✅ |
| title_ar | VARCHAR(500) | العنوان بالعربي | ✅ |
| title_en | VARCHAR(500) | العنوان بالإنجليزي | ✅ |
| description_ar | TEXT | الوصف المختصر بالعربي | ✅ |
| description_en | TEXT | الوصف المختصر بالإنجليزي | ✅ |
| content_ar | TEXT | المحتوى الكامل بالعربي | ✅ |
| content_en | TEXT | المحتوى الكامل بالإنجليزي | ✅ |
| image | VARCHAR(500) | الصورة الرئيسية | ❌ |
| date | DATE | تاريخ النشر | ✅ |
| views | INTEGER | عدد المشاهدات | ✅ |
| tags | TEXT[] | الوسوم (مصفوفة) | ❌ |
| is_featured | BOOLEAN | خبر مميز | ❌ |
| is_published | BOOLEAN | حالة النشر | ✅ |
| created_at | TIMESTAMP | تاريخ الإنشاء | ✅ |
| updated_at | TIMESTAMP | تاريخ التحديث | ✅ |

### API Endpoints:
```
GET    /api/news                        - جلب جميع الأخبار
GET    /api/news/:slug                  - جلب خبر واحد
GET    /api/news/featured               - جلب الأخبار المميزة
GET    /api/news/latest?limit=5         - جلب أحدث الأخبار
POST   /api/news                        - إنشاء خبر جديد
PUT    /api/news/:id                    - تحديث خبر
DELETE /api/news/:id                    - حذف خبر
POST   /api/news/:id/views              - زيادة عدد المشاهدات
```

---

## 📅 جدول 10: الفعاليات (events)

### الحقول:
| الحقل | النوع | الوصف | مطلوب |
|-------|------|-------|-------|
| id | UUID | المعرف الفريد | ✅ |
| slug | VARCHAR(255) | الرابط الفريد | ✅ |
| title_ar | VARCHAR(500) | العنوان بالعربي | ✅ |
| title_en | VARCHAR(500) | العنوان بالإنجليزي | ✅ |
| description_ar | TEXT | الوصف بالعربي | ✅ |
| description_en | TEXT | الوصف بالإنجليزي | ✅ |
| content_ar | TEXT | المحتوى التفصيلي بالعربي | ❌ |
| content_en | TEXT | المحتوى التفصيلي بالإنجليزي | ❌ |
| date | DATE | تاريخ البداية | ✅ |
| end_date | DATE | تاريخ النهاية | ❌ |
| location_ar | VARCHAR(255) | المكان بالعربي | ✅ |
| location_en | VARCHAR(255) | المكان بالإنجليزي | ✅ |
| organizer_ar | VARCHAR(255) | الجهة المنظمة بالعربي | ✅ |
| organizer_en | VARCHAR(255) | الجهة المنظمة بالإنجليزي | ✅ |
| category | ENUM | التصنيف (academic/cultural/sports/social/other) | ✅ |
| status | ENUM | الحالة (upcoming/ongoing/completed) | ✅ |
| registration_required | BOOLEAN | يتطلب تسجيل | ✅ |
| registration_link | VARCHAR(500) | رابط التسجيل | ❌ |
| image | VARCHAR(500) | الصورة | ❌ |
| is_published | BOOLEAN | حالة النشر | ✅ |
| created_at | TIMESTAMP | تاريخ الإنشاء | ✅ |
| updated_at | TIMESTAMP | تاريخ التحديث | ✅ |

### API Endpoints:
```
GET    /api/events                      - جلب جميع الفعاليات
GET    /api/events/:slug                - جلب فعالية واحدة
GET    /api/events/upcoming             - جلب الفعاليات القادمة
GET    /api/events/category/:cat        - جلب فعاليات حسب التصنيف
POST   /api/events                      - إنشاء فعالية جديدة
PUT    /api/events/:id                  - تحديث فعالية
DELETE /api/events/:id                  - حذف فعالية
```

---

## 🏢 جدول 11: المراكز (centers)

### الحقول:
| الحقل | النوع | الوصف | مطلوب |
|-------|------|-------|-------|
| id | UUID | المعرف الفريد | ✅ |
| title_ar | VARCHAR(255) | العنوان بالعربي | ✅ |
| title_en | VARCHAR(255) | العنوان بالإنجليزي | ✅ |
| desc_ar | TEXT | الوصف بالعربي | ✅ |
| desc_en | TEXT | الوصف بالإنجليزي | ✅ |
| image | VARCHAR(500) | الصورة | ❌ |
| location | VARCHAR(255) | الموقع | ❌ |
| phone | VARCHAR(50) | رقم الهاتف | ❌ |
| email | VARCHAR(255) | البريد الإلكتروني | ❌ |
| order_index | INTEGER | ترتيب العرض | ❌ |
| is_active | BOOLEAN | حالة النشر | ✅ |
| created_at | TIMESTAMP | تاريخ الإنشاء | ✅ |
| updated_at | TIMESTAMP | تاريخ التحديث | ✅ |

### API Endpoints:
```
GET    /api/centers                     - جلب جميع المراكز
GET    /api/centers/:id                 - جلب مركز واحد
POST   /api/centers                     - إنشاء مركز جديد
PUT    /api/centers/:id                 - تحديث مركز
DELETE /api/centers/:id                 - حذف مركز
```

---

## 🛠️ جدول 12: خدمات المراكز (center_services)

### الحقول:
| الحقل | النوع | الوصف | مطلوب |
|-------|------|-------|-------|
| id | UUID | المعرف الفريد | ✅ |
| center_id | UUID | معرف المركز (FK) | ✅ |
| text_ar | VARCHAR(500) | الخدمة بالعربي | ✅ |
| text_en | VARCHAR(500) | الخدمة بالإنجليزي | ✅ |
| order_index | INTEGER | ترتيب العرض | ❌ |

---

## 📋 جدول 13: برامج المراكز (center_programs)

### الحقول:
| الحقل | النوع | الوصف | مطلوب |
|-------|------|-------|-------|
| id | UUID | المعرف الفريد | ✅ |
| center_id | UUID | معرف المركز (FK) | ✅ |
| text_ar | VARCHAR(500) | البرنامج بالعربي | ✅ |
| text_en | VARCHAR(500) | البرنامج بالإنجليزي | ✅ |
| order_index | INTEGER | ترتيب العرض | ❌ |

---

## 🤝 جدول 14: الشركاء (partners)

### الحقول:
| الحقل | النوع | الوصف | مطلوب |
|-------|------|-------|-------|
| id | UUID | المعرف الفريد | ✅ |
| name_ar | VARCHAR(255) | الاسم بالعربي | ✅ |
| name_en | VARCHAR(255) | الاسم بالإنجليزي | ✅ |
| logo | VARCHAR(500) | شعار الشريك | ✅ |
| type | ENUM | النوع (local/international) | ✅ |
| website | VARCHAR(500) | الموقع الإلكتروني | ❌ |
| order_index | INTEGER | ترتيب العرض | ❌ |
| is_active | BOOLEAN | حالة النشر | ✅ |
| created_at | TIMESTAMP | تاريخ الإنشاء | ✅ |

### API Endpoints:
```
GET    /api/partners                    - جلب جميع الشركاء
GET    /api/partners/type/:type         - جلب شركاء حسب النوع
POST   /api/partners                    - إضافة شريك جديد
PUT    /api/partners/:id                - تحديث شريك
DELETE /api/partners/:id                - حذف شريك
```

---

## 🎁 جدول 15: العروض (offers)

### الحقول:
| الحقل | النوع | الوصف | مطلوب |
|-------|------|-------|-------|
| id | UUID | المعرف الفريد | ✅ |
| title_ar | VARCHAR(255) | العنوان بالعربي | ✅ |
| title_en | VARCHAR(255) | العنوان بالإنجليزي | ✅ |
| desc_ar | TEXT | الوصف بالعربي | ✅ |
| desc_en | TEXT | الوصف بالإنجليزي | ✅ |
| image | VARCHAR(500) | الصورة | ❌ |
| category | ENUM | التصنيف (academic/scholarship/training/other) | ✅ |
| valid_until | DATE | تاريخ الانتهاء | ❌ |
| is_active | BOOLEAN | حالة النشر | ✅ |
| created_at | TIMESTAMP | تاريخ الإنشاء | ✅ |
| updated_at | TIMESTAMP | تاريخ التحديث | ✅ |

### API Endpoints:
```
GET    /api/offers                      - جلب جميع العروض
GET    /api/offers/active               - جلب العروض النشطة
GET    /api/offers/category/:cat        - جلب عروض حسب التصنيف
POST   /api/offers                      - إضافة عرض جديد
PUT    /api/offers/:id                  - تحديث عرض
DELETE /api/offers/:id                  - حذف عرض
```

---

## ❓ جدول 16: الأسئلة الشائعة (faqs)

### الحقول:
| الحقل | النوع | الوصف | مطلوب |
|-------|------|-------|-------|
| id | UUID | المعرف الفريد | ✅ |
| question_ar | TEXT | السؤال بالعربي | ✅ |
| question_en | TEXT | السؤال بالإنجليزي | ✅ |
| answer_ar | TEXT | الإجابة بالعربي | ✅ |
| answer_en | TEXT | الإجابة بالإنجليزي | ✅ |
| category | VARCHAR(100) | التصنيف | ❌ |
| order_index | INTEGER | ترتيب العرض | ❌ |
| is_active | BOOLEAN | حالة النشر | ✅ |
| created_at | TIMESTAMP | تاريخ الإنشاء | ✅ |

### API Endpoints:
```
GET    /api/faqs                        - جلب جميع الأسئلة
GET    /api/faqs/category/:cat          - جلب أسئلة حسب التصنيف
POST   /api/faqs                        - إضافة سؤال جديد
PUT    /api/faqs/:id                    - تحديث سؤال
DELETE /api/faqs/:id                    - حذف سؤال
```

---

## 👥 جدول 17: فريق العمل (team_members)

### الحقول:
| الحقل | النوع | الوصف | مطلوب |
|-------|------|-------|-------|
| id | UUID | المعرف الفريد | ✅ |
| name_ar | VARCHAR(255) | الاسم بالعربي | ✅ |
| name_en | VARCHAR(255) | الاسم بالإنجليزي | ✅ |
| position_ar | VARCHAR(255) | المنصب بالعربي | ✅ |
| position_en | VARCHAR(255) | المنصب بالإنجليزي | ✅ |
| email | VARCHAR(255) | البريد الإلكتروني | ❌ |
| phone | VARCHAR(50) | رقم الهاتف | ❌ |
| bio_ar | TEXT | السيرة الذاتية بالعربي | ❌ |
| bio_en | TEXT | السيرة الذاتية بالإنجليزي | ❌ |
| image | VARCHAR(500) | الصورة | ❌ |
| order_index | INTEGER | ترتيب العرض | ❌ |
| is_active | BOOLEAN | حالة النشر | ✅ |
| created_at | TIMESTAMP | تاريخ الإنشاء | ✅ |

### API Endpoints:
```
GET    /api/team                        - جلب جميع الأعضاء
GET    /api/team/:id                    - جلب عضو واحد
POST   /api/team                        - إضافة عضو جديد
PUT    /api/team/:id                    - تحديث عضو
DELETE /api/team/:id                    - حذف عضو
```

---

## 💼 جدول 18: المشاريع (projects)

### الحقول:
| الحقل | النوع | الوصف | مطلوب |
|-------|------|-------|-------|
| id | UUID | المعرف الفريد | ✅ |
| slug | VARCHAR(255) | الرابط الفريد | ✅ |
| title_ar | VARCHAR(500) | العنوان بالعربي | ✅ |
| title_en | VARCHAR(500) | العنوان بالإنجليزي | ✅ |
| desc_ar | TEXT | الوصف بالعربي | ✅ |
| desc_en | TEXT | الوصف بالإنجليزي | ✅ |
| details_ar | TEXT | التفاصيل بالعربي | ❌ |
| details_en | TEXT | التفاصيل بالإنجليزي | ❌ |
| students | TEXT[] | أسماء الطلاب (مصفوفة) | ✅ |
| progress | INTEGER | نسبة التقدم (0-100) | ❌ |
| year | INTEGER | السنة | ❌ |
| status | ENUM | الحالة (current/completed) | ✅ |
| images | TEXT[] | صور المشروع (مصفوفة) | ❌ |
| start_date | DATE | تاريخ البداية | ❌ |
| end_date | DATE | تاريخ النهاية | ❌ |
| is_published | BOOLEAN | حالة النشر | ✅ |
| created_at | TIMESTAMP | تاريخ الإنشاء | ✅ |
| updated_at | TIMESTAMP | تاريخ التحديث | ✅ |

### API Endpoints:
```
GET    /api/projects                    - جلب جميع المشاريع
GET    /api/projects/:slug              - جلب مشروع واحد
GET    /api/projects/current            - جلب المشاريع الجارية
GET    /api/projects/completed          - جلب المشاريع المكتملة
POST   /api/projects                    - إنشاء مشروع جديد
PUT    /api/projects/:id                - تحديث مشروع
DELETE /api/projects/:id                - حذف مشروع
```

---

## 🏫 جدول 19: الحياة الجامعية (campus_life)

### الحقول:
| الحقل | النوع | الوصف | مطلوب |
|-------|------|-------|-------|
| id | UUID | المعرف الفريد | ✅ |
| title_ar | VARCHAR(255) | العنوان بالعربي | ✅ |
| title_en | VARCHAR(255) | العنوان بالإنجليزي | ✅ |
| description_ar | TEXT | الوصف بالعربي | ✅ |
| description_en | TEXT | الوصف بالإنجليزي | ✅ |
| category | ENUM | التصنيف (facilities/activities/campus) | ✅ |
| image | VARCHAR(500) | الصورة | ❌ |
| order_index | INTEGER | ترتيب العرض | ❌ |
| is_active | BOOLEAN | حالة النشر | ✅ |
| created_at | TIMESTAMP | تاريخ الإنشاء | ✅ |

### API Endpoints:
```
GET    /api/campus-life                 - جلب جميع العناصر
GET    /api/campus-life/category/:cat   - جلب عناصر حسب التصنيف
POST   /api/campus-life                 - إضافة عنصر جديد
PUT    /api/campus-life/:id             - تحديث عنصر
DELETE /api/campus-life/:id             - حذف عنصر
```

---

## ✍️ جدول 20: المدونة (blog_posts)

### الحقول:
| الحقل | النوع | الوصف | مطلوب |
|-------|------|-------|-------|
| id | UUID | المعرف الفريد | ✅ |
| slug | VARCHAR(255) | الرابط الفريد | ✅ |
| title_ar | VARCHAR(500) | العنوان بالعربي | ✅ |
| title_en | VARCHAR(500) | العنوان بالإنجليزي | ✅ |
| excerpt_ar | TEXT | المقتطف بالعربي | ✅ |
| excerpt_en | TEXT | المقتطف بالإنجليزي | ✅ |
| content_ar | TEXT | المحتوى بالعربي | ✅ |
| content_en | TEXT | المحتوى بالإنجليزي | ✅ |
| author_ar | VARCHAR(255) | الكاتب بالعربي | ✅ |
| author_en | VARCHAR(255) | الكاتب بالإنجليزي | ✅ |
| category | VARCHAR(100) | التصنيف | ✅ |
| tags | TEXT[] | الوسوم (مصفوفة) | ❌ |
| image | VARCHAR(500) | الصورة الرئيسية | ❌ |
| views | INTEGER | عدد المشاهدات | ✅ |
| is_published | BOOLEAN | حالة النشر | ✅ |
| published_at | TIMESTAMP | تاريخ النشر | ❌ |
| created_at | TIMESTAMP | تاريخ الإنشاء | ✅ |
| updated_at | TIMESTAMP | تاريخ التحديث | ✅ |

### API Endpoints:
```
GET    /api/blog                        - جلب جميع المقالات
GET    /api/blog/:slug                  - جلب مقالة واحدة
GET    /api/blog/category/:cat          - جلب مقالات حسب التصنيف
GET    /api/blog/latest?limit=5         - جلب أحدث المقالات
POST   /api/blog                        - إنشاء مقالة جديدة
PUT    /api/blog/:id                    - تحديث مقالة
DELETE /api/blog/:id                    - حذف مقالة
POST   /api/blog/:id/views              - زيادة عدد المشاهدات
```

---

## 📄 جدول 21: الصفحات التعريفية (pages)

### الحقول:
| الحقل | النوع | الوصف | مطلوب |
|-------|------|-------|-------|
| id | UUID | المعرف الفريد | ✅ |
| slug | VARCHAR(100) | المعرف الفريد (about/admission/campus-life) | ✅ |
| title_ar | VARCHAR(255) | العنوان بالعربي | ✅ |
| title_en | VARCHAR(255) | العنوان بالإنجليزي | ✅ |
| content_ar | TEXT | المحتوى بالعربي | ✅ |
| content_en | TEXT | المحتوى بالإنجليزي | ✅ |
| meta_description_ar | TEXT | وصف SEO بالعربي | ❌ |
| meta_description_en | TEXT | وصف SEO بالإنجليزي | ❌ |
| hero_image | VARCHAR(500) | صورة الهيرو | ❌ |
| updated_at | TIMESTAMP | تاريخ التحديث | ✅ |

### API Endpoints:
```
GET    /api/pages/:slug                 - جلب صفحة واحدة
PUT    /api/pages/:slug                 - تحديث صفحة
```

---

## 🖼️ جدول 22: مكتبة الوسائط (media)

### الحقول:
| الحقل | النوع | الوصف | مطلوب |
|-------|------|-------|-------|
| id | UUID | المعرف الفريد | ✅ |
| file_name | VARCHAR(255) | اسم الملف | ✅ |
| file_path | VARCHAR(500) | مسار الملف | ✅ |
| file_type | VARCHAR(50) | نوع الملف (image/video/document) | ✅ |
| file_size | INTEGER | حجم الملف (bytes) | ✅ |
| alt_ar | VARCHAR(255) | النص البديل بالعربي | ❌ |
| alt_en | VARCHAR(255) | النص البديل بالإنجليزي | ❌ |
| folder | VARCHAR(100) | المجلد | ❌ |
| uploaded_by | UUID | معرف المستخدم | ✅ |
| created_at | TIMESTAMP | تاريخ الرفع | ✅ |

### API Endpoints:
```
GET    /api/media                       - جلب جميع الملفات
GET    /api/media/folder/:folder        - جلب ملفات مجلد معين
POST   /api/media/upload                - رفع ملف جديد
DELETE /api/media/:id                   - حذف ملف
```

---

## ⚙️ جدول 23: الإعدادات العامة (settings)

### الحقول:
| الحقل | النوع | الوصف | مطلوب |
|-------|------|-------|-------|
| id | UUID | المعرف الفريد | ✅ |
| key | VARCHAR(100) | مفتاح الإعداد | ✅ |
| value_ar | TEXT | القيمة بالعربي | ✅ |
| value_en | TEXT | القيمة بالإنجليزي | ✅ |
| type | VARCHAR(50) | نوع القيمة (text/image/json) | ✅ |
| category | VARCHAR(50) | التصنيف (general/contact/social) | ✅ |
| updated_at | TIMESTAMP | تاريخ التحديث | ✅ |

### الإعدادات المطلوبة:
```
- site_name               اسم الموقع
- site_logo               شعار الموقع
- site_favicon            أيقونة الموقع
- hero_title              عنوان الهيرو
- hero_subtitle           العنوان الفرعي للهيرو
- hero_image              صورة الهيرو
- hero_video              فيديو الهيرو (اختياري)
- about_short             نبذة مختصرة
- phone                   رقم الهاتف
- email                   البريد الإلكتروني
- address                 العنوان
- map_location            إحداثيات الخريطة
- facebook                رابط فيسبوك
- twitter                 رابط تويتر
- instagram               رابط انستجرام
- linkedin                رابط لينكدإن
- youtube                 رابط يوتيوب
- working_hours           ساعات العمل
- footer_text             نص الفوتر
```

### API Endpoints:
```
GET    /api/settings                    - جلب جميع الإعدادات
GET    /api/settings/:key               - جلب إعداد معين
PUT    /api/settings/:key               - تحديث إعداد
```

---

## 📧 جدول 24: رسائل التواصل (contact_messages)

### الحقول:
| الحقل | النوع | الوصف | مطلوب |
|-------|------|-------|-------|
| id | UUID | المعرف الفريد | ✅ |
| name | VARCHAR(255) | الاسم | ✅ |
| email | VARCHAR(255) | البريد الإلكتروني | ✅ |
| phone | VARCHAR(50) | رقم الهاتف | ❌ |
| subject | VARCHAR(255) | الموضوع | ✅ |
| message | TEXT | الرسالة | ✅ |
| status | ENUM | الحالة (new/read/replied/archived) | ✅ |
| replied_at | TIMESTAMP | تاريخ الرد | ❌ |
| created_at | TIMESTAMP | تاريخ الإرسال | ✅ |

### API Endpoints:
```
GET    /api/contact-messages            - جلب جميع الرسائل
GET    /api/contact-messages/:id        - جلب رسالة واحدة
POST   /api/contact-messages            - إرسال رسالة جديدة
PUT    /api/contact-messages/:id/status - تحديث حالة الرسالة
DELETE /api/contact-messages/:id        - حذف رسالة
```

---

## 📝 جدول 25: طلبات الانضمام (join_requests)

### الحقول:
| الحقل | النوع | الوصف | مطلوب |
|-------|------|-------|-------|
| id | UUID | المعرف الفريد | ✅ |
| type | ENUM | النوع (student/employee) | ✅ |
| name | VARCHAR(255) | الاسم الكامل | ✅ |
| email | VARCHAR(255) | البريد الإلكتروني | ✅ |
| phone | VARCHAR(50) | رقم الهاتف | ✅ |
| specialty | VARCHAR(255) | التخصص | ✅ |
| experience | TEXT | الخبرة (للموظفين) | ❌ |
| cv_file | VARCHAR(500) | رابط السيرة الذاتية | ❌ |
| message | TEXT | رسالة إضافية | ❌ |
| status | ENUM | الحالة (pending/reviewed/accepted/rejected) | ✅ |
| reviewed_at | TIMESTAMP | تاريخ المراجعة | ❌ |
| created_at | TIMESTAMP | تاريخ الطلب | ✅ |

### API Endpoints:
```
GET    /api/join-requests               - جلب جميع الطلبات
GET    /api/join-requests/:id           - جلب طلب واحد
POST   /api/join-requests               - تقديم طلب جديد
PUT    /api/join-requests/:id/status    - تحديث حالة الطلب
DELETE /api/join-requests/:id           - حذف طلب
```

---

## 🔍 البحث (Search API)

### API Endpoints:
```
GET    /api/search?q=query              - البحث العام
GET    /api/search?q=query&type=news    - البحث في نوع محدد
```

### أنواع البحث المدعومة:
- news (الأخبار)
- events (الفعاليات)
- projects (المشاريع)
- centers (المراكز)
- offers (العروض)
- colleges (الكليات)
- programs (البرامج)
- faculty (أعضاء هيئة التدريس)
- blog (المدونة)

---

## 📊 ملخص الجداول

| # | الجدول | الوصف |
|---|--------|-------|
| 1 | colleges | الكليات |
| 2 | college_deans | عمداء الكليات |
| 3 | academic_programs | البرامج الأكاديمية |
| 4 | program_objectives | أهداف البرامج |
| 5 | study_plans | الخطط الدراسية |
| 6 | study_plan_courses | مقررات الخطط |
| 7 | faculty_members | أعضاء هيئة التدريس |
| 8 | program_faculty | أعضاء تدريس البرامج |
| 9 | news | الأخبار |
| 10 | events | الفعاليات |
| 11 | centers | المراكز |
| 12 | center_services | خدمات المراكز |
| 13 | center_programs | برامج المراكز |
| 14 | partners | الشركاء |
| 15 | offers | العروض |
| 16 | faqs | الأسئلة الشائعة |
| 17 | team_members | فريق العمل |
| 18 | projects | المشاريع |
| 19 | campus_life | الحياة الجامعية |
| 20 | blog_posts | المدونة |
| 21 | pages | الصفحات التعريفية |
| 22 | media | مكتبة الوسائط |
| 23 | settings | الإعدادات |
| 24 | contact_messages | رسائل التواصل |
| 25 | join_requests | طلبات الانضمام |

---

## 📊 ملخص API Endpoints

**إجمالي عدد الـ Endpoints: 85+**

| القسم | عدد الـ Endpoints |
|-------|------------------|
| الكليات والبرامج | 15 |
| الأخبار والفعاليات | 12 |
| المراكز والشركاء | 8 |
| أعضاء هيئة التدريس | 6 |
| العروض والأسئلة الشائعة | 8 |
| المشاريع | 6 |
| المدونة | 7 |
| الإعدادات والوسائط | 6 |
| التواصل والطلبات | 10 |
| البحث | 2 |
| أخرى | 5 |

---

## 🔐 ملاحظات أمنية

1. جميع الـ POST/PUT/DELETE تحتاج مصادقة (Authentication)
2. يجب استخدام HTTPS لجميع الطلبات
3. استخدام Token-based authentication (JWT)
4. التحقق من الصلاحيات قبل أي عملية كتابة
5. تقييد معدل الطلبات (Rate Limiting)
6. التحقق من صحة البيانات المدخلة (Validation)
