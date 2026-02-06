# -*- coding: utf-8 -*-
from __future__ import annotations

import frappe

from .resources import (
    delete_entity,
    get_entity_by_field,
    list_entities,
    update_entity_by_field,
    upload_media,
)
from .utils import api_endpoint


@frappe.whitelist(allow_guest=True)
@api_endpoint
def list_media():
    """List media files."""
    result = list_entities("media", public=True)
    return {"data": result["data"], "meta": result["meta"], "__meta__": True}


@frappe.whitelist(allow_guest=True)
@api_endpoint
def list_media_by_folder(folder: str):
    """List media by folder."""
    frappe.form_dict["folder"] = folder
    result = list_entities("media", public=True)
    return {"data": result["data"], "meta": result["meta"], "__meta__": True}


@frappe.whitelist()
@api_endpoint
def upload_media_file():
    """Upload a media file."""
    return upload_media(), 201


@frappe.whitelist()
@api_endpoint
def delete_media(media_id: str):
    """Delete a media file."""
    return delete_entity("media", media_id, by="id")


@frappe.whitelist(allow_guest=True)
@api_endpoint
def list_settings():
    """List settings."""
    result = list_entities("settings", public=True)
    return {"data": result["data"], "meta": result["meta"], "__meta__": True}


@frappe.whitelist(allow_guest=True)
@api_endpoint
def get_setting(key: str):
    """Get a setting by key."""
    return get_entity_by_field("settings", "key", key, public=True)


@frappe.whitelist()
@api_endpoint
def update_setting(key: str, **payload):
    """Update a setting by key."""
    return update_entity_by_field("settings", "key", key, payload)
