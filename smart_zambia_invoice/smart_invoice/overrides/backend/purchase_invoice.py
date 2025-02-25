from collections import defaultdict
from functools import partial

import frappe
from frappe.model.document import Document
from erpnext.controllers.taxes_and_totals import get_itemised_tax_breakup_data
from frappe.utils import get_link_to_form 

from ...api.api_builder import EndpointConstructor
from ...api.remote_response_handler import (
	on_error,
	purchase_invoice_submission_on_success,
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
	if not doc.branch:
		frappe.throw("Please ensure the branch is set before saving the document")
	item_taxes = get_itemised_tax_breakup_data(doc)
	# if not doc.branch:
	#     frappe.throw("Please ensure the branch is set before submitting the document")
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
	if doc.is_return == 0 and doc.update_stock == 1:
		# TODO: Handle cases when item tax templates have not been picked
		company_name = doc.company
		vendor="OSCU KRA"
		headers = build_request_headers(company_name,vendor, doc.branch)
		server_url = get_server_url(company_name,vendor, doc.branch)
		route_path, last_request_date = get_route_path("TrnsPurchaseSaveReq")

		if headers and server_url and route_path:
			url = f"{server_url}{route_path}"
			payload = build_purchase_invoice_payload(doc)

			endpoints_maker.url = url
			endpoints_maker.headers = headers
			endpoints_maker.payload = payload
			endpoints_maker.success_callback = partial(
				purchase_invoice_submission_on_success, document_name=doc.name
			)

			endpoints_maker.error_callback = on_error

			frappe.enqueue(
				endpoints_maker.make_remote_call,
				is_async=True,
				queue="default",
				timeout=300,
				job_name=f"{doc.name}_send_purchase_information",
				doctype="Purchase Invoice",
				document_name=doc.name,
			)


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
		"pchsTyCd": doc.custom_purchase_type_code,
		"rcptTyCd": doc.custom_receipt_type_code,
		"pmtTyCd": doc.custom_payment_type_code,
		"pchsSttsCd": doc.custom_purchase_status_code,
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
	items_list = []

	for index, item in enumerate(doc.items):

		items_list.append(
			{
				"itemSeq": item.idx,
				"itemCd": item.custom_item_code_etims,
				"itemClsCd": item.custom_item_classification_code,
				"itemNm": item.item_name,
				"bcd": "",
				"spplrItemClsCd": None,
				"spplrItemCd": None,
				"spplrItemNm": None,
				"pkgUnitCd": item.custom_packaging_unit_code,
				"pkg": 1,
				"qtyUnitCd": item.custom_unit_of_quantity_code,
				"qty": abs(item.qty),
				"prc": item.base_rate,
				"splyAmt": item.base_amount,
				"dcRt": quantize_amount(item.discount_percentage) or 0,
				"dcAmt": quantize_amount(item.discount_amount) or 0,
				"taxblAmt": quantize_amount(item.net_amount),
				"taxTyCd": item.custom_taxation_type or "B",
				"taxAmt": quantize_amount(item.custom_tax_amount) or 0,
				"totAmt": quantize_amount(item.net_amount + item.custom_tax_amount),
				"itemExprDt": None,
			}
		)

	return items_list

def validate_item_registration(items):
	for item in items:
		item_code = item.item_code
		validation_message(item_code)
		
def validation_message(item_code):
	item_doc = frappe.get_doc("Item", item_code)
	
	if item_doc.custom_referenced_imported_item and (item_doc.custom_item_registered == 0 or item_doc.custom_imported_item_submitted == 0):
		item_link = get_link_to_form("Item", item_doc.name)
		frappe.throw(f"Register or submit the item: {item_link}")
	
	elif not item_doc.custom_referenced_imported_item and item_doc.custom_item_registered == 0:
		item_link = get_link_to_form("Item", item_doc.name)
		frappe.throw(f"Register the item: {item_link}")

