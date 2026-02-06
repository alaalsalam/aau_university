# -*- coding: utf-8 -*-
from __future__ import annotations

import frappe

from aau_university.setup.aau_screen_audit_fix import run as run_audit_fix


def execute():
    logger = frappe.logger("aau_university")
    logger.info("[AAU SCREEN AUDIT] PATCH START")
    try:
        report = run_audit_fix(update_existing=True, dry_run=False)
        logger.info(
            "[AAU SCREEN AUDIT] PATCH END | CREATED={created} UPDATED={updated} SKIPPED={skipped}".format(
                created=report.get("created_count", 0),
                updated=report.get("updated_count", 0),
                skipped=report.get("skipped_count", 0),
            )
        )
    except Exception:
        tb = frappe.get_traceback()
        logger.error("[AAU SCREEN AUDIT] PATCH FAILED\n" + tb)
        return
