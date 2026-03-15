# -*- coding: utf-8 -*-
from __future__ import annotations

import frappe
from frappe.utils.file_manager import save_file

from .registry import ENTITY_CONFIG, ENTITY_ROLE_PERMISSIONS, ENTITY_SUPERADMIN_ONLY_FIELDS, SUPER_ADMIN_ROLES
from .utils import (
    ApiError,
    build_filters,
    deserialize_child_rows,
    ensure_uuid,
    get_table_field_map,
    normalize_payload,
    now_ts,
    parse_json_list,
    parse_pagination,
    parse_sort,
    require_roles,
    serialize_doc,
    to_snake,
)


def _get_entity_config(entity_key: str) -> dict:
    if entity_key not in ENTITY_CONFIG:
        raise ApiError("NOT_FOUND", "Unknown entity", status_code=404)
    return ENTITY_CONFIG[entity_key]


def _require_entity_permission(entity_key: str, mode: str):
    user_roles = set(frappe.get_roles(frappe.session.user))
    if user_roles.intersection(SUPER_ADMIN_ROLES):
        return

    config = ENTITY_ROLE_PERMISSIONS.get(entity_key) or {}
    allowed = set(config.get(mode) or [])
    if not allowed:
        allowed = set(config.get("write") or [])
    if not allowed:
        allowed = set(config.get("read") or [])
    if not allowed:
        allowed = {"AAU Admin", "AUU Admin", "System Manager", "Administrator"}

    require_roles(allowed)


def _is_super_admin() -> bool:
    user_roles = set(frappe.get_roles(frappe.session.user))
    return bool(user_roles.intersection(SUPER_ADMIN_ROLES))


def _enforce_super_admin_field_restrictions(entity_key: str, payload: dict):
    if _is_super_admin():
        return
    restricted_fields = ENTITY_SUPERADMIN_ONLY_FIELDS.get(entity_key) or set()
    blocked_fields = sorted(field for field in payload.keys() if field in restricted_fields)
    if blocked_fields:
        raise ApiError(
            "FORBIDDEN",
            "You are not allowed to modify publishing/order fields for this entity",
            details={"entity": entity_key, "fields": blocked_fields},
            status_code=403,
        )


def _resolve_doctype(config: dict) -> str:
    candidates = config.get("doctype_candidates") or []
    primary = config.get("doctype")
    if primary:
        candidates = [primary] + [candidate for candidate in candidates if candidate != primary]
    for doctype in candidates:
        if doctype and frappe.db.exists("DocType", doctype):
            return doctype
    if primary:
        raise ApiError("NOT_FOUND", f"DocType {primary} is not available", status_code=404)
    raise ApiError("NOT_FOUND", "Configured DocType is not available", status_code=404)


def _get_meta(doctype: str):
    return frappe.get_meta(doctype)


def _resolve_identifier_field(meta, config: dict, by: str = "id") -> str:
    if by == "slug":
        slug_field = config.get("slug_field")
        if slug_field and meta.get_field(slug_field):
            return slug_field
    id_field = config.get("id_field", "id")
    if id_field and meta.get_field(id_field):
        return id_field
    return "name"


_SYSTEM_FIELDNAMES = {
    "name",
    "owner",
    "creation",
    "modified",
    "modified_by",
    "docstatus",
    "idx",
    "parent",
    "parentfield",
    "parenttype",
    "lft",
    "rgt",
}

_NON_FIELD_PAYLOAD_KEYS = {
    "cmd",
    "data",
    "doctype",
    "name",
    "csrf_token",
    "sid",
    "_",
}


def _get_query_fieldnames(doctype: str) -> list[str]:
    # WHY+WHAT: `frappe.get_all(fields=...)` must only receive real DB columns. Selecting
    # layout/table fields (Section Break / HTML / Table, etc.) causes SQL "Unknown column" 500s.
    meta = _get_meta(doctype)
    get_valid_columns = getattr(meta, "get_valid_columns", None)
    if callable(get_valid_columns):
        columns = [c for c in get_valid_columns() if c and c not in _SYSTEM_FIELDNAMES]
        if "name" not in columns:
            columns.insert(0, "name")
        return columns

    # Fallback for older meta implementations: exclude non-column fieldtypes.
    non_column_fieldtypes = {
        "Section Break",
        "Column Break",
        "Tab Break",
        "Fold",
        "HTML",
        "Button",
        "Heading",
        "Read Only",
        "Table",
        "Table MultiSelect",
        "Image",
    }
    columns = [
        df.fieldname
        for df in meta.fields
        if df.fieldname and df.fieldtype not in non_column_fieldtypes and df.fieldname not in _SYSTEM_FIELDNAMES
    ]
    if "name" not in columns:
        columns.insert(0, "name")
    return columns


def _get_payload_fieldnames(doctype: str) -> list[str]:
    # WHY+WHAT: allow API create/update payloads to include table fields (child tables),
    # while keeping list queries restricted to DB columns only.
    meta = _get_meta(doctype)
    columns = _get_query_fieldnames(doctype)
    table_fields = [df.fieldname for df in meta.get_table_fields() if df.fieldname]
    return columns + [f for f in table_fields if f not in columns]


def _assert_payload_keys(entity_key: str, payload: dict, payload_fieldnames: list[str]):
    allowed = set(payload_fieldnames)
    unknown = []
    for key in (payload or {}).keys():
        key_str = str(key)
        if key_str in _NON_FIELD_PAYLOAD_KEYS:
            continue
        normalized_key = key_str if key_str in allowed else to_snake(key_str)
        if normalized_key not in allowed:
            unknown.append(key_str)
    if unknown:
        raise ApiError(
            "VALIDATION_ERROR",
            "Payload contains unsupported fields",
            details={"entity": entity_key, "fields": sorted(set(unknown))},
            status_code=400,
        )


def _prepare_child_tables(meta, payload: dict) -> dict:
    table_fields = get_table_field_map(meta)
    for fieldname, value_field in table_fields.items():
        if fieldname not in payload:
            continue
        values = parse_json_list(payload[fieldname])
        payload[fieldname] = deserialize_child_rows(values, meta.get_field(fieldname).options, value_field)
    return payload


def _resolve_doc_name(doctype: str, fieldname: str, value: str) -> str:
    result = frappe.get_all(
        doctype,
        filters={fieldname: value},
        fields=["name"],
        limit=1,
        ignore_permissions=True,
    )
    if not result:
        raise frappe.DoesNotExistError
    return result[0]["name"]


def list_entities(entity_key: str, search_fields: list[str] | None = None, public: bool = True):
    if not public:
        _require_entity_permission(entity_key, "read")
    config = _get_entity_config(entity_key)
    doctype = _resolve_doctype(config)
    meta = _get_meta(doctype)
    query_fieldnames = _get_query_fieldnames(doctype)
    table_fields = get_table_field_map(meta)

    filters = build_filters(query_fieldnames)
    or_filters = []
    query = frappe.form_dict.get("q")
    if query and search_fields:
        or_filters = [["{0}".format(field), "like", f"%{query}%"] for field in search_fields]

    pagination = parse_pagination()
    order_by = parse_sort(default=f"{meta.sort_field or 'modified'} {meta.sort_order or 'desc'}")

    rows = frappe.get_all(
        doctype,
        filters=filters,
        or_filters=or_filters,
        fields=query_fieldnames,
        limit_start=pagination["offset"],
        limit_page_length=pagination["limit"],
        order_by=order_by,
        ignore_permissions=public,
    )
    # WHY+WHAT: `frappe.db.count` doesn't support `or_filters` on some Frappe versions, so
    # use a safe aggregate query when OR-search is present.
    if or_filters:
        total_row = frappe.get_all(
            doctype,
            filters=filters,
            or_filters=or_filters,
            fields=["count(name) as total"],
            ignore_permissions=public,
            limit_page_length=1,
        )
        total = int((total_row[0] or {}).get("total") or 0) if total_row else 0
    else:
        total = frappe.db.count(doctype, filters=filters)

    data = [serialize_doc(row, table_fields) for row in rows]
    meta_out = {
        "page": pagination["page"],
        "limit": pagination["limit"],
        "total": total,
        "totalPages": (total + pagination["limit"] - 1) // pagination["limit"] if pagination["limit"] else 1,
    }
    return {"data": data, "meta": meta_out}


def get_entity(entity_key: str, identifier: str, by: str = "id", public: bool = True):
    if not public:
        _require_entity_permission(entity_key, "read")
    config = _get_entity_config(entity_key)
    doctype = _resolve_doctype(config)
    meta = _get_meta(doctype)
    table_fields = get_table_field_map(meta)

    fieldname = _resolve_identifier_field(meta, config, by=by)
    doc_name = _resolve_doc_name(doctype, fieldname, identifier)
    doc = frappe.get_doc(doctype, doc_name)

    if not public and not doc.has_permission("read"):
        raise frappe.PermissionError

    return serialize_doc(doc.as_dict(), table_fields)


def get_entity_by_field(entity_key: str, fieldname: str, value: str, public: bool = True):
    if not public:
        _require_entity_permission(entity_key, "read")
    config = _get_entity_config(entity_key)
    doctype = _resolve_doctype(config)
    meta = _get_meta(doctype)
    table_fields = get_table_field_map(meta)
    doc_name = _resolve_doc_name(doctype, fieldname, value)
    doc = frappe.get_doc(doctype, doc_name)
    if not public and not doc.has_permission("read"):
        raise frappe.PermissionError
    return serialize_doc(doc.as_dict(), table_fields)


def create_entity(entity_key: str, payload: dict, public: bool = False):
    if not public:
        _require_entity_permission(entity_key, "write")
        _enforce_super_admin_field_restrictions(entity_key, payload)
    config = _get_entity_config(entity_key)
    doctype = _resolve_doctype(config)
    meta = _get_meta(doctype)
    payload_fieldnames = _get_payload_fieldnames(doctype)
    table_fields = get_table_field_map(meta)
    _assert_payload_keys(entity_key, payload, payload_fieldnames)

    data = normalize_payload(payload, payload_fieldnames)
    id_field = config.get("id_field")
    if id_field and id_field in payload_fieldnames:
        data[id_field] = ensure_uuid(data.get(id_field))
    if "created_at" in payload_fieldnames:
        data.setdefault("created_at", now_ts())
    if "updated_at" in payload_fieldnames:
        data["updated_at"] = now_ts()

    data = _prepare_child_tables(meta, data)
    doc = frappe.get_doc({"doctype": doctype, **data})
    doc.insert(ignore_permissions=True)
    return serialize_doc(doc.as_dict(), table_fields)


def update_entity(entity_key: str, identifier: str, payload: dict, by: str = "id"):
    _require_entity_permission(entity_key, "write")
    _enforce_super_admin_field_restrictions(entity_key, payload)
    config = _get_entity_config(entity_key)
    doctype = _resolve_doctype(config)
    meta = _get_meta(doctype)
    payload_fieldnames = _get_payload_fieldnames(doctype)
    table_fields = get_table_field_map(meta)
    _assert_payload_keys(entity_key, payload, payload_fieldnames)

    fieldname = _resolve_identifier_field(meta, config, by=by)
    doc_name = _resolve_doc_name(doctype, fieldname, identifier)
    doc = frappe.get_doc(doctype, doc_name)

    data = normalize_payload(payload, payload_fieldnames)
    if "updated_at" in payload_fieldnames:
        data["updated_at"] = now_ts()
    data = _prepare_child_tables(meta, data)
    doc.update(data)
    doc.save(ignore_permissions=True)
    return serialize_doc(doc.as_dict(), table_fields)


def update_entity_by_field(entity_key: str, fieldname: str, value: str, payload: dict):
    _require_entity_permission(entity_key, "write")
    _enforce_super_admin_field_restrictions(entity_key, payload)
    config = _get_entity_config(entity_key)
    doctype = _resolve_doctype(config)
    meta = _get_meta(doctype)
    payload_fieldnames = _get_payload_fieldnames(doctype)
    table_fields = get_table_field_map(meta)
    _assert_payload_keys(entity_key, payload, payload_fieldnames)

    doc_name = _resolve_doc_name(doctype, fieldname, value)
    doc = frappe.get_doc(doctype, doc_name)
    data = normalize_payload(payload, payload_fieldnames)
    if "updated_at" in payload_fieldnames:
        data["updated_at"] = now_ts()
    data = _prepare_child_tables(meta, data)
    doc.update(data)
    doc.save(ignore_permissions=True)
    return serialize_doc(doc.as_dict(), table_fields)


def delete_entity(entity_key: str, identifier: str, by: str = "id"):
    _require_entity_permission(entity_key, "write")
    config = _get_entity_config(entity_key)
    doctype = _resolve_doctype(config)
    meta = _get_meta(doctype)
    fieldname = _resolve_identifier_field(meta, config, by=by)
    doc_name = _resolve_doc_name(doctype, fieldname, identifier)
    frappe.delete_doc(doctype, doc_name, ignore_permissions=True)
    return {"deleted": True}


def increment_counter(entity_key: str, identifier: str, fieldname: str, public: bool = True):
    if not public:
        _require_entity_permission(entity_key, "write")
    config = _get_entity_config(entity_key)
    doctype = _resolve_doctype(config)
    meta = _get_meta(doctype)
    id_field = _resolve_identifier_field(meta, config, by="id")
    doc_name = _resolve_doc_name(doctype, id_field, identifier)
    doc = frappe.get_doc(doctype, doc_name)
    current = int(getattr(doc, fieldname, 0) or 0)
    doc.set(fieldname, current + 1)
    doc.save(ignore_permissions=True)
    return {"id": identifier, fieldname: current + 1}


def update_status(entity_key: str, identifier: str, status_field: str, status_value: str):
    _require_entity_permission(entity_key, "write")
    _enforce_super_admin_field_restrictions(entity_key, {status_field: status_value})
    config = _get_entity_config(entity_key)
    doctype = _resolve_doctype(config)
    meta = _get_meta(doctype)
    id_field = _resolve_identifier_field(meta, config, by="id")
    doc_name = _resolve_doc_name(doctype, id_field, identifier)
    doc = frappe.get_doc(doctype, doc_name)
    doc.set(status_field, status_value)
    if hasattr(doc, "reviewed_at"):
        doc.set("reviewed_at", now_ts())
    if hasattr(doc, "replied_at"):
        doc.set("replied_at", now_ts())
    doc.save(ignore_permissions=True)
    return {"id": identifier, status_field: status_value}


def upload_media():
    _require_entity_permission("media", "write")
    if not frappe.request.files:
        raise ApiError("VALIDATION_ERROR", "No file uploaded", status_code=400)

    fileobj = next(iter(frappe.request.files.values()))
    saved = save_file(fileobj.filename, fileobj.stream.read(), None, None, None)
    doctype = _resolve_doctype(ENTITY_CONFIG["media"])
    meta = _get_meta(doctype)
    payload_fieldnames = _get_payload_fieldnames(doctype)
    table_fields = get_table_field_map(meta)

    doc = frappe.get_doc(
        {
            "doctype": doctype,
            "id": ensure_uuid(None),
            "file_name": saved.file_name,
            "file_path": saved.file_url,
            "file_type": saved.file_type,
            "file_size": saved.file_size,
            "uploaded_by": frappe.session.user,
            "created_at": now_ts(),
        }
    )
    doc.insert(ignore_permissions=True)
    return serialize_doc(doc.as_dict(), table_fields)
