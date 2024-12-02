# Imports
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
        


async def send_initialization_request(tpin: str, bhf_id: str, dvc_srl_no: str):
    # Get environment settings from the ZRA Smart Invoice Settings DocType
    settings = frappe.get_single("ZRA Smart Invoice Settings")
    
    if settings.sandbox_test_environment_:  # Sandbox or test environment
        url = 'https://sandbox.zra.org/initializer/selectInitInfo'
    elif settings.production_environment_:  # Production environment
        url = 'https://production.zra.org/initializer/selectInitInfo'
    else:
        frappe.throw("Please select either Sandbox or Production environment in the ZRA settings.")
    
    """ Sends the initialization request to ZRA's API """

    headers = {
        "Content-Type": "application/json",
    }
    data = {
        "tpin": tpin,
        "bhfId": bhf_id,
        "dvcSrlNo": dvc_srl_no
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=data, headers=headers) as response:
            if response.status != 200:
                frappe.throw(_("Error communicating with ZRA API"))
            result = await response.json()
            if result['resultCd'] != '000':
                frappe.throw(_("Error: {0}").format(result['resultMsg']))
            return result



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
