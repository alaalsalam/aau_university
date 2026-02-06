# -*- coding: utf-8 -*-
from __future__ import annotations

import frappe

from .resources import (
    create_entity,
    delete_entity,
    get_entity,
    increment_counter,
    list_entities,
    update_entity,
)
from .utils import api_endpoint


@frappe.whitelist(allow_guest=True)
@api_endpoint
def list_news():
    """List news items."""
    result = list_entities(
        "news",
        search_fields=["title_ar", "title_en", "description_ar", "description_en"],
        public=True,
    )
    return {"data": result["data"], "meta": result["meta"], "__meta__": True}


@frappe.whitelist(allow_guest=True)
@api_endpoint
def get_news(slug: str):
    """Get a news item by slug."""
    return get_entity("news", slug, by="slug", public=True)


@frappe.whitelist(allow_guest=True)
@api_endpoint
def list_news_featured():
    """List featured news."""
    frappe.form_dict["is_featured"] = 1
    result = list_entities("news", public=True)
    return {"data": result["data"], "meta": result["meta"], "__meta__": True}


@frappe.whitelist(allow_guest=True)
@api_endpoint
def list_news_recent(limit: int = 3):
    """List recent news."""
    frappe.form_dict["limit"] = limit
    result = list_entities("news", public=True)
    return {"data": result["data"], "meta": result["meta"], "__meta__": True}


@frappe.whitelist(allow_guest=True)
@api_endpoint
def list_news_latest(limit: int = 5):
    """List latest news."""
    frappe.form_dict["limit"] = limit
    result = list_entities("news", public=True)
    return {"data": result["data"], "meta": result["meta"], "__meta__": True}


@frappe.whitelist(allow_guest=True)
@api_endpoint
def search_news(q: str):
    """Search news."""
    frappe.form_dict["q"] = q
    result = list_entities(
        "news",
        search_fields=["title_ar", "title_en", "description_ar", "description_en"],
        public=True,
    )
    return {"data": result["data"], "meta": result["meta"], "__meta__": True}


@frappe.whitelist()
@api_endpoint
def create_news(**payload):
    """Create news."""
    return create_entity("news", payload), 201


@frappe.whitelist()
@api_endpoint
def update_news(news_id: str, **payload):
    """Update news."""
    return update_entity("news", news_id, payload, by="id")


@frappe.whitelist()
@api_endpoint
def delete_news(news_id: str):
    """Delete news."""
    return delete_entity("news", news_id, by="id")


@frappe.whitelist(allow_guest=True)
@api_endpoint
def increment_news_views(news_id: str):
    """Increment news views."""
    return increment_counter("news", news_id, "views")


@frappe.whitelist(allow_guest=True)
@api_endpoint
def list_events():
    """List events."""
    result = list_entities(
        "events",
        search_fields=["title_ar", "title_en", "description_ar", "description_en"],
        public=True,
    )
    return {"data": result["data"], "meta": result["meta"], "__meta__": True}


@frappe.whitelist(allow_guest=True)
@api_endpoint
def get_event(event_id: str):
    """Get an event by id."""
    return get_entity("events", event_id, by="id", public=True)


@frappe.whitelist(allow_guest=True)
@api_endpoint
def get_event_by_slug(slug: str):
    """Get an event by slug."""
    return get_entity("events", slug, by="slug", public=True)


@frappe.whitelist(allow_guest=True)
@api_endpoint
def list_events_upcoming():
    """List upcoming events."""
    frappe.form_dict["status"] = "upcoming"
    result = list_entities("events", public=True)
    return {"data": result["data"], "meta": result["meta"], "__meta__": True}


@frappe.whitelist(allow_guest=True)
@api_endpoint
def list_events_category(category: str):
    """List events by category."""
    frappe.form_dict["category"] = category
    result = list_entities("events", public=True)
    return {"data": result["data"], "meta": result["meta"], "__meta__": True}


@frappe.whitelist()
@api_endpoint
def create_event(**payload):
    """Create event."""
    return create_entity("events", payload), 201


@frappe.whitelist()
@api_endpoint
def update_event(event_id: str, **payload):
    """Update event."""
    return update_entity("events", event_id, payload, by="id")


@frappe.whitelist()
@api_endpoint
def delete_event(event_id: str):
    """Delete event."""
    return delete_entity("events", event_id, by="id")


@frappe.whitelist(allow_guest=True)
@api_endpoint
def list_centers():
    """List centers."""
    result = list_entities("centers", public=True)
    return {"data": result["data"], "meta": result["meta"], "__meta__": True}


@frappe.whitelist(allow_guest=True)
@api_endpoint
def get_center(center_id: str):
    """Get center by id."""
    return get_entity("centers", center_id, by="id", public=True)


@frappe.whitelist()
@api_endpoint
def create_center(**payload):
    """Create center."""
    return create_entity("centers", payload), 201


@frappe.whitelist()
@api_endpoint
def update_center(center_id: str, **payload):
    """Update center."""
    return update_entity("centers", center_id, payload, by="id")


@frappe.whitelist()
@api_endpoint
def delete_center(center_id: str):
    """Delete center."""
    return delete_entity("centers", center_id, by="id")


@frappe.whitelist(allow_guest=True)
@api_endpoint
def list_partners():
    """List partners."""
    result = list_entities("partners", public=True)
    return {"data": result["data"], "meta": result["meta"], "__meta__": True}


@frappe.whitelist(allow_guest=True)
@api_endpoint
def list_partners_by_type(partner_type: str):
    """List partners by type."""
    frappe.form_dict["type"] = partner_type
    result = list_entities("partners", public=True)
    return {"data": result["data"], "meta": result["meta"], "__meta__": True}


@frappe.whitelist()
@api_endpoint
def create_partner(**payload):
    """Create partner."""
    return create_entity("partners", payload), 201


@frappe.whitelist()
@api_endpoint
def update_partner(partner_id: str, **payload):
    """Update partner."""
    return update_entity("partners", partner_id, payload, by="id")


@frappe.whitelist()
@api_endpoint
def delete_partner(partner_id: str):
    """Delete partner."""
    return delete_entity("partners", partner_id, by="id")


@frappe.whitelist(allow_guest=True)
@api_endpoint
def list_offers():
    """List offers."""
    result = list_entities("offers", public=True)
    return {"data": result["data"], "meta": result["meta"], "__meta__": True}


@frappe.whitelist(allow_guest=True)
@api_endpoint
def list_offers_active():
    """List active offers."""
    frappe.form_dict["is_active"] = 1
    result = list_entities("offers", public=True)
    return {"data": result["data"], "meta": result["meta"], "__meta__": True}


@frappe.whitelist(allow_guest=True)
@api_endpoint
def list_offers_by_category(category: str):
    """List offers by category."""
    frappe.form_dict["category"] = category
    result = list_entities("offers", public=True)
    return {"data": result["data"], "meta": result["meta"], "__meta__": True}


@frappe.whitelist(allow_guest=True)
@api_endpoint
def search_offers(q: str):
    """Search offers."""
    frappe.form_dict["q"] = q
    result = list_entities("offers", search_fields=["title_ar", "title_en", "desc_ar", "desc_en"], public=True)
    return {"data": result["data"], "meta": result["meta"], "__meta__": True}


@frappe.whitelist()
@api_endpoint
def create_offer(**payload):
    """Create offer."""
    return create_entity("offers", payload), 201


@frappe.whitelist()
@api_endpoint
def update_offer(offer_id: str, **payload):
    """Update offer."""
    return update_entity("offers", offer_id, payload, by="id")


@frappe.whitelist()
@api_endpoint
def delete_offer(offer_id: str):
    """Delete offer."""
    return delete_entity("offers", offer_id, by="id")


@frappe.whitelist(allow_guest=True)
@api_endpoint
def list_faqs():
    """List FAQs."""
    result = list_entities("faqs", public=True)
    return {"data": result["data"], "meta": result["meta"], "__meta__": True}


@frappe.whitelist(allow_guest=True)
@api_endpoint
def list_faqs_by_category(category: str):
    """List FAQs by category."""
    frappe.form_dict["category"] = category
    result = list_entities("faqs", public=True)
    return {"data": result["data"], "meta": result["meta"], "__meta__": True}


@frappe.whitelist()
@api_endpoint
def create_faq(**payload):
    """Create FAQ."""
    return create_entity("faqs", payload), 201


@frappe.whitelist()
@api_endpoint
def update_faq(faq_id: str, **payload):
    """Update FAQ."""
    return update_entity("faqs", faq_id, payload, by="id")


@frappe.whitelist()
@api_endpoint
def delete_faq(faq_id: str):
    """Delete FAQ."""
    return delete_entity("faqs", faq_id, by="id")


@frappe.whitelist(allow_guest=True)
@api_endpoint
def list_team_members():
    """List team members."""
    result = list_entities("team_members", public=True)
    return {"data": result["data"], "meta": result["meta"], "__meta__": True}


@frappe.whitelist(allow_guest=True)
@api_endpoint
def get_team_member(member_id: str):
    """Get team member by id."""
    return get_entity("team_members", member_id, by="id", public=True)


@frappe.whitelist()
@api_endpoint
def create_team_member(**payload):
    """Create team member."""
    return create_entity("team_members", payload), 201


@frappe.whitelist()
@api_endpoint
def update_team_member(member_id: str, **payload):
    """Update team member."""
    return update_entity("team_members", member_id, payload, by="id")


@frappe.whitelist()
@api_endpoint
def delete_team_member(member_id: str):
    """Delete team member."""
    return delete_entity("team_members", member_id, by="id")


@frappe.whitelist(allow_guest=True)
@api_endpoint
def list_projects():
    """List projects."""
    result = list_entities("projects", public=True)
    return {"data": result["data"], "meta": result["meta"], "__meta__": True}


@frappe.whitelist(allow_guest=True)
@api_endpoint
def get_project(slug: str):
    """Get project by slug."""
    return get_entity("projects", slug, by="slug", public=True)


@frappe.whitelist(allow_guest=True)
@api_endpoint
def list_projects_current():
    """List current projects."""
    frappe.form_dict["status"] = "current"
    result = list_entities("projects", public=True)
    return {"data": result["data"], "meta": result["meta"], "__meta__": True}


@frappe.whitelist(allow_guest=True)
@api_endpoint
def list_projects_completed():
    """List completed projects."""
    frappe.form_dict["status"] = "completed"
    result = list_entities("projects", public=True)
    return {"data": result["data"], "meta": result["meta"], "__meta__": True}


@frappe.whitelist(allow_guest=True)
@api_endpoint
def search_projects(q: str):
    """Search projects."""
    frappe.form_dict["q"] = q
    result = list_entities("projects", search_fields=["title_ar", "title_en", "desc_ar", "desc_en"], public=True)
    return {"data": result["data"], "meta": result["meta"], "__meta__": True}


@frappe.whitelist()
@api_endpoint
def create_project(**payload):
    """Create project."""
    return create_entity("projects", payload), 201


@frappe.whitelist()
@api_endpoint
def update_project(project_id: str, **payload):
    """Update project."""
    return update_entity("projects", project_id, payload, by="id")


@frappe.whitelist()
@api_endpoint
def delete_project(project_id: str):
    """Delete project."""
    return delete_entity("projects", project_id, by="id")


@frappe.whitelist(allow_guest=True)
@api_endpoint
def list_campus_life():
    """List campus life items."""
    result = list_entities("campus_life", public=True)
    return {"data": result["data"], "meta": result["meta"], "__meta__": True}


@frappe.whitelist(allow_guest=True)
@api_endpoint
def list_campus_life_by_category(category: str):
    """List campus life by category."""
    frappe.form_dict["category"] = category
    result = list_entities("campus_life", public=True)
    return {"data": result["data"], "meta": result["meta"], "__meta__": True}


@frappe.whitelist()
@api_endpoint
def create_campus_life(**payload):
    """Create campus life item."""
    return create_entity("campus_life", payload), 201


@frappe.whitelist()
@api_endpoint
def update_campus_life(item_id: str, **payload):
    """Update campus life item."""
    return update_entity("campus_life", item_id, payload, by="id")


@frappe.whitelist()
@api_endpoint
def delete_campus_life(item_id: str):
    """Delete campus life item."""
    return delete_entity("campus_life", item_id, by="id")


@frappe.whitelist(allow_guest=True)
@api_endpoint
def list_blog_posts():
    """List blog posts."""
    result = list_entities("blog_posts", public=True)
    return {"data": result["data"], "meta": result["meta"], "__meta__": True}


@frappe.whitelist(allow_guest=True)
@api_endpoint
def get_blog_post(blog_id: str):
    """Get blog post by id."""
    return get_entity("blog_posts", blog_id, by="id", public=True)


@frappe.whitelist(allow_guest=True)
@api_endpoint
def get_blog_post_by_slug(slug: str):
    """Get blog post by slug."""
    return get_entity("blog_posts", slug, by="slug", public=True)


@frappe.whitelist(allow_guest=True)
@api_endpoint
def list_blog_categories():
    """List blog categories."""
    rows = frappe.get_all(
        "Blog Posts",
        fields=["category"],
        distinct=True,
        ignore_permissions=True,
    )
    return [row["category"] for row in rows if row.get("category")]


@frappe.whitelist(allow_guest=True)
@api_endpoint
def list_blog_by_category(category: str):
    """List blog posts by category."""
    frappe.form_dict["category"] = category
    result = list_entities("blog_posts", public=True)
    return {"data": result["data"], "meta": result["meta"], "__meta__": True}


@frappe.whitelist()
@api_endpoint
def create_blog_post(**payload):
    """Create blog post."""
    return create_entity("blog_posts", payload), 201


@frappe.whitelist()
@api_endpoint
def update_blog_post(post_id: str, **payload):
    """Update blog post."""
    return update_entity("blog_posts", post_id, payload, by="id")


@frappe.whitelist()
@api_endpoint
def delete_blog_post(post_id: str):
    """Delete blog post."""
    return delete_entity("blog_posts", post_id, by="id")


@frappe.whitelist(allow_guest=True)
@api_endpoint
def increment_blog_views(post_id: str):
    """Increment blog post views."""
    return increment_counter("blog_posts", post_id, "views")


@frappe.whitelist(allow_guest=True)
@api_endpoint
def get_page(slug: str):
    """Get a page by slug."""
    return get_entity("pages", slug, by="slug", public=True)


@frappe.whitelist()
@api_endpoint
def update_page(slug: str, **payload):
    """Update a page by slug."""
    return update_entity("pages", slug, payload, by="slug")
