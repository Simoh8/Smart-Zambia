import frappe
from frappe.model.document import Document
from.zra_logger import zra_vsdc_logger
from .utilities import update_last_request_date


def handle_errors(
    response: dict[str, str | None],  # Allow None values
    route: str,
    document_name: str,
    doctype: str | Document | None = None,
    integration_request_name: str | None = None,
) -> None:
    error_message = response.get("resultMsg") or "An unknown error occurred."
    error_code = response.get("resultCd") or "Unknown Code"

    zra_vsdc_logger.error(f"{error_message}, Code: {error_code}")

    try:
        frappe.throw(
            error_message,
            frappe.InvalidStatusError,
            title=f"Error: {error_code}",
        )

    except frappe.InvalidStatusError as error:
        frappe.log_error(
            frappe.get_traceback(with_context=True),
            str(error),
            reference_name=document_name,
            reference_doctype=doctype,
        )
        raise

    finally:
        result_dt = response.get("resultDt")
        if result_dt:
            update_last_request_date(result_dt, route)
