# API Specification - جامعة الجيل الجديد
# دليل APIs الكامل للموقع

> هذا الملف يحتوي على جميع APIs المطلوبة مع البيانات المثالية لكل منها

---

## 📋 جدول المحتويات

1. [الأخبار (News)](#1-الأخبار-news)
2. [الأحداث (Events)](#2-الأحداث-events)
3. [الكليات والبرامج (Colleges & Programs)](#3-الكليات-والبرامج-colleges--programs)
4. [أعضاء هيئة التدريس (Faculty)](#4-أعضاء-هيئة-التدريس-faculty)
5. [الشركاء (Partners)](#5-الشركاء-partners)
6. [المراكز (Centers)](#6-المراكز-centers)
7. [العروض (Offers)](#7-العروض-offers)
8. [الأسئلة الشائعة (FAQ)](#8-الأسئلة-الشائعة-faq)
9. [فريق العمل (Team)](#9-فريق-العمل-team)
10. [المشاريع الطلابية (Projects)](#10-المشاريع-الطلابية-projects)
11. [المدونة (Blog)](#11-المدونة-blog)
12. [الحياة الجامعية (Campus Life)](#12-الحياة-الجامعية-campus-life)
13. [البحث (Search)](#13-البحث-search)
14. [إدارة المستخدمين (Users & Roles)](#14-إدارة-المستخدمين-users--roles)
15. [بوابة الدكتور (Doctor Portal)](#15-بوابة-الدكتور-doctor-portal)
16. [بوابة الطالب (Student Portal)](#16-بوابة-الطالب-student-portal)
17. [الرسائل (Messages)](#17-الرسائل-messages)

---

## 1. الأخبار (News)

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/news` | جلب جميع الأخبار |
| GET | `/api/news/:slug` | جلب خبر بواسطة slug |
| GET | `/api/news/recent?limit=3` | جلب أحدث الأخبار |
| GET | `/api/news/search?q=query` | البحث في الأخبار |
| POST | `/api/news` | إضافة خبر جديد (Admin) |
| PUT | `/api/news/:id` | تعديل خبر (Admin) |
| DELETE | `/api/news/:id` | حذف خبر (Admin) |

### Data Structure

```typescript
interface NewsItem {
  id: string;
  slug: string;
  titleAr: string;
  titleEn: string;
  descriptionAr: string;
  descriptionEn: string;
  contentAr: string;          // HTML content
  contentEn: string;          // HTML content
  image?: string;             // URL
  date: string;               // ISO date "2024-01-15"
  views: number;
  tags?: string[];
}
```

### Sample Data

```json
{
  "id": "1",
  "slug": "university-partnership-mit",
  "titleAr": "جامعة الجيل الجديد توقع اتفاقية شراكة مع MIT",
  "titleEn": "NGU Signs Partnership Agreement with MIT",
  "descriptionAr": "وقعت جامعة الجيل الجديد اتفاقية شراكة استراتيجية مع معهد ماساتشوستس للتكنولوجيا",
  "descriptionEn": "New Generation University signed a strategic partnership agreement with MIT",
  "contentAr": "<h2>تفاصيل الشراكة</h2><p>تتضمن الاتفاقية تبادل الطلاب والأبحاث المشتركة...</p>",
  "contentEn": "<h2>Partnership Details</h2><p>The agreement includes student exchange and joint research...</p>",
  "image": "https://example.com/images/news/partnership.jpg",
  "date": "2024-01-15",
  "views": 1250,
  "tags": ["شراكات", "دولي", "أكاديمي"]
}
```

---

## 2. الأحداث (Events)

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/events` | جلب جميع الأحداث |
| GET | `/api/events/:id` | جلب حدث بواسطة ID |
| GET | `/api/events/slug/:slug` | جلب حدث بواسطة slug |
| GET | `/api/events/upcoming` | جلب الأحداث القادمة |
| GET | `/api/events/category/:category` | فلترة حسب الفئة |
| POST | `/api/events` | إضافة حدث (Admin) |
| PUT | `/api/events/:id` | تعديل حدث (Admin) |
| DELETE | `/api/events/:id` | حذف حدث (Admin) |

### Data Structure

```typescript
interface EventItem {
  id: string;
  slug: string;
  titleAr: string;
  titleEn: string;
  descriptionAr: string;
  descriptionEn: string;
  contentAr?: string;         // HTML content
  contentEn?: string;         // HTML content
  date: string;               // ISO date
  endDate?: string;           // ISO date (for multi-day events)
  locationAr: string;
  locationEn: string;
  organizerAr: string;
  organizerEn: string;
  category: 'academic' | 'cultural' | 'sports' | 'social' | 'other';
  status: 'upcoming' | 'ongoing' | 'completed';
  registrationRequired: boolean;
  registrationLink?: string;
  image?: string;
}
```

### Sample Data

```json
{
  "id": "1",
  "slug": "annual-science-conference-2024",
  "titleAr": "المؤتمر العلمي السنوي 2024",
  "titleEn": "Annual Science Conference 2024",
  "descriptionAr": "المؤتمر العلمي السنوي لعرض أحدث الأبحاث والابتكارات",
  "descriptionEn": "Annual science conference showcasing latest research and innovations",
  "contentAr": "<h2>برنامج المؤتمر</h2><p>يتضمن المؤتمر عروض تقديمية...</p>",
  "contentEn": "<h2>Conference Program</h2><p>The conference includes presentations...</p>",
  "date": "2024-03-15",
  "endDate": "2024-03-17",
  "locationAr": "قاعة المؤتمرات الرئيسية",
  "locationEn": "Main Conference Hall",
  "organizerAr": "عمادة البحث العلمي",
  "organizerEn": "Deanship of Scientific Research",
  "category": "academic",
  "status": "upcoming",
  "registrationRequired": true,
  "registrationLink": "https://register.ngu.edu/conference2024",
  "image": "https://example.com/images/events/conference.jpg"
}
```

---

## 3. الكليات والبرامج (Colleges & Programs)

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/colleges` | جلب جميع الكليات |
| GET | `/api/colleges/:slug` | جلب كلية بالتفاصيل الكاملة |
| GET | `/api/colleges/:id/programs` | برامج كلية معينة |
| GET | `/api/programs/:id` | تفاصيل برنامج أكاديمي |
| POST | `/api/colleges` | إضافة كلية (Admin) |
| PUT | `/api/colleges/:id` | تعديل كلية (Admin) |
| DELETE | `/api/colleges/:id` | حذف كلية (Admin) |

### Data Structures

```typescript
// العميد
interface CollegeDean {
  id: string;
  nameAr: string;
  nameEn: string;
  titleAr: string;
  titleEn: string;
  image: string;
  email?: string;
  phone?: string;
  bioAr?: string;
  bioEn?: string;
  messageAr?: string;       // كلمة العميد
  messageEn?: string;
}

// عضو هيئة تدريس البرنامج
interface ProgramFacultyMember {
  id: string;
  nameAr: string;
  nameEn: string;
  titleAr: string;
  titleEn: string;
  image?: string;
  email?: string;
  specializationAr?: string;
  specializationEn?: string;
}

// أهداف البرنامج
interface ProgramObjective {
  id: string;
  textAr: string;
  textEn: string;
}

// البرنامج الأكاديمي
interface AcademicProgram {
  id: string;
  nameAr: string;
  nameEn: string;
  departmentAr: string;
  departmentEn: string;
  admissionRate: number;                    // نسبة القبول (0-100)
  highSchoolType: 'علمي' | 'ادبي' | 'علمي + ادبي';
  highSchoolTypeEn: 'Scientific' | 'Literary' | 'Scientific + Literary';
  studyYears: string;                       // مثال: "1 + 6" أو "4"
  image?: string;
  descriptionAr?: string;
  descriptionEn?: string;
  objectives?: ProgramObjective[];
  careerProspectsAr?: string[];
  careerProspectsEn?: string[];
  facultyMembers?: ProgramFacultyMember[];
}

// الكلية
interface College {
  id: string;
  slug: string;
  nameAr: string;
  nameEn: string;
  descriptionAr: string;
  descriptionEn: string;
  visionAr: string;
  visionEn: string;
  missionAr: string;
  missionEn: string;
  admissionRequirementsAr: string;
  admissionRequirementsEn: string;
  icon?: string;                           // اسم أيقونة Lucide
  image?: string;
  dean?: CollegeDean;
  programs: AcademicProgram[];
}
```

### Sample Data

```json
{
  "id": "medicine",
  "slug": "medicine",
  "nameAr": "كلية الطب البشري",
  "nameEn": "College of Human Medicine",
  "descriptionAr": "كلية الطب البشري تقدم برنامجاً أكاديمياً متميزاً لإعداد أطباء مؤهلين",
  "descriptionEn": "The College of Human Medicine offers an outstanding academic program",
  "visionAr": "أن نكون كلية طبية رائدة في المنطقة",
  "visionEn": "To be a leading medical college in the region",
  "missionAr": "إعداد أطباء أكفاء مزودين بالمعرفة والمهارات",
  "missionEn": "Preparing competent physicians equipped with knowledge and skills",
  "admissionRequirementsAr": "شهادة الثانوية العامة الفرع العلمي بنسبة لا تقل عن 78%",
  "admissionRequirementsEn": "High school certificate scientific branch with minimum 78%",
  "icon": "Stethoscope",
  "image": "https://example.com/images/colleges/medicine.jpg",
  "dean": {
    "id": "dean-medicine",
    "nameAr": "أ.د. عبد الله محمد الراشد",
    "nameEn": "Prof. Abdullah Mohammed Al-Rashid",
    "titleAr": "عميد كلية الطب البشري",
    "titleEn": "Dean of College of Human Medicine",
    "image": "https://example.com/images/deans/medicine-dean.jpg",
    "email": "dean.medicine@ngu.edu",
    "phone": "+966 50 123 4567",
    "bioAr": "أستاذ دكتور في الجراحة العامة، خبرة أكاديمية تزيد عن 25 عاماً",
    "bioEn": "Professor of General Surgery with over 25 years of experience",
    "messageAr": "نسعى في كلية الطب البشري إلى إعداد جيل من الأطباء المتميزين...",
    "messageEn": "At the College of Human Medicine, we strive to prepare distinguished physicians..."
  },
  "programs": [
    {
      "id": "med-1",
      "nameAr": "برنامج طب وجراحة",
      "nameEn": "Medicine and Surgery Program",
      "departmentAr": "",
      "departmentEn": "",
      "admissionRate": 78,
      "highSchoolType": "علمي",
      "highSchoolTypeEn": "Scientific",
      "studyYears": "1 + 6",
      "image": "https://example.com/images/programs/medicine-surgery.jpg",
      "descriptionAr": "برنامج الطب والجراحة يهدف إلى إعداد أطباء متميزين",
      "descriptionEn": "The Medicine and Surgery program aims to prepare distinguished physicians",
      "objectives": [
        { "id": "1", "textAr": "إعداد أطباء مؤهلين علمياً وعملياً", "textEn": "Prepare qualified physicians" },
        { "id": "2", "textAr": "تطوير مهارات التشخيص والعلاج", "textEn": "Develop diagnostic skills" }
      ],
      "careerProspectsAr": ["طبيب عام", "طبيب متخصص", "باحث طبي"],
      "careerProspectsEn": ["General Physician", "Specialist Doctor", "Medical Researcher"],
      "facultyMembers": [
        {
          "id": "f1",
          "nameAr": "د. أحمد محمود الحسن",
          "nameEn": "Dr. Ahmed Mahmoud",
          "titleAr": "أستاذ دكتور",
          "titleEn": "Professor",
          "image": "https://example.com/images/faculty/f1.jpg"
        }
      ]
    }
  ]
}
```

---

## 4. أعضاء هيئة التدريس (Faculty)

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/faculty` | جلب جميع أعضاء هيئة التدريس |
| GET | `/api/faculty/:id` | تفاصيل عضو هيئة تدريس |
| GET | `/api/faculty/search?q=query` | البحث |
| GET | `/api/faculty/filter` | فلترة (college, degree, specialization) |
| GET | `/api/faculty/colleges` | قائمة الكليات للفلتر |
| GET | `/api/faculty/degrees` | قائمة الدرجات للفلتر |
| GET | `/api/faculty/specializations` | قائمة التخصصات للفلتر |
| POST | `/api/faculty` | إضافة عضو (Admin) |
| PUT | `/api/faculty/:id` | تعديل (Admin) |
| DELETE | `/api/faculty/:id` | حذف (Admin) |

### Data Structure

```typescript
interface FacultyMember {
  id: string;
  nameAr: string;
  nameEn: string;
  degreeAr: string;              // أستاذ دكتور / أستاذ مشارك / أستاذ مساعد
  degreeEn: string;              // Professor / Associate Professor / Assistant Professor
  specializationAr: string;
  specializationEn: string;
  collegeAr: string;
  collegeEn: string;
  departmentAr?: string;
  departmentEn?: string;
  email?: string;
  phone?: string;
  bioAr?: string;
  bioEn?: string;
  image?: string;
  
  // تفاصيل إضافية (للصفحة التفصيلية)
  officeHoursAr?: string;
  officeHoursEn?: string;
  researchInterestsAr?: string[];
  researchInterestsEn?: string[];
  
  publications?: {
    id: string;
    titleAr: string;
    titleEn: string;
    journal: string;
    year: string;
    link?: string;
  }[];
  
  courses?: {
    id: string;
    code: string;
    nameAr: string;
    nameEn: string;
    semester: string;
  }[];
  
  education?: {
    id: string;
    degreeAr: string;
    degreeEn: string;
    institutionAr: string;
    institutionEn: string;
    year: string;
  }[];
  
  experience?: {
    id: string;
    positionAr: string;
    positionEn: string;
    organizationAr: string;
    organizationEn: string;
    periodAr: string;
    periodEn: string;
  }[];
}
```

### Sample Data

```json
{
  "id": "1",
  "nameAr": "د. أحمد محمود الحسن",
  "nameEn": "Dr. Ahmed Mahmoud Alhasan",
  "degreeAr": "أستاذ دكتور",
  "degreeEn": "Professor",
  "specializationAr": "هندسة البرمجيات",
  "specializationEn": "Software Engineering",
  "collegeAr": "كلية الهندسة المعلوماتية",
  "collegeEn": "College of Informatics Engineering",
  "departmentAr": "قسم هندسة البرمجيات",
  "departmentEn": "Software Engineering Department",
  "email": "ahmed.hasan@ngu.edu",
  "phone": "+967 1 234567",
  "bioAr": "دكتور أحمد محمود الحسن هو أستاذ متميز في مجال هندسة البرمجيات...",
  "bioEn": "Dr. Ahmed Mahmoud Alhasan is a distinguished professor in Software Engineering...",
  "image": "https://example.com/images/faculty/ahmed.jpg",
  "officeHoursAr": "الأحد والثلاثاء 10:00 - 12:00",
  "officeHoursEn": "Sunday and Tuesday 10:00 - 12:00",
  "researchInterestsAr": ["الذكاء الاصطناعي", "هندسة البرمجيات", "تحليل البيانات"],
  "researchInterestsEn": ["Artificial Intelligence", "Software Engineering", "Data Analytics"],
  "publications": [
    {
      "id": "1",
      "titleAr": "نهج جديد لتحسين أداء نماذج التعلم العميق",
      "titleEn": "A Novel Approach for Improving Deep Learning Model Performance",
      "journal": "IEEE Transactions on Neural Networks",
      "year": "2024",
      "link": "https://doi.org/example"
    }
  ],
  "courses": [
    {
      "id": "1",
      "code": "CS401",
      "nameAr": "هندسة البرمجيات المتقدمة",
      "nameEn": "Advanced Software Engineering",
      "semester": "2024-1"
    }
  ],
  "education": [
    {
      "id": "1",
      "degreeAr": "دكتوراه في هندسة البرمجيات",
      "degreeEn": "PhD in Software Engineering",
      "institutionAr": "جامعة كامبريدج، المملكة المتحدة",
      "institutionEn": "Cambridge University, UK",
      "year": "2010"
    }
  ],
  "experience": [
    {
      "id": "1",
      "positionAr": "أستاذ دكتور",
      "positionEn": "Professor",
      "organizationAr": "جامعة الجيل الجديد",
      "organizationEn": "New Generation University",
      "periodAr": "2018 - الآن",
      "periodEn": "2018 - Present"
    }
  ]
}
```

---

## 5. الشركاء (Partners)

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/partners` | جلب جميع الشركاء |
| GET | `/api/partners/type/:type` | فلترة (local / international) |
| POST | `/api/partners` | إضافة شريك (Admin) |
| PUT | `/api/partners/:id` | تعديل (Admin) |
| DELETE | `/api/partners/:id` | حذف (Admin) |

### Data Structure

```typescript
interface PartnerItem {
  id: string;
  nameAr: string;
  nameEn: string;
  logo: string;               // URL للشعار
  type: 'local' | 'international';
  website?: string;
}
```

### Sample Data

```json
[
  {
    "id": "1",
    "nameAr": "جامعة كامبريدج",
    "nameEn": "Cambridge University",
    "logo": "https://example.com/logos/cambridge.png",
    "type": "international",
    "website": "https://www.cam.ac.uk"
  },
  {
    "id": "2",
    "nameAr": "شركة التقنيات المتقدمة",
    "nameEn": "Advanced Technologies Corp",
    "logo": "https://example.com/logos/atc.png",
    "type": "local"
  }
]
```

---

## 6. المراكز (Centers)

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/centers` | جلب جميع المراكز |
| GET | `/api/centers/:id` | تفاصيل مركز |
| POST | `/api/centers` | إضافة مركز (Admin) |
| PUT | `/api/centers/:id` | تعديل (Admin) |
| DELETE | `/api/centers/:id` | حذف (Admin) |

### Data Structure

```typescript
interface CenterItem {
  id: string;
  titleAr: string;
  titleEn: string;
  descAr: string;
  descEn: string;
  services: { ar: string; en: string }[];
  programs: { ar: string; en: string }[];
  image?: string;
  location?: string;
  phone?: string;
  email?: string;
}
```

### Sample Data

```json
{
  "id": "1",
  "titleAr": "مركز البحث العلمي",
  "titleEn": "Scientific Research Center",
  "descAr": "مركز متخصص في دعم البحث العلمي والابتكار",
  "descEn": "A specialized center for supporting scientific research and innovation",
  "services": [
    { "ar": "دعم الأبحاث", "en": "Research Support" },
    { "ar": "استشارات علمية", "en": "Scientific Consulting" }
  ],
  "programs": [
    { "ar": "برنامج الباحث الناشئ", "en": "Young Researcher Program" }
  ],
  "image": "https://example.com/images/centers/research.jpg",
  "location": "المبنى A - الطابق الثالث",
  "phone": "+967 1 234567",
  "email": "research@ngu.edu"
}
```

---

## 7. العروض (Offers)

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/offers` | جلب جميع العروض |
| GET | `/api/offers/category/:category` | فلترة حسب الفئة |
| GET | `/api/offers/search?q=query` | البحث |
| POST | `/api/offers` | إضافة عرض (Admin) |
| PUT | `/api/offers/:id` | تعديل (Admin) |
| DELETE | `/api/offers/:id` | حذف (Admin) |

### Data Structure

```typescript
interface OfferItem {
  id: string;
  titleAr: string;
  titleEn: string;
  descAr: string;
  descEn: string;
  image?: string;
  category: 'academic' | 'scholarship' | 'training' | 'other';
  validUntil?: string;        // تاريخ انتهاء العرض
}
```

### Sample Data

```json
{
  "id": "1",
  "titleAr": "منحة التفوق الأكاديمي",
  "titleEn": "Academic Excellence Scholarship",
  "descAr": "منحة كاملة للطلاب المتفوقين بنسبة 50% من الرسوم الدراسية",
  "descEn": "Full scholarship for outstanding students covering 50% of tuition fees",
  "image": "https://example.com/images/offers/scholarship.jpg",
  "category": "scholarship",
  "validUntil": "2024-09-01"
}
```

---

## 8. الأسئلة الشائعة (FAQ)

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/faq` | جلب جميع الأسئلة |
| GET | `/api/faq/category/:category` | فلترة حسب الفئة |
| POST | `/api/faq` | إضافة سؤال (Admin) |
| PUT | `/api/faq/:id` | تعديل (Admin) |
| DELETE | `/api/faq/:id` | حذف (Admin) |

### Data Structure

```typescript
interface FAQItem {
  id: string;
  questionAr: string;
  questionEn: string;
  answerAr: string;
  answerEn: string;
  category?: string;          // admission, academic, financial, general
}
```

### Sample Data

```json
{
  "id": "1",
  "questionAr": "ما هي شروط القبول في الجامعة؟",
  "questionEn": "What are the admission requirements?",
  "answerAr": "يجب أن يكون الطالب حاصلاً على شهادة الثانوية العامة بتقدير لا يقل عن 60%",
  "answerEn": "Students must have a high school certificate with a minimum grade of 60%",
  "category": "admission"
}
```

---

## 9. فريق العمل (Team)

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/team` | جلب جميع أعضاء الفريق |
| GET | `/api/team/:id` | تفاصيل عضو |
| POST | `/api/team` | إضافة عضو (Admin) |
| PUT | `/api/team/:id` | تعديل (Admin) |
| DELETE | `/api/team/:id` | حذف (Admin) |

### Data Structure

```typescript
interface TeamMember {
  id: string;
  nameAr: string;
  nameEn: string;
  positionAr: string;
  positionEn: string;
  email?: string;
  phone?: string;
  bioAr?: string;
  bioEn?: string;
  image?: string;
}
```

### Sample Data

```json
{
  "id": "1",
  "nameAr": "أ.د. محمد عبد الله الأحمد",
  "nameEn": "Prof. Mohammed Abdullah Al-Ahmad",
  "positionAr": "رئيس الجامعة",
  "positionEn": "University President",
  "email": "president@ngu.edu",
  "phone": "+967 1 234567",
  "bioAr": "رئيس جامعة الجيل الجديد، حاصل على الدكتوراه من جامعة هارفارد",
  "bioEn": "President of NGU, PhD from Harvard University",
  "image": "https://example.com/images/team/president.jpg"
}
```

---

## 10. المشاريع الطلابية (Projects)

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/projects` | جلب جميع المشاريع |
| GET | `/api/projects/current` | المشاريع الحالية |
| GET | `/api/projects/completed` | المشاريع المكتملة |
| GET | `/api/projects/:slug` | تفاصيل مشروع |
| GET | `/api/projects/search?q=query` | البحث |
| POST | `/api/projects` | إضافة مشروع (Admin) |
| PUT | `/api/projects/:id` | تعديل (Admin) |
| DELETE | `/api/projects/:id` | حذف (Admin) |

### Data Structure

```typescript
interface ProjectItem {
  id: string;
  slug: string;
  titleAr: string;
  titleEn: string;
  descAr: string;
  descEn: string;
  students: string[];           // أسماء الطلاب
  progress?: number;            // 0-100
  year?: number;
  status: 'current' | 'completed';
  images?: string[];
  detailsAr?: string;           // HTML content
  detailsEn?: string;           // HTML content
  startDate?: string;
  endDate?: string;
}
```

### Sample Data

```json
{
  "id": "1",
  "slug": "smart-parking-system",
  "titleAr": "نظام مواقف السيارات الذكي",
  "titleEn": "Smart Parking System",
  "descAr": "نظام ذكي لإدارة مواقف السيارات باستخدام IoT",
  "descEn": "Smart parking management system using IoT technology",
  "students": ["أحمد محمد", "سارة علي", "خالد حسن"],
  "progress": 75,
  "year": 2024,
  "status": "current",
  "images": [
    "https://example.com/images/projects/parking-1.jpg",
    "https://example.com/images/projects/parking-2.jpg"
  ],
  "detailsAr": "<h2>وصف المشروع</h2><p>يهدف المشروع إلى...</p>",
  "detailsEn": "<h2>Project Description</h2><p>The project aims to...</p>",
  "startDate": "2024-01-15",
  "endDate": "2024-06-30"
}
```

---

## 11. المدونة (Blog)

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/blog` | جلب جميع المقالات |
| GET | `/api/blog/:id` | تفاصيل مقال |
| GET | `/api/blog/categories` | قائمة الفئات |
| POST | `/api/blog` | إضافة مقال (Admin) |
| PUT | `/api/blog/:id` | تعديل (Admin) |
| DELETE | `/api/blog/:id` | حذف (Admin) |

### Data Structure

```typescript
interface BlogPost {
  id: string;
  title: {
    ar: string;
    en: string;
  };
  excerpt: {
    ar: string;
    en: string;
  };
  content: {
    ar: string;              // HTML content
    en: string;              // HTML content
  };
  author: {
    name: { ar: string; en: string };
    avatar: string;
    role: { ar: string; en: string };
  };
  category: { ar: string; en: string };
  image: string;
  publishedAt: string;       // ISO date
  readTime: number;          // minutes
  tags: { ar: string; en: string }[];
}
```

### Sample Data

```json
{
  "id": "1",
  "title": {
    "ar": "نصائح للنجاح في الحياة الجامعية",
    "en": "Tips for Success in University Life"
  },
  "excerpt": {
    "ar": "اكتشف أهم النصائح التي ستساعدك على التفوق في دراستك",
    "en": "Discover the top tips that will help you excel in your studies"
  },
  "content": {
    "ar": "<h2>مقدمة</h2><p>الحياة الجامعية مرحلة مهمة...</p>",
    "en": "<h2>Introduction</h2><p>University life is an important phase...</p>"
  },
  "author": {
    "name": { "ar": "د. أحمد الصالح", "en": "Dr. Ahmed Al-Saleh" },
    "avatar": "https://example.com/images/authors/ahmed.jpg",
    "role": { "ar": "أستاذ مشارك", "en": "Associate Professor" }
  },
  "category": { "ar": "نصائح أكاديمية", "en": "Academic Tips" },
  "image": "https://example.com/images/blog/tips.jpg",
  "publishedAt": "2024-01-15",
  "readTime": 5,
  "tags": [
    { "ar": "نجاح", "en": "Success" },
    { "ar": "دراسة", "en": "Study" }
  ]
}
```

---

## 12. الحياة الجامعية (Campus Life)

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/campus-life` | جلب جميع العناصر |
| GET | `/api/campus-life/category/:category` | فلترة حسب الفئة |
| POST | `/api/campus-life` | إضافة عنصر (Admin) |
| PUT | `/api/campus-life/:id` | تعديل (Admin) |
| DELETE | `/api/campus-life/:id` | حذف (Admin) |

### Data Structure

```typescript
interface CampusLifeItem {
  id: string;
  titleAr: string;
  titleEn: string;
  descriptionAr: string;
  descriptionEn: string;
  category: 'facilities' | 'activities' | 'campus';
  image?: string;
}
```

### Sample Data

```json
{
  "id": "1",
  "titleAr": "المكتبة المركزية",
  "titleEn": "Central Library",
  "descriptionAr": "مكتبة حديثة تضم أكثر من 50,000 كتاب ومرجع",
  "descriptionEn": "Modern library with over 50,000 books and references",
  "category": "facilities",
  "image": "https://example.com/images/campus/library.jpg"
}
```

---

## 13. البحث (Search)

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/search?q=query` | البحث العام في جميع المحتوى |

### Data Structure

```typescript
interface SearchResult {
  id: string;
  type: 'news' | 'project' | 'center' | 'offer' | 'event' | 'faculty';
  titleAr: string;
  titleEn: string;
  descriptionAr: string;
  descriptionEn: string;
  link: string;
  image?: string;
}
```

### Sample Response

```json
{
  "results": [
    {
      "id": "1",
      "type": "news",
      "titleAr": "اتفاقية شراكة جديدة",
      "titleEn": "New Partnership Agreement",
      "descriptionAr": "وقعت الجامعة اتفاقية شراكة...",
      "descriptionEn": "The university signed a partnership...",
      "link": "/news/new-partnership",
      "image": "https://example.com/images/news/partnership.jpg"
    }
  ],
  "total": 15
}
```

---

## 14. إدارة المستخدمين (Users & Roles)

### Endpoints - المستخدمين

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/users` | جلب جميع المستخدمين |
| GET | `/api/users/:id` | تفاصيل مستخدم |
| POST | `/api/users` | إضافة مستخدم |
| PUT | `/api/users/:id` | تعديل مستخدم |
| DELETE | `/api/users/:id` | حذف مستخدم |

### Endpoints - الأدوار

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/roles` | جلب جميع الأدوار |
| GET | `/api/roles/:id` | تفاصيل دور |
| POST | `/api/roles` | إضافة دور |
| PUT | `/api/roles/:id` | تعديل دور |
| DELETE | `/api/roles/:id` | حذف دور |

### Endpoints - الصلاحيات

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/permissions` | جلب جميع الصلاحيات |
| GET | `/api/permissions/category/:category` | فلترة حسب الفئة |

### Data Structures

```typescript
type AppRole = 'admin' | 'content_editor' | 'doctor' | 'student';

interface Permission {
  id: string;
  key: string;
  nameAr: string;
  nameEn: string;
  descriptionAr: string;
  descriptionEn: string;
  category: 'users' | 'content' | 'settings' | 'reports';
}

interface Role {
  id: string;
  key: AppRole;
  nameAr: string;
  nameEn: string;
  descriptionAr: string;
  descriptionEn: string;
  permissions: string[];         // Permission IDs
  isSystem: boolean;
  createdAt: string;
}

interface User {
  id: string;
  nameAr: string;
  nameEn: string;
  email: string;
  phone?: string;
  avatar?: string;
  roleId: string;
  status: 'active' | 'inactive' | 'suspended';
  lastLogin?: string;
  createdAt: string;
}
```

### Sample Data - Permissions

```json
[
  {
    "id": "1",
    "key": "users.view",
    "nameAr": "عرض المستخدمين",
    "nameEn": "View Users",
    "descriptionAr": "عرض قائمة المستخدمين",
    "descriptionEn": "View users list",
    "category": "users"
  },
  {
    "id": "2",
    "key": "users.create",
    "nameAr": "إضافة مستخدمين",
    "nameEn": "Create Users",
    "descriptionAr": "إضافة مستخدمين جدد",
    "descriptionEn": "Add new users",
    "category": "users"
  },
  {
    "id": "3",
    "key": "content.news",
    "nameAr": "إدارة الأخبار",
    "nameEn": "Manage News",
    "descriptionAr": "إضافة وتعديل وحذف الأخبار",
    "descriptionEn": "Add, edit and delete news",
    "category": "content"
  }
]
```

### Sample Data - Roles

```json
{
  "id": "1",
  "key": "admin",
  "nameAr": "مدير النظام",
  "nameEn": "System Admin",
  "descriptionAr": "صلاحيات كاملة للنظام",
  "descriptionEn": "Full system access",
  "permissions": ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"],
  "isSystem": true,
  "createdAt": "2024-01-01"
}
```

### Sample Data - Users

```json
{
  "id": "1",
  "nameAr": "أحمد محمد علي",
  "nameEn": "Ahmed Mohammed Ali",
  "email": "ahmed@ngu.edu",
  "phone": "+967 771 234567",
  "avatar": "https://example.com/images/users/ahmed.jpg",
  "roleId": "1",
  "status": "active",
  "lastLogin": "2024-01-20T10:30:00Z",
  "createdAt": "2024-01-01T00:00:00Z"
}
```

---

## 15. بوابة الدكتور (Doctor Portal)

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/doctor/profile` | الملف الشخصي للدكتور |
| PUT | `/api/doctor/profile` | تحديث الملف الشخصي |
| GET | `/api/doctor/courses` | المقررات التي يدرسها |
| GET | `/api/doctor/students` | طلاب الدكتور |
| GET | `/api/doctor/students?courseId=:id` | طلاب مقرر معين |
| PUT | `/api/doctor/students/:id/grades` | تحديث درجات طالب |
| GET | `/api/doctor/schedule` | الجدول الأسبوعي |
| GET | `/api/doctor/finance` | المالية والرواتب |
| GET | `/api/doctor/notifications` | الإشعارات |
| PUT | `/api/doctor/notifications/:id/read` | تعيين إشعار كمقروء |
| GET | `/api/doctor/messages` | الرسائل من الطلاب |
| PUT | `/api/doctor/messages/:id/read` | تعيين رسالة كمقروءة |
| GET | `/api/doctor/materials` | المواد التعليمية |
| GET | `/api/doctor/materials?courseId=:id` | مواد مقرر معين |
| POST | `/api/doctor/materials` | رفع مادة تعليمية |
| DELETE | `/api/doctor/materials/:id` | حذف مادة |

### Data Structures

```typescript
// الملف الشخصي
interface DoctorProfile {
  id: string;
  nameAr: string;
  nameEn: string;
  degreeAr: string;
  degreeEn: string;
  specializationAr: string;
  specializationEn: string;
  collegeAr: string;
  collegeEn: string;
  departmentAr?: string;
  departmentEn?: string;
  email: string;
  phone: string;
  officeHoursAr: string;
  officeHoursEn: string;
  bioAr?: string;
  bioEn?: string;
  image?: string;
}

// المقررات
interface TeachingCourse {
  id: string;
  code: string;
  nameAr: string;
  nameEn: string;
  creditHours: number;
  semester: string;
  studentsCount: number;
  scheduleAr: string;
  scheduleEn: string;
  classroom: string;
}

// الطلاب
interface DoctorStudent {
  id: string;
  nameAr: string;
  nameEn: string;
  academicNumber: string;
  courseId: string;
  courseCode: string;
  attendance: number;         // نسبة الحضور
  midterm?: number;           // درجة النصفي
  final?: number;             // درجة النهائي
  total?: number;             // المجموع
}

// الجدول
interface DoctorScheduleItem {
  id: string;
  dayAr: string;
  dayEn: string;
  time: string;
  courseCode: string;
  courseNameAr: string;
  courseNameEn: string;
  classroom: string;
  type: 'lecture' | 'lab' | 'office';
}

// سجل الدفع
interface PaymentRecord {
  id: string;
  monthAr: string;
  monthEn: string;
  baseSalary: number;
  allowances: number;
  deductions: number;
  netSalary: number;
  status: 'paid' | 'pending' | 'delayed';
  paidDate?: string;
}

// المالية
interface DoctorFinance {
  baseSalary: number;
  allowances: {
    housingAr: string;
    housingEn: string;
    housingAmount: number;
    transportAr: string;
    transportEn: string;
    transportAmount: number;
    otherAr: string;
    otherEn: string;
    otherAmount: number;
    total: number;
  };
  deductions: {
    taxAr: string;
    taxEn: string;
    taxAmount: number;
    insuranceAr: string;
    insuranceEn: string;
    insuranceAmount: number;
    otherAr: string;
    otherEn: string;
    otherAmount: number;
    total: number;
  };
  netSalary: number;
  paymentHistory: PaymentRecord[];
}

// الإشعارات
interface DoctorNotification {
  id: string;
  titleAr: string;
  titleEn: string;
  messageAr: string;
  messageEn: string;
  type: 'announcement' | 'reminder' | 'alert' | 'system';
  senderAr: string;
  senderEn: string;
  senderType: 'admin' | 'system';
  date: string;
  isRead: boolean;
}

// رسائل الطلاب
interface DoctorMessage {
  id: string;
  studentId: string;
  studentNameAr: string;
  studentNameEn: string;
  studentAcademicNumber: string;
  subjectAr: string;
  subjectEn: string;
  messageAr: string;
  messageEn: string;
  date: string;
  isRead: boolean;
  courseCode?: string;
}

// المواد التعليمية
interface CourseMaterial {
  id: string;
  courseId: string;
  titleAr: string;
  titleEn: string;
  descriptionAr?: string;
  descriptionEn?: string;
  type: 'lecture' | 'assignment' | 'resource' | 'video';
  fileName: string;
  fileSize: string;
  uploadDate: string;
  downloadCount: number;
}
```

### Sample Data - Profile

```json
{
  "id": "1",
  "nameAr": "د. أحمد محمود الحسن",
  "nameEn": "Dr. Ahmed Mahmoud Alhasan",
  "degreeAr": "أستاذ دكتور",
  "degreeEn": "Professor",
  "specializationAr": "هندسة البرمجيات",
  "specializationEn": "Software Engineering",
  "collegeAr": "كلية الهندسة وتقنية المعلومات",
  "collegeEn": "College of Engineering & IT",
  "departmentAr": "قسم علوم الحاسوب",
  "departmentEn": "Computer Science Department",
  "email": "ahmed.alhasan@ngu.edu.ye",
  "phone": "+967 777 123 456",
  "officeHoursAr": "الأحد والثلاثاء 10:00 - 12:00",
  "officeHoursEn": "Sunday & Tuesday 10:00 AM - 12:00 PM",
  "bioAr": "أستاذ متخصص في هندسة البرمجيات مع خبرة تزيد عن 15 عاماً",
  "bioEn": "Professor specializing in Software Engineering with over 15 years of experience",
  "image": "https://example.com/images/doctors/ahmed.jpg"
}
```

---

## 16. بوابة الطالب (Student Portal)

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/student/profile` | الملف الشخصي للطالب |
| PUT | `/api/student/profile` | تحديث الملف الشخصي |
| GET | `/api/student/courses` | المقررات المسجلة |
| GET | `/api/student/schedule` | الجدول الأسبوعي |
| GET | `/api/student/grades` | السجل الأكاديمي |
| GET | `/api/student/grades?semester=:id` | درجات فصل معين |
| GET | `/api/student/finance` | المالية والأقساط |
| GET | `/api/student/materials` | المواد التعليمية |
| GET | `/api/student/materials?courseId=:id` | مواد مقرر معين |
| GET | `/api/student/notifications` | الإشعارات |
| PUT | `/api/student/notifications/:id/read` | تعيين إشعار كمقروء |

### Data Structures

```typescript
// الملف الشخصي
interface StudentProfile {
  id: string;
  academicNumber: string;
  nameAr: string;
  nameEn: string;
  emailPersonal: string;
  emailUniversity: string;
  phone: string;
  collegeAr: string;
  collegeEn: string;
  departmentAr: string;
  departmentEn: string;
  specializationAr: string;
  specializationEn: string;
  levelAr: string;
  levelEn: string;
  status: 'active' | 'suspended' | 'graduated';
  gpa: number;
  totalCredits: number;
  completedCredits: number;
  admissionDate: string;
  expectedGraduation: string;
  advisorAr: string;
  advisorEn: string;
  image?: string;
}

// المقررات
interface StudentCourse {
  id: string;
  code: string;
  nameAr: string;
  nameEn: string;
  creditHours: number;
  doctorAr: string;
  doctorEn: string;
  classroom: string;
  scheduleAr: string;
  scheduleEn: string;
  semester: string;
  status: 'current' | 'completed' | 'upcoming';
}

// ملفات المقرر
interface CourseFile {
  id: string;
  courseId: string;
  courseCode: string;
  titleAr: string;
  titleEn: string;
  descriptionAr?: string;
  descriptionEn?: string;
  type: 'lecture' | 'assignment' | 'resource' | 'video' | 'exam';
  fileName: string;
  fileSize: string;
  uploadDate: string;
  downloadCount: number;
}

// الجدول
interface StudentScheduleItem {
  id: string;
  dayAr: string;
  dayEn: string;
  time: string;
  courseCode: string;
  courseNameAr: string;
  courseNameEn: string;
  doctorAr: string;
  doctorEn: string;
  classroom: string;
  type: 'lecture' | 'lab' | 'tutorial';
}

// الدرجات
interface StudentGrade {
  id: string;
  courseId: string;
  courseCode: string;
  courseNameAr: string;
  courseNameEn: string;
  creditHours: number;
  semester: string;
  semesterAr: string;
  semesterEn: string;
  attendance: number;
  coursework: number;
  midterm: number;
  final: number;
  total: number;
  grade: string;             // A+, A, A-, B+, etc.
  points: number;            // GPA points
  status: 'pass' | 'fail' | 'in_progress';
}

// الأقساط
interface StudentInstallment {
  id: string;
  installmentNumber: number;
  amountTotal: number;
  amountPaid: number;
  amountRemaining: number;
  dueDate: string;
  paidDate?: string;
  status: 'paid' | 'pending' | 'overdue' | 'partial';
  semester: string;
}

// المدفوعات
interface StudentPayment {
  id: string;
  receiptNumber: string;
  amount: number;
  date: string;
  method: 'cash' | 'bank_transfer' | 'card' | 'check';
  methodAr: string;
  methodEn: string;
  descriptionAr: string;
  descriptionEn: string;
  installmentId?: string;
}

// المالية الكاملة
interface StudentFinance {
  totalFees: number;
  totalPaid: number;
  totalRemaining: number;
  discountAmount: number;
  discountType?: string;
  installments: StudentInstallment[];
  payments: StudentPayment[];
}

// الإشعارات
interface StudentNotification {
  id: string;
  titleAr: string;
  titleEn: string;
  messageAr: string;
  messageEn: string;
  type: 'announcement' | 'grade' | 'payment' | 'course' | 'system';
  date: string;
  isRead: boolean;
}
```

### Sample Data - Profile

```json
{
  "id": "1",
  "academicNumber": "202401234",
  "nameAr": "محمد أحمد علي الحسني",
  "nameEn": "Mohammed Ahmed Ali Alhusni",
  "emailPersonal": "mohammed.ali@gmail.com",
  "emailUniversity": "mohammed.alhusni@ngu.edu.ye",
  "phone": "+967 771 234 567",
  "collegeAr": "كلية الهندسة وتقنية المعلومات",
  "collegeEn": "College of Engineering & IT",
  "departmentAr": "قسم علوم الحاسوب",
  "departmentEn": "Computer Science Department",
  "specializationAr": "هندسة البرمجيات",
  "specializationEn": "Software Engineering",
  "levelAr": "المستوى الثالث",
  "levelEn": "Level 3",
  "status": "active",
  "gpa": 3.85,
  "totalCredits": 136,
  "completedCredits": 78,
  "admissionDate": "2022-09-01",
  "expectedGraduation": "2026-06-30",
  "advisorAr": "د. أحمد محمود الحسن",
  "advisorEn": "Dr. Ahmed Mahmoud Alhasan",
  "image": "https://example.com/images/students/mohammed.jpg"
}
```

---

## 17. الرسائل (Messages)

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/messages/conversations` | جلب المحادثات |
| GET | `/api/messages/conversations/:id` | رسائل محادثة |
| POST | `/api/messages/send` | إرسال رسالة |
| PUT | `/api/messages/conversations/:id/read` | تعيين كمقروء |
| GET | `/api/messages/unread-count` | عدد الرسائل غير المقروءة |

### Data Structures

```typescript
interface Message {
  id: string;
  conversationId: string;
  senderId: string;
  senderType: 'student' | 'doctor';
  senderName: string;
  text: string;
  createdAt: string;
  isRead: boolean;
}

interface Conversation {
  id: string;
  studentId: string;
  studentName: string;
  studentAcademicNumber: string;
  doctorId: string;
  doctorName: string;
  doctorEmail: string;
  lastMessage: string;
  lastMessageDate: string;
  unreadCount: number;
}
```

### Sample Data

```json
{
  "id": "conv-1",
  "studentId": "student-1",
  "studentName": "محمد أحمد علي",
  "studentAcademicNumber": "202401234",
  "doctorId": "doctor-1",
  "doctorName": "د. أحمد محمود الحسن",
  "doctorEmail": "ahmed.alhasan@ngu.edu.ye",
  "lastMessage": "شكراً دكتور على الشرح",
  "lastMessageDate": "2024-01-20T14:30:00Z",
  "unreadCount": 2
}
```

---

## 📌 ملاحظات مهمة

### التوثيق (Authentication)
جميع APIs المحمية تتطلب Bearer Token في الـ Header:
```
Authorization: Bearer <token>
```

### الاستجابات
- **نجاح**: `{ "success": true, "data": {...} }`
- **خطأ**: `{ "success": false, "error": { "code": "ERROR_CODE", "message": "..." } }`

### التصفح (Pagination)
للقوائم الكبيرة:
```
GET /api/news?page=1&limit=10&sort=date&order=desc
```

Response:
```json
{
  "data": [...],
  "pagination": {
    "page": 1,
    "limit": 10,
    "total": 100,
    "totalPages": 10
  }
}
```

### الفلترة
```
GET /api/events?status=upcoming&category=academic
GET /api/faculty?college=engineering&degree=professor
```

---

## 📊 ملخص الـ APIs

| القسم | عدد الـ Endpoints | الحالة |
|-------|------------------|--------|
| الأخبار | 7 | جاهز للتكامل |
| الأحداث | 8 | جاهز للتكامل |
| الكليات | 6 | جاهز للتكامل |
| هيئة التدريس | 10 | جاهز للتكامل |
| الشركاء | 5 | جاهز للتكامل |
| المراكز | 5 | جاهز للتكامل |
| العروض | 6 | جاهز للتكامل |
| الأسئلة الشائعة | 5 | جاهز للتكامل |
| فريق العمل | 5 | جاهز للتكامل |
| المشاريع | 8 | جاهز للتكامل |
| المدونة | 5 | جاهز للتكامل |
| الحياة الجامعية | 5 | جاهز للتكامل |
| البحث | 1 | جاهز للتكامل |
| المستخدمين والأدوار | 13 | جاهز للتكامل |
| بوابة الدكتور | 16 | جاهز للتكامل |
| بوابة الطالب | 11 | جاهز للتكامل |
| الرسائل | 5 | جاهز للتكامل |

**المجموع: ~116 Endpoint**

---

> تم إنشاء هذا الملف بتاريخ: 2026-01-14
> إصدار التوثيق: 1.0
