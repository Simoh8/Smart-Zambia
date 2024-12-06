import frappe
from frappe.model.document import Document
from.zra_logger import zra_vsdc_logger
from .utilities import upate_last_request_date


def handle_errors(
    response: dict[str, str],
    route: str,
    document_name: str,
    doctype: str | Document | None = None,
    integration_request_name: str | None = None,
) -> None:
    error_message, error_code = response["resultMsg"], response["resultCd"]

    zra_vsdc_logger.error("%s, Code: %s" % (error_message, error_code))

    try:
        frappe.throw(
            error_message,
            frappe.InvalidStatusError,
            title=f"Error: {error_code}",
        )

    except frappe.InvalidStatusError as error:
        frappe.log_error(
            frappe.get_traceback(with_context=True),
            error,
            reference_name=document_name,
            reference_doctype=doctype,
        )
        raise

    finally:
        update_last_request_date(response["resultDt"], route)
