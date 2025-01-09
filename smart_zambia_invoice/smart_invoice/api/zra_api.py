import asyncio
from functools import partial
import aiohttp
import frappe
import json
import datetime
from datetime import datetime

from frappe.utils.dateutils import add_to_date
from .api_builder import EndpointConstructor

from .remote_response_handler import  on_success_customer_search, on_success_item_registration, on_success_customer_insurance_details_submission,on_success_customer_branch_details_submission,notices_search_on_success,item_composition_submission_succes,on_error,fetch_branch_request_on_success, on_imported_items_search_success, on_success_user_details_submission
from .. utilities import (build_request_headers,get_route_path, last_request_less_payload,make_get_request,make_post_request,split_user_mail,get_server_url,build_common_payload)



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


@frappe.whitelist()
def submit_item_composition(request_data: str) -> None:
    data: dict = json.loads(request_data)

    company_name = data["company_name"]

    headers = build_request_headers(company_name)
    server_url = get_server_url(company_name)
    route_path, last_request_date = get_route_path("SaveItemComposition")

    if headers and server_url and route_path:
        url = f"{server_url}{route_path}"

        all_items = frappe.db.get_all("Item", ["*"])

        # Check if item to manufacture is registered before proceeding
        manufactured_item = frappe.get_value(
            "Item",
            {"name": data["item_name"]},
            ["custom_item_registered", "name"],
            as_dict=True,
        )

        if not manufactured_item.custom_item_registered:
            frappe.throw(
                f"Please register item: <b>{manufactured_item.name}</b> first to proceed.",
                title="Integration Error",
            )

        for item in data["items"]:
            for fetched_item in all_items:
                if item["item_code"] == fetched_item.item_code:
                    if fetched_item.custom_item_registered == 1:
                        payload = {
                            "itemCd": data["item_code"],
                            "cpstItemCd": fetched_item.custom_item_code_etims,
                            "cpstQty": item["qty"],
                            "regrId": split_user_mail(data["registration_id"]),
                            "regrNm": data["registration_id"],
                        }

                        endpoint_builder.headers = headers
                        endpoint_builder.url = url
                        endpoint_builder.payload = payload
                        endpoint_builder.success_callback = partial(
                            item_composition_submission_succes,
                            document_name=data["name"],
                        )
                        endpoint_builder.error_callback = on_error

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
            on_succesful_customer_search, document_name=data["name"]
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
            "adrs": data.get("customer_address", ""),
            "telNo": data.get("customer_phone"),
            "email": data.get("customer_email"),
            "faxNo": "",
            "useYn": "Y",
            "remark": data.get["customer_remarks"],
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

        endpoint_builder.perform_remote_calls()


        # Enqueue the task for asynchronous execution
        # frappe.enqueue(
        #     endpoint_builder.perform_remote_calls,
        #     is_async=True,
        #     queue="default",
        #     timeout=300,
        #     doctype="Customer",
        #     document_name=data["name"],
        #     job_name=f"{data['name']}_submit_customer_branch_details",
        # )





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








# @frappe.whitelist()
# def create_zra_branch_user() -> None:
#     # TODO: Implement auto-creation through background tasks
#     present_users = frappe.db.get_all(
#         "User", {"name": ["not in", ["Administrator", "Guest"]]}, ["name", "email"]
#     )

#     for user in present_users:
#         doc = frappe.new_doc("ZRA Smart Invoice User")

#         doc.system_user = user.email
#         doc.branch_id = frappe.get_value(
#             "Branch", {"custom_branch_code": "00"}, ["name"]
#         )  # Created users are assigned to Branch 00

#         doc.save()

#     frappe.msgprint("Inspect the Branches to make sure they are mapped correctly")



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
            "userId": data["user_id"],
            "userNm": data["full_names"],
            "pwd": "password",  # TODO: Find a fix for this
            "adrs": None,
            "cntc": None,
            "authCd": None,
            "remark": None,
            "useYn": "Y",
            "regrNm": data["registration_id"],
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
        endpoint_builder.perform_remote_calls()

        # frappe.enqueue(
        #     endpoints_builder.make_remote_call,
        #     is_async=True,
        #     queue="default",
        #     timeout=300,
        #     job_name=f"{data['name']}_send_branch_user_information",
        #     doctype=USER_DOCTYPE_NAME,
        #     document_name=data["name"],
        # )







@frappe.whitelist()
def make_item_registration(request_data: str) -> dict | None:
    """
    Registers an item with ZRA by making a remote call.

    Args:
        request_data (str): JSON string containing request data.

    Returns:
        dict | None: None if the function is executed asynchronously, or a result dictionary if needed.
    """
    # Parse incoming data
    data: dict = json.loads(request_data)

    # Extract company name and build headers, server URL, and route path
    company_name = data.pop("company_name")
    headers = build_request_headers(company_name)
    server_url = get_server_url(company_name)
    route_path, last_req_date = get_route_path("SAVE ITEM")

    if headers and server_url and route_path:
        # Construct the full URL
        url = f"{server_url}{route_path}"

        # Build the common payload fields
        common_payload = build_common_payload(headers, last_req_date)

        # Combine the common payload with the specific item data
        payload = {**common_payload, **data}
        

        # Set up the endpoint builder
        endpoint_builder.headers = headers
        endpoint_builder.url = url
        endpoint_builder.payload = payload
        endpoint_builder.success_callback = partial(
            on_success_item_registration, document_name=data["name"]
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

        # frappe.enqueue(
        #     endpoint_builder.perform_remote_calls,
        #     is_async=True,
        #     queue="default",
        #     timeout=300,
        #     doctype="Customer",
        #     document_name=data["name"],
        #     job_name=f"{data['name']}_customer_search",
        # )
