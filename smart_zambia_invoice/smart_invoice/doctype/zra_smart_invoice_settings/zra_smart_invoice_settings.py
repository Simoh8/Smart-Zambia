# Copyright (c) 2024, simon muturi and contributors
# For license information, please see license.txt

import frappe
import asyncio
import aiohttp
import frappe.defaults
from frappe.integrations.utils import create_request_log
from frappe.model.document import Document
from ...utilities import send_initialization_request


class ZRASmartInvoiceSettings(Document):
	def validate(self):


		def initialize_device(self):
			"""Handles the ZRA initialization request"""
			# Fetch the required settings from your DocType
			tpin = self.company_tpin
			bhf_id = self.branch_id
			dvc_srl_no = self.vsdc_device_serial_number
			
			# Run the initialization asynchronously
			response = asyncio.run(send_initialization_request(tpin, bhf_id, dvc_srl_no))
			
			# Process the response and do further actions (e.g., save to logs, notify user, etc.)
			if response:
				# Optionally, save some response data in your doc or log it
				self.last_initialized = frappe.utils.now()  # Example field for storing timestamp
				self.save()
			
			return response