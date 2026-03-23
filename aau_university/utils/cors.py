# -*- coding: utf-8 -*-
from __future__ import annotations


ALLOWED_ORIGINS = {
    "https://auusite.yemenfrappe.com",
    "http://auusite.yemenfrappe.com",
    "https://edu.yemenfrappe.com",
    "http://edu.yemenfrappe.com",
}


def apply_cors_headers(response=None, request=None):
    """Attach CORS headers for AAU frontend domains."""
    if not response or not request:
        return response

    origin = (request.headers.get("Origin") or "").strip()
    if origin and origin in ALLOWED_ORIGINS:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, PATCH, DELETE, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = (
            "Content-Type, Authorization, X-Frappe-CSRF-Token, X-Requested-With, Accept"
        )
        response.headers["Access-Control-Expose-Headers"] = "Content-Type, Set-Cookie"
        response.headers["Vary"] = "Origin"

    return response

