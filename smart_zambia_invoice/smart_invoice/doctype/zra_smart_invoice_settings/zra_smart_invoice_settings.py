# Copyright (c) 2024, simon muturi and contributors
# For license information, please see license.txt

import frappe
import _asyncio
import aiohttp
import frappe.defaults
from frappe.integrations.utils import create_request_log
from frappe.model.document import Document


class ZRASmartInvoiceSettings(Document):
	pass
