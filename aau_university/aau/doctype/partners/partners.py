# Copyright (c) 2026, AAU University
# For license information, please see license.txt

from frappe.model.document import Document


def _text(value) -> str:
    if value is None:
        return ""
    return str(value).strip()


class Partners(Document):
    def validate(self):
        # Keep Arabic/English fields synchronized so frontend always gets values.
        if _text(self.title) and not _text(self.title_en):
            self.title_en = _text(self.title)
        if _text(self.content) and not _text(self.content_en):
            self.content_en = _text(self.content)
