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

SETTINGS_KEY_MAP = {
    "siteName": "siteName",
    "site_name": "siteName",
    "siteNameAr": "siteNameAr",
    "site_name_ar": "siteNameAr",
    "siteDescriptionAr": "siteDescriptionAr",
    "site_description_ar": "siteDescriptionAr",
    "siteDescriptionEn": "siteDescriptionEn",
    "site_description_en": "siteDescriptionEn",
    "contactPhone": "contactPhone",
    "contact_phone": "contactPhone",
    "contactEmail": "contactEmail",
    "contact_email": "contactEmail",
    "addressAr": "addressAr",
    "address_ar": "addressAr",
    "addressEn": "addressEn",
    "address_en": "addressEn",
    "mapLocation": "mapLocation",
    "map_location": "mapLocation",
    "facebook": "facebook",
    "twitter": "twitter",
    "instagram": "instagram",
    "linkedin": "linkedin",
    "youtube": "youtube",
    "footerBackgroundType": "footerBackgroundType",
    "footer_background_type": "footerBackgroundType",
    "footerBackgroundImage": "footerBackgroundImage",
    "footer_background_image": "footerBackgroundImage",
    "footerBackgroundVideo": "footerBackgroundVideo",
    "footer_background_video": "footerBackgroundVideo",
    "footerBackgroundOverlayOpacity": "footerBackgroundOverlayOpacity",
    "footer_background_overlay_opacity": "footerBackgroundOverlayOpacity",
}


def _site_profile_payload() -> dict:
    from .public import _build_site_profile_payload

    return _build_site_profile_payload()


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
    """Return the stable site profile settings payload."""
    return _site_profile_payload()


@frappe.whitelist(allow_guest=True)
@api_endpoint
def get_setting(key: str):
    """Get a single setting value by key from the site profile payload."""
    profile = _site_profile_payload()
    profile_key = SETTINGS_KEY_MAP.get(key)
    if not profile_key:
        raise frappe.DoesNotExistError(f"Unknown setting key: {key}")
    return {"key": key, "value": profile.get(profile_key)}


@frappe.whitelist()
@api_endpoint
def update_setting(key: str, **payload):
    """Update a single site profile setting value by key."""
    from .public import update_site_profile

    profile_key = SETTINGS_KEY_MAP.get(key)
    if not profile_key:
        raise frappe.DoesNotExistError(f"Unknown setting key: {key}")

    value = payload.get("value")
    if value is None and profile_key in payload:
        value = payload.get(profile_key)

    if value is None:
        return get_setting(key)

    return update_site_profile.__wrapped__(**{profile_key: value})
