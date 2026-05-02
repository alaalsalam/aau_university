# Copyright (c) 2026, AAU University
# For license information, please see license.txt

from frappe.model.document import Document


def _text(value) -> str:
    if value is None:
        return ""
    return str(value).strip()


class Offers(Document):
    def validate(self):
        # Keep primary image field synchronized with explicit upload field.
        offer_image = _text(getattr(self, "offer_image", ""))
        image = _text(getattr(self, "image", ""))
        if offer_image and not image:
            self.image = offer_image
        elif image and not offer_image:
            self.offer_image = image

        # Keep Arabic/English field pairs synchronized to avoid missing values in frontend.
        pairs = [
            ("title_ar", "title_en"),
            ("desc_ar", "desc_en"),
            ("details_ar", "details_en"),
            ("target_audience_ar", "target_audience_en"),
            ("benefits_ar", "benefits_en"),
            ("duration_ar", "duration_en"),
            ("location_ar", "location_en"),
            ("requirements_ar", "requirements_en"),
        ]
        for source_field, target_field in pairs:
            source = _text(getattr(self, source_field, ""))
            target = _text(getattr(self, target_field, ""))
            if source and not target:
                setattr(self, target_field, source)
