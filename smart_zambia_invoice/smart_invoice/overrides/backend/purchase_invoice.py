from collections import defaultdict
from functools import partial

import frappe
from frappe.model.document import Document
from erpnext.controllers.taxes_and_totals import get_itemised_tax_breakup_data
from frappe.utils import get_link_to_form
from smart_zambia_invoice.smart_invoice.overrides.backend.common_overrides import last_request_less_payload 

from ...api.api_builder import EndpointConstructor
from ...api.remote_response_handler import (
	on_error,
	on_succesful_purchase_invoice_submission,
	
)
from ...utilities import (
	build_request_headers,
	extract_doc_series_number,
	get_route_path,
	get_server_url,
	quantize_amount,
	split_user_mail,
	get_taxation_types
)

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

    company_name = doc.company
    headers = build_request_headers(company_name)
    server_url = get_server_url(company_name)
    route_path, last_request_date = get_route_path("SAVE PURCHASES")

    if headers and server_url and route_path:
        url = f"{server_url}{route_path}"

        # Fetch common payload fields (includes tpin and bhfId)
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
	taxation_type=get_taxation_types(doc)

	payload = {
		"invcNo": series_no,
		"orgInvcNo": 0,
		"spplrTin": doc.tax_id,
		"spplrBhfId": doc.custom_supplier_branch_id,
		"spplrNm": doc.supplier,
		"spplrInvcNo": doc.bill_no,
		"regTyCd": "A",
		"pchsTyCd": doc.custom_zra_purchase_type_code_,  # Correct field name
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
		
		"taxRtA": taxation_type.get("A", {}).get("tax_rate", 0),
		"taxRtB": taxation_type.get("B", {}).get("tax_rate", 0),
		"taxRtC": taxation_type.get("C", {}).get("tax_rate", 0),
		"taxRtD": taxation_type.get("D", {}).get("tax_rate", 0),
		"taxRtE": taxation_type.get("E", {}).get("tax_rate", 0),
		"taxAmtA": taxation_type.get("A", {}).get("tax_amount", 0),
		"taxAmtB": taxation_type.get("B", {}).get("tax_amount", 0),
		"taxAmtC": taxation_type.get("C", {}).get("tax_amount", 0),
		"taxAmtD": taxation_type.get("D", {}).get("tax_amount", 0),
		"taxAmtE": taxation_type.get("E", {}).get("tax_amount", 0),
		"taxblAmtA": taxation_type.get("A", {}).get("taxable_amount", 0),
		"taxblAmtB": taxation_type.get("B", {}).get("taxable_amount", 0),
		"taxblAmtC": taxation_type.get("C", {}).get("taxable_amount", 0),
		"taxblAmtD": taxation_type.get("D", {}).get("taxable_amount", 0),
		"taxblAmtE": taxation_type.get("E", {}).get("taxable_amount", 0),
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



def get_items_details(doc: Document) -> list:
    """Constructs a list of item details with proper tax allocation.

    Args:
        doc (Document): The invoice document.

    Returns:
        list: A list of dictionaries containing item details.
    """
    items_list = []

    for index, item in enumerate(doc.items):
        print(f"Item {index + 1} Details: {item.as_dict()}")

        vatCatCd = None
        iplCatCd = None
        tlCatCd = None
        exciseTxCatCd = None

        taxTyCd = getattr(item, "custom_taxation_type", "B")

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
        dcRt = round(float(quantize_amount(float(getattr(item, "discount_percentage", 0) or 0))), 2)
        dcAmt = round(float(quantize_amount(float(getattr(item, "discount_amount", 0) or 0))), 2)
        taxblAmt = round(float(getattr(item, "net_amount", 0) or 0), 2)
        taxAmt = round(float(quantize_amount(float(getattr(item, "custom_tax_amount", 0) or 0))), 2)

        # Allocate taxable amounts based on tax type
        vatTaxblAmt = taxblAmt if vatCatCd else 0
        iplTaxblAmt = taxblAmt if iplCatCd else 0
        exciseTaxblAmt = taxblAmt if exciseTxCatCd else 0
        tlTaxblAmt = taxblAmt if tlCatCd else 0

        vatAmt = taxAmt if vatTaxblAmt > 0 else 0
        iplAmt = taxAmt if iplTaxblAmt > 0 else 0
        exciseTxAmt = taxAmt if exciseTaxblAmt > 0 else 0
        tlAmt = taxAmt if tlTaxblAmt > 0 else 0

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


