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

from ...utilities import (get_route_path,is_url_valid,is_valid_tpin,make_post_request,update_last_request_date)


class ZRASmartInvoiceSettings(Document):
	pass



def before_insert(self) -> None:
        """Before Insertion Hook"""
        route_path, last_request_date = get_route_path("evice initialization")
		
        if route_path:
            print(route_path,"hello world ")
            url = f"{self.server_url}{route_path}"
            payload = {
                "tpin": self.company_tpin,
                "bhfId": self.branch_id,
                "dvcSrlNo": self.vsdc_device_serial_number,
            }

            integration_request = create_request_log(
                data=payload,
                service_name="vsdc",
                url=url,
                request_headers=None,
                is_remote_request=True,
            )

            try:
                response = asyncio.run(make_post_request(url, payload))

                if response["resultCd"] == "000":
                    info = response["data"]["info"]

                    self.communication_key = info["cmcKey"]
                    self.sales_control_unit_id = info["sdcId"]

                    update_last_request_date(response["resultDt"], route_path)
                    update_integration_request(
                        integration_request.name,
                        "Completed",
                        output=f'{response["resultMsg"]}, {response["resultCd"]}',
                        error=None,
                    )

                else:
                    update_integration_request(
                        integration_request.name,
                        "Failed",
                        output=None,
                        error=f'{response["resultMsg"]}, {response["resultCd"]}',
                    )
                    handle_errors(
                        response, route_path, self.name, "ZRA Smart Invoice Settings"
                    )

            except aiohttp.client_exceptions.ClientConnectorError as error:
                self.error_title = "Connection failed during initialisation"

                zra_vsdc_logger.exception(error, exc_info=True)
                frappe.log_error(
                    title=self.error_title,
                    message=error,
                    reference_doctype="ZRA Smart Invoice Settings",
                )
                update_integration_request(
                    integration_request.name,
                    "Failed",
                    output=None,
                    error=self.error_title,
                )
                frappe.throw(
                    "Connection failed",
                    error,
                    title=self.error_title,
                )

            except aiohttp.client_exceptions.ClientOSError as error:
                self.error_title = "Connection reset by peer"

                zra_vsdc_logger.exception(error, exc_info=True)
                frappe.log_error(
                    title=self.error_title,
                    message=error,
                    reference_doctype="ZRA Smart Invoice Settings",
                )
                update_integration_request(
                    integration_request.name,
                    "Failed",
                    output=None,
                    error=self.error_title,
                )
                frappe.throw(
                    "Connection reset by peer",
                    error,
                    title=self.error_title,
                )

            except asyncio.exceptions.TimeoutError as error:
                self.error_title = "Timeout Error"

                zra_vsdc_logger.exception(error, exc_info=True)
                frappe.log_error(
                    title=self.error_title,
                    message=error,
                    reference_doctype="ZRA Smart Invoice Settings",
                )
                update_integration_request(
                    integration_request.name,
                    "Failed",
                    output=None,
                    error=self.error_title,
                )
                frappe.throw("Timeout Encountered", error, title=self.error_title)

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
