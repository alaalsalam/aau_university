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
    "centers": {"doctype": "Centers", "id_field": "id"},
    "center_services": {"doctype": "Center Services", "id_field": "id"},
    "center_programs": {"doctype": "Center Programs", "id_field": "id"},
    "partners": {"doctype": "Partners", "id_field": "id"},
    "offers": {"doctype": "Offers", "id_field": "id"},
    "faqs": {"doctype": "FAQs", "id_field": "id"},
    "team_members": {"doctype": "Team Members", "id_field": "id"},
    "projects": {"doctype": "Projects", "id_field": "id", "slug_field": "slug"},
    "campus_life": {"doctype": "Campus Life", "id_field": "id"},
    "blog_posts": {"doctype": "Blog Posts", "id_field": "id", "slug_field": "slug"},
    "pages": {"doctype": "Pages", "id_field": "id", "slug_field": "slug"},
    "media": {"doctype": "Media Library", "id_field": "id"},
    "settings": {"doctype": "Website Settings", "id_field": "id"},
    "contact_messages": {"doctype": "Contact Messages", "id_field": "id"},
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
