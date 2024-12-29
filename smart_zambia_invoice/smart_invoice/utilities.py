import re
import frappe
import aiohttp
import qrcode
import asyncio

from base64 import b64encode
from datetime import datetime, timedelta
from io import BytesIO
from typing import Literal, Optional, Union
from aiohttp import ClientTimeout
from frappe.model.document import Document
from frappe.utils import cint
from .zra_logger import zra_vsdc_logger



from erpnext.controllers.taxes_and_totals import get_itemised_tax_breakup_data


# -------------------------------
# Utility Functions
# -------------------------------

def is_valid_tpin(tpin: str) -> bool:
    """Validates if the string is a valid TPIN pattern (10 digits)."""
    pattern = r"^\d{10}$"
    return bool(re.match(pattern, tpin))


def before_doc_save_(doc: "Document", method: str | None = None) -> None:
    calculate_tax(doc)


def is_url_valid(url: str) -> bool:
    """Checks if the entered URL is valid."""
    pattern = r"^(https?|ftp):\/\/[^\s/$.?#].[^\s]*"
    return bool(re.match(pattern, url))


def make_datetime_from_string(
    date_string: str, format: str = "%Y-%m-%d %H:%M:%S"
) -> datetime:
    """Builds a Datetime object from string, and format provided

    Args:
        date_string (str): The string to build object from
        format (str, optional): The format of the date_string string. Defaults to "%Y-%m-%d".

    Returns:
        datetime: The datetime object
    """
    date_object = datetime.strptime(date_string, format)

    return date_object

def get_docment_series_number(document: Document) -> int | None:
    """Extracts the series number from the document name."""
    split_invoice_name = document.name.split("-")
    if len(split_invoice_name) == 4:
        return int(split_invoice_name[-1])
    if len(split_invoice_name) == 5:
        return int(split_invoice_name[-2])
    return None


def get_server_url(company_name: str, branch_id: str = "001") -> str | None:
    settings = get_current_env_settings(company_name, branch_id)

    if settings:
        server_url = settings.get("server_url")

        return server_url

    return



def build_request_headers(company_name: str, branch_id: str = "001") -> dict[str, str] | None:
    settings = get_current_env_settings(company_name, branch_id=branch_id)
    print("on the build headers ", settings)

    if settings:
        # current_time = datetime.now().strftime("%Y%m%d%H%M%S")

        headers = {
            "tpin": settings.get("company_tpin"),  # Adjusted to match the key in `settings`
            "bhfId": settings.get("branch_id"), 
            # "companyName": settings.get("company_name"),
            "Content-Type": "application/json"
        }

        return headers

    return None



def get_route_path(
    search_field: str,
    child_doctype: str = "ZRA VSDC Route Table Item"
) -> tuple[str, str] | None:
    """
    Fetch the route path and last request date from the child table based on the search field.

    Args:
        search_field (str): The path function to search for.
        child_doctype (str): The child DocType containing the route data.

    Returns:
        tuple[str, str] | None: The route path and last request date, or None if not found.
    """
    query = f"""
        SELECT
            path AS route_path, 
            last_req_date AS last_request_date
        FROM `tab{child_doctype}`
        WHERE path_function LIKE %s
        LIMIT 1
    """

    results = frappe.db.sql(query, (search_field,), as_dict=True)

    if results:
        return results[0]["route_path"], results[0]["last_request_date"]
    return None

# -------------------------------
# Async HTTP Requests
# -------------------------------

async def make_get_request(url: str) -> aiohttp.ClientResponse:
    """Make an Asynchronous GET Request to the specified URL.

    Args:
        url (str): The URL to request.

    Returns:
        aiohttp.ClientResponse: The response object containing status and content.
    """
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                return response

    except aiohttp.ClientConnectorError:
        return None  # Return None if connection error occurs
    except Exception as e:
        return f"Unexpected error: {str(e)}"



async def make_post_request(
    url: str,
    data: dict[str, str] | None = None,
    headers: dict[str, str | int] | None = None,
) -> dict[str, str | dict]:
    """Make an Asynchronous POST Request to specified URL

    Args:
        url (str): The URL
        data (dict[str, str] | None, optional): Data to send to server. Defaults to None.
        headers (dict[str, str | int] | None, optional): Headers to set. Defaults to None.

    Returns:
        dict: The Server Response
    """
    # TODO: Refactor to a more efficient handling of creation of the session object
    # as described in documentation
    async with aiohttp.ClientSession(timeout=ClientTimeout(1800)) as session:
        # Timeout of 1800 or 30 mins, especially for fetching Item classification
        async with session.post(url, json=data, headers=headers) as response:
            return await response.json()
        
        

def get_document_series(document: Document) -> int | None:
    split_invoive_name= document.name.split("-")

    if len(split_invoive_name) ==4:
        return int(split_invoive_name[-1])
    if len(split_invoive_name) ==5:
        return int(split_invoive_name[-2])





def split_user_mail(email_string: str) -> str:
    """Retrieve portion before @ from an email string"""
    return email_string.split("@")[0]

def update_last_request_date(
    response_datetime: str,
    route: str,
    routes_table: str = "ZRA VSDC Routes",
) -> None:
    try:
        # Fetch the document
        doc = frappe.get_doc(
            routes_table,
            {"url_path": route},
            ["*"],
        )
        
        # Validate and parse the response datetime
        if response_datetime:
            try:
                doc.last_req_date = make_datetime_from_string(
                    response_datetime, "%Y%m%d%H%M%S"
                )
            except ValueError:
                frappe.log_error(
                    f"Invalid date format: {response_datetime}. Expected format: %Y%m%d%H%M%S",
                    "Date Parsing Error",
                )
                return
        else:
            frappe.log_error(
                f"Response datetime is None for route: {route}",
                "Missing Response Datetime",
            )
            return

        # Save and commit changes
        doc.save()
        frappe.db.commit()
        frappe.log("Last request date updated successfully", title="Update Success")

    except frappe.DoesNotExistError:
        frappe.log_error(
            f"Document not found for route: {route} in table: {routes_table}",
            "Document Not Found",
        )
    except Exception as e:
        frappe.log_error(
            frappe.get_traceback(), f"Unexpected error: {str(e)}"
        )


    
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




def generate_qr_code(data: str) -> BytesIO:
    """Generates a QR code for the provided data and returns it as an image."""
    img = qrcode.make(data)
    byte_io = BytesIO()
    img.save(byte_io, 'PNG')
    byte_io.seek(0)
    return byte_io




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



def get_environment_settings(
    company_name: str,
    doctype: str = "ZRA Smart Invoice Settings",
    cur_environment: str = "Sandbox",
    branch_id: str = "001",
) -> Document | None:
    error_message = None
    query = f"""
    SELECT server_url,
        company_tpin,
        name,
        vsdc_device_serial_number,
        branch_id,
        company_name,
        zra_sales_control_unit_id
    FROM `tab{doctype}`
    WHERE company_name = '{company_name}'
        AND environment = '{cur_environment}'
        AND name IN (
            SELECT name
            FROM `tab{doctype}`
            WHERE is_active_ = 1
        )
    """
    if branch_id:
        query += f"AND branch_id = '{branch_id}';"

    setting_doctype = frappe.db.sql(query, as_dict=True)

    if setting_doctype:
        return setting_doctype[0]

    error_message = f"""
        There is no valid environment setting for these credentials:
            <ul>
                <li>Company: <b>{company_name}</b></li>
                <li>Branch ID: <b>{branch_id}</b></li>
                <li>Environment: <b>{cur_environment}</b></li>
            </ul>
        <p>Please ensure a valid <a href="/app/zra-smart-invoice-settings">ZRA Smart Invoice Settings</a> record exists.</p>
    """

    zra_vsdc_logger.error(error_message)
    frappe.log_error(
        title="Incorrect Setup", message=error_message, reference_doctype=doctype
    )
    frappe.throw(error_message, title="Incorrect Setup")


    
def get_current_env_settings(company_name: str, branch_id: str = "001") -> Document | None:

    current_env = get_current_environment_state("ZRA VSDC Environment Identifier")
    
    # Fetch the environment settings based on the current environment and branch_id
    settings = get_environment_settings(
        company_name, cur_environment=current_env, branch_id=branch_id
    )
    print("The document settings are: ", settings)

    # Check if settings were retrieved successfully
    if settings:
        return settings


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