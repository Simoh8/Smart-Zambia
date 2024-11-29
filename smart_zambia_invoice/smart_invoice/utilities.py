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
    pattern = r"^\d{10}$"
    return bool(re.match(pattern, tpin))

async def make_get_request(url: str) -> dict[str,str] |str:
    """this is liable for makinng the get request t the spcific url given by zra
    
    Args:
        url which is the url to be used

    Return:
        a dictionary which has the response
    """
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.content_type.startswith("text"):
                return await response.text()
            
            return await response.json()
        
async def make_post_reqest(
        url: str,
        data:dict[str, str]| None=None, 
        headers: dict[str, str |int ] |None=None, 
        ) -> dict [str,str | dict]:
    """this is rensposible for making the post request with the headers with the data as arguments"""
    async with aiohttp.ClientSession(timeout=ClientTimeout(1800)) as session:
        async with session.post(url, Json=data, headers=headers) as response:
            return await response.json()
        

def is_url_valid(url: str) -> bool:
    """is the entered url valid"""
    pattern=r"^(https?|ftp):\/\/[^\s/$.?#].[^\s]*"
    return bool(re.match(pattern, url))

def make_datetime_from_string(date_string:str, format:str= "%Y-%m-%d %H:%M:%S")-> datetime:

    """This functin converts the datetime string to the correct date time format"""

    datetime_object =datetime.strptime(date_string,format)

    return datetime_object