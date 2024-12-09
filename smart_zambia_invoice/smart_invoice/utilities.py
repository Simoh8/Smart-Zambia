import re
import frappe
import aiohttp
import qrcode
import asyncio

from base64 import b64encode
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


def get_route_path(
    search_field:str,
    routes_table_doctype: str
      ="ZRA VSDC Routes", 
 ) ->tuple[str,str] | None:
    
    query =f"""
    SELECT
        path,
        last_request_date
    FROM `tab{routes_table_doctype}`
    WHERE url_path_function LIKE %s
    AND parent LIKE %s
    LIMIT 1
    """
    results = frappe.db.sql(query, as_dict=True)

    if results:
        return results[0]["path"], results[0]["last_request_date"]

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
        


  
def fetch_server_url( company_name:str, branch_id: str ="00") -> dict[str,str] | None:
    settings = get_zra_settings(company_name,branch_id=branch_id)

    if settings:
        headers ={
            "tpin":settings.get("tpin"),
            "bhfid":settings.get("bhfid"),
            "cmckey":settings.get("communication_key"),
            "Content-Type": "applications/json"
        }

def get_document_series(document: Document) -> int | None:
    split_invoive_name= document.name.split("-")

    if len(split_invoive_name) ==4:
        return int(split_invoive_name[-1])
    if len(split_invoive_name) ==5:
        return int(split_invoive_name[-2])



def update_last_request_date(
    response_datetime: str,
    route: str,
    routes_table: str ,
) -> None:
    doc = frappe.get_doc(
        routes_table,
        {"url_path": route},
        ["*"],
    )

    doc.last_request_date = make_datetime_from_string(
        response_datetime, "%Y%m%d%H%M%S"
    )

    doc.save()
    frappe.db.commit()


    
def get_current_environment_state(
    environment_identifier_doctype: str = "ZRA Smart Invoice Settings",
) -> str:
    """Fetches the Environment Identifier from the relevant doctype.

    Args:
        environment_identifier_doctype (str, optional): The doctype containing environment information.
        Defaults to "Environment Specification".

    Returns:
        str: The environment identifier. Either "Sandbox" or "Production".
    """
    environment = frappe.db.get_single_value(
        environment_identifier_doctype, "environment"
    )

    return environment
   
def add_file_info(data: str) -> str:
    """Add info about the file type and encoding.

    This is required so the browser can make sense of the data."""
    return f"data:image/png;base64, {data}"

def bytes_to_base64_string(data: bytes) -> str:
    """Convert bytes to a base64 encoded string."""
    return b64encode(data).decode("utf-8")


@frappe.whitelist()
def initialize_device_sync(settings_doc_name):
    """
    Wrapper to call the asynchronous initialize_device function synchronously.
    """
    try:
        # Run the asynchronous device initialization function synchronously
        result = asyncio.run(initialize_device(settings_doc_name))
        
        # Assuming the result has a "resultCd" or something similar for success/failure indication
        if result.get("resultCd") == "902":  # Check if the device initialization was successful (902 indicates success)
            return {"success": False, "message": result.get("resultMsg", "This device is installed.")}

        return {"success": True, "message": "Device initialization Failed."}

    except frappe.exceptions.ValidationError as ve:
        frappe.log_error(frappe.get_traceback(), "Device Initialization Error - Validation Error")
        return {"success": False, "message": f"Validation error occurred: {str(ve)}"}

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Device Initialization Error")
        return {"success": False, "message": f"An unexpected error occurred: {str(e)}"}


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
            print("The response is ", response)
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
                    frappe.throw(result.get("resultMsg", "The device is invalid."))

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




def calculate_tax(doc: "Document") -> None:
    """Calculate tax for each item in the document based on item-level or document-level tax template."""
    for item in doc.items:
        tax: float = 0
        tax_rate: float | None = None
        
        # Check if the item has its own Item Tax Template
        if item.item_tax_template:
            tax_rate = get_item_tax_rate(item.item_tax_template)
        else:
            continue
        
        # Calculate tax if we have a valid tax rate
        if tax_rate is not None:
            tax = item.net_amount * tax_rate / 100
        
        # Set the custom tax fields in the item
        item.custom_tax_amount = tax
        item.custom_tax_rate = tax_rate if tax_rate else 0

def get_item_tax_rate(item_tax_template: str) -> float | None:
    """Fetch the tax rate from the Item Tax Template."""
    tax_template = frappe.get_doc("Item Tax Template", item_tax_template)
    if tax_template.taxes:
        return tax_template.taxes[0].tax_rate
    return None

'''Uncomment this function if you need document-level tax rate calculation in the future
A classic example usecase is Apex tevin typecase where the tax rate is fetched from the document's Sales Taxes and Charges Template
'''
# def get_doc_tax_rate(doc_tax_template: str) -> float | None:
#     """Fetch the tax rate from the document's Sales Taxes and Charges Template."""
#     tax_template = frappe.get_doc("Sales Taxes and Charges Template", doc_tax_template)
#     if tax_template.taxes:
#         return tax_template.taxes[0].rate
#     return None



def before_save_(doc: "Document", method: str | None = None) -> None:
    calculate_tax(doc)

def get_invoice_number(invoice_name):
    """
    Extracts the numeric portion from the invoice naming series.
    
    Args:
        invoice_name (str): The name of the Sales Invoice document (e.g., 'eTIMS-INV-00-00001').

    Returns:
        int: The extracted invoice number.
    """
    parts = invoice_name.split('-')
    if len(parts) >= 3:
        return int(parts[-1])
    else:
        raise ValueError("Invoice name format is incorrect")

'''For cancelled and amended invoices'''


def build_request_headers(company_name: str, branch_id: str = "00") -> dict[str, str] | None:
    settings = get_curr_env_etims_settings(company_name, branch_id=branch_id)

    if settings:
        headers = {
            "tin": settings.get("tin"),
            "bhfId": settings.get("bhfid"),
            "cmcKey": settings.get("communication_key"),
            "Content-Type": "application/json"
        }

        return headers


def clean_invc_no(invoice_name):
    if "-" in invoice_name:
        invoice_name = "-".join(invoice_name.split("-")[:-1])
    return invoice_name

def get_taxation_types(doc):
    taxation_totals = {}

    # Loop through each item in the Sales Invoice
    for item in doc.items:
        taxation_type = item.custom_taxation_type
        taxable_amount = item.net_amount  
        tax_amount = item.custom_tax_amount  

        # Fetch the tax rate for the current taxation type from the specified doctype
        tax_rate = frappe.db.get_value("Navari KRA eTims Taxation Type", taxation_type, "userdfncd1")
        # If the taxation type already exists in the dictionary, update the totals
        if taxation_type in taxation_totals:
            taxation_totals[taxation_type]["taxable_amount"] += taxable_amount
            taxation_totals[taxation_type]["tax_amount"] += tax_amount

        else:
            taxation_totals[taxation_type] = {
                "tax_rate": tax_rate,
                "tax_amount": tax_amount,
                "taxable_amount": taxable_amount
            }


    return taxation_totals