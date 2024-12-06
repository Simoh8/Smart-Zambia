"""zra vsdc Logger initialisation"""

import frappe
from frappe.utils import logger

logger.set_log_level("DEBUG")
zra_vsdc_logger = frappe.logger("ZRA", allow_site=True, file_count=50)
