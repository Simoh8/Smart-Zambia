import frappe


from ..error_handlers import handle_errors

def notices_search_on_success(response: dict) -> None:
    notices_list = response["data"]["noticeList"]

    for notice in notices_list:
        doc = frappe.new_doc("ZRA Notice ")

        doc.notice_number = notice["noticeNo"]
        doc.notice_title = notice["title"]
        doc.registration_name = notice["regrNm"]
        doc.notice_url = notice["dtlUrl"]
        doc.notice_registration_datetime = notice["regDt"]
        doc.notice_contents = notice["cont"]

        try:
            doc.submit()

        except frappe.exceptions.DuplicateEntryError:
            frappe.log_error(title="Duplicate entries")


def item_composition_submission_succes(response: dict, document_name: str) -> None:
    frappe.db.set_value(
        "BOM", document_name, {"custom_item_composition_submitted_successfully": 1}
    )




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


def fetch_branch_request_on_success(response: dict) -> None:
    for branch in response["data"]["bhfList"]:
        doc = None

        try:
            doc = frappe.get_doc(
                "Branch",
                {"branch": branch["bhfId"]},
                for_update=True,
            )

        except frappe.exceptions.DoesNotExistError:
            doc = frappe.new_doc("Branch")

        finally:
            doc.branch = branch["bhfId"]
            doc.custom_branch_code = branch["bhfId"]
            doc.custom_pin = branch["tin"]
            doc.custom_branch_name = branch["bhfNm"]
            doc.custom_branch_status_code = branch["bhfSttsCd"]
            doc.custom_county_name = branch["prvncNm"]
            doc.custom_sub_county_name = branch["dstrtNm"]
            doc.custom_tax_locality_name = branch["sctrNm"]
            doc.custom_location_description = branch["locDesc"]
            doc.custom_manager_name = branch["mgrNm"]
            doc.custom_manager_contact = branch["mgrTelNo"]
            doc.custom_manager_email = branch["mgrEmail"]
            doc.custom_is_head_office = branch["hqYn"]
            doc.custom_is_etims_branch = 1

            doc.save()
            
def on_succesful_customer_search(
    response: dict,
    document_name: str,
) -> None:
    frappe.db.set_value(
        "Customer",
        document_name,
        {
            "custom_tax_payers_name": response["taxprNm"],
            "custom_tax_payers_status": response["taxprSttsCd"],
            "custom_county_name": response["prvncNm"],
            "custom_subcounty_name": response["dstrtNm"],
            "custom_tax_locality_name": response["sctrNm"],
            "custom_location_name": response["locDesc"],
            "custom_is_validated": 1,
        },
    )
