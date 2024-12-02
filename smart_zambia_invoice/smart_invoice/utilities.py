import re
import frappe
import aiohttp
import qrcode
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
async def initialize_device(settings_doc_name):
    """
    Makes an API call to ZRA's initialization endpoint.
    """
    # Fetch the ZRA Settings document
    settings = frappe.get_doc("ZRA Smart Invoice Settings", settings_doc_name)

    # Prepare the data for the request
    data = {
        "tpin": settings.company_tpin,
        "bhfId": settings.branch_id,
        "dvcSrlNo": settings.vsdc_device_serial_number
    }
    print("Data being sent to the API:", data)

    # Determine the server URL (ensure the endpoint is correctly appended)
    url = settings.server_url + "/initializer/selectInitInfo"

    # Make the POST request to the API with a timeout
    async with aiohttp.ClientSession(timeout=ClientTimeout(total=30)) as session:
        try:
            async with session.post(url, json=data) as response:
                # Check if the status code is 200 (success)
                if response.status == 200:
                    result = await response.json()
                    print("API Response:", result)

                    # Handle successful response
                    if result.get("resultCd") == "902":  # Assuming 902 is success
                        settings.update({
                            "zra_sales_control_unit_id": result["data"]["info"].get("sdcId"),
                            "mrc_number": result["data"]["info"].get("mrcNo")
                        })
                        settings.save()

                        # Return success message
                        return {"message": "Initialization Successful", "data": result}
                    else:
                        # If the response code is not the expected success code, raise an error
                        error_message = result.get("errorMessage", "Unknown error occurred.")
                        frappe.throw(f"Initialization failed: {error_message}")
                else:
                    # Handle the error if the HTTP response status is not 200
                    error_text = await response.text()
                    frappe.throw(f"Failed to initialize device. HTTP Status: {response.status}. Response: {error_text}")
        except Exception as e:
            # If there's an exception during the request, log and raise an error
            frappe.log_error(f"Error in device initialization: {str(e)}", "Device Initialization Error")
            frappe.throw(f"An error occurred during device initialization: {str(e)}")

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



