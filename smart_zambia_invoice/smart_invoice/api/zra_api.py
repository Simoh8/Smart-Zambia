import asyncio
from functools import partial
import aiohttp
import frappe
import json
import datetime
from datetime import datetime

from frappe.utils.dateutils import add_to_date
from .api_builder import EndpointConstructor

from .remote_response_handler import notices_search_on_success,item_composition_submission_succes,on_error,fetch_branch_request_on_success
from .. utilities import (build_request_headers,get_route_path,make_get_request,make_post_request,split_user_mail,get_server_url)



endpoint_builder = EndpointConstructor()


@frappe.whitelist()
def search_branch_request(request_data: str) -> None:
    data: dict = json.loads(request_data)

    company_name = data["company_name"]

    headers = build_request_headers(company_name)
    server_url = get_server_url(company_name)
    route_path, last_request_date = get_route_path("BhfSearchReq")

    if headers and server_url and route_path:
        url = f"{server_url}{route_path}"

        request_date = last_request_date.strftime("%Y%m%d%H%M%S")

        payload = {"lastReqDt": "20240101000000"}

        endpoint_builder.headers = headers
        endpoint_builder.url = url
        endpoint_builder.payload = payload
        endpoint_builder.success_callback = fetch_branch_request_on_success
        endpoint_builder.error_callback = on_error

        endpoint_builder.make_remote_call(
            doctype="Branch",
        )


@frappe.whitelist()
def perform_zra_notice_search(request_data: str) -> None:
    data: dict = json.loads(request_data)

    company_name = data["company_name"]

    headers = build_request_headers(company_name)
    server_url = get_server_url(company_name)

    # Get route path and last request date
    route_path, last_request_date = get_route_path("Notices")
    request_date = add_to_date(datetime.now(), years=-1).strftime("%Y%m%d%H%M%S")
    print("The headers are ",headers)

    if headers and server_url and route_path:
        url = f"{server_url}{route_path}"
        print("The url is ", url)
        payload = {"lastReqDt": request_date}

        endpoint_builder.headers = headers
        endpoint_builder.url = url
        endpoint_builder.payload = payload
        endpoint_builder.success_callback = notices_search_on_success
        endpoint_builder.error_callback = on_error

        endpoint_builder.make_remote_call(
            doctype="ZRA Smart Invoice Settings", document_name=data.get("name", None)
        )

    # route_result = get_route_path("Notices")
    # if not route_result:
    #     frappe.throw(("No route found for the specified path function."))

    # route_path, last_request_date = route_result

    # request_date = add_to_date(datetime.now(), years=-1).strftime("%Y%m%d%H%M%S")

    # if headers and server_url and route_path:
    #     url = f"{server_url}{route_path}"
    #     payload = {"lastReqDt": request_date}
    #     print("The url is ",url ,"and the paylod has ",payload)

    #     endpoint_builder.headers = headers
    #     endpoint_builder.url = url
    #     endpoint_builder.payload = payload
    #     endpoint_builder.success_callback = notices_search_on_success
    #     endpoint_builder.error_callback = on_error

    #     endpoint_builder.perform_remote_calls(
    #         doctype="ZRA Smart Invoice Settings", document_name=data.get("name", None)
    #     )







@frappe.whitelist()
def ping_zra_server(request_data: str) -> None:
    data = json.loads(request_data)
    url = data.get("server_url")
    print("The URL is", url)

    try:
        response = asyncio.run(make_get_request(url))
        print("The response data is here:", response)

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
                            endpoint_builder.make_remote_call,
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
