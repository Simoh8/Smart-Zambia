from collections import defaultdict
from functools import partial
import json
import frappe
from functools import partial
from frappe import _

import frappe
from frappe.model.document import Document
from erpnext.controllers.taxes_and_totals import get_itemised_tax_breakup_data
from frappe.utils import get_link_to_form
from smart_zambia_invoice.smart_invoice.overrides.backend.common_overrides import last_request_less_payload, on_submit_override_generic_invoices, on_success_sales_information_submission 

from ...api.api_builder import EndpointConstructor
from ...api.remote_response_handler import (
	on_error,
	on_succesful_purchase_invoice_submission,
	on_success_debit_sales_information_submission,
	
)
from ...utilities import (build_request_headers,extract_doc_series_number,get_route_path, get_route_path_with_last_req_date,get_server_url,quantize_amount,split_user_mail,get_taxation_types)


import frappe
from frappe.utils import now_datetime
from decimal import Decimal

endpoints_maker = EndpointConstructor()





def validate(doc: Document, method: str) -> None:

	item_taxes = get_itemised_tax_breakup_data(doc)
	taxes_breakdown = defaultdict(list)
	taxable_breakdown = defaultdict(list)
	if not doc.taxes:
		vat_acct = frappe.get_value(
			"Account", {"account_type": "Tax", "tax_rate": "16"}, ["name"], as_dict=True
		)
		doc.set(
			"taxes",
			[
				{
					"account_head": vat_acct.name,
					"included_in_print_rate": 1,
					"description": vat_acct.name.split("-", 1)[0].strip(),
					"category": "Total",
					"add_deduct_tax": "Add",
					"charge_type": "On Net Total",
				}
			],
		)






def on_submit(doc: Document, method: str) -> None:
    validate_item_registration(doc.items)

    if doc.is_return:
        # If it's a return (debit invoice), send to ZRA via debit registration
        perform_debit_invoice_registration(doc.name, doc.company)
        return  # Skip the rest for debit invoices

    company_name = doc.company
    headers = build_request_headers(company_name)
    server_url = get_server_url(company_name)
    route_path = get_route_path("SAVE PURCHASES")

    if headers and server_url and route_path:
        url = f"{server_url}{route_path}"

        common_payload = last_request_less_payload(headers)
        invoice_payload = build_purchase_invoice_payload(doc)
        payload = {**common_payload, **invoice_payload}

        endpoints_maker.url = url
        endpoints_maker.headers = headers
        endpoints_maker.payload = payload
        endpoints_maker.success_callback = partial(
            on_succesful_purchase_invoice_submission,
            document_name=doc.name
        )
        endpoints_maker.error_callback = on_error

        endpoints_maker.perform_remote_calls()




def build_purchase_invoice_payload(doc: Document) -> dict:
    series_no = extract_doc_series_number(doc)
    items_list = get_items_details(doc)
    taxation_type = get_taxation_types(doc)
    
    # Convert taxation_type list into a dictionary
    taxation_dict = {item["tax_code"]: item for item in taxation_type}
    
    payload = {
        "invcNo": series_no,
        "orgInvcNo": 0,
        "spplrTin": doc.tax_id,
        "spplrBhfId": doc.custom_supplier_branch_id,
        "spplrNm": doc.supplier,
        "spplrInvcNo": doc.bill_no,
        "regTyCd": "A",
        "pchsTyCd": doc.custom_zra_purchase_type_code_,
        "rcptTyCd": doc.custom_zra_receipt_type_code,
        "pmtTyCd": doc.custom_zra_payment_type_code,
        "pchsSttsCd": doc.custom_zra_purchase_status_code,
        "cfmDt": None,
        "pchsDt": "".join(str(doc.posting_date).split("-")),
        "wrhsDt": None,
        "cnclReqDt": "",
        "cnclDt": "",
        "rfdDt": None,
        "totItemCnt": len(items_list),
        "totTaxblAmt": quantize_amount(doc.base_net_total),
        "totTaxAmt": quantize_amount(doc.total_taxes_and_charges),
        "totAmt": quantize_amount(doc.grand_total),
        "remark": None,
        "regrNm": doc.owner,
        "regrId": split_user_mail(doc.owner),
        "modrNm": doc.modified_by,
        "modrId": split_user_mail(doc.modified_by),
        "itemList": items_list,
    }
    
    return payload





def get_tax_rate(taxTyCd):
    """Fetch tax rate from ZRA Tax Type DocType."""
    return float(frappe.db.get_value("ZRA Tax Type", {"code": taxTyCd}, "tax_rate_") or 0)




def get_items_details(doc: Document) -> list:
    """Constructs a list of item details with proper tax allocation.

    Args:
        doc (Document): The invoice document.

    Returns:
        list: A list of dictionaries containing item details.
    """
    items_list = []

    for index, item in enumerate(doc.items):

        vatCatCd = None
        iplCatCd = None
        tlCatCd = None
        exciseTxCatCd = None

        taxTyCd = getattr(item, "custom_taxation_type", "B")
        taxRate = get_tax_rate(taxTyCd)  # Get the tax rate from ZRA Tax Type

        # Categorize tax types
        if taxTyCd in ["A", "B", "C1", "C2", "C3", "D", "E", "RVAT"]:
            vatCatCd = taxTyCd
        elif taxTyCd in ["IPL1", "IPL2"]:
            iplCatCd = taxTyCd
        elif taxTyCd == "TL":
            tlCatCd = "TL"
        elif taxTyCd in ["ECM", "EXEEG"]:
            exciseTxCatCd = taxTyCd

        qty = abs(getattr(item, "qty", 0))
        prc = round(getattr(item, "base_rate", 0), 2)
        splyAmt = round(getattr(item, "base_amount", 0), 2)
        dcRt = round(float(getattr(item, "discount_percentage", 0) or 0), 2)
        dcAmt = round(float(getattr(item, "discount_amount", 0) or 0), 2)
        taxblAmt = round(float(getattr(item, "net_amount", 0) or 0), 2)

        # Calculate tax amounts
        taxAmt = round(taxblAmt * (taxRate / 100), 2)

        # Allocate taxable amounts based on tax type
        vatTaxblAmt = taxblAmt if vatCatCd else 0
        iplTaxblAmt = taxblAmt if iplCatCd else 0
        exciseTaxblAmt = taxblAmt if exciseTxCatCd else 0
        tlTaxblAmt = taxblAmt if tlCatCd else 0

        # Assign tax amounts
        vatAmt = taxAmt if vatCatCd else 0
        iplAmt = taxAmt if iplCatCd else 0
        exciseTxAmt = taxAmt if exciseTxCatCd else 0
        tlAmt = taxAmt if tlCatCd else 0

        totAmt = round(taxblAmt + taxAmt, 2)

        items_list.append({
            "itemSeq": item.idx,
            "itemCd": getattr(item, "custom_item_classification", ""),
            "itemClsCd": getattr(item, "custom_item_classification_code", ""),
            "itemNm": getattr(item, "item_name", ""),
            "bcd": "",
            "spplrItemClsCd": None,
            "spplrItemCd": None,
            "spplrItemNm": None,
            "pkgUnitCd": getattr(item, "custom_packaging_unit_code", ""),
            "pkg": 1,
            "qtyUnitCd": getattr(item, "custom_unit_of_quantity_code", ""),
            "qty": qty,
            "prc": prc,
            "splyAmt": splyAmt,
            "dcRt": dcRt,
            "dcAmt": dcAmt,
            "tlTaxblAmt": tlTaxblAmt,
            "vatCatCd": vatCatCd,
            "iplTaxblAmt": iplTaxblAmt,
            "exciseTaxblAmt": exciseTaxblAmt,
            "exciseTxCatCd": exciseTxCatCd,
            "vatTaxblAmt": vatTaxblAmt,
            "exciseTxAmt": exciseTxAmt,
            "vatAmt": vatAmt,
            "tlAmt": tlAmt,
            "iplAmt": iplAmt,
            "iplCatCd": iplCatCd,
            "tlCatCd": tlCatCd,
            "taxTyCd": taxTyCd,
            "taxblAmt": taxblAmt,
            "taxAmt": taxAmt,
            "totAmt": totAmt,
            "itemExprDt": None,
        })

    return items_list


def validate_item_registration(items):
    for item in items:
        item_code = item.item_code
        validation_message(item_code)





def validation_message(item_code):
    item_doc = frappe.get_doc("Item", item_code)

    if item_doc.custom_zra_referenced_imported_item and (item_doc.custom_zra_item_registered_ == 0 or item_doc.custom_imported_item_submitted == 0):
        item_link = get_link_to_form("Item", item_doc.name)
        frappe.throw(f"Register or submit the item: {item_link}")

    elif not item_doc.custom_zra_referenced_imported_item and item_doc.custom_zra_item_registered_ == 0:
        item_link = get_link_to_form("Item", item_doc.name)
        frappe.throw(f"Register the item: {item_link}")

    if not item_doc.custom_zra_tax_type:
        item_link = get_link_to_form("Item", item_doc.name)
        frappe.throw(f"Specify the Tax Type for the item: {item_link}")

        



@frappe.whitelist()
def perform_debit_invoice_registration(document_name: str, company_name: str) -> dict | None:
    headers = build_request_headers(company_name)
    server_url = get_server_url(company_name)
    route_path, last_req_date= get_route_path_with_last_req_date("SAVE SALES INVOICE")

    if not (headers and server_url and route_path):
        return 
        pass

    try:
        invoice_payload = build_debit_invoice_payload(document_name)
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Payload Build Failed")
        frappe.throw(_("Failed to build invoice payload."))

    common_payload = last_request_less_payload(headers)
    full_payload = {**common_payload, **invoice_payload}

    invoice_type = "Purchase Invoice"
    invoice_number = full_payload.get("cisInvcNo", "")
    tpin = full_payload.get("custTpin", "")

    # Setup remote call
    endpoints_maker.url = f"{server_url}{route_path}"
    endpoints_maker.payload = full_payload
    endpoints_maker.success_callback = partial(
        on_success_debit_sales_information_submission,
        invoice_type=invoice_type,
        document_name=document_name,
        company_name=company_name,
        invoice_number=invoice_number,
        payload=full_payload,
        tpin=tpin,
    )
    endpoints_maker.error_callback = on_error

    endpoints_maker.perform_remote_calls()

    return {"status": "submitted", "invoice": document_name}








def build_debit_invoice_payload(invoice_name):
    invoice = frappe.get_doc("Purchase Invoice", invoice_name)
    items = get_items_details(invoice)

    tax_codes = [
        "A", "B", "C1", "C2", "C3", "D", "RVAT", "E", "F",
        "IPL1", "IPL2", "TL", "ECM", "EXEEG"
    ]

    tax_aggregates = {
        code: {
            "taxblAmt": Decimal("0.00"),
            "taxAmt": Decimal("0.00"),
            "taxRt": Decimal(str(get_tax_rate(code)))
        } for code in tax_codes
    }

    total_taxable = Decimal("0.00")
    total_tax = Decimal("0.00")

    for item in items:
        code = item.get("taxTyCd")
        taxbl_amt = Decimal(item.get("taxblAmt", 0))
        tax_amt = Decimal(item.get("taxAmt", 0))

        if code in tax_aggregates:
            tax_aggregates[code]["taxblAmt"] += taxbl_amt
            tax_aggregates[code]["taxAmt"] += tax_amt

        total_taxable += taxbl_amt
        total_tax += tax_amt

        # Corrected Total Amount calculation
        item["totAmt"] = abs(item["splyAmt"] - item["vatAmt"])  # Total amount = Supply Amount - VAT Amount

        # Ensure positive values for fields
        item["taxblAmt"] = abs(item.get("taxblAmt", 0))
        item["taxAmt"] = abs(item.get("taxAmt", 0))
        item["splyAmt"] = abs(item.get("splyAmt", 0))
        item["vatTaxblAmt"] = abs(item.get("vatTaxblAmt", 0))
        item["vatAmt"] = abs(item.get("vatAmt", 0))

    payload = {
        "orgInvcNo": invoice.custom_original_smart_invoice_number,
        "cisInvcNo": invoice.name,
        "custTpin": "1017138037",
        "custNm": invoice.company,
        "salesTyCd": "N",
        "rcptTyCd": "D",
        "pmtTyCd": "01",
        "salesSttsCd": "02",
        "cfmDt": now_datetime().strftime("%Y%m%d%H%M%S"),
        "salesDt": invoice.posting_date.strftime("%Y%m%d"),
        "stockRlsDt": None,
        "cnclReqDt": None,
        "cnclDt": None,
        "rfdDt": None,
        "rfdRsnCd": None,
        "totItemCnt": len(items),
        "totTaxblAmt": float(abs(total_taxable)),
        "totTaxAmt": float(abs(total_tax)),
        "cashDcRt": 0,
        "cashDcAmt": 0,
        "totAmt": float(abs(invoice.grand_total)),
        "prchrAcptcYn": "N",
        "remark": invoice.remarks or "",
        "regrId": "ADMIN",
        "regrNm": "ADMIN",
        "modrId": "ADMIN",
        "modrNm": "ADMIN",
        "saleCtyCd": "1",
        "lpoNumber": getattr(invoice, "lpo_number", None),
        "currencyTyCd": invoice.currency,
        "exchangeRt": str(invoice.conversion_rate or 1),
        "destnCountryCd": "",
        "dbtRsnCd": "03",
        "invcAdjustReason": "Omitted Item"
    }

    # Add tax fields before item list
    for code in tax_codes:
        payload[f"taxblAmt{code}"] = float(abs(tax_aggregates[code]["taxblAmt"]))
        payload[f"taxAmt{code}"] = float(abs(tax_aggregates[code]["taxAmt"]))
        payload[f"taxRt{code}"] = float(tax_aggregates[code]["taxRt"])

    payload["taxblAmtTot"] = 0
    payload["taxAmtTot"] = 0
    payload["taxRtTot"] = 0

    # Final section: item list
    payload["itemList"] = items

    return payload
