from __future__ import annotations

import frappe


BAD_VALUES = {
    "hg",
    "k",
    "j",
    "hi",
    "kj",
    "kn",
    "kkkkkk",
    "mj",
    "jg",
    "hiiiii",
    "hiiiiiiiiiiiiiiiiiiiii",
}

ABOUT_FIELDS = [
    "page_badge_en",
    "page_title_en",
    "page_description_en",
    "intro_body_en",
    "vision_title_en",
    "vision_description_en",
    "mission_title_en",
    "mission_description_en",
    "goals_title_en",
    "goals_description_en",
    "values_title_en",
    "values_description_en",
    "president_section_title_en",
    "president_message_intro_en",
    "president_message_body_en",
    "president_message_closing_en",
    "president_name_en",
    "president_role_en",
    "team_section_title_en",
    "team_section_description_en",
]

TEAM_FIELDS = ["group_name_en", "full_name_en", "job_title_en"]


def _should_clear(value: str | None) -> bool:
    text = (value or "").strip()
    if not text:
        return False
    if text in BAD_VALUES:
        return True
    return len(text) <= 2


def execute():
    doc = frappe.get_doc("About University", "About University")
    cleared: list[str] = []

    for fieldname in ABOUT_FIELDS:
        if _should_clear(doc.get(fieldname)):
            doc.set(fieldname, "")
            cleared.append(fieldname)

    for row in doc.get("team_members") or []:
        for fieldname in TEAM_FIELDS:
            if _should_clear(row.get(fieldname)):
                row.set(fieldname, "")
                cleared.append(f"team_members:{row.idx}:{fieldname}")

    doc.save(ignore_permissions=True)
    frappe.db.commit()
    return {"cleared_count": len(cleared), "cleared": cleared}
