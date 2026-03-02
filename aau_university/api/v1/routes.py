# -*- coding: utf-8 -*-
from __future__ import annotations

from werkzeug.routing import Map, Rule, Submount

import frappe
from frappe.api import ApiVersion
from frappe.api.v1 import url_rules as v1_rules
from frappe.api.v2 import url_rules as v2_rules

from . import access, academic, cms, content, portal, public

_ROUTES_ADDED = False


def ensure_routes():
    """Register AAU API routes on the Frappe API router."""
    global _ROUTES_ADDED
    if _ROUTES_ADDED:
        return

    extra_rules = [
        # News
        Rule("/news", methods=["GET"], endpoint=content.list_news),
        Rule("/news", methods=["POST"], endpoint=content.create_news),
        Rule("/news/featured", methods=["GET"], endpoint=content.list_news_featured),
        Rule("/news/latest", methods=["GET"], endpoint=content.list_news_latest),
        Rule("/news/recent", methods=["GET"], endpoint=content.list_news_recent),
        Rule("/news/search", methods=["GET"], endpoint=content.search_news),
        Rule("/news/<path:slug>", methods=["GET"], endpoint=content.get_news),
        Rule("/news/<path:news_id>", methods=["PUT"], endpoint=content.update_news),
        Rule("/news/<path:news_id>", methods=["DELETE"], endpoint=content.delete_news),
        Rule("/news/<path:news_id>/views", methods=["POST"], endpoint=content.increment_news_views),
        # Events
        Rule("/events", methods=["GET"], endpoint=content.list_events),
        Rule("/events", methods=["POST"], endpoint=content.create_event),
        Rule("/events/upcoming", methods=["GET"], endpoint=content.list_events_upcoming),
        Rule("/events/category/<path:category>", methods=["GET"], endpoint=content.list_events_category),
        Rule("/events/slug/<path:slug>", methods=["GET"], endpoint=content.get_event_by_slug),
        Rule("/events/<path:event_id>", methods=["GET"], endpoint=content.get_event),
        Rule("/events/<path:event_id>", methods=["PUT"], endpoint=content.update_event),
        Rule("/events/<path:event_id>", methods=["DELETE"], endpoint=content.delete_event),
        # Colleges & Programs
        Rule("/colleges", methods=["GET"], endpoint=academic.list_colleges),
        Rule("/colleges", methods=["POST"], endpoint=academic.create_college),
        Rule("/colleges/<path:slug>", methods=["GET"], endpoint=academic.get_college),
        Rule("/colleges/<path:college_id>", methods=["PUT"], endpoint=academic.update_college),
        Rule("/colleges/<path:college_id>", methods=["DELETE"], endpoint=academic.delete_college),
        Rule("/colleges/<path:college_id>/programs", methods=["GET"], endpoint=academic.list_college_programs),
        Rule("/colleges/<path:college_id>/dean", methods=["GET"], endpoint=academic.get_college_dean),
        Rule("/college-deans/<path:dean_id>", methods=["PUT"], endpoint=academic.update_college_dean),
        Rule("/programs", methods=["GET"], endpoint=academic.list_programs),
        Rule("/programs", methods=["POST"], endpoint=academic.create_program),
        Rule("/programs/<path:program_id>", methods=["GET"], endpoint=academic.get_program),
        Rule("/programs/<path:program_id>", methods=["PUT"], endpoint=academic.update_program),
        Rule("/programs/<path:program_id>", methods=["DELETE"], endpoint=academic.delete_program),
        Rule("/programs/<path:program_id>/objectives", methods=["GET"], endpoint=academic.list_program_objectives),
        Rule("/program-objectives", methods=["POST"], endpoint=academic.create_program_objective),
        Rule("/program-objectives/<path:objective_id>", methods=["PUT"], endpoint=academic.update_program_objective),
        Rule("/program-objectives/<path:objective_id>", methods=["DELETE"], endpoint=academic.delete_program_objective),
        Rule("/programs/<path:program_id>/faculty", methods=["GET"], endpoint=academic.list_program_faculty),
        Rule("/program-faculty", methods=["POST"], endpoint=academic.create_program_faculty),
        Rule("/program-faculty/<path:program_faculty_id>", methods=["PUT"], endpoint=academic.update_program_faculty),
        Rule("/program-faculty/<path:program_faculty_id>", methods=["DELETE"], endpoint=academic.delete_program_faculty),
        # Faculty
        Rule("/faculty", methods=["GET"], endpoint=academic.list_faculty),
        Rule("/faculty", methods=["POST"], endpoint=academic.create_faculty),
        Rule("/faculty/search", methods=["GET"], endpoint=academic.search_faculty),
        Rule("/faculty/filter", methods=["GET"], endpoint=academic.filter_faculty),
        Rule("/faculty/colleges", methods=["GET"], endpoint=academic.list_faculty_colleges),
        Rule("/faculty/degrees", methods=["GET"], endpoint=academic.list_faculty_degrees),
        Rule("/faculty/specializations", methods=["GET"], endpoint=academic.list_faculty_specializations),
        Rule("/faculty/<path:member_id>", methods=["GET"], endpoint=academic.get_faculty),
        Rule("/faculty/<path:member_id>", methods=["PUT"], endpoint=academic.update_faculty),
        Rule("/faculty/<path:member_id>", methods=["DELETE"], endpoint=academic.delete_faculty),
        # Centers & Partners
        Rule("/centers", methods=["GET"], endpoint=content.list_centers),
        Rule("/centers", methods=["POST"], endpoint=content.create_center),
        Rule("/centers/<path:center_id>", methods=["GET"], endpoint=content.get_center),
        Rule("/centers/<path:center_id>", methods=["PUT"], endpoint=content.update_center),
        Rule("/centers/<path:center_id>", methods=["DELETE"], endpoint=content.delete_center),
        Rule("/partners", methods=["GET"], endpoint=content.list_partners),
        Rule("/partners", methods=["POST"], endpoint=content.create_partner),
        Rule("/partners/type/<path:partner_type>", methods=["GET"], endpoint=content.list_partners_by_type),
        Rule("/partners/<path:partner_id>", methods=["PUT"], endpoint=content.update_partner),
        Rule("/partners/<path:partner_id>", methods=["DELETE"], endpoint=content.delete_partner),
        # Offers
        Rule("/offers", methods=["GET"], endpoint=content.list_offers),
        Rule("/offers", methods=["POST"], endpoint=content.create_offer),
        Rule("/offers/active", methods=["GET"], endpoint=content.list_offers_active),
        Rule("/offers/category/<path:category>", methods=["GET"], endpoint=content.list_offers_by_category),
        Rule("/offers/search", methods=["GET"], endpoint=content.search_offers),
        Rule("/offers/<path:offer_id>", methods=["PUT"], endpoint=content.update_offer),
        Rule("/offers/<path:offer_id>", methods=["DELETE"], endpoint=content.delete_offer),
        # FAQs
        Rule("/faq", methods=["GET"], endpoint=content.list_faqs),
        Rule("/faq", methods=["POST"], endpoint=content.create_faq),
        Rule("/faq/category/<path:category>", methods=["GET"], endpoint=content.list_faqs_by_category),
        Rule("/faq/<path:faq_id>", methods=["PUT"], endpoint=content.update_faq),
        Rule("/faq/<path:faq_id>", methods=["DELETE"], endpoint=content.delete_faq),
        Rule("/faqs", methods=["GET"], endpoint=content.list_faqs),
        Rule("/faqs", methods=["POST"], endpoint=content.create_faq),
        Rule("/faqs/category/<path:category>", methods=["GET"], endpoint=content.list_faqs_by_category),
        Rule("/faqs/<path:faq_id>", methods=["PUT"], endpoint=content.update_faq),
        Rule("/faqs/<path:faq_id>", methods=["DELETE"], endpoint=content.delete_faq),
        # Team
        Rule("/team", methods=["GET"], endpoint=content.list_team_members),
        Rule("/team", methods=["POST"], endpoint=content.create_team_member),
        Rule("/team/<path:member_id>", methods=["GET"], endpoint=content.get_team_member),
        Rule("/team/<path:member_id>", methods=["PUT"], endpoint=content.update_team_member),
        Rule("/team/<path:member_id>", methods=["DELETE"], endpoint=content.delete_team_member),
        # Projects
        Rule("/projects", methods=["GET"], endpoint=content.list_projects),
        Rule("/projects", methods=["POST"], endpoint=content.create_project),
        Rule("/projects/current", methods=["GET"], endpoint=content.list_projects_current),
        Rule("/projects/completed", methods=["GET"], endpoint=content.list_projects_completed),
        Rule("/projects/search", methods=["GET"], endpoint=content.search_projects),
        Rule("/projects/<path:slug>", methods=["GET"], endpoint=content.get_project),
        Rule("/projects/<path:project_id>", methods=["PUT"], endpoint=content.update_project),
        Rule("/projects/<path:project_id>", methods=["DELETE"], endpoint=content.delete_project),
        # Campus life
        Rule("/campus-life", methods=["GET"], endpoint=content.list_campus_life),
        Rule("/campus-life", methods=["POST"], endpoint=content.create_campus_life),
        Rule("/campus-life/category/<path:category>", methods=["GET"], endpoint=content.list_campus_life_by_category),
        Rule("/campus-life/<path:item_id>", methods=["PUT"], endpoint=content.update_campus_life),
        Rule("/campus-life/<path:item_id>", methods=["DELETE"], endpoint=content.delete_campus_life),
        # Blog
        Rule("/blog", methods=["GET"], endpoint=content.list_blog_posts),
        Rule("/blog", methods=["POST"], endpoint=content.create_blog_post),
        Rule("/blog/categories", methods=["GET"], endpoint=content.list_blog_categories),
        Rule("/blog/category/<path:category>", methods=["GET"], endpoint=content.list_blog_by_category),
        Rule("/blog/<path:blog_id>", methods=["GET"], endpoint=content.get_blog_post),
        Rule("/blog/<path:blog_id>", methods=["PUT"], endpoint=content.update_blog_post),
        Rule("/blog/<path:blog_id>", methods=["DELETE"], endpoint=content.delete_blog_post),
        Rule("/blog/slug/<path:slug>", methods=["GET"], endpoint=content.get_blog_post_by_slug),
        Rule("/blog/<path:post_id>/views", methods=["POST"], endpoint=content.increment_blog_views),
        # Pages
        Rule("/pages/<path:slug>", methods=["GET"], endpoint=content.get_page),
        Rule("/pages/<path:slug>", methods=["PUT"], endpoint=content.update_page),
        # Media
        Rule("/media", methods=["GET"], endpoint=cms.list_media),
        Rule("/media/folder/<path:folder>", methods=["GET"], endpoint=cms.list_media_by_folder),
        Rule("/media/upload", methods=["POST"], endpoint=cms.upload_media_file),
        Rule("/media/<path:media_id>", methods=["DELETE"], endpoint=cms.delete_media),
        # Settings
        Rule("/settings", methods=["GET"], endpoint=cms.list_settings),
        Rule("/settings/<path:key>", methods=["GET"], endpoint=cms.get_setting),
        Rule("/settings/<path:key>", methods=["PUT"], endpoint=cms.update_setting),
        # Contact messages
        Rule("/contact-messages", methods=["GET"], endpoint=public.list_contact_messages),
        Rule("/contact-messages", methods=["POST"], endpoint=public.create_contact_message),
        Rule("/contact-messages/<path:message_id>", methods=["GET"], endpoint=public.get_contact_message),
        Rule("/contact-messages/<path:message_id>", methods=["DELETE"], endpoint=public.delete_contact_message),
        Rule("/contact-messages/<path:message_id>/status", methods=["PUT"], endpoint=public.update_contact_message_status),
        # Join requests
        Rule("/join-requests", methods=["GET"], endpoint=public.list_join_requests),
        Rule("/join-requests", methods=["POST"], endpoint=public.create_join_request),
        Rule("/join-requests/<path:request_id>", methods=["GET"], endpoint=public.get_join_request),
        Rule("/join-requests/<path:request_id>", methods=["DELETE"], endpoint=public.delete_join_request),
        Rule("/join-requests/<path:request_id>/status", methods=["PUT"], endpoint=public.update_join_request_status),
        # Search
        Rule("/search", methods=["GET"], endpoint=public.search),
        Rule("/aau/home", methods=["GET"], endpoint=public.get_home),
        Rule("/aau/news", methods=["GET"], endpoint=public.list_public_news),
        Rule("/aau/news/<path:slug>", methods=["GET"], endpoint=public.get_public_news),
        Rule("/aau/events", methods=["GET"], endpoint=public.list_public_events),
        Rule("/aau/events/<path:slug>", methods=["GET"], endpoint=public.get_public_event),
        Rule("/aau/colleges", methods=["GET"], endpoint=public.list_public_colleges),
        Rule("/aau/colleges/<path:slug>", methods=["GET"], endpoint=public.get_public_college),
        Rule("/aau/page/<path:slug>", methods=["GET"], endpoint=public.get_public_page),
        Rule("/aau/menu/<path:key>", methods=["GET"], endpoint=public.get_public_menu),
        Rule("/aau/profile", methods=["GET"], endpoint=public.get_site_profile),
        Rule("/aau/profile", methods=["PUT"], endpoint=public.update_site_profile),
        Rule("/access/me", methods=["GET"], endpoint=access.get_current_access),
        # Users & roles
        Rule("/users", methods=["GET"], endpoint=access.list_users),
        Rule("/users", methods=["POST"], endpoint=access.create_user),
        Rule("/users/<path:user_id>", methods=["GET"], endpoint=access.get_user),
        Rule("/users/<path:user_id>", methods=["PUT"], endpoint=access.update_user),
        Rule("/users/<path:user_id>", methods=["DELETE"], endpoint=access.delete_user),
        Rule("/roles", methods=["GET"], endpoint=access.list_roles),
        Rule("/roles", methods=["POST"], endpoint=access.create_role),
        Rule("/roles/<path:role_id>", methods=["GET"], endpoint=access.get_role),
        Rule("/roles/<path:role_id>", methods=["PUT"], endpoint=access.update_role),
        Rule("/roles/<path:role_id>", methods=["DELETE"], endpoint=access.delete_role),
        Rule("/permissions", methods=["GET"], endpoint=access.list_permissions),
        Rule("/permissions/category/<path:category>", methods=["GET"], endpoint=access.list_permissions),
        # Account links
        Rule("/account-links/summary", methods=["GET"], endpoint=access.get_account_link_summary),
        Rule("/account-links/users", methods=["GET"], endpoint=access.list_linkable_users),
        Rule("/account-links/doctors", methods=["GET"], endpoint=access.list_doctor_links),
        Rule("/account-links/doctors/<path:instructor_id>", methods=["PUT"], endpoint=access.link_doctor_account),
        Rule("/account-links/doctors/<path:instructor_id>", methods=["DELETE"], endpoint=access.unlink_doctor_account),
        Rule("/account-links/students", methods=["GET"], endpoint=access.list_student_links),
        Rule("/account-links/students/<path:student_id>", methods=["PUT"], endpoint=access.link_student_account),
        Rule("/account-links/students/<path:student_id>", methods=["DELETE"], endpoint=access.unlink_student_account),
        # Doctor portal
        Rule("/doctor/profile", methods=["GET"], endpoint=portal.get_doctor_profile),
        Rule("/doctor/profile", methods=["PUT"], endpoint=portal.update_doctor_profile),
        Rule("/doctor/courses", methods=["GET"], endpoint=portal.list_doctor_courses),
        Rule("/doctor/students", methods=["GET"], endpoint=portal.list_doctor_students),
        Rule("/doctor/students/<path:student_id>/grades", methods=["PUT"], endpoint=portal.update_doctor_student_grades),
        Rule("/doctor/schedule", methods=["GET"], endpoint=portal.list_doctor_schedule),
        Rule("/doctor/finance", methods=["GET"], endpoint=portal.get_doctor_finance),
        Rule("/doctor/notifications", methods=["GET"], endpoint=portal.list_doctor_notifications),
        Rule("/doctor/notifications/<path:notification_id>/read", methods=["PUT"], endpoint=portal.mark_doctor_notification_read),
        Rule("/doctor/messages", methods=["GET"], endpoint=portal.list_doctor_messages),
        Rule("/doctor/messages/<path:message_id>/read", methods=["PUT"], endpoint=portal.mark_doctor_message_read),
        Rule("/doctor/materials", methods=["GET"], endpoint=portal.list_doctor_materials),
        Rule("/doctor/materials", methods=["POST"], endpoint=portal.upload_doctor_material),
        Rule("/doctor/materials/<path:material_id>", methods=["DELETE"], endpoint=portal.delete_doctor_material),
        # Student portal
        Rule("/student/profile", methods=["GET"], endpoint=portal.get_student_profile),
        Rule("/student/profile", methods=["PUT"], endpoint=portal.update_student_profile),
        Rule("/student/courses", methods=["GET"], endpoint=portal.list_student_courses),
        Rule("/student/schedule", methods=["GET"], endpoint=portal.list_student_schedule),
        Rule("/student/grades", methods=["GET"], endpoint=portal.list_student_grades),
        Rule("/student/finance", methods=["GET"], endpoint=portal.get_student_finance),
        Rule("/student/materials", methods=["GET"], endpoint=portal.list_student_materials),
        Rule("/student/notifications", methods=["GET"], endpoint=portal.list_student_notifications),
        Rule("/student/notifications/<path:notification_id>/read", methods=["PUT"], endpoint=portal.mark_student_notification_read),
        # Messages
        Rule("/messages/conversations", methods=["GET"], endpoint=portal.list_conversations),
        Rule("/messages/conversations/<path:conversation_id>", methods=["GET"], endpoint=portal.get_conversation),
        Rule("/messages/send", methods=["POST"], endpoint=portal.send_message),
        Rule("/messages/conversations/<path:conversation_id>/read", methods=["PUT"], endpoint=portal.mark_conversation_read),
        Rule("/messages/unread-count", methods=["GET"], endpoint=portal.unread_message_count),
    ]

    v1_rules.extend(extra_rules)

    frappe.api.API_URL_MAP = Map(
        [
            Submount("/api", v1_rules),
            Submount(f"/api/{ApiVersion.V1.value}", v1_rules),
            Submount(f"/api/{ApiVersion.V2.value}", v2_rules),
        ],
        strict_slashes=False,
        merge_slashes=False,
    )
    _ROUTES_ADDED = True
