# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import re
import uuid
from functools import wraps
from typing import Any, Iterable

import frappe
from frappe import _
from frappe.utils import now


class ApiError(Exception):
    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = 400,
        details: Any | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details


def api_endpoint(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
            meta = None
            status_code = 200
            if isinstance(result, dict) and result.pop("__meta__", False):
                meta = result.get("meta")
                result = result.get("data")
            elif isinstance(result, tuple):
                if len(result) == 2:
                    result, status_code = result
                elif len(result) == 3:
                    result, meta, status_code = result
            return ok_response(result, meta=meta, status_code=status_code)
        except ApiError as exc:
            return error_response(
                exc.code,
                exc.message,
                details=exc.details,
                status_code=exc.status_code,
            )
        except frappe.PermissionError:
            return error_response("FORBIDDEN", _("Not permitted"), status_code=403)
        except frappe.DoesNotExistError:
            return error_response("NOT_FOUND", _("Not found"), status_code=404)
        except frappe.ValidationError as exc:
            return error_response("VALIDATION_ERROR", str(exc), status_code=400)
        except Exception:
            tb = frappe.get_traceback()
            frappe.logger("aau_university").error("[AAU API] UNHANDLED\n" + tb)
            return error_response("SERVER_ERROR", _("Unexpected server error"), status_code=500)

    return wrapper


def ok_response(data: Any = None, meta: dict | None = None, status_code: int = 200) -> dict:
    frappe.response.http_status_code = status_code
    return {"ok": True, "data": data, "error": None, "meta": meta or {}}


def error_response(
    code: str,
    message: str,
    details: Any | None = None,
    status_code: int = 400,
) -> dict:
    frappe.response.http_status_code = status_code
    return {"ok": False, "data": None, "error": {"code": code, "message": message, "details": details}, "meta": {}}


def require_auth():
    if frappe.session.user == "Guest":
        raise ApiError("UNAUTHORIZED", _("Authentication required"), status_code=401)


def require_roles(roles: Iterable[str]):
    require_auth()
    user_roles = set(frappe.get_roles(frappe.session.user))
    if not any(role in user_roles for role in roles):
        raise ApiError("FORBIDDEN", _("Insufficient permissions"), status_code=403)


def to_snake(value: str) -> str:
    value = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", value)
    value = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", value)
    return value.replace("-", "_").lower()


def to_camel(value: str) -> str:
    parts = value.split("_")
    return parts[0] + "".join(word.capitalize() for word in parts[1:])


def normalize_payload(data: dict, fieldnames: Iterable[str]) -> dict:
    normalized = {}
    allowed = set(fieldnames)
    for key, value in (data or {}).items():
        candidate = key if key in allowed else to_snake(key)
        if candidate in allowed:
            normalized[candidate] = value
    return normalized


def ensure_uuid(value: str | None = None) -> str:
    if value:
        return value
    return str(uuid.uuid4())


def now_ts() -> str:
    return now()


def parse_json_list(value: Any) -> list:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except Exception:
            return []
        if isinstance(parsed, list):
            return parsed
    return []


def parse_pagination():
    page = int(frappe.form_dict.get("page") or 1)
    limit = frappe.form_dict.get("limit") or frappe.form_dict.get("page_size") or 20
    limit = int(limit)
    offset = (page - 1) * limit
    return {"page": page, "limit": limit, "offset": offset}


def parse_sort(default: str = "modified desc") -> str:
    sort = frappe.form_dict.get("sort") or frappe.form_dict.get("sort_by")
    order = frappe.form_dict.get("order") or frappe.form_dict.get("sort_order")
    if sort:
        order = (order or "desc").lower()
        direction = "desc" if order not in ("asc", "desc") else order
        return f"{sort} {direction}"
    return default


def build_filters(allowed_fields: Iterable[str]) -> list:
    filters = []
    allowed = set(allowed_fields)
    for key, value in frappe.form_dict.items():
        if key in ("page", "limit", "page_size", "offset", "sort", "sort_by", "order", "sort_order", "q"):
            continue
        if key.endswith("_from") and key[:-5] in allowed:
            filters.append([key[:-5], ">=", value])
            continue
        if key.endswith("_to") and key[:-3] in allowed:
            filters.append([key[:-3], "<=", value])
            continue
        if key in allowed:
            filters.append([key, "=", value])
    return filters


def serialize_doc(doc: dict, table_fields: dict[str, str]) -> dict:
    output = {}
    for key, value in doc.items():
        if key in ("doctype", "name", "owner", "creation", "modified", "modified_by"):
            continue
        if key in table_fields:
            output[to_camel(key)] = serialize_child_rows(value, table_fields[key])
        else:
            output[to_camel(key)] = value
    return output


def serialize_child_rows(rows: list, value_field: str) -> list:
    values = []
    for row in rows or []:
        if isinstance(row, dict):
            if value_field in row:
                values.append(row[value_field])
        else:
            if hasattr(row, value_field):
                values.append(getattr(row, value_field))
    return values


def deserialize_child_rows(values: list, doctype: str, value_field: str) -> list:
    return [{"doctype": doctype, value_field: value} for value in values or []]


def get_table_field_map(meta) -> dict[str, str]:
    mapping = {}
    for field in meta.get_table_fields():
        child_meta = frappe.get_meta(field.options)
        value_field = None
        for df in child_meta.fields:
            if df.fieldname == "value":
                value_field = "value"
                break
        if value_field:
            mapping[field.fieldname] = value_field
    return mapping


def smoke_test() -> dict:
    """Basic smoke test for AAU APIs (internal calls)."""
    frappe.form_dict = frappe._dict({})
    from .resources import list_entities, get_entity

    results = {
        "news": list_entities("news", public=True)["data"],
        "events": list_entities("events", public=True)["data"],
        "colleges": list_entities("colleges", public=True)["data"],
    }
    if results["news"]:
        results["news_detail"] = get_entity("news", results["news"][0]["id"], by="id", public=True)
    return results
