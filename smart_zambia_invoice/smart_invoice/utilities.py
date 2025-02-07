
import base64
from urllib.parse import quote, unquote
from urllib.parse import urlsplit, urlunsplit
import re
import frappe
import aiohttp
from frappe.auth import quote
import qrcode
import asyncio

from base64 import b64encode
from datetime import datetime, timedelta
from io import BytesIO
from typing import Literal, Optional, Union
from aiohttp import ClientTimeout, InvalidURL
from frappe.model.document import Document
from frappe.utils import cint
from .zra_logger import zra_vsdc_logger



from erpnext.controllers.taxes_and_totals import get_itemised_tax_breakup_data


# -------------------------------
# Utility Functions
# -------------------------------
UNRESERVED_SET = frozenset(
    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz" + "0123456789-._~"
)

def unquote_unreserved(url):
    """Un-escape any percent-escape sequences in a URI that are unreserved
    characters. This leaves all reserved, illegal and non-ASCII bytes encoded.

    :rtype: str
    """
    parts = url.split("%")
    for i in range(1, len(parts)):
        h = parts[i][0:2]
        if len(h) == 2 and h.isalnum():
            try:
                c = chr(int(h, 16))
            except ValueError:
                raise InvalidURL(f"Invalid percent-escape sequence: '{h}'")

            if c in UNRESERVED_SET:
                parts[i] = c + parts[i][2:]
            else:
                parts[i] = f"%{parts[i]}"
        else:
            parts[i] = f"%{parts[i]}"
    return "".join(parts)

def unquote_unreserved(url):
    """
    Unquote only unreserved characters as per RFC 3986.
    """
    unreserved = re.compile(r'([A-Za-z0-9._~-]+)')
    parts = urlsplit(url)
    unquoted_path = unreserved.sub(lambda m: unquote(m.group(0)), parts.path)
    return urlunsplit((parts.scheme, parts.netloc, unquoted_path, parts.query, parts.fragment))

class InvalidURL(Exception):
    """Custom exception for invalid URLs."""
    pass

def requote_current_url(url):
    """
    Re-quote the given URI.

    This function passes the given URI through an unquote/quote cycle to
    ensure that it is fully and consistently quoted.

    :rtype: str
    """
    safe_with_percent = "!#$%&'()*+,/:;=?@[]~"
    safe_without_percent = "!#$&'()*+,/:;=?@[]~"

    try:
        # Unquote only the unreserved characters
        # Then quote only illegal characters (do not quote reserved,
        # unreserved, or '%')
        return quote(unquote_unreserved(url), safe=safe_with_percent)
    except Exception as e:
        # Handle invalid URL cases
        return quote(url, safe=safe_without_percent)


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



def build_common_payload(headers: dict, last_req_date: datetime) -> dict:
    """
    Constructs the common payload fields used in both APIs.
    Args:
        headers (dict): HTTP headers containing 'tpin' and 'bhfId'.
        last_req_date (datetime): The last request date.

    Returns:
        dict: A dictionary containing the common payload fields.
    """
    return {
        "tpin": headers.get("tpin"),
        "lastReqDt": last_req_date.strftime("%Y%m%d%H%M%S"),
        "bhfId": headers.get("bhfId"),
    }

def last_request_less_payload (headers: dict, last_req_date: datetime = None) -> dict:
    """
    Constructs the common payload fields used in both APIs.
    
    Args:
        headers (dict): HTTP headers containing 'tpin' and 'bhfId'.
        last_req_date (datetime, optional): The last request date. Defaults to None.
    
    Returns:
        dict: A dictionary containing the common payload fields.
    """
    payload = {
        "tpin": headers.get("tpin"),
        "bhfId": headers.get("bhfId"),
    }

    if last_req_date:
        payload["lastReqDt"] = last_req_date.strftime("%Y%m%d%H%M%S")

    return payload


def build_request_headers(company_name: str, branch_id: str = "001") -> dict[str, str] | None:
    settings = get_current_env_settings(company_name, branch_id=branch_id)

    if settings:
        # current_time = datetime.now().strftime("%Y%m%d%H%M%S")

        headers = {
            "tpin": settings.get("company_tpin"),  # Adjusted to match the key in `settings`
            "bhfId": settings.get("branch_id"), 
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




def fetch_qr_code(data: str) -> str:
    """Generates a QR code for the provided data and returns it as a base64-encoded string."""
    img = qrcode.make(data)
    byte_io = BytesIO()
    img.save(byte_io, 'PNG')
    byte_io.seek(0)
    # Convert the BytesIO content to a base64 string
    return base64.b64encode(byte_io.read()).decode('utf-8')



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
        custom_sales_control_unit_id
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

    # Check if settings were retrieved successfully
    if settings:
        return settings







def show_success_message(msg: str) -> None:
    """
    Display a success message dialog in Frappe.
    
    Args:
        msg (str): The success message to display.
    """
    frappe.msgprint(
        msg=msg,
        title="Success",
        indicator="green"
    )



def show_que_success(job, connection, result, *args, **kwargs):
    # This function is executed after the job has completed successfully
    frappe.msgprint("The activity has been completed successfully!")
    # You can also do additional logic here if needed



def truncate_user_id(user_id, max_length=20):
    """
    Truncate the user_id to a maximum length.

    Args:
        user_id (str): The original user_id.
        max_length (int): The maximum allowed length for the user_id.

    Returns:
        str: The truncated user_id.
    """
    return user_id[:max_length]


def generate_next_item_code(country_code, product_type, packaging_unit, quantity_unit):
    """
    Generate the next unique item code based on the last registered item code.
    """
    # Fetch the latest item code
    last_item_code = frappe.db.get_value('Item', 
                                         {'custom_zra_country_origin_code': country_code, 
                                          'custom_zra_product_type_code': product_type,
                                          'custom_zra_packaging_unit_code': packaging_unit, 
                                          'custom_zra_unit_quantity_code': quantity_unit},
                                         'custom_zra_item_code',
                                         order_by='custom_zra_item_code DESC')

    # If there's no previous item code, start from 1
    if not last_item_code:
        increment = 1
    else:
        # Extract the last increment value from the item code (assuming it's the last 7 digits)
        last_increment = int(last_item_code[-7:])
        increment = last_increment + 1

    # Format the increment value with zero padding
    increment_str = f"{increment:07d}"  # Ensure the increment is 7 digits

    # Return the new item code by concatenating the parts
    return f"{country_code}{product_type}{packaging_unit}{quantity_unit}{increment_str}"





def get_real_name(doctype, field_name, value, target_field):
    """
    Fetches a target field (default 'code_name') from a specified doctype 
    based on a given field's value.
    
    Args:
        doctype (str): The name of the doctype to query.
        field_name (str): The field to filter on (e.g., 'country_code').
        value (str): The value to match in the field.
        target_field (str): The field to retrieve (default is 'code_name').
    
    Returns:
        str: The value of the target field if found, or None if no match is found.
    """
    if not (doctype and field_name and value):
        frappe.throw("Doctype, field_name, and value must all be provided.")

    result = frappe.db.get_value(doctype, {field_name: value}, target_field)
    
    if result:
        return result
    else:
        return None



def get_invoice_items_list(invoice: Document) -> list[dict[str, str | int | None]]:
    """Iterates over the invoice items and extracts relevant data

    Args:
        invoice (Document): The invoice

    Returns:
        list[dict[str, str | int | None]]: The parsed data as a list of dictionaries
    """
    # FIXME: Handle cases where same item can appear on different lines with different rates etc.
    # item_taxes = get_itemised_tax_breakup_data(invoice)
    taxation_type = get_taxation_types(invoice)
    print("The taxation type is ",taxation_type)

    items_list = []

    for index, item in enumerate(invoice.items):

        items_list.append(
            {
                "itemSeq": item.idx,
                "itemCd": item.custom_zra_item_code,
                "itemClsCd": item.custom_zra_item_classification_code,
                "itemNm": item.item_name,
                "bcd": item.barcode,
                "pkgUnitCd": item.custom_zra_packaging_unit_code,
                "pkg": 1,
                "qtyUnitCd": item.custom_zra_unit_of_quantity_code,
                "qty": abs(item.qty),
                "prc": round(item.base_rate, 2),
                "splyAmt": round(item.base_amount, 2),
                "dcRt": round(item.discount_percentage, 2) or 0,
                "dcAmt": round(item.discount_amount, 2) or 0,
                "tlTaxblAmt": round(item.custom_tourism_levy_taxable_amoun or 0, 2),
                "vatCatCd": item.custom_vat_category_code,
                "iplTaxblAmt": round(item.custom_insurance_premium_levy_taxable_amount or 0,2),
                "exciseTaxblAmt": round(item.custom_excise_tax_amount or 0, 2),
                "exciseTxCatCd": item.custom_zra_taxation_type if item.custom_zra_taxation_type in ["ECM", "EXEEG"] else None,
                "vatTaxblAmt": round(item.custom_vat_taxable_amount or 0, 2) ,
                "exciseTxAmt": round(item.custom_excise_tax_amount or 0, 2) ,
                "vatAmt": round(item.custom_tax_amount or 0,2),
                "iplCatCd": item.custom_zra_taxation_type if item.custom_zra_taxation_type in ["IPL1", "IPL2"] else None,
                "taxTyCd": item.custom_zra_taxation_type_code,
                "taxblAmt": round(item.net_amount or 0, 2) , #taxable_amount,
                "taxAmt": round(item.custom_tax_amount or 0, 2),
                "totAmt": round(item.net_amount + item.custom_tax_amount or 0, 2) ,
            }
        )

    return items_list


def success(success_codes: list) -> str:
    """
    Generates a success message for successfully inserted codes.

    :param success_codes: List of successfully inserted codes.
    :return: A formatted success message.
    """
    if success_codes:
        return f"Successfully entered codes: {', '.join(success_codes)}"
    return "No codes were successfully entered."

def duplicate(duplicate_codes: list) -> str:
    """
    Generates a duplicate message for codes that could not be inserted.

    :param duplicate_codes: List of duplicate codes.
    :return: A formatted duplicate message.
    """
    if duplicate_codes:
        return f"Duplicate codes (not entered): {', '.join(duplicate_codes)}"
    return "No duplicate codes were found."




def before_save_(doc: "Document", method: str | None = None) -> None:
    calculate_tax(doc)



def clean_invc_no(invoice_name):
    if "-" in invoice_name:
        invoice_name = "-".join(invoice_name.split("-")[:-1])
    return invoice_name



def get_taxation_types(doc):
    taxation_totals = {}

    # Loop through each item in the Sales Invoice
    for item in doc.items:
        taxation_type = item.custom_zra_taxation_type
        taxable_amount = item.net_amount  
        tax_amount = item.custom_tax_amount  

        # Fetch the tax rate for the current taxation type from the specified doctype
        tax_rate = frappe.db.get_value("ZRA Tax Type", taxation_type, "code")
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





def build_invoice_payload(
    invoice: Document, invoice_type_identifier: Literal["S", "C"], company_name: str
) -> dict[str, str | int | float]:
    # Retrieve taxation data for the invoice
    taxation_type = get_taxation_types(invoice)
    # frappe.throw(str(taxation_type))
    """Converts relevant invoice data to a JSON payload

    Args:
        invoice (Document): The Invoice record to generate data from
        invoice_type_identifier (Literal["S", "C"]): The
        Invoice type identifier. S for Sales Invoice, C for Credit Notes
        company_name (str): The company name used to fetch the valid settings doctype record

    Returns:
        dict[str, str | int | float]: The payload
    """
    post_time = invoice.posting_time

    # Ensure post_time is a string if it's a timedelta
    if isinstance(post_time, timedelta):
        post_time = str(post_time)

    # Parse posting date and time
    posting_date = make_datetime_from_string(
        f"{invoice.posting_date} {post_time[:8].replace('.', '')}",
        format="%Y-%m-%d %H:%M:%S",
    )

    validated_date = posting_date.strftime("%Y%m%d%H%M%S")
    sales_date = posting_date.strftime("%Y%m%d")

    # Fetch list of invoice items
    items_list = get_invoice_items_list(invoice)

    # Determine the invoice number format
    invoice_name = invoice.name
    
    if invoice.amended_from:
        invoice_name = clean_invc_no(invoice_name)
        
    payload = {
        "orgInvcNo": (
            0 if invoice_type_identifier == "S"
            else frappe.get_doc("Sales Invoice", invoice.return_against).custom_submission_sequence_number
        ),
        "cisInvcNo": invoice_name,
        "custTpin": invoice.tax_id if invoice.tax_id else None,
        "custNm": invoice.customer,
        "salesTyCd": "N",
        "rcptTyCd": invoice_type_identifier if invoice_type_identifier == "S" else "R",
        "pmtTyCd": invoice.custom_zra_payment_code,
        "salesSttsCd": invoice.custom_progress_status_code,
        "cfmDt": validated_date,
        "salesDt": sales_date,
        "stockRlsDt": validated_date,
        "cnclReqDt": None,
        "cnclDt": None,
        "rfdDt": None,
        "rfdRsnCd": None,
        "totItemCnt": len(items_list),

        "taxblAmtA": taxation_type.get("A", {}).get("taxable_amount", 0),
        "taxblAmtB": taxation_type.get("B", {}).get("taxable_amount", 0),
        "taxblAmtC1": taxation_type.get("C1", {}).get("taxable_amount", 0),
        "taxblAmtC2": taxation_type.get("C2", {}).get("taxable_amount", 0),
        "taxblAmtC3": taxation_type.get("C3", {}).get("taxable_amount", 0),
        "taxblAmtD": taxation_type.get("D", {}).get("taxable_amount", 0),
        "taxblAmtRVAT": taxation_type.get("RVAT", {}).get("taxable_amount", 0),
        "taxblAmtE": taxation_type.get("E", {}).get("taxable_amount", 0),
        "taxblAmtF": taxation_type.get("F", {}).get("taxable_amount", 0),
        "taxblAmtIpl1": taxation_type.get("IPL1", {}).get("taxable_amount", 0),
        "taxblAmtIpl2": taxation_type.get("IPL2", {}).get("taxable_amount", 0),
        "taxblAmtTl": taxation_type.get("TL", {}).get("taxable_amount", 0),
        "taxblAmtEcm": taxation_type.get("ECM", {}).get("taxable_amount", 0),
        "taxblAmtExeeg": taxation_type.get("EXEEG", {}).get("taxable_amount", 0),
        "taxblAmtTot": taxation_type.get("TOT", {}).get("taxable_amount", 0),
        
        "taxRtA": taxation_type.get("A", {}).get("tax_rate", 0),
        "taxRtB": taxation_type.get("B", {}).get("tax_rate", 0),
        "taxRtC1": taxation_type.get("C1", {}).get("tax_rate", 0),
        "taxRtC2": taxation_type.get("C2", {}).get("tax_rate", 0),
        "taxRtC3": taxation_type.get("C3", {}).get("tax_rate", 0),
        "taxRtD": taxation_type.get("D", {}).get("tax_rate", 0),
        "taxRtRVAT": taxation_type.get("RVAT", {}).get("tax_rate", 0),
        "taxRtE": taxation_type.get("E", {}).get("tax_rate", 0),
        "taxRtF": taxation_type.get("F", {}).get("tax_rate", 0),
        "taxRtIpl1": taxation_type.get("IPL1", {}).get("tax_rate", 0),
        "taxRtIpl2": taxation_type.get("IPL2", {}).get("tax_rate", 0),
        "taxRtTl": taxation_type.get("TL", {}).get("tax_rate", 0),
        "taxRtEcm": taxation_type.get("ECM", {}).get("tax_rate", 0),
        "taxRtExeeg": taxation_type.get("EXEEG", {}).get("tax_rate", 0),
        "taxRtTot": taxation_type.get("TOT", {}).get("tax_rate", 0),

        "taxAmtA": taxation_type.get("A", {}).get("tax_amount", 0),
        "taxAmtB": taxation_type.get("B", {}).get("tax_amount", 0),
        "taxAmtC1": taxation_type.get("C1", {}).get("tax_amount", 0),
        "taxAmtC2": taxation_type.get("C2", {}).get("tax_amount", 0),
        "taxAmtC3": taxation_type.get("C3", {}).get("tax_amount", 0),
        "taxAmtD": taxation_type.get("D", {}).get("tax_amount", 0),
        "taxAmtRVAT": taxation_type.get("RVAT", {}).get("tax_amount", 0),
        "taxAmtE": taxation_type.get("E", {}).get("tax_amount", 0),
        "taxAmtF": taxation_type.get("F", {}).get("tax_amount", 0),
        "taxAmtIpl1": taxation_type.get("IPL1", {}).get("tax_amount", 0),
        "taxAmtIpl2": taxation_type.get("IPL2", {}).get("tax_amount", 0),
        "taxAmtTl": taxation_type.get("TL", {}).get("tax_amount", 0),
        "taxAmtEcm": taxation_type.get("ECM", {}).get("tax_amount", 0),
        "taxAmtExeeg": taxation_type.get("EXEEG", {}).get("tax_amount", 0),
        "taxAmtTot": taxation_type.get("TOT", {}).get("tax_amount", 0),

        "totTaxblAmt": round(invoice.base_net_total, 2),
        "totTaxAmt": round(invoice.total_taxes_and_charges, 2),
        "cashDcRt": 25,
        "cashDcAmt": 50,
        
        "totAmt": round(invoice.grand_total, 2),
        "prchrAcptcYn": "Y",
        "remark": None,
        "regrId": split_user_mail(invoice.owner),
        "lpoNumber": None,
        "currencyTyCd": "ZMW",
        "exchangeRt": "1",
        "destnCountryCd": "",
        "dbtRsnCd": "",
        "invcAdjustReason": "",
        "regrNm": invoice.owner,
        "modrId": split_user_mail(invoice.modified_by),
        "modrNm": invoice.modified_by,
        "itemList": items_list,
    }
    
    return payload

    