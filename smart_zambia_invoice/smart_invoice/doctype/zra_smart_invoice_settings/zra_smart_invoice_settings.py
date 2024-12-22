# Copyright (c) 2024, simon muturi and contributors
# For license information, please see license.txt

import asyncio
import frappe
import _asyncio
import aiohttp
import frappe.defaults
from ...error_handlers import handle_errors
from ...zra_logger import zra_vsdc_logger
from frappe.integrations.utils import create_request_log
from frappe.model.document import Document
from ... api.api_builder import update_integration_request

from ...utilities import (get_route_path,is_valid_tpin,is_valid_tpin,make_post_request,update_last_request_date)


class ZRASmartInvoiceSettings(Document):

    def __init__(self, *args, **kwargs) -> None:
            super().__init__(*args, **kwargs)
            self.error = None
            self.message = None
            self.error_title = None

    def before_insert(self) -> None:
            """Before Insertion Hook"""
            route_path, last_request_date = get_route_path("device initialization")
            
            if route_path:
                url = f"{self.server_url}{route_path}"
                payload = {
                    "tpin": self.company_tpin,
                    "bhfId": self.branch_id,
                    "dvcSrlNo": self.vsdc_device_serial_number,
                }
                print("The Payload is ", payload)

                integration_request = create_request_log(
                    data=payload,
                    service_name="zra vsdc",
                    url=url,
                    request_headers=None,
                    is_remote_request=True,
                )

                try:
                    response = asyncio.run(make_post_request(url, payload))
                    print("The response is ", response)

                    # Validate response structure
                    if not response or "resultCd" not in response:
                        self.error_title = "Unexpected API Response"
                        error_message = f"Response from {url}: {response}"
                        zra_vsdc_logger.error(error_message, exc_info=True)
                        frappe.log_error(
                            title=self.error_title,
                            message=error_message,
                            reference_doctype="ZRA Smart Invoice Settings",
                        )
                        update_integration_request(
                            integration_request.name,
                            "Failed",
                            output=None,
                            error=self.error_title,
                        )
                        frappe.throw("Server Error. Check logs.")

                    # Process the response
                    if response["resultCd"] == "000":
                        info = response.get("data", {}).get("info", {})
                        self.communication_key = info.get("cmcKey")
                        self.sales_control_unit_id = info.get("sdcId")

                        update_last_request_date(response.get("resultDt"), route_path)
                        update_integration_request(
                            integration_request.name,
                            "Completed",
                            output=f'{response.get("resultMsg", "Success")}, {response["resultCd"]}',
                            error=None,
                        )
                    else:
                        error_message = f'{response.get("resultMsg", "Error")}, {response["resultCd"]}'
                        update_integration_request(
                            integration_request.name,
                            "Failed",
                            output=None,
                            error=error_message,
                        )
                        handle_errors(response, route_path, self.name, "ZRA Smart Invoice Settings")

                except aiohttp.client_exceptions.ClientConnectorError as error:
                    self.log_and_throw_error(
                        integration_request,
                        "Connection failed during initialisation",
                        error,
                    )

                except aiohttp.client_exceptions.ClientOSError as error:
                    self.log_and_throw_error(
                        integration_request,
                        "Connection reset by peer",
                        error,
                    )

                except asyncio.exceptions.TimeoutError as error:
                    self.log_and_throw_error(
                        integration_request,
                        "Timeout Error",
                        error,
                    )

            if self.autocreate_branch_dimension and self.is_active:
                if frappe.db.exists("Accounting Dimension", "Branch", cache=False):
                    return

                company = frappe.defaults.get_user_default("Company")
                dimension = frappe.new_doc("Accounting Dimension")
                dimension.document_type = "Branch"
                dimension.set("dimension_defaults", [])
                dimension.append(
                    "dimension_defaults",
                    {
                        "company": company,
                        "mandatory_for_pl": 1,
                    },
                )
                dimension.save()


    def log_and_throw_error(self, integration_request, error_title, error):
            """Log and throw errors"""
            self.error_title = error_title
            zra_vsdc_logger.exception(error, exc_info=True)
            frappe.log_error(
                title=self.error_title,
                message=str(error),
                reference_doctype="ZRA Smart Invoice Settings",
            )
            update_integration_request(
                integration_request.name,
                "Failed",
                output=None,
                error=self.error_title,
            )
            frappe.throw(self.error_title, str(error))
