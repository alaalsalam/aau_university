# CMS Phase 0 Baseline Audit

تاريخ التدقيق: `2026-03-01`  
النطاق: `aau_university` (Frappe backend) + `AAU-16.24` (Next.js frontend)

## 1) مصادر التحليل (بدون افتراضات)

- باكند:
  - `api/v1/routes.py`
  - `api/v1/public.py`
  - `api/v1/content.py`
  - `api/v1/academic.py`
  - `api/v1/cms.py`
  - `api/v1/registry.py`
  - `api/v1/resources.py`
- فرونت:
  - `../AAU-16.24/app/(public)/**`
  - `../AAU-16.24/app/(auth)/**`
  - `../AAU-16.24/app/admin/**`
  - `../AAU-16.24/services/server/**`
  - `../AAU-16.24/services/client/**`
  - `../AAU-16.24/components/**`
- تحقق Runtime (site حي):
  - `https://edu.yemenfrappe.com`
  - تم فحص endpoints مباشرة بحالات HTTP.

## 2) جرد فعلي للبنية

### Backend API inventory

- عدد قواعد الراوت في `api/v1/routes.py`: **172**.
- عدد دوال `@frappe.whitelist`:
  - `content.py`: 69
  - `academic.py`: 31
  - `public.py`: 20
  - `portal.py`: 28
  - `access.py`: 11
  - `cms.py`: 7

### Frontend inventory

- Public pages: **26**
- Auth pages: **4**
- Admin pages: **18**
- Next API route handlers (`app/api/**`): **18**
- Server data services (`services/server/**`): **15**

## 3) مصفوفة الربط الرئيسية (UI -> API -> Backend -> Data Source)

| واجهة الفرونت | خدمة الفرونت | Endpoint | Handler باكند | DocType/مصدر | الحالة الحالية |
|---|---|---|---|---|---|
| `/` Home | `services/server/home.ts` | `/api/aau/home` | `public.get_home` | `Home Page`, `News`, `Events`, `Colleges`, `FAQ/FAQs` | يعمل (200) |
| Header/Footer | `services/server/menus.ts` | `/api/aau/menu/:key` | `public.get_public_menu` | `AAU Menu` + child items | يعمل (200) |
| `/news` + detail | `services/server/news.ts` | `/api/aau/news`, `/api/aau/news/:slug` | `public.list_public_news`, `public.get_public_news` | `News` | يعمل (200) |
| `/events` + detail | `services/server/events.ts` | `/api/aau/events`, `/api/aau/events/:slug` | `public.list_public_events`, `public.get_public_event` | `Events` | يعمل (200) |
| `/colleges` + detail | `services/server/colleges.ts` | `/api/aau/colleges`, `/api/aau/colleges/:slug` | `public.list_public_colleges`, `public.get_public_college` | `Colleges` + `Academic Programs` | يعمل (200) |
| `/about`, `/contact`, `/admission` | `services/server/pages.ts` | `/api/aau/page/:slug` | `public.get_public_page` | `AAU Page` | يعمل (200) |
| `/partners` | `services/server/partners.ts` | `/api/partners` | `content.list_partners` | `Partners` | يعمل (200، حالياً بدون بيانات) |
| `/faculty` + detail | `services/server/faculty.ts` | `/api/faculty`, `/api/faculty/:id` | `academic.list_faculty`, `academic.get_faculty` | `Faculty Members` | يعمل (200، حالياً بدون بيانات) |
| `/campus-life` | `services/server/campusLife.ts` | `/api/campus-life` | `content.list_campus_life` | `Campus Life` | يعمل (200، حالياً بدون بيانات) |
| `/centers` | `services/server/centers.ts` | `/api/centers` | `content.list_centers` | `Centers` | **متوقف** (404: DocType مفقود) |
| `/offers` | `services/server/offers.ts` | `/api/offers` | `content.list_offers` | `Offers` | **متوقف** (404: DocType مفقود) |
| `/projects-studio` | `services/server/projects.ts` | `/api/projects` | `content.list_projects` | `Projects` | **متوقف** (404: DocType مفقود) |
| `/team` | `services/server/team.ts` | `/api/team` | `content.list_team_members` | `Team Members` | **متوقف** (404: DocType مفقود) |
| `/blog` | `services/server/blog.ts` | `/api/blog` | `content.list_blog_posts` | `Blog Posts` | **متوقف** (404: DocType مفقود) |
| `/search` | `app/api/search/route.ts` | Next aggregator فوق عدة APIs | - | يعتمد على News/Events/Blog/Colleges/Centers/Offers | **جزئي** (يتأثر بأي endpoint ناقص) |

## 4) تحقق Runtime للأندبوينتات الأساسية

- `200`:  
  `/api/aau/home`, `/api/aau/news`, `/api/aau/events`, `/api/aau/colleges`, `/api/aau/page/about`, `/api/aau/menu/main`, `/api/partners`, `/api/faculty`, `/api/campus-life`
- `404` (مصادر ناقصة أو mismatch):  
  `/api/centers`, `/api/offers`, `/api/projects`, `/api/team`, `/api/blog`, `/api/faq`
- `401` (Admin protected):  
  `/api/contact-messages`, `/api/join-requests`
- POST checks:
  - `POST /api/contact-messages` -> `404` (registry يشير إلى `Contact Messages` بينما الموجود بالمشروع `Contact Us Messages`)
  - `POST /api/join-requests` -> `400` (validation يعمل)

## 5) ربط أقسام الهوم بالحقول الفعلية (Field-level)

| قسم UI | مصدر API | DocType | الحقول المستخدمة حالياً |
|---|---|---|---|
| Hero | `/api/aau/home` | `Home Page` | `hero_title`, `hero_subtitle`, `hero_description`, `hero_image`, `hero_cta_text`, `hero_cta_link` |
| Stats | `/api/aau/home` | `Home Page` + count | `students_count`, `programs_count`, + count من `Colleges` |
| About | `/api/aau/home` | `Home Page` | `about_title`, `about_description` |
| News cards | `/api/aau/home` | `News` | `title_ar/en`, `description_ar/en`, `summary`, `image/featured_image`, `date/publish_date`, `tags`, `views` |
| Events cards | `/api/aau/home` | `Events` | `event_title`, `description`, `event_date`, `location`, `image` (+ أي حقول متاحة) |
| Colleges cards | `/api/aau/home` | `Colleges` + `Academic Programs` | `name_ar/en`, `description_ar/en`, `icon`, `image`, وربط البرامج عبر `college` |
| FAQs | `/api/aau/home` | `FAQ` (fallback عند غياب `FAQs`) | `title/question*`, `content/answer*` وفق الحقول المتاحة |
| Header/Footer menus | `/api/aau/menu/:key` | `AAU Menu` | `key`, `published`, child `items` |

## 6) فجوات حرجة تم رصدها

1. **DocType coverage غير مكتمل** لصفحات عامة موجودة في الفرونت:  
   `Centers`, `Offers`, `Projects`, `Team Members`, `Blog Posts` غير موجودة -> 404 مباشر.

2. **Mismatch في FAQ**:  
   API entity مرتبط بـ `FAQs` بينما الموجود فعلياً `FAQ` -> `GET /api/faq` يرجع 404.

3. **Mismatch في Contact Messages**:  
   API entity مرتبط بـ `Contact Messages` بينما الموجود بالمشروع `Contact Us Messages` -> `POST /api/contact-messages` يفشل.

4. **Fallback/Static content ما زال موجود في الفرونت**:
   - `HeroSection.tsx` يحتوي نصوص افتراضية.
   - `AboutSection.tsx` يحتوي قيم/فقرات افتراضية طويلة.
   - `Footer.tsx` يحتوي quick/social/contact افتراضي.
   - `ContactSection.tsx` نموذج الإرسال لا يستدعي API (toast محلي فقط).

5. **Admin CMS UI غير موصول بالكامل بالباكند**:
   صفحات admin عديدة تعمل على state محلي/بيانات ثابتة (مثال: events/news/partners/offers/team) وليست CRUD حقيقي.

6. **Auth في صفحة login ما زال mock**:
   تخزين role في `localStorage` وتوجيه dashboard بدون مصادقة فعلية.

## 7) Checklist نهائي للمرحلة 0 (منجز)

- [x] حصر كل مصادر المحتوى المستخدمة فعلياً في الفرونت.
- [x] حصر كل endpoints المعرّفة فعلياً في الباكند.
- [x] مطابقة UI pages مع endpoints.
- [x] مطابقة endpoints مع DocTypes الحالية على الموقع.
- [x] قياس readiness لكل مسار (Working / Partial / Blocked).
- [x] توثيق فجوات التنفيذ التي تمنع CMS احترافي كامل.

## 8) مخرجات المرحلة 0 لاعتماد الانتقال للمرحلة 1

الانتقال للمرحلة 1 (Implementation) مشروط بالبنود التالية:

1. اعتماد canonical DocTypes المطلوبة للصفحات المتوقفة:  
   `Centers`, `Offers`, `Projects`, `Team Members`, `Blog Posts`.
2. حسم تسمية FAQ: توحيدها على `FAQ` أو `FAQs` في كل من registry + routes + frontend.
3. حسم Contact schema: توحيد `Contact Messages` مقابل `Contact Us Messages`.
4. اعتماد سياسة "No static fallback in production" في components المذكورة.
5. اعتماد خطة توصيل admin screens إلى CRUD حقيقي عبر APIs.

