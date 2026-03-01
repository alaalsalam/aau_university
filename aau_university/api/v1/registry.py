# -*- coding: utf-8 -*-
from __future__ import annotations


ENTITY_CONFIG = {
    "colleges": {"doctype": "Colleges", "id_field": "id", "slug_field": "slug"},
    "college_deans": {"doctype": "College Deans", "id_field": "id"},
    "academic_programs": {"doctype": "Academic Programs", "id_field": "id"},
    "program_objectives": {"doctype": "Program Objectives", "id_field": "id"},
    "study_plans": {"doctype": "Study Plans", "id_field": "id"},
    "study_plan_courses": {"doctype": "Study Plan Courses", "id_field": "id"},
    "faculty_members": {"doctype": "Faculty Members", "id_field": "id"},
    "program_faculty": {"doctype": "Program Faculty", "id_field": "id"},
    "news": {"doctype": "News", "id_field": "id", "slug_field": "slug"},
    "events": {"doctype": "Events", "id_field": "id", "slug_field": "slug"},
    "centers": {"doctype": "Centers", "doctype_candidates": ["Centers", "University Centers"], "id_field": "id"},
    "center_services": {"doctype": "Center Services", "id_field": "id"},
    "center_programs": {"doctype": "Center Programs", "id_field": "id"},
    "partners": {"doctype": "Partners", "id_field": "id"},
    "offers": {"doctype": "Offers", "id_field": "id"},
    "faqs": {"doctype": "FAQ", "doctype_candidates": ["FAQ", "FAQs"], "id_field": "id"},
    "team_members": {"doctype": "Team Members", "id_field": "id"},
    "projects": {"doctype": "Projects", "id_field": "id", "slug_field": "slug"},
    "campus_life": {"doctype": "Campus Life", "id_field": "id"},
    "blog_posts": {"doctype": "Blog Posts", "id_field": "id", "slug_field": "slug"},
    "pages": {"doctype": "Pages", "doctype_candidates": ["Pages", "AAU Page", "Static Page"], "id_field": "id", "slug_field": "slug"},
    "media": {"doctype": "Media Library", "id_field": "id"},
    "settings": {"doctype": "Website Settings", "id_field": "id"},
    "contact_messages": {
        "doctype": "Contact Us Messages",
        "doctype_candidates": ["Contact Us Messages", "Contact Messages"],
        "id_field": "id",
    },
    "join_requests": {"doctype": "Join Requests", "id_field": "id"},
}


SEARCH_TYPES = {
    "news": "News",
    "events": "Events",
    "projects": "Projects",
    "centers": "Centers",
    "offers": "Offers",
    "colleges": "Colleges",
    "programs": "Academic Programs",
    "faculty": "Faculty Members",
    "blog": "Blog Posts",
}


ADMIN_ROLES = {"System Manager", "Administrator", "AAU Admin", "AAU Content Manager"}

SUPER_ADMIN_ROLES = {"System Manager", "Administrator", "AAU Admin", "AUU Admin"}
CONTENT_MANAGER_ROLES = {"AAU Content Manager", "Website Manager", "Blogger"}
ACADEMIC_MANAGER_ROLES = {"AAU Academic Manager", "Education Manager", "Academics User", "Instructor"}
SERVICE_MANAGER_ROLES = {"AAU Service Manager", "Support Team"}

ENTITY_ROLE_PERMISSIONS = {
    "colleges": {"read": ACADEMIC_MANAGER_ROLES, "write": ACADEMIC_MANAGER_ROLES},
    "college_deans": {"read": ACADEMIC_MANAGER_ROLES, "write": ACADEMIC_MANAGER_ROLES},
    "academic_programs": {"read": ACADEMIC_MANAGER_ROLES, "write": ACADEMIC_MANAGER_ROLES},
    "program_objectives": {"read": ACADEMIC_MANAGER_ROLES, "write": ACADEMIC_MANAGER_ROLES},
    "study_plans": {"read": ACADEMIC_MANAGER_ROLES, "write": ACADEMIC_MANAGER_ROLES},
    "study_plan_courses": {"read": ACADEMIC_MANAGER_ROLES, "write": ACADEMIC_MANAGER_ROLES},
    "faculty_members": {"read": ACADEMIC_MANAGER_ROLES, "write": ACADEMIC_MANAGER_ROLES},
    "program_faculty": {"read": ACADEMIC_MANAGER_ROLES, "write": ACADEMIC_MANAGER_ROLES},
    "news": {"read": CONTENT_MANAGER_ROLES, "write": CONTENT_MANAGER_ROLES},
    "events": {"read": CONTENT_MANAGER_ROLES, "write": CONTENT_MANAGER_ROLES},
    "centers": {"read": CONTENT_MANAGER_ROLES, "write": CONTENT_MANAGER_ROLES},
    "center_services": {"read": CONTENT_MANAGER_ROLES, "write": CONTENT_MANAGER_ROLES},
    "center_programs": {"read": CONTENT_MANAGER_ROLES, "write": CONTENT_MANAGER_ROLES},
    "partners": {"read": CONTENT_MANAGER_ROLES, "write": CONTENT_MANAGER_ROLES},
    "offers": {"read": CONTENT_MANAGER_ROLES, "write": CONTENT_MANAGER_ROLES},
    "faqs": {"read": CONTENT_MANAGER_ROLES, "write": CONTENT_MANAGER_ROLES},
    "team_members": {"read": CONTENT_MANAGER_ROLES, "write": CONTENT_MANAGER_ROLES},
    "projects": {"read": CONTENT_MANAGER_ROLES, "write": CONTENT_MANAGER_ROLES},
    "campus_life": {"read": CONTENT_MANAGER_ROLES, "write": CONTENT_MANAGER_ROLES},
    "blog_posts": {"read": CONTENT_MANAGER_ROLES, "write": CONTENT_MANAGER_ROLES},
    "pages": {"read": CONTENT_MANAGER_ROLES, "write": CONTENT_MANAGER_ROLES},
    "media": {"read": CONTENT_MANAGER_ROLES, "write": CONTENT_MANAGER_ROLES},
    "settings": {"read": CONTENT_MANAGER_ROLES, "write": CONTENT_MANAGER_ROLES},
    "contact_messages": {"read": SERVICE_MANAGER_ROLES, "write": SERVICE_MANAGER_ROLES},
    "join_requests": {"read": SERVICE_MANAGER_ROLES, "write": SERVICE_MANAGER_ROLES},
}
