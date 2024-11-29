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


def is_valid_tpin(tpin: str) -> bool:
    """Checks if the string provided conforms to the pattern of a TPIN.
    This function does not validate if the TPIN actually exists, only that
    it resembles a valid TPIN.

    Args:
        tpin (str): The TPIN to test

    Returns:
        bool: True if input is a valid TPIN, False otherwise
    """
    # Define a pattern for a valid TPIN (e.g., exactly 10 digits)
    pattern = r"^\d{10}$"
    return bool(re.match(pattern, tpin))
