# Copyright (c) 2026, alaalsalam and contributors
# For license information, please see license.txt

import re

import frappe
from frappe.model.document import Document
from frappe.permissions import get_user_permissions


def _contains_arabic(value: str | None) -> bool:
    text = (value or "").strip()
    return bool(re.search(r"[\u0600-\u06FF]", text))


class Colleges(Document):
    def validate(self):
        self._sync_name_fields()
        self._sync_description_fields()
        self._ensure_public_background_image()

    def _sync_name_fields(self):
        name_changed = self.has_value_changed("college_name")
        name_ar_changed = self.has_value_changed("name_ar")
        name_en_changed = self.has_value_changed("name_en")
        college_name = (self.college_name or "").strip()

        if name_changed and not name_ar_changed and _contains_arabic(college_name):
            self.name_ar = college_name
        if name_changed and not name_en_changed and not _contains_arabic(college_name):
            self.name_en = college_name
        if name_ar_changed and not name_changed and (self.name_ar or "").strip():
            self.college_name = self.name_ar.strip()
        elif name_en_changed and not name_changed and (self.name_en or "").strip():
            self.college_name = self.name_en.strip()

    def _sync_description_fields(self):
        description_changed = self.has_value_changed("description")
        description_ar_changed = self.has_value_changed("description_ar")
        description_en_changed = self.has_value_changed("description_en")
        description = (self.description or "").strip()

        # If editor updates the general description with Arabic text, keep Arabic website field in sync.
        if description_changed and not description_ar_changed and _contains_arabic(description):
            self.description_ar = description
        # If editor updates the general description with non-Arabic text, keep English field in sync.
        if description_changed and not description_en_changed and description and not _contains_arabic(description):
            self.description_en = description

        if description_ar_changed and not description_changed and (self.description_ar or "").strip():
            self.description = self.description_ar.strip()
        elif description_en_changed and not description_changed and (self.description_en or "").strip():
            self.description = self.description_en.strip()

    def _ensure_public_background_image(self):
        """Ensure college hero background is web-accessible on public pages."""
        image_url = (self.background_image or "").strip()
        if not image_url or not image_url.startswith("/private/files/"):
            return

        file_name = frappe.db.get_value("File", {"file_url": image_url}, "name")
        if not file_name:
            return

        file_doc = frappe.get_doc("File", file_name)
        file_doc.is_private = 0
        file_doc.file_url = image_url.replace("/private/files/", "/files/", 1)
        file_doc.save(ignore_permissions=True)
        self.background_image = file_doc.file_url


def _allowed_college_names_for_editor(user: str) -> list[str]:
    user_perms = get_user_permissions(user) or {}
    rows = user_perms.get("Colleges") or []
    allowed: list[str] = []
    for row in rows:
        if isinstance(row, dict):
            value = row.get("doc") or row.get("for_value") or row.get("name")
            if value:
                allowed.append(str(value))
        elif row:
            allowed.append(str(row))
    return sorted(set(allowed))

def _user_has_role(user: str, role: str) -> bool:
    try:
        return role in (frappe.get_roles(user) or [])
    except Exception:
        return False


def get_permission_query_conditions(user: str | None = None) -> str | None:
    user = user or frappe.session.user
    if not user or user == "Administrator":
        return None

    if not _user_has_role(user, "AAU Editor"):
        return None

    allowed = _allowed_college_names_for_editor(user)
    if not allowed:
        return "1=0"

    values = ", ".join(frappe.db.escape(name) for name in allowed)
    return f"`tabColleges`.`name` in ({values})"


def has_permission(doc=None, user: str | None = None, ptype: str | None = None):
    user = user or frappe.session.user
    if not user or user == "Administrator":
        return None

    if not _user_has_role(user, "AAU Editor"):
        return None

    if ptype in {"create", "delete", "submit", "cancel", "amend"}:
        return False

    allowed = set(_allowed_college_names_for_editor(user))
    if not allowed:
        return False

    if doc is None:
        return True

    doc_name = doc if isinstance(doc, str) else getattr(doc, "name", None)
    return bool(doc_name and doc_name in allowed)
