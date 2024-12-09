import frappe


from ..error_handlers import handle_errors

def notices_search_on_success(response: dict) -> None:
    notices_list = response["data"]["noticeList"]

    for notice in notices_list:
        doc = frappe.new_doc("ZRA Notice ")

        doc.notice_number = notice["noticeNo"]
        doc.title = notice["title"]
        doc.registration_name = notice["regrNm"]
        doc.details_url = notice["dtlUrl"]
        doc.registration_datetime = notice["regDt"]
        doc.contents = notice["cont"]

        try:
            doc.submit()

        except frappe.exceptions.DuplicateEntryError:
            frappe.log_error(title="Duplicate entries")




def on_error(
    response: dict | str,
    url: str | None = None,
    doctype: str | None = None,
    document_name: str | None = None,
) -> None:
    """Base "on-error" callback.

    Args:
        response (dict | str): The remote response
        url (str | None, optional): The remote address. Defaults to None.
        doctype (str | None, optional): The doctype calling the remote address. Defaults to None.
        document_name (str | None, optional): The document calling the remote address. Defaults to None.
        integration_reqeust_name (str | None, optional): The created Integration Request document name. Defaults to None.
    """
    handle_errors(
        response,
        route=url,
        doctype=doctype,
        document_name=document_name,
    )


