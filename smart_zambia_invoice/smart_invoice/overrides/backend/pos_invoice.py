import frappe
from frappe.model.document import Document
from smart_zambia_invoice.smart_invoice.overrides.backend.purchase_invoice import validate_item_registration

from .common_overrides import on_submit_override_generic_invoices


def on_submit(doc: Document, method: str) -> None:
    """Intercepts POS Invoice or Sales Invoice on submit event and ensures mandatory fields."""



    # Ensure Payment Code and Status Code are set
    if doc.doctype == "POS Invoice" and doc.custom_has_been_submitted_to_zra == 0 :
        # Initialize default values
        payment_code = "0"  # Default (Other)
        status_code = "02"  # Always 02 for POS

        # Derive payment code based on POS payment method
        for payment in doc.payments:
            payment_type = payment.mode_of_payment.lower() if payment.mode_of_payment else ""

            if payment_type in ["cash", "mobile money"]:
                payment_code = "1"  # Cash or Mobile Money

        # Assign values to the doc (even if the fields don't exist in POS Invoice, we pass them in the function)
        doc.custom_zra_payment_code = payment_code
        doc.custom_progress_status_code = status_code

    else:
        # Ensure Sales Invoice has the required fields
        if not doc.custom_zra_payment_code:
            frappe.throw("ZRA Payment Code is required for submission.")
        
        if not doc.custom_progress_status_code:
            frappe.throw("ZRA Progress Status Code is required for submission.")

    # Proceed with submission for both Sales and POS Invoices
    on_submit_override_generic_invoices(doc, doc.doctype)
