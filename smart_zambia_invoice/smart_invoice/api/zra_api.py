import asyncio
from functools import partial
import aiohttp
import frappe
import json
import datetime
from datetime import datetime
import frappe.defaults
from frappe.model.document import Document 

from frappe.utils.dateutils import add_to_date
from smart_zambia_invoice.smart_invoice.overrides.backend.common_overrides import on_error
from smart_zambia_invoice.smart_invoice.overrides.backend.purchase_invoice import on_succesful_purchase_invoice_submission
from smart_zambia_invoice.smart_invoice.overrides.backend.sales_invoice import on_submit
from .api_builder import EndpointConstructor

from .remote_response_handler import on_succesful_inventory_submission, on_succesfull_purchase_search_zra, on_success_item_classification_search, on_success_sales_information_submission,  on_success_customer_search, on_success_item_composition_submission, on_success_item_registration, on_success_customer_insurance_details_submission,on_success_customer_branch_details_submission,notices_search_on_success,on_error,fetch_branch_request_on_success, on_imported_items_search_success, on_success_rrp_item_registration, on_success_submit_inventory, on_success_user_details_submission, on_successful_fetch_latest_items
from .. utilities import (build_request_headers,get_route_path, get_route_path_with_last_req_date, get_stock_balance, last_request_less_payload,make_get_request,split_user_mail,get_server_url,build_common_payload, truncate_user_id)

endpoint_builder = EndpointConstructor()


@frappe.whitelist()
def make_branch_request(request_data: str) -> None:
    data: dict = json.loads(request_data)

    company_name = data["company_name"]

    headers = build_request_headers(company_name)
    
    server_url = get_server_url(company_name)
    route_path, last_req_date = get_route_path_with_last_req_date("GET BRANCHES")

    if headers and server_url and route_path:
        url = f"{server_url}{route_path}"

        payload = last_request_less_payload(headers, last_req_date )

        endpoint_builder.url = url
        endpoint_builder.payload = payload
        endpoint_builder.success_callback = fetch_branch_request_on_success
        endpoint_builder.error_callback = on_error

        endpoint_builder.perform_remote_calls(
            doctype="Branch",
        )






@frappe.whitelist()
def ping_zra_server(request_data: str) -> None:
    data = json.loads(request_data)
    url = data.get("server_url")
    

    try:
        response = asyncio.run(make_get_request(url))

        # Check if response is None, indicating a connection issue
        if response is None:
            frappe.msgprint("The ZRA Server is Offline Please Again Try  Later")
            return

        # Check if the status code is 200 (OK)
        if response.status == 200:
            frappe.msgprint("The Server is Online")
        else:
            frappe.msgprint(f"The Server returned an error: {response.status}")

    except Exception as e:
        frappe.msgprint(f"Unexpected error: {str(e)}")




        
# Searching for the new notices available from ZRA
@frappe.whitelist()
def perform_zra_notice_search(request_data: str) -> None:
    data: dict = json.loads(request_data)
    company_name = data["company_name"]
    headers = build_request_headers(company_name)  # Keep headers for payload construction

    server_url = get_server_url(company_name)

    # Get route path and last request date
    route_path, last_req_date = get_route_path_with_last_req_date("Notices Fetching")

    if headers and server_url and route_path:
        url = f"{server_url}{route_path}"

        payload = last_request_less_payload(headers, last_req_date)  # Use headers only here

        endpoint_builder.url = url
        endpoint_builder.payload = payload
        endpoint_builder.success_callback = notices_search_on_success
        endpoint_builder.error_callback = on_error

        # Remove headers from perform_remote_calls
        endpoint_builder.perform_remote_calls(doctype="ZRA Smart Invoice Settings", document_name=data.get("name", None))


                        
                        
@frappe.whitelist()
def perform_customer_search(request_data: str) -> None:
    """Search customer details in the ZRA Server

    Args:
        request_data (str): Data received from the client
    """
    data: dict = json.loads(request_data)

    company_name = data["company_name"]

    headers = build_request_headers(company_name)
    server_url = get_server_url(company_name)
    route_path = get_route_path("GET CUSTOMERS")

    if headers and server_url and route_path:
        url = f"{server_url}{route_path}"
        payload = {"custmTpin": data["tax_id"]}

        endpoint_builder.url = url
        endpoint_builder.payload = payload
        endpoint_builder.success_callback = partial(
            on_success_customer_search, document_name=data["name"]
        )
        endpoint_builder.error_callback = on_error

        frappe.enqueue(
            endpoint_builder.perform_remote_calls,
            is_async=True,
            queue="default",
            timeout=300,
            doctype="Customer",
            document_name=data["name"],
            job_name=f"{data['name']}_customer_search",
        )





@frappe.whitelist()
def submit_branch_customer_details(request_data: str) -> None:
    """
    Submits branch customer details to the ZRA system.

    Args:
        request_data (str): JSON string containing request data.

    Returns:
        None
    """
    # Parse request data
    data: dict = json.loads(request_data)

    # Extract company information and build headers, server URL, and route path
    company_name = data["company_name"]
    headers = build_request_headers(company_name)
    server_url = get_server_url(company_name)
    route_path = get_route_path("SAVE BRANCH CUSTOMER")


    if headers and server_url and route_path:
        url = f"{server_url}{route_path}"
        common_payload = last_request_less_payload(headers)

        specific_payload = {
            "custNo": data["customer_phone"],
            "custTpin": data["customer_pin"],
            "custNm": data["customer_name"],
            "adrs": data["customer_address"],
            "telNo": data.get("customer_phone"),
            "email": data.get("customer_email"),
            "faxNo": "",
            "useYn": "Y",
            "remark": data["customer_remarks"],
            "regrNm": data["registration_id"],
            "regrId": split_user_mail(data["registration_id"]),
            "modrNm": data["modifier_id"],
            "modrId": split_user_mail(data["modifier_id"]),
        }

        # Merge the common payload and specific payload
        payload = {**common_payload, **specific_payload}

        # Configure the endpoint builder
        endpoint_builder.url = url
        endpoint_builder.payload = payload
        endpoint_builder.success_callback = partial(
            on_success_customer_branch_details_submission, document_name=data["name"]
        )
        endpoint_builder.error_callback = on_error

        # endpoint_builder.perform_remote_calls()


        # Enqueue the task for asynchronous execution
        frappe.enqueue(
            endpoint_builder.perform_remote_calls,
            is_async=True,
            queue="default",
            timeout=300,
            doctype="Customer",
            document_name=data["name"],
            job_name=f"{data['name']}_submit_customer_branch_details",
        )






@frappe.whitelist()
def perform_import_item_search(request_data: str) -> None:
    data: dict = json.loads(request_data)

    company_name = data["company_name"]

    if "branch_code" in data:
        headers = build_request_headers(company_name, data["branch_code"])
        server_url = get_server_url(company_name, data["branch_code"])

    else:
        headers = build_request_headers(company_name)
        server_url = get_server_url(company_name)

    route_path ,last_req_date = get_route_path_with_last_req_date("GET IMPORTS")


    if headers and server_url and route_path:
        url = f"{server_url}{route_path}"
        common_payload = last_request_less_payload(headers, last_req_date)

        payload = {
            **common_payload,
            "dclRefNum": "CX1100096839",
        }

        endpoint_builder.url = url
        endpoint_builder.payload = payload
        endpoint_builder.success_callback = on_imported_items_search_success
        endpoint_builder.error_callback = on_error

        endpoint_builder.perform_remote_calls()
        





# Not applicable to the zambian ZRA API for now but its working

@frappe.whitelist()
def send_customer_insurance_details(request_data: str) -> None:
    data: dict = json.loads(request_data)

    company_name = data["company_name"]

    headers = build_request_headers(company_name)
    server_url = get_server_url(company_name)
    route_path = get_route_path("BhfInsuranceSaveReq")

    if headers and server_url and route_path:
        url = f"{server_url}{route_path}"
        payload = {
            "isrccCd": data["insurance_code"],
            "isrccNm": data["insurance_name"],
            "isrcRt": round(data["premium_rate"], 0),
            "useYn": "Y",
            "regrNm": data["registration_id"],
            "regrId": split_user_mail(data["registration_id"]),
            "modrNm": data["modifier_id"],
            "modrId": split_user_mail(data["modifier_id"]),
        }

        endpoint_builder.url = url
        endpoint_builder.payload = payload
        endpoint_builder.success_callback = partial(
            on_success_customer_insurance_details_submission, document_name=data["name"]
        )
        endpoint_builder.error_callback = on_error

        frappe.enqueue(
            endpoint_builder.perform_remote_calls,
            is_async=True,
            queue="default",
            timeout=300,
            doctype="Customer",
            document_name=data["name"],
            job_name=f"{data['name']}_submit_insurance_information",
        )





@frappe.whitelist()
def submit_zra_branch_user_details(request_data: str) -> None:
    data: dict = json.loads(request_data)
    company_name = data["company_name"]
    headers = build_request_headers(company_name)
    server_url = get_server_url(company_name)
    route_path = get_route_path("SAVE BRANCH USER")

    if headers and server_url and route_path:
        url = f"{server_url}{route_path}"
        common_payload = last_request_less_payload(headers)


        custom_payload = {
            "userId": truncate_user_id(data["user_id"]),
            "userNm": data["full_names"],
            "adrs": None,
            "useYn": "Y",
            "regrNm": data["modifier_id"],
            "regrId": split_user_mail(data["registration_id"]),
            "modrNm": data["modifier_id"],
            "modrId": split_user_mail(data["modifier_id"]),
        }
        payload = {**common_payload, **custom_payload}


        endpoint_builder.url = url
        endpoint_builder.payload = payload
        endpoint_builder.success_callback = partial(
            on_success_user_details_submission, document_name=data["name"]
        )
        endpoint_builder.error_callback = on_error


        frappe.enqueue(
            endpoint_builder.perform_remote_calls,
            is_async=True,
            queue="default",
            timeout=300,
            doctype="ZRA Smart Invoice User",
            document_name=data["name"][:20],  # Ensure `document_name` is truncated
            job_name=f"{data['name'][:10]}_info",  # Ensure `job_name` fits
        )






@frappe.whitelist()
def fetch_customer_info(request_data: str) -> None:
    """Search customer details in the ZRA Server

    Args:
        request_data (str): Data received from the client
    """
    data: dict = json.loads(request_data)

    company_name = data["company_name"]

    headers = build_request_headers(company_name)
    server_url = get_server_url(company_name)
    route_path = get_route_path("GET CUSTOMERS")

    if headers and server_url and route_path:
        url = f"{server_url}{route_path}"

        common_payload = last_request_less_payload(headers)

        custom_payload = {"custmTpin": data["tax_id"]}
        payload= {**common_payload, **custom_payload}         

        endpoint_builder.url = url
        endpoint_builder.payload = payload
        endpoint_builder.success_callback = partial(on_success_customer_search, document_name=data["name"])
        endpoint_builder.error_callback = on_error

        # endpoint_builder.perform_remote_calls()

        frappe.enqueue(
            endpoint_builder.perform_remote_calls,
            is_async=True,
            queue="default",
            timeout=300,
            doctype="Customer",
            document_name=data["name"],
            job_name=f"{data['name']}_customer_search",
        )






@frappe.whitelist()
def make_zra_item_registration(request_data: str) -> dict | None:
  
    data: dict = json.loads(request_data)
    company_name = data["company_name"]
    headers = build_request_headers(company_name )
    server_url = get_server_url(company_name)
    route_path = get_route_path("SAVE ITEM")

    if headers and server_url and route_path:
            url = f"{server_url}{route_path}"

            # Build the common payload fields
            common_payload = last_request_less_payload(headers)

            data_to_send = {key: value for key, value in data.items() if key not in ["name", "company_name"]}
            payload = {**common_payload, **data_to_send}

            endpoint_builder.url = url
            endpoint_builder.payload = payload
            endpoint_builder.success_callback = partial(
                on_success_item_registration, document_name=data.get("name")
            )
            endpoint_builder.error_callback = on_error

            # Enqueue the task for asynchronous execution
            frappe.enqueue(
                endpoint_builder.perform_remote_calls,
                is_async=True,
                queue="default",
                timeout=300,
                doctype="Item",
                document_name=data["name"],
                job_name=f"{data['name']}_register_item",
            )









@frappe.whitelist()
def fetch_Previous_registered_zra_items(request_data: str, frm: dict = None) -> None:  # Default to None if frm is not passed
    data: dict = json.loads(request_data)

    company_name = data["company_name"]
    headers = build_request_headers(company_name)
    server_url = get_server_url(company_name)
    route_path, last_req_date = get_route_path("GET ITEMS")

    if headers and server_url and route_path:
        url = f"{server_url}{route_path}"

        request_date = last_req_date.strftime("%Y%m%d%H%M%S")
        payload = build_common_payload(headers, last_req_date)

      
        endpoint_builder.url = url
        endpoint_builder.payload = payload
        endpoint_builder.success_callback = lambda response: on_successful_fetch_latest_items(frm, response)  # Pass frm here if available
        endpoint_builder.error_callback = on_error

        endpoint_builder.perform_remote_calls(doctype="ZRA Smart Invoice Settings", document_name=data.get("name", None))







@frappe.whitelist()
def fetch_rrp_latest_items(request_data: str, frm: dict = None) -> None:  # Default to None if frm is not passed
    data: dict = json.loads(request_data)

    company_name = data["company_name"]
    headers = build_request_headers(company_name)
    server_url = get_server_url(company_name)
    route_path, last_req_date = get_route_path("SELECT RRP ITEMS")

    if headers and server_url and route_path:
        url = f"{server_url}{route_path}"

        request_date = last_req_date.strftime("%Y%m%d%H%M%S")
        payload = build_common_payload(headers, last_req_date)

        endpoint_builder.url = url
        endpoint_builder.payload = payload
        endpoint_builder.success_callback = lambda response: on_successful_fetch_latest_items(frm, response)  # Pass frm here if available
        endpoint_builder.error_callback = on_error

        endpoint_builder.perform_remote_calls(doctype="ZRA Smart Invoice Settings", document_name=data.get("name", None))








@frappe.whitelist()
def save_item_composition(request_data: str) -> None:
    data: dict = json.loads(request_data)

    company_name = data["company_name"]

    headers = build_request_headers(company_name)
    server_url = get_server_url(company_name)
    route_path, last_req_date = get_route_path_with_last_req_date("SAVE ITEM COMPOSITION")

    if headers and server_url and route_path:
        url = f"{server_url}{route_path}"

        all_items = frappe.db.get_all("Item", ["*"])

        # Check if item to manufacture is registered before proceeding
        manufactured_item = frappe.get_value(
            "Item",
            {"name": data["item_name"]},
            ["custom_zra_item_registered_", "name"],
            as_dict=True,
        )

        if not manufactured_item.custom_zra_item_registered_:
            frappe.throw(
                f"Please register item: <b>{manufactured_item.name}</b> first to proceed.",
                title="Integration Error",
            )

        for item in data["items"]:
            for fetched_item in all_items:
                if item["item_code"] == fetched_item.item_code:
                    if fetched_item.custom_zra_item_registered_ == 1:
                        composition_payload = {
                            "itemCd": data["item_code"],
                            "cpstItemCd": fetched_item.custom_zra_item_code,
                            "cpstQty": item["qty"],
                            "regrId": split_user_mail(data["registration_id"]),
                            "regrNm": data["registration_id"],
                        }
                        common_payload = last_request_less_payload(headers)
                        payload= {**common_payload, **composition_payload}         


                        endpoint_builder.url = url
                        endpoint_builder.payload = payload
                        endpoint_builder.success_callback = partial(on_success_item_composition_submission,
                            document_name=data["name"],
                        )
                        endpoint_builder.error_callback = on_error
                        # endpoint_builder.perform_remote_calls()

                        frappe.enqueue(
                            endpoint_builder.perform_remote_calls,
                            is_async=True,
                            queue="default",
                            timeout=300,
                            job_name=f"{data['name']}_submit_item_composition",
                            doctype="BOM",
                            document_name=data["name"],
                        )

                    else:
                        frappe.throw(
                            f"""
                            Item: <b>{fetched_item.name}</b> is not registered.
                            <b>Ensure ALL Items are registered first to submit this composition</b>""",
                            title="Integration Error",
                        )





@frappe.whitelist()
def make_rrp_item_registration(request_data: str) -> dict | None:
  
    data: dict = json.loads(request_data)
    company_name = data["company_name"]
    headers = build_request_headers(company_name )
    server_url = get_server_url(company_name)
    route_path = get_route_path("SAVE RRP ITEMS")

    if headers and server_url and route_path:
            url = f"{server_url}{route_path}"

            common_payload = last_request_less_payload(headers)

            item_data = {key: value for key, value in data.items() if key not in ["name", "company_name"]}
            item_list = [item_data]
            payload = {**common_payload, "itemList": item_list}

            endpoint_builder.url = url
            endpoint_builder.payload = payload
            endpoint_builder.success_callback = partial(
                on_success_rrp_item_registration, document_name=data.get("name")
            )
            endpoint_builder.error_callback = on_error
            # endpoint_builder.perform_remote_calls()


            frappe.enqueue(
                endpoint_builder.perform_remote_calls,
                is_async=True,
                queue="default",
                timeout=300,
                doctype="Item",
                document_name=data["name"],
                job_name=f"{data['name']}_register_item",
            )









# @frappe.whitelist()
# def perform_zra_item_code_classification_search(request_data: str) -> None:
#     data: dict = json.loads(request_data)
#     company_name = data["company_name"]
#     headers = build_request_headers(company_name)


#     server_url = get_server_url(company_name)

#     # Get route path and last request date
#     route_path, last_req_date = get_route_path("Classification Codes")
#     last_req_date_str = last_req_date.strftime("%Y%m%d%H%M%S")

#     request_date = add_to_date(datetime.now(), years=-1).strftime("%Y%m%d%H%M%S")

#     if headers and server_url and route_path:
#         url = f"{server_url}{route_path}"


#         # Include tpin and bhfId in the payload
#         payload = build_common_payload(headers, last_req_date)


#         endpoint_builder.url = url
#         endpoint_builder.payload = payload
#         endpoint_builder.success_callback = on_success_item_classification_search
#         endpoint_builder.error_callback = on_error

#         # endpoint_builder.perform_remote_calls(doctype="ZRA Item Classification", document_name=data.get("name", None))
#         frappe.enqueue(
#                 endpoint_builder.perform_remote_calls,
#                 is_async=True,
#                 queue="default",
#                 timeout=300,
#                 doctype="ZRA Item Classification",
#                 job_name=f"_register_item_calssification",
#             )






@frappe.whitelist()
def perform_purchases_search_on_zra(request_data: str) -> None:
    data: dict = json.loads(request_data)

    print("The data is ", data)
    company_name = data["company_name"]
    headers = build_request_headers(company_name)
    server_url = get_server_url(company_name)
    route_path, last_req_date = get_route_path_with_last_req_date("GET PURCHASES")
    if headers and server_url and route_path:
        request_date = last_req_date.strftime("%Y%m%d%H%M%S")
        url = f"{server_url}{route_path}"

        payload = build_common_payload(headers, last_req_date)


        endpoint_builder.url = url
        endpoint_builder.payload = payload
        endpoint_builder.success_callback = on_succesfull_purchase_search_zra
        endpoint_builder.error_callback = on_error
        endpoint_builder.perform_remote_calls( 
            doctype="Purchase Invoice",
        )





@frappe.whitelist()
def perform_sales_invoice_registration(request_data: str) -> dict | None:
    data: dict = json.loads(request_data)
    company_name = data["company_name"]
    headers = build_request_headers(company_name)
    server_url = get_server_url(company_name)
    route_path, last_req_date = get_route_path("SAVE SALES")

    if headers and server_url and route_path:
        url = f"{server_url}{route_path}"

        # Common payload with tpin and bhfId from headers
        common_payload = last_request_less_payload(headers)

        # Merge common payload and request data
        payload = {**common_payload, **data}
        # Fetch additional required data for callback
        invoice_type = "Sales Invoice"  # Example: replace with appropriate DocType if different
        document_name = data["name"]
        invoice_number = data.get("cisInvcNo", "")
        tpin = data.get("custTpin", "")

        endpoint_builder.url = url
        endpoint_builder.payload = payload
        endpoint_builder.success_callback = partial(
            invoice_type=invoice_type,
            document_name=document_name,
            company_name=company_name,
            invoice_number=invoice_number,
            tpin=tpin,
        )
        endpoint_builder.error_callback = on_error

        endpoint_builder.perform_remote_calls()



        

@frappe.whitelist()
def submit_bulk_sales_invoices(docs_list: str) -> None:


    data = json.loads(docs_list)
    all_sales_invoices = frappe.db.get_all(
        "Sales Invoice", {"docstatus": 1, "custom_has_it_been_successfully_submitted": 0}, ["name"]
    )

    for record in data:
        for invoice in all_sales_invoices:
            if record == invoice.name:
                doc = frappe.get_doc("Sales Invoice", record)
                on_submit(doc, method=None)






@frappe.whitelist()
def save_stock_inventory(request_data: str) -> None:
    data: dict = json.loads(request_data)
    print("The request data is ",request_data)

    company_name = frappe.defaults.get_user_default("Company")

    headers = build_request_headers(company_name)
    server_url = get_server_url(company_name)
    route_path = get_route_path("SAVE STOCK MASTER")
    # frappe.throw(str(route_path))

    if headers and server_url and route_path:
        url = f"{server_url}{route_path}"


        common_payload = last_request_less_payload(headers)

        stock_items = []
        if "items" in data and isinstance(data["items"], list):
            for item in data["items"]:
                stock_items.append({
                    "itemCd": item.get("item_code", ""),
                    "rsdQty": get_stock_balance(item.get("item", ""))
                })
        else:
            stock_items.append({
                "itemCd": data.get("item_code", ""),
                "rsdQty": get_stock_balance(data.get("item", ""))
            })

        payload = {
            **common_payload,
            "regrId": split_user_mail(data.get("owner", "")),
            "regrNm": data.get("owner", ""),
            "modrId": split_user_mail(data.get("owner", "")),
            "modrNm": data.get("owner", ""),
            "stockItemList": stock_items  
        }


        endpoint_builder.url = url
        endpoint_builder.payload = payload
        endpoint_builder.success_callback = partial(
            on_succesful_inventory_submission, document_name=data["name"]
        )
        endpoint_builder.error_callback = on_error



        frappe.enqueue(
            endpoint_builder.perform_remote_calls,
            is_async=True,
            queue="default",
            timeout=300,
            job_name=f"{data['name']}_submit_inventory",
            doctype="Stock Ledger Entry",
            document_name=data["name"],
        )








@frappe.whitelist()
def bulk_register_item(docs_list: str) -> None:
    data = json.loads(docs_list)
    all_items = frappe.db.get_all("Item", {"custom_zra_item_registered_": 0}, ["name"])
    for record in data:
        for item in all_items:
            if record == item.name:
                process_single_item(record)
                # frappe.throw(str(all_items))


@frappe.whitelist()
def bulk_register_item(docs_list: str, is_rrp: bool = False) -> None:
    """
    Bulk registers items, supporting both normal and RRP item registration.

    Args:
        docs_list (str): JSON list of item names to be registered.
        is_rrp (bool): If True, register items as RRP items; otherwise, register as normal items.
    """
    data = json.loads(docs_list)
    all_items = frappe.db.get_all("Item", {"custom_zra_item_registered_": 0}, ["name"])
    
    for record in data:
        for item in all_items:
            if record == item.name:
                process_single_item(record, is_rrp=is_rrp)


@frappe.whitelist()
def process_single_item(record: str, is_rrp: bool = False) -> None:
    """
    Process a single item for registration, determining automatically if it's an RRP item.
    
    Args:
        record (str): Name of the item to process.
    """
    item = frappe.get_doc("Item", record, for_update=False)
    
    # Automatically determine if it's an RRP item
    is_rrp = item.get("custom_has_a_recommended_retail_price_rrp_", False)
    rrp_price = item.get("custom_recommended_retail_price")


    valuation_rate = item.valuation_rate if item.valuation_rate is not None else 0

    request_data = {
        "name": item.name,
        "company_name": frappe.defaults.get_user_default("Company"),
        "itemCd": item.custom_zra_item_code,
        "itemClsCd": item.custom_zra_item_classification_code,
        "itemTyCd": item.custom_product_code,
        "itemNm": item.item_name,
        "temStdNm": None,
        "orgnNatCd": item.custom_zra_country_origin_code,
        "pkgUnitCd": item.custom_zra_packaging_unit_code,
        "qtyUnitCd": item.custom_zra_unit_quantity_code,
        "taxTyCd": item.get("custom_zra_tax_type", "B"),
        "btchNo": None,
        "bcd": None,
        "dftPrc": round(valuation_rate, 2),
        "grpPrcL1": None,
        "grpPrcL2": None,
        "grpPrcL3": None,
        "grpPrcL4": None,
        "grpPrcL5": None,
        "addInfo": None,
        "sftyQty": None,
        "isrcAplcbYn": "Y",
        "useYn": "Y",
        "regrId": split_user_mail(item.owner),
        "regrNm": item.owner,
        "modrId": split_user_mail(item.modified_by),
        "modrNm": item.modified_by,
    }

    if is_rrp:
        request_data["rrp"] = rrp_price

    if is_rrp:
        make_rrp_item_registration(request_data=json.dumps(request_data))
    else:
        make_zra_item_registration(request_data=json.dumps(request_data))



