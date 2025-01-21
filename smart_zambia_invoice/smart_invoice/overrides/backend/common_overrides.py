from collections import defaultdict
from functools import partial
from typing import Literal

import frappe
from frappe.model.document import Document
from erpnext.controllers.taxes_and_totals import get_itemised_tax_breakup_data

from ...api.api_builder import EndpointConstructor
from ...api. remote_response_handler import (
    on_error,
    on_success_sales_information_submission,
)
from ...utilities import (
    build_request_headers,
    get_server_url,
    get_route_path,
    get_current_env_settings
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
    headers = build_request_headers(company_name, doc.branch)
    server_url = get_server_url(company_name, doc.branch)
    route_path, last_req_date = get_route_path("SAVE SALES")

    if headers and server_url and route_path:
        url = f"{server_url}{route_path}"

        invoice_identifier = "C" if doc.is_return else "S"
        payload = build_request_headers(doc, invoice_identifier, company_name)

        endpoint_builder.headers = headers
        endpoint_builder.url = url
        endpoint_builder.payload = payload
        endpoint_builder.success_callback = partial(
            on_success_sales_information_submission,
            document_name=doc.name,
            invoice_type=invoice_type,
            company_name=company_name,
            invoice_number=payload["invcNo"],
            pin=headers.get("tpin"),
            branch_id=headers.get("bhfId"),
        )
        endpoint_builder.error_callback = on_error

        frappe.enqueue(
            endpoint_builder.perform_remote_calls,
            is_async=True,
            queue="default",
            timeout=300,
            job_name=f"{doc.name}_send_sales_request",
            doctype=invoice_type,
            document_name=doc.name,
        )


def validate(doc: Document, method: str) -> None:
    doc.custom_scu_id = get_current_env_settings(
        frappe.defaults.get_user_default("Company"), doc.branch
    ).scu_id
    if not doc.branch:
        frappe.throw("Please ensure the branch is set before saving the documents")
    # item_taxes = get_itemised_tax_breakup_data(doc)

    # taxes_breakdown = defaultdict(list)
    # taxable_breakdown = defaultdict(list)
    # tax_head = doc.taxes[0].description

    # for index, item in enumerate(doc.items):
    #     taxes_breakdown[item.custom_taxation_type_code].append(
    #         item_taxes[index][tax_head]["tax_amount"]
    #     )
    #     taxable_breakdown[item.custom_taxation_type_code].append(
    #         item_taxes[index]["taxable_amount"]
    #     )

    # update_tax_breakdowns(doc, (taxes_breakdown, taxable_breakdown))


# def update_tax_breakdowns(invoice: Document, mapping: tuple) -> None:
#     invoice.custom_tax_a = round(sum(mapping[0]["A"]), 2)
#     invoice.custom_tax_b = round(sum(mapping[0]["B"]), 2)
#     invoice.custom_tax_c = round(sum(mapping[0]["C"]), 2)
#     invoice.custom_tax_d = round(sum(mapping[0]["D"]), 2)
#     invoice.custom_tax_e = round(sum(mapping[0]["E"]), 2)

#     invoice.custom_taxbl_amount_a = round(sum(mapping[1]["A"]), 2)
#     invoice.custom_taxbl_amount_b = round(sum(mapping[1]["B"]), 2)
#     invoice.custom_taxbl_amount_c = round(sum(mapping[1]["C"]), 2)
#     invoice.custom_taxbl_amount_d = round(sum(mapping[1]["D"]), 2)
#     invoice.custom_taxbl_amount_e = round(sum(mapping[1]["E"]), 2)


