import datetime
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


def on_success_customer_branch_details_submission(
    response: dict, document_name: str
) -> None:
    frappe.db.set_value(
        "Customer",
        document_name,
        {"custom_details_submitted_successfully": 1},
    )


# def user_details_submission_on_success(response: dict, document_name: str) -> None:
#     frappe.db.set_value(
#         USER_DOCTYPE_NAME, document_name, {"submitted_successfully_to_etims": 1}
#     )



def on_success_customer_insurance_details_submission(
    response: dict, document_name: str
) -> None:
    frappe.db.set_value(
        "Customer",
        document_name,
        {"custom_insurance_details_submitted_successfully": 1},
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
            "custom__province_name": response["prvncNm"],
            "custom_tax_locality_name": response["dstrtNm"],
            "custom_customer_sector_name": response["sctrNm"],
            "custom_is_validated": 1,
        },
    )



def on_imported_items_search_success(response: dict) -> None:
    items = response["data"]["itemList"]
    

    def create_if_not_exists(doctype: str, code: str) -> str:
        """Create the code if the record doesn't exist for the doctype

        Args:
            doctype (str): The doctype to check and create
            code (str): The code to filter the record

        Returns:
            str: The code of the created record
        """
        present_code = frappe.db.exists(doctype, {"code": code})

        if not present_code:
            created = frappe.get_doc(
                {
                    "doctype": doctype,
                    "code": code,
                    "code_name": code,
                    "code_description": code,
                }
            ).insert(ignore_permissions=True, ignore_if_duplicate=True)

            return created.code_name

        return present_code

    for item in items:
        doc = frappe.new_doc("ZRA Registered Imported Item")

        doc.item_name = item["itemNm"]
        doc.task_code = item["taskCd"]
        doc.declaration_date = datetime.strptime(item["dclDe"], "%d%m%Y")
        doc.item_sequence = item["itemSeq"]
        doc.declaration_number = item["dclNo"]
        doc.hs_code = item["hsCd"]
        doc.origin_nation_code = frappe.db.get_value(
            "Smart Zambia Country", {"code": item["orgnNatCd"]}, "code_name"
        )
        doc.export_nation_code = frappe.db.get_value(
            "Smart Zambia Country", {"code": item["exptNatCd"]}, "code_name"
        )
        doc.package = item["pkg"]
        doc.packaging_unit_code = create_if_not_exists(
            "Smart Zambia Country", item["pkgUnitCd"]
        )
        doc.quantity = item["qty"]
        doc.quantity_unit_code = create_if_not_exists(
            "ZRA Unit of Quantity", item["qtyUnitCd"]
        )
        doc.gross_weight = item["totWt"]
        doc.net_weight = item["netWt"]
        doc.suppliers_name = item["spplrNm"]
        doc.agent_name = item["agntNm"]
        doc.invoice_foreign_currency_amount = item["invcFcurAmt"]
        doc.invoice_foreign_currency = item["invcFcurCd"]
        doc.invoice_foreign_currency_rate = item["invcFcurExcrt"]

        doc.save()

    frappe.msgprint(
        "Imported Items Fetched. Go to <b>ZRA Registered Imported Item</b> Doctype for more information"
    )
def on_success_search_branch_request(response: dict) -> None:
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
