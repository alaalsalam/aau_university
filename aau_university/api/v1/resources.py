# -*- coding: utf-8 -*-
from __future__ import annotations

import frappe
from frappe.utils.file_manager import save_file

from .registry import ADMIN_ROLES, ENTITY_CONFIG
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
)


def _get_entity_config(entity_key: str) -> dict:
    if entity_key not in ENTITY_CONFIG:
        raise ApiError("NOT_FOUND", "Unknown entity", status_code=404)
    return ENTITY_CONFIG[entity_key]


def _get_meta(doctype: str):
    return frappe.get_meta(doctype)


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


def _get_query_fieldnames(doctype: str) -> list[str]:
    # WHY+WHAT: `frappe.get_all(fields=...)` must only receive real DB columns. Selecting
    # layout/table fields (Section Break / HTML / Table, etc.) causes SQL "Unknown column" 500s.
    meta = _get_meta(doctype)
    get_valid_columns = getattr(meta, "get_valid_columns", None)
    if callable(get_valid_columns):
        columns = [c for c in get_valid_columns() if c and c not in _SYSTEM_FIELDNAMES]
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
    return columns


def _get_payload_fieldnames(doctype: str) -> list[str]:
    # WHY+WHAT: allow API create/update payloads to include table fields (child tables),
    # while keeping list queries restricted to DB columns only.
    meta = _get_meta(doctype)
    columns = _get_query_fieldnames(doctype)
    table_fields = [df.fieldname for df in meta.get_table_fields() if df.fieldname]
    return columns + [f for f in table_fields if f not in columns]


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
    config = _get_entity_config(entity_key)
    doctype = config["doctype"]
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
    config = _get_entity_config(entity_key)
    doctype = config["doctype"]
    meta = _get_meta(doctype)
    table_fields = get_table_field_map(meta)

    fieldname = config.get("slug_field") if by == "slug" else config.get("id_field", "id")
    doc_name = _resolve_doc_name(doctype, fieldname, identifier)
    doc = frappe.get_doc(doctype, doc_name)

    if not public and not doc.has_permission("read"):
        raise frappe.PermissionError

    return serialize_doc(doc.as_dict(), table_fields)


def get_entity_by_field(entity_key: str, fieldname: str, value: str, public: bool = True):
    config = _get_entity_config(entity_key)
    doctype = config["doctype"]
    meta = _get_meta(doctype)
    table_fields = get_table_field_map(meta)
    doc_name = _resolve_doc_name(doctype, fieldname, value)
    doc = frappe.get_doc(doctype, doc_name)
    if not public and not doc.has_permission("read"):
        raise frappe.PermissionError
    return serialize_doc(doc.as_dict(), table_fields)


def create_entity(entity_key: str, payload: dict, public: bool = False):
    if not public:
        require_roles(ADMIN_ROLES)
    config = _get_entity_config(entity_key)
    doctype = config["doctype"]
    meta = _get_meta(doctype)
    payload_fieldnames = _get_payload_fieldnames(doctype)
    table_fields = get_table_field_map(meta)

    data = normalize_payload(payload, payload_fieldnames)
    if config.get("id_field"):
        data[config["id_field"]] = ensure_uuid(data.get(config["id_field"]))
    if "created_at" in payload_fieldnames:
        data.setdefault("created_at", now_ts())
    if "updated_at" in payload_fieldnames:
        data["updated_at"] = now_ts()

    data = _prepare_child_tables(meta, data)
    doc = frappe.get_doc({"doctype": doctype, **data})
    doc.insert(ignore_permissions=True)
    return serialize_doc(doc.as_dict(), table_fields)


def update_entity(entity_key: str, identifier: str, payload: dict, by: str = "id"):
    require_roles(ADMIN_ROLES)
    config = _get_entity_config(entity_key)
    doctype = config["doctype"]
    meta = _get_meta(doctype)
    payload_fieldnames = _get_payload_fieldnames(doctype)
    table_fields = get_table_field_map(meta)

    fieldname = config.get("slug_field") if by == "slug" else config.get("id_field", "id")
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
    require_roles(ADMIN_ROLES)
    config = _get_entity_config(entity_key)
    doctype = config["doctype"]
    meta = _get_meta(doctype)
    payload_fieldnames = _get_payload_fieldnames(doctype)
    table_fields = get_table_field_map(meta)

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
    require_roles(ADMIN_ROLES)
    config = _get_entity_config(entity_key)
    doctype = config["doctype"]
    fieldname = config.get("slug_field") if by == "slug" else config.get("id_field", "id")
    doc_name = _resolve_doc_name(doctype, fieldname, identifier)
    frappe.delete_doc(doctype, doc_name, ignore_permissions=True)
    return {"deleted": True}


def increment_counter(entity_key: str, identifier: str, fieldname: str, public: bool = True):
    if not public:
        require_roles(ADMIN_ROLES)
    config = _get_entity_config(entity_key)
    doctype = config["doctype"]
    id_field = config.get("id_field", "id")
    doc_name = _resolve_doc_name(doctype, id_field, identifier)
    doc = frappe.get_doc(doctype, doc_name)
    current = int(getattr(doc, fieldname, 0) or 0)
    doc.set(fieldname, current + 1)
    doc.save(ignore_permissions=True)
    return {"id": identifier, fieldname: current + 1}


def update_status(entity_key: str, identifier: str, status_field: str, status_value: str):
    require_roles(ADMIN_ROLES)
    config = _get_entity_config(entity_key)
    doctype = config["doctype"]
    id_field = config.get("id_field", "id")
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
    require_roles(ADMIN_ROLES)
    if not frappe.request.files:
        raise ApiError("VALIDATION_ERROR", "No file uploaded", status_code=400)

    fileobj = next(iter(frappe.request.files.values()))
    saved = save_file(fileobj.filename, fileobj.stream.read(), None, None, None)
    doctype = ENTITY_CONFIG["media"]["doctype"]
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
