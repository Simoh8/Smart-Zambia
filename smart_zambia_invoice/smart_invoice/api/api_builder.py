from __future__ import annotations
from typing import Literal,Callable
from urllib import parse
from  frappe.integrations.utils import create_request_log
from frappe.model.document import Document

import _asyncio
import aiohttp

import frappe
 