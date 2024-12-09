from ..utilities import EndpointConstructor
import frappe
import json
import datetime
from frappe.utils.dateutils import add_to_date

from .remote_response_handler import notices_search_on_success,on_error
from .. utilities import (build_request_headers,
                        fetch_server_url,
                        get_route_path,
                        make_get_request,
                        make_post_request,
                        )






endpoint_builder = EndpointConstructor()


@frappe.whitelist()
def search_branch_request(request_data: str) -> None:
    data: dict = json.loads(request_data)

    company_name = data["company_name"]

    headers = build_headers(company_name)
    server_url = get_server_url(company_name)
    route_path, last_request_date = get_route_path("BhfSearchReq")

    if headers and server_url and route_path:
        url = f"{server_url}{route_path}"

        request_date = last_request_date.strftime("%Y%m%d%H%M%S")

        payload = {"lastReqDt": "20240101000000"}

        endpoints_builder.headers = headers
        endpoints_builder.url = url
        endpoints_builder.payload = payload
        endpoints_builder.success_callback = search_branch_request_on_success
        endpoints_builder.error_callback = on_error

        endpoints_builder.make_remote_call(
            doctype="Branch",
        )


@frappe.whitelist()
def perform_notice_search(request_data: str) -> None:
    data: dict = json.loads(request_data)

    company_name = data["company_name"]

    headers = build_request_headers(company_name)
    server_url = fetch_server_url(company_name)

    route_path, last_request_date = get_route_path("NoticeSearchReq")
    request_date = add_to_date(datetime.now(), years=-1).strftime("%Y%m%d%H%M%S")

    if headers and server_url and route_path:
        url = f"{server_url}{route_path}"
        payload = {"lastReqDt": request_date}

        endpoint_builder.headers = headers
        endpoint_builder.url = url
        endpoint_builder.payload = payload
        endpoint_builder.success_callback = notices_search_on_success
        endpoint_builder.error_callback = on_error

        endpoint_builder.make_remote_call(
            doctype=SETTINGS_DOCTYPE_NAME, document_name=data.get("name", None)
        )

