import asyncio
from functools import partial
import aiohttp
import frappe
import json
import datetime
from datetime import datetime
from frappe.utils.dateutils import add_to_date
from .api_builder import EndpointConstructor

from .remote_response_handler import  on_success_customer_search, on_success_item_composition_submission, on_success_item_registration, on_success_customer_insurance_details_submission,on_success_customer_branch_details_submission,notices_search_on_success,item_composition_submission_succes,on_error,fetch_branch_request_on_success, on_imported_items_search_success, on_success_user_details_submission, on_successful_fetch_latest_items
from .. utilities import (build_request_headers,get_route_path, last_request_less_payload,make_get_request,make_post_request,split_user_mail,get_server_url,build_common_payload, truncate_user_id)

endpoint_builder = EndpointConstructor()


@frappe.whitelist()
def make_branch_request(request_data: str) -> None:
    data: dict = json.loads(request_data)

    company_name = data["company_name"]

    headers = build_request_headers(company_name)
    
    server_url = get_server_url(company_name)
    route_path, last_req_date = get_route_path("GET BRANCHES")

    if headers and server_url and route_path:
        url = f"{server_url}{route_path}"

        request_date = last_req_date.strftime("%Y%m%d%H%M%S")

        payload = build_common_payload(headers, last_req_date)

        endpoint_builder.headers = headers
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




        
# searching for the new notices available from zra
@frappe.whitelist()
def perform_zra_notice_search(request_data: str) -> None:
    data: dict = json.loads(request_data)
    company_name = data["company_name"]
    headers = build_request_headers(company_name)


    server_url = get_server_url(company_name)

    # Get route path and last request date
    route_path, last_req_date = get_route_path("Notices Fetching")
    last_req_date_str = last_req_date.strftime("%Y%m%d%H%M%S")

    request_date = add_to_date(datetime.now(), years=-1).strftime("%Y%m%d%H%M%S")

    if headers and server_url and route_path:
        url = f"{server_url}{route_path}"

        # Include tpin and bhfId in the payload
        payload = build_common_payload(headers, last_req_date)


        endpoint_builder.headers = headers
        endpoint_builder.url = url
        endpoint_builder.payload = payload
        endpoint_builder.success_callback = notices_search_on_success
        endpoint_builder.error_callback = on_error

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
    route_path, last_request_date = get_route_path("GET CUSTOMERS")

    if headers and server_url and route_path:
        url = f"{server_url}{route_path}"
        payload = {"custmTpin": data["tax_id"]}

        endpoint_builder.headers = headers
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
    route_path, last_req_date = get_route_path("SAVE BRANCH CUSTOMER")


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
        endpoint_builder.headers = headers
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

    route_path, last_req_date = get_route_path("GET IMPORTS")


    if headers and server_url and route_path:
        url = f"{server_url}{route_path}"
        common_payload = build_common_payload(headers, last_req_date)

        payload = {**common_payload, "dclRefNum": "CX1100096839"}


        endpoint_builder.headers = headers
        endpoint_builder.url = url
        endpoint_builder.payload = payload
        endpoint_builder.success_callback = on_imported_items_search_success
        endpoint_builder.error_callback = on_error

        endpoint_builder.perform_remote_calls()
        



# Not applicable to the zabian ZRA API for now but its working

@frappe.whitelist()
def send_customer_insurance_details(request_data: str) -> None:
    data: dict = json.loads(request_data)

    company_name = data["company_name"]

    headers = build_request_headers(company_name)
    server_url = get_server_url(company_name)
    route_path, last_request_date = get_route_path("BhfInsuranceSaveReq")

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

        endpoint_builder.headers = headers
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
    route_path, last_request_date = get_route_path("SAVE BRANCH USER")

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


        endpoint_builder.headers = headers
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
    route_path, last_req_date = get_route_path("GET CUSTOMERS")

    if headers and server_url and route_path:
        url = f"{server_url}{route_path}"

        common_payload = last_request_less_payload(headers)

        custom_payload = {"custmTpin": data["tax_id"]}
        payload= {**common_payload, **custom_payload}         

        endpoint_builder.headers = headers
        endpoint_builder.url = url
        endpoint_builder.payload = payload
        endpoint_builder.success_callback = partial(on_success_customer_search, document_name=data["name"])
        endpoint_builder.error_callback = on_error

        endpoint_builder.perform_remote_calls()

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
    route_path, last_req_date = get_route_path("SAVE ITEM")

    if headers and server_url and route_path:
            url = f"{server_url}{route_path}"

            # Build the common payload fields
            common_payload = last_request_less_payload(headers)

            # Exclude `name` and `company_name` from `data`
            data_to_send = {key: value for key, value in data.items() if key not in ["name", "company_name"]}
            payload = {**common_payload, **data_to_send}

            endpoint_builder.headers = headers
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
def fetch_latest_items(request_data: str, frm: dict = None) -> None:  # Default to None if frm is not passed
    data: dict = json.loads(request_data)

    company_name = data["company_name"]
    headers = build_request_headers(company_name)
    server_url = get_server_url(company_name)
    route_path, last_req_date = get_route_path("GET ITEMS")

    if headers and server_url and route_path:
        url = f"{server_url}{route_path}"

        request_date = last_req_date.strftime("%Y%m%d%H%M%S")
        payload = build_common_payload(headers, last_req_date)

        endpoint_builder.headers = headers
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
    print("headers are:", headers)
    server_url = get_server_url(company_name)
    route_path, last_req_date = get_route_path("SAVE ITEM COMPOSITION")

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


                        endpoint_builder.headers = headers
                        endpoint_builder.url = url
                        endpoint_builder.payload = payload
                        endpoint_builder.success_callback = partial(on_success_item_composition_submission,
                            document_name=data["name"],
                        )
                        endpoint_builder.error_callback = on_error
                        endpoint_builder.perform_remote_calls()

                        # frappe.enqueue(
                        #     endpoint_builder.perform_remote_calls,
                        #     is_async=True,
                        #     queue="default",
                        #     timeout=300,
                        #     job_name=f"{data['name']}_submit_item_composition",
                        #     doctype="BOM",
                        #     document_name=data["name"],
                        # )

                    else:
                        frappe.throw(
                            f"""
                            Item: <b>{fetched_item.name}</b> is not registered.
                            <b>Ensure ALL Items are registered first to submit this composition</b>""",
                            title="Integration Error",
                        )

