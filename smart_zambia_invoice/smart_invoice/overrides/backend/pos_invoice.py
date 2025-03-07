import frappe
from frappe.model.document import Document
from smart_zambia_invoice.smart_invoice.overrides.backend.purchase_invoice import validate_item_registration

from .common_overrides import on_submit_override_generic_invoices


def on_submit(doc: Document, method: str) -> None:
    """Intercepts POS invoice on submit event"""

    if not doc.custom_has_been_submitted_to_zra ==0:
        on_submit_override_generic_invoices(doc, "POS Invoice")
