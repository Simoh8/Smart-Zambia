from functools import partial
from hashlib import sha256
import json
from typing import Literal

import frappe
from frappe.model.document import Document
from erpnext.controllers.taxes_and_totals import get_itemised_tax_breakup_data

from ...api.api_builder import EndpointConstructor
from ...api.remote_response_handler import (
    on_error,
    on_success_stock_movement,
)
from ...utilities import (
    build_request_headers,
    extract_doc_series_number,
    get_route_path,
    get_server_url,
    split_user_mail,
    quantize_amount,
)

endpoint_maker = EndpointConstructor()



def on_update(doc: Document, method: str | None = None) -> None:
    company_name = doc.company
    all_items = frappe.db.get_all(
        "Item", ["*"]
    )  # Get all items to filter and fetch metadata
    record = frappe.get_doc(doc.voucher_type, doc.voucher_no)
    series_no = extract_doc_series_number(record)
    headers = build_request_headers(company_name )
    payload = {
        "sarNo": series_no,
        "orgSarNo": series_no,
        "regTyCd": "M",
        "custTin": None,
        "custNm": None,
        "custBhfId": headers.get("bhfId") or None,
        "ocrnDt": record.posting_date.strftime("%Y%m%d"),
        "totTaxblAmt": 0,
        "totItemCnt": len(record.items),
        "totTaxAmt": 0,
        "totAmt": 0,
        "remark": None,
        "regrId": split_user_mail(record.owner),
        "regrNm": record.owner,
        "modrNm": record.modified_by,
        "modrId": split_user_mail(record.modified_by),
    }
    headers = build_request_headers(company_name )
    payload["tpin"] = headers.get("tpin")
    payload["bhfId"] = headers.get("bhfId")

    if doc.voucher_type == "Stock Reconciliation":
        items_list = get_stock_recon_movement_items_details(
            record.items, all_items
        )  
        current_item = list(
            filter(lambda item: item["itemNm"] == doc.item_code, items_list)
        )  
        qty_diff = int(
            current_item[0].pop("quantity_difference")
        )  
        payload["itemList"] = current_item
        payload["totItemCnt"] = len(current_item)

        if record.purpose == "Opening Stock":
            payload["sarTyCd"] = "06"

        else:
            if qty_diff < 0:
                payload["sarTyCd"] = "16"

            else:
                payload["sarTyCd"] = "06"

    if doc.voucher_type == "Stock Entry":
        items_list = get_stock_entry_movement_items_details(record.items, all_items)
        current_item = list(
            filter(lambda item: item["itemNm"] == doc.item_code, items_list)
        )

        payload["itemList"] = current_item
        payload["totItemCnt"] = len(current_item)

        if record.stock_entry_type == "Material Receipt":
            payload["sarTyCd"] = "04"

        if record.stock_entry_type == "Material Transfer":
            doc_warehouse_branch_id = get_warehouse_branch_id(doc.warehouse)
            voucher_details = frappe.db.get_value(
                "Stock Entry Detail",
                {"name": doc.voucher_detail_no},
                ["s_warehouse", "t_warehouse"],
                as_dict=True,
            )

            if doc.actual_qty < 0:
                headers = build_request_headers(doc.company, doc_warehouse_branch_id)
                payload["custBhfId"] = headers.get("bhfId")
                payload["sarTyCd"] = "13"

            else:
                headers = build_request_headers(doc.company)
                payload["custBhfId"] = headers.get("bhfId")
                payload["sarTyCd"] = "04"

        if record.stock_entry_type == "Manufacture":
            if doc.actual_qty > 0:
                payload["sarTyCd"] = "05"

            else:
                payload["sarTyCd"] = "14"

        if record.stock_entry_type in ("Send to Subcontractor", "Material Issue"):
            payload["sarTyCd"] = "13"

        if record.stock_entry_type == "Repack":
            if doc.actual_qty < 0:
                payload["sarTyCd"] = "14"

            else:
                payload["sarTyCd"] = "05"

    if doc.voucher_type in ("Purchase Receipt", "Purchase Invoice"):

        items_list = get_purchase_docs_items_details(record.items, all_items)
        item_taxes = get_itemised_tax_breakup_data(record)

        current_item = list(
            filter(lambda item: item["itemNm"] == doc.item_code, items_list)
        )
        tax_details = list(filter(lambda i: i["item"] == doc.item_code, item_taxes))[0]

        # current_item[0]["taxblAmt"] = round(
        #     tax_details["taxable_amount"] / current_item[0]["qty"], 2
        # )
        # current_item[0]["totAmt"] = round(
        #     tax_details["taxable_amount"] / current_item[0]["qty"], 2
        # )

        # actual_tax_amount = 0
        # tax_head = doc.taxes[0].description

        # actual_tax_amount = tax_details[tax_head]["tax_amount"]

        # current_item[0]["taxAmt"] = round(actual_tax_amount / current_item[0]["qty"], 2)

        payload["itemList"] = current_item
        payload["totItemCnt"] = len(current_item)

        if record.is_return:
            payload["sarTyCd"] = "12"

        else:
            if current_item[0]["is_imported_item"]:
                payload["sarTyCd"] = "01"

            else:
                payload["sarTyCd"] = "02"

    if doc.voucher_type in ("Delivery Note", "Sales Invoice"):
        if (
            doc.voucher_type == "Sales Invoice"
            and record.custom_successfully_submitted != 1
        ):
            return

        items_list = get_notes_docs_items_details(record.items, all_items)
        item_taxes = get_itemised_tax_breakup_data(record)

        current_item = list(
            filter(lambda item: item["itemNm"] == doc.item_code, items_list)
        )  # Get current item only
        tax_details = list(filter(lambda i: i["item"] == doc.item_code, item_taxes))[
            0
        ]  
      

        payload["itemList"] = current_item
        payload["totItemCnt"] = len(current_item)
        payload["custNm"] = record.customer
        payload["custTin"] = record.tax_id
        payload["vatCatCd"]= current_item.custom_zra_tax_type or "B"

        if record.is_return:
            if doc.actual_qty > 0:
                payload["sarTyCd"] = "03"

            else:
                payload["sarTyCd"] = "11"

        else:
            payload["sarTyCd"] = "11"

    server_url = get_server_url(company_name)
    route_path = get_route_path("SAVE STOCK ITEM")
    if headers and server_url and route_path:
        route_path = route_path[0] if isinstance(route_path, tuple) else route_path
        url = f"{server_url}{route_path}"        
        # frappe.throw(url)

        endpoint_maker.url = url
        endpoint_maker.headers = headers
        endpoint_maker.payload = payload
        endpoint_maker.error_callback = on_error
        endpoint_maker.success_callback = partial(
            on_success_stock_movement, document_name=doc.name
        )

        job_name = sha256(
            f"{doc.name}{doc.creation}{doc.modified}".encode(), usedforsecurity=False
        ).hexdigest()


        endpoint_maker.perform_remote_calls()

        # frappe.enqueue(
        #     endpoint_maker.perform_remote_calls,
        #     queue="default",
        #     is_async=True,
        #     timeout=300,
        #     job_name=job_name,
        #     doctype="Stock Ledger Entry",
        #     document_name=doc.name,
        # )

def get_stock_entry_movement_items_details(
    records: list[Document], all_items: list[Document]
) -> list[dict]:
    items_list = []

    for item in records:
        for fetched_item in all_items:
            if item.item_code == fetched_item.name:
                items_list.append(
                    {
                        "itemSeq": item.idx,
                        "itemCd": fetched_item.custom_zra_item_code,
                        "itemClsCd": fetched_item.custom_zra_item_classification_code,
                        "itemNm": fetched_item.item_code,
                        "bcd": None,
                        "pkgUnitCd": fetched_item.custom_zra_packaging_unit_code,
                        "pkg": 1,
                        "qtyUnitCd": fetched_item.custom_zra_unit_quantity_code,
                        "qty": abs(item.qty),
                        "itemExprDt": "",
                        "prc": (
                            round(int(item.basic_rate), 2) if item.basic_rate else 0
                        ),
                        "splyAmt": (
                            round(int(item.basic_rate), 2) if item.basic_rate else 0
                        ),
                        "totDcAmt": 0,
                        "taxTyCd": fetched_item.custom_zra_tax_type or "B",
                        "vatCatCd": fetched_item.custom_zra_tax_type or "B",
                        "taxblAmt": 0,
                        "taxAmt": 0,
                        "totAmt": 0,
                    }
                )

    return items_list


def get_stock_recon_movement_items_details(
    records: list, all_items: list
) -> list[dict]:
    items_list = []
    # current_qty

    for item in records:
        for fetched_item in all_items:
            if item.item_code == fetched_item.name:
                items_list.append(
                    {
                        "itemSeq": item.idx,
                        "itemCd": fetched_item.custom_zra_item_code,
                        "itemClsCd": fetched_item.custom_zra_item_classification_code,
                        "itemNm": fetched_item.item_code,
                        "bcd": None,
                        "pkgUnitCd": fetched_item.custom_packaging_unit_code,
                        "pkg": 1,
                        "qtyUnitCd": fetched_item.custom_unit_of_quantity_code,
                        "qty": abs(int(item.quantity_difference)),
                        "itemExprDt": "",
                        "prc": (
                            round(int(item.valuation_rate), 2)
                            if item.valuation_rate
                            else 0
                        ),
                        "splyAmt": (
                            round(int(item.valuation_rate), 2)
                            if item.valuation_rate
                            else 0
                        ),
                        "totDcAmt": 0,
                        "taxTyCd": fetched_item.custom_zra_tax_type or "B",
                        "taxblAmt": 0,
                        "taxAmt": 0,
                        "totAmt": 0,
                        "vatCatCd": fetched_item.custom_zra_tax_type or "B",
                        "quantity_difference": item.quantity_difference,
                    }
                )

    return items_list


def get_purchase_docs_items_details(
    items: list, all_present_items: list[Document]
) -> list[dict]:
    items_list = []

    for item in items:
        for fetched_item in all_present_items:
            if item.item_code == fetched_item.name:
                items_list.append(
                    {
                        "itemSeq": item.idx,
                        "itemCd": fetched_item.custom_zra_item_code,
                        "itemClsCd": fetched_item.custom_zra_item_classification_code,
                        "itemNm": fetched_item.item_code,
                        "bcd": None,
                        "pkgUnitCd": fetched_item.custom_packaging_unit_code,
                        "pkg": 1,
                        "qtyUnitCd": fetched_item.custom_unit_of_quantity_code,
                        "qty": abs(item.qty),
                        "itemExprDt": "",
                        "prc": (
                            round(int(item.valuation_rate), 2)
                            if item.valuation_rate
                            else 0
                        ),
                        "splyAmt": (
                            round(int(item.valuation_rate), 2)
                            if item.valuation_rate
                            else 0
                        ),
                        "totDcAmt": 0,
                        "taxTyCd": fetched_item.custom_zra_tax_type or "B",
                        "vatCatCd": fetched_item.custom_zra_tax_type or "B",
                        "taxblAmt": quantize_amount(item.net_amount),
                        "taxAmt": quantize_amount(item.custom_tax_amount) or 0,
                        "totAmt": quantize_amount(item.net_amount + item.custom_tax_amount),
                        "is_imported_item": (
                            True
                            if (
                                fetched_item.custom_imported_item_status
                                and fetched_item.custom_imported_item_task_code
                            )
                            else False
                        ),
                    }
                )

    return items_list


def get_notes_docs_items_details(
    items: list[Document], all_present_items: list[Document]
) -> list[dict]:
    items_list = []

    for item in items:
        for fetched_item in all_present_items:
            if item.item_code == fetched_item.name:
                items_list.append(
                    {
                        "itemSeq": item.idx,
                        "itemCd": fetched_item.custom_zra_item_code,
                        "itemClsCd": fetched_item.custom_zra_item_classification_code,
                        "itemNm": fetched_item.item_code,
                        "bcd": None,
                        "pkgUnitCd": fetched_item.custom_packaging_unit_code,
                        "pkg": 1,
                        "qtyUnitCd": fetched_item.custom_unit_of_quantity_code,
                        "qty": abs(item.qty),
                        "itemExprDt": "",
                        "prc": (
                            round(int(item.base_net_rate), 2)
                            if item.base_net_rate
                            else 0
                        ),
                        "splyAmt": (
                            round(int(item.base_net_rate), 2)
                            if item.base_net_rate
                            else 0
                        ),
                        "totDcAmt": 0,
                        "vatCatCd": fetched_item.custom_zra_tax_type or "B",
                        "taxTyCd": fetched_item.custom_zra_tax_type or "B",
                        "taxblAmt": quantize_amount(item.net_amount),
                        "taxAmt": quantize_amount(item.custom_tax_amount) or 0,
                        "totAmt": quantize_amount(item.net_amount + item.custom_tax_amount),
                    }
                )

    return items_list


def get_warehouse_branch_id(warehouse_name: str) -> str | Literal[0]:
    branch_id = frappe.db.get_value(
        "Warehouse", {"name": warehouse_name}, ["custom_branch"], as_dict=True
    )

    if branch_id:
        return branch_id.custom_branch

    return 0
