# -*- coding: utf-8 -*-
from __future__ import annotations

import frappe

from aau_university.content_access import (
    CONTENT_DOCTYPES,
    CONTENT_MANAGER_ROLE,
    ensure_doctype_permission,
    ensure_role,
    ensure_workspace_access,
    hide_legacy_workspace,
    sync_content_manager_user,
)

LOG_PREFIX = "[AAU CONTENT ACCESS]"


def execute():
    logger = frappe.logger("aau_university")
    logger.info(f"{LOG_PREFIX} START")
    try:
        created_role = ensure_role()
        updated_doctypes = []
        for doctype_name in CONTENT_DOCTYPES:
            if ensure_doctype_permission(doctype_name):
                updated_doctypes.append(doctype_name)

        workspace_changed = ensure_workspace_access()
        legacy_changed = hide_legacy_workspace()
        user_changed = sync_content_manager_user()

        frappe.clear_cache()
        frappe.db.commit()

        logger.info(
            "%s DONE role_created=%s doctypes_updated=%s workspace_changed=%s legacy_changed=%s user_changed=%s role=%s"
            % (
                LOG_PREFIX,
                int(created_role),
                len(updated_doctypes),
                int(workspace_changed),
                int(legacy_changed),
                int(user_changed),
                CONTENT_MANAGER_ROLE,
            )
        )
        if updated_doctypes:
            logger.info("%s DOCTYPES %s" % (LOG_PREFIX, ", ".join(updated_doctypes)))
    except Exception:
        logger.error(f"{LOG_PREFIX} FAILED\n{frappe.get_traceback()}")
        raise
