import frappe
from frappe.model.document import Document

from .common_overrides import on_submit_override_generic_invoices

def on_submit(doc: Document, method: str) -> None:
    """Intercepts submit event for document"""

    if doc.update_stock == 1:
        if doc.custom_has_it_been_successfully_submitted == 0:
            on_submit_override_generic_invoices(doc, "Sales Invoice")

        elif getattr(doc, "is_return", 0) == 1:
            on_submit_override_generic_invoices(doc, "Sales Invoice")  # Still process it

def before_cancel(doc: Document, method: str) -> None:
    """Disallow cancelling of submitted invoice to ZRA ."""
    
    if doc.doctype == "Sales Invoice" and doc.custom_has_it_been_successfully_submitted:
        frappe.throw(
            "This invoice has already been <b>submitted</b> to ZRA and cannot be <span style='color:red'>Canceled.</span>\n"
            "If you need to make adjustments, please create a Credit Note instead."
        )
    elif doc.doctype == "Purchase Invoice" and doc.custom_has_it_been_successfully_submitted:
        frappe.throw(
            "This invoice has already been <b>submitted</b> to ZRA and cannot be <span style='color:red'>Canceled.</span>.\nIf you need to make adjustments, please create a Debit Note instead."
        )