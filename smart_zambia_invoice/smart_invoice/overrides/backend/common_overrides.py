from collections import defaultdict
from functools import partial
from typing import Literal
import frappe

from frappe.model.document import Document

from ...api.api_builder import EndpointConstructor
from ...api. remote_response_handler import (on_error,on_success_sales_information_submission)
from ...utilities import (build_request_headers,get_server_url,build_invoice_payload,get_route_path, last_request_less_payload
)

endpoint_builder = EndpointConstructor()


def on_submit_override_generic_invoices(
    doc: Document, invoice_type: Literal["Sales Invoice", "POS Invoice"]
) -> None:
    """Defines a function to handle sending of Sales information from relevant invoice documents

    Args:
        doc (Document): The doctype object or record
        invoice_type (Literal[&quot;Sales Invoice&quot;, &quot;POS Invoice&quot;]):
        The Type of the invoice. Either Sales, or POS
    """
    company_name = doc.company
    headers = build_request_headers(company_name)
    server_url = get_server_url(company_name)
    route_path = get_route_path("SAVE SALES INVOICE")
    # frappe.throw("This is a return invoice")


    if headers and server_url and route_path:
        url = f"{server_url}{route_path}"
        invoice_identifier = "C" if doc.is_return else "S"
        print("I have xmade a return note ")

        invoice_payload = build_invoice_payload(doc, invoice_identifier, company_name)
        common_payload = last_request_less_payload(headers)
        payload = {**common_payload, **invoice_payload}
        endpoint_builder.headers = headers
        endpoint_builder.url = url
        endpoint_builder.payload = payload
        endpoint_builder.success_callback = partial(
            on_success_sales_information_submission,
            document_name=doc.name,
            invoice_type=invoice_type,
            invoice_number=doc.name,  
            company_name=company_name,
            tpin=headers.get("tpin"),
            branch_id=headers.get("bhfId"),
        )
        endpoint_builder.error_callback = on_error
        endpoint_builder.perform_remote_calls()

        # frappe.enqueue(
        #     endpoint_builder.perform_remote_calls,
        #     is_async=True,
        #     queue="default",
        #     timeout=300,
        #     job_name=f"{doc.name}_send_sales_request",
        #     doctype=invoice_type,
        #     document_name=doc.name,
        # )

