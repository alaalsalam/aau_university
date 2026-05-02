# Copyright (c) 2026, alaalsalam and contributors
# For license information, please see license.txt

from frappe.model.document import Document


def _clean_text(value) -> str:
	if value is None:
		return ""
	return str(value).strip()


class News(Document):
	def validate(self):
		self._sync_bilingual_fields()

	def _sync_bilingual_fields(self):
		"""Keep legacy/public API fields in sync with the visible edit fields."""
		title_ar = _clean_text(self.title) or _clean_text(self.title_ar)
		summary_ar = _clean_text(self.summary) or _clean_text(self.description_ar)
		content_ar = _clean_text(self.content) or _clean_text(self.content_ar)

		if title_ar:
			self.title = title_ar
			self.title_ar = title_ar
		if summary_ar:
			self.summary = summary_ar
			self.description_ar = summary_ar
		if content_ar:
			self.content = content_ar
			self.content_ar = content_ar
