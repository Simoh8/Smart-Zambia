import re
import frappe
import aiohttp
import qrcode
import asyncio

from base64 import b64decode
from datetime import datetime, timedelta
from io import BytesIO
from typing import Literal
from aiohttp import ClientTimeout
from frappe.model.document import Document
from frappe.utils import cint

from erpnext.controllers.taxes_and_totals import get_itemised_tax_breakup_data


# -------------------------------
# Utility Functions
# -------------------------------

def is_valid_tpin(tpin: str) -> bool:
    """Validates if the string is a valid TPIN pattern (10 digits)."""
    pattern = r"^\d{10}$"
    return bool(re.match(pattern, tpin))


def is_url_valid(url: str) -> bool:
    """Checks if the entered URL is valid."""
    pattern = r"^(https?|ftp):\/\/[^\s/$.?#].[^\s]*"
    return bool(re.match(pattern, url))


def make_datetime_from_string(date_string: str, format: str = "%Y-%m-%d %H:%M:%S") -> datetime:
    """Converts a datetime string to a datetime object."""
    return datetime.strptime(date_string, format)


def get_docment_series_number(document: Document) -> int | None:
    """Extracts the series number from the document name."""
    split_invoice_name = document.name.split("-")
    if len(split_invoice_name) == 4:
        return int(split_invoice_name[-1])
    if len(split_invoice_name) == 5:
        return int(split_invoice_name[-2])
    return None


# -------------------------------
# Async HTTP Requests
# -------------------------------

async def make_get_request(url: str) -> dict[str, str] | str:
    """Makes a GET request to the specified URL."""
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.content_type.startswith("text"):
                return await response.text()
            return await response.json()


async def make_post_request(
        url: str,
        data: dict[str, str] | None = None,
        headers: dict[str, str | int] | None = None) -> dict[str, str | dict]:
    """Makes a POST request with optional data and headers."""
    async with aiohttp.ClientSession(timeout=ClientTimeout(1800)) as session:
        async with session.post(url, json=data, headers=headers) as response:
            return await response.json()
  

@frappe.whitelist()
def initialize_device_sync(settings_doc_name):
    """
    Wrapper to call the asynchronous initialize_device function synchronously.
    """
    try:
        return asyncio.run(initialize_device(settings_doc_name))
    except frappe.ValidationError as e:
        frappe.log_error(f"Validation Error: {str(e)}", "Device Initialization Error")
        raise
    except Exception as e:
        frappe.log_error(f"Unexpected Error: {str(e)}", "Device Initialization Error")
        frappe.throw("An unexpected error occurred during device initialization. Please check the logs.")


async def initialize_device(settings_doc_name):
    """
    Makes an API call to ZRA's initialization endpoint.
    """
    # Ensure _realtime_log is initialized
    if not hasattr(frappe.local, "_realtime_log"):
        frappe.local._realtime_log = []

    # Fetch the ZRA Settings document
    settings = frappe.get_doc("ZRA Smart Invoice Settings", settings_doc_name)

    # Prepare the data for the request
    data = {
        "tpin": settings.company_tpin,
        "bhfId": settings.branch_id,
        "dvcSrlNo": settings.vsdc_device_serial_number
    }

    # Log debugging information
    frappe.log_error(f"Data being sent to the API: {data}", "Device Initialization Debug")

    # Determine the server URL
    url = f"{settings.server_url}/initializer/selectInitInfo"
    frappe.log_error(f"API Endpoint URL: {url}", "Device Initialization Debug")

    async with aiohttp.ClientSession(timeout=ClientTimeout(total=30)) as session:
        async with session.post(url, json=data) as response:
            if response.status == 200:
                result = await response.json()
                frappe.log_error(f"API Response: {result}", "Device Initialization Debug")

                # Handle response codes
                if result.get("resultCd") == "902":  # Device Installed (Success)
                    if result.get("data"):
                        settings.update({
                            "zra_sales_control_unit_id": result["data"].get("sdcId", ""),
                            "mrc_number": result["data"].get("mrcNo", "")
                        })
                        settings.save()
                        return {"message": "Initialization Successful", "data": result}
                    else:
                        return {"message": result.get("resultMsg", "Missing result message.")}

                elif result.get("resultCd") == "901":  # Invalid Device (Failure)
                    frappe.throw(result.get("resultMsg", "Unknown error occurred."))

                else:
                    frappe.throw(result.get("resultMsg", "Unknown result code."))

            else:
                error_text = await response.text()
                frappe.throw(f"Failed to initialize device. HTTP Status: {response.status}. Response: {error_text}")


            
# -------------------------------
# QR Code Generation
# -------------------------------

def generate_qr_code(data: str) -> BytesIO:
    """Generates a QR code for the provided data and returns it as an image."""
    img = qrcode.make(data)
    byte_io = BytesIO()
    img.save(byte_io, 'PNG')
    byte_io.seek(0)
    return byte_io


# -------------------------------
# ZRA Settings
# -------------------------------

def get_zra_settings():
    """Fetches the ZRA Smart Invoice settings from the settings DocType."""
    try:
        zra_settings = frappe.get_single("ZRA Smart Invoice Settings")
        return zra_settings
    except frappe.DoesNotExistError:
        frappe.throw("ZRA Smart Invoice Settings not found. Please configure it.")
    except Exception as e:
        frappe.log_error(f"Error fetching ZRA settings: {str(e)}", "ZRA Settings Error")
        raise



