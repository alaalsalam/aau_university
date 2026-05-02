# Copyright (c) 2026, alaalsalam and contributors
# For license information, please see license.txt

from frappe.model.document import Document


def _text(value) -> str:
    if value is None:
        return ""
    return str(value).strip()


class Events(Document):
    def validate(self):
        # Keep Arabic/English fields synchronized so frontend always gets values.
        if _text(self.event_title) and not _text(self.event_title_en):
            self.event_title_en = _text(self.event_title)
        if _text(self.description) and not _text(self.description_en):
            self.description_en = _text(self.description)
        if _text(self.location) and not _text(self.location_en):
            self.location_en = _text(self.location)
