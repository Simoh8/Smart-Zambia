
import json
import frappe
import frappe.defaults
from frappe.model.document import Document
from smart_zambia_invoice.smart_invoice.overrides.backend.common_overrides import EndpointConstructor, build_request_headers, get_route_path, get_server_url, on_error
from smart_zambia_invoice.smart_invoice.utilities import last_request_less_payload
from..overrides.backend.stock_ledger_entry import on_update
from..overrides.backend.sales_invoice import on_submit

from ..api.zra_api import save_stock_inventory,perform_zra_notice_search


endpoint_maker = EndpointConstructor()


def frequent_refresh_notices() -> None:

    company = frappe.defaults.get_user_default("Company")

    perform_zra_notice_search(json.dumps({"company_name": company}))





def send_stock_update_information() -> None:
    all_stock_ledger_entries: list[Document] = frappe.get_all(
        "Stock Ledger Entry",
        {"docstatus": 1, "custom_submitted_successfully": 0},
        ["name"],
    )
    for entry in all_stock_ledger_entries:
        doc = frappe.get_doc(
            "Stock Ledger Entry", entry.name, for_update=False
        )  
        try:
            on_update(
                doc, method=None
            ) 

        except TypeError:
            continue





def send_item_inventory_information() -> None:

    query = """
        SELECT sle.name as name,
            sle.owner,
            sle.custom_submitted_successfully,
            sle.custom_inventory_submitted_successfully,
            qty_after_transaction as residual_qty,
            sle.warehouse,
            w.custom_branch as branch_id,
            i.item_code as item,
            custom_zra_item_code as item_code
        FROM `tabStock Ledger Entry` sle
            INNER JOIN tabItem i ON sle.item_code = i.item_code
            INNER JOIN tabWarehouse w ON sle.warehouse = w.name
        WHERE sle.custom_submitted_successfully = '1'
            AND sle.custom_inventory_submitted_successfully = '0'
        ORDER BY sle.creation DESC;
        """

    stock_ledgers = frappe.db.sql(query, as_dict=True)

    for stock_ledger in stock_ledgers:
        response = json.dumps(stock_ledger)

        try:
            save_stock_inventory(response)

        except Exception as error:
            
            frappe.throw("Error Encountered", type(error), title="Error")


def submit_pos_invoices_information() -> None:

    all_pending_pos_invoices: list[Document] = frappe.get_all(
        "POS Invoice", {"docstatus": 1, "custom_successfully_submitted": 0}, ["name"]
    )

    if all_pending_pos_invoices:
        for pos_invoice in all_pending_pos_invoices:
            doc = frappe.get_doc(
                "POS Invoice", pos_invoice.name, for_update=False
            )  # Refetch to get the document representation of the record

            try:
                on_submit(
                    doc, method=None
                ) 
            except TypeError:
                continue






@frappe.whitelist()
def refresh_code_lists() -> str | None:
    company_name: str | None = frappe.defaults.get_user_default("Company")

    headers = build_request_headers (company_name)
    server_url = get_server_url(company_name)

    code_search_route_path, last_req_date = get_route_path(
        "Standard Codes (Constants)"
    )  # endpoint for code search

    if headers and server_url and code_search_route_path:
        url = f"{server_url}{code_search_route_path}"
        payload = {
            "lastReqDt": "20200101000000"
        }  

        endpoint_maker.headers = headers
        endpoint_maker.payload = payload
        endpoint_maker.error_callback = on_error

        # Fetch and update codes obtained from CodeSearchReq endpoint
        endpoint_maker.url = url
        endpoint_maker.success_callback = run_updater_functions
        endpoint_maker.perform_remote_calls(doctype=None, document_name=None)

        return "succeeded"


@frappe.whitelist()
def get_item_classification_codes() -> str | None:
    company_name: str | None = frappe.defaults.get_user_default("Company")

    headers = build_request_headers(company_name)
    server_url = get_server_url(company_name)

    item_cls_route_path = get_route_path("Classification Codes")  # overwriting last_request_date since it's not used elsewhere for this task

    if headers and server_url and item_cls_route_path:
        url = f"{server_url}{item_cls_route_path}"

        common_payload = last_request_less_payload(headers)
        payload = {**common_payload,
            "lastReqDt": "20230101000000"
        }  # Hard-coded to a this date to get all code lists.

        endpoint_maker.url = url
        endpoint_maker.headers = headers
        endpoint_maker.payload = payload
        endpoint_maker.error_callback = on_error

        # Fetch and update item classification codes from ItemClsSearchReq endpoint
        endpoint_maker.url = f"{server_url}{item_cls_route_path}"
        endpoint_maker.success_callback = update_item_classification_codes

        endpoint_maker.perform_remote_calls(doctype=None, document_name=None)
        frappe.enqueue(
            endpoint_maker.perform_remote_calls,
            is_async=True,
            queue="long",
            timeout=1200,
            doctype="ZRA Smart Invoice Settings",
        )

        return "succeeded"


def run_updater_functions(response: dict) -> None:
    for class_list in response["data"]["clsList"]:
        if class_list["cdClsNm"] == "Quantity Unit":
            update_unit_of_quantity(class_list)

        if class_list["cdClsNm"] == "Taxation Type":
            update_taxation_type(class_list)

        if class_list["cdClsNm"] == "Packing Unit":
            update_packaging_units(class_list)

        if class_list["cdClsNm"] == "Country":
            update_countries(class_list)


def update_unit_of_quantity(data: dict) -> None:
    doc: Document | None = None

    for unit_of_quantity in data["dtlList"]:
        try:
            doc = frappe.get_doc("ZRA Unit of Quantity", unit_of_quantity["cd"])

        except frappe.DoesNotExistError:
            doc = frappe.new_doc("ZRA Unit of Quantity")

        finally:
            doc.code = unit_of_quantity["cd"]
            doc.sort_order = unit_of_quantity["srtOrd"]
            doc.code_name = unit_of_quantity["cdNm"]
            doc.code_description = unit_of_quantity["cdDesc"]

            doc.save()

    frappe.db.commit()


def update_taxation_type(data: dict) -> None:
    doc: Document | None = None

    for taxation_type in data["dtlList"]:
        try:
            doc = frappe.get_doc("ZRA Tax Type", taxation_type["cd"])

        except frappe.DoesNotExistError:
            doc = frappe.new_doc("ZRA Tax Type")

        finally:
            doc.cd = taxation_type["cd"]
            doc.cdnm = taxation_type["cdNm"]
            doc.cddesc = taxation_type["cdDesc"]
            doc.useyn = 1 if taxation_type["useYn"] == "Y" else 0
            doc.srtord = taxation_type["srtOrd"]
            doc.userdfncd1 = taxation_type["userDfnCd1"]
            doc.userdfncd2 = taxation_type["userDfnCd2"]
            doc.userdfncd3 = taxation_type["userDfnCd3"]

            doc.save()

    frappe.db.commit()


def update_packaging_units(data: dict) -> None:
    doc: Document | None = None

    for packaging_unit in data["dtlList"]:
        try:
            doc = frappe.get_doc("ZRA Packaging Unit", packaging_unit["cd"])

        except frappe.DoesNotExistError:
            doc = frappe.new_doc("ZRA Packaging Unit")

        finally:
            doc.code = packaging_unit["cd"]
            doc.code_name = packaging_unit["cdNm"]
            doc.sort_order = packaging_unit["srtOrd"]
            doc.code_description = packaging_unit["cdDesc"]

            doc.save()

    frappe.db.commit()


def update_countries(data: dict) -> None:
    doc: Document | None = None

    for country in data["dtlList"]:
        try:
            doc = frappe.get_doc("Smart Zambia Country", country["cdNm"])

        except frappe.DoesNotExistError:
            doc = frappe.new_doc("Smart Zambia Country")

        finally:
            doc.code = country["cd"]
            doc.code_name = country["cdNm"]
            doc.sort_order = country["srtOrd"]
            doc.code_description = country["cdDesc"]

            doc.save()

    frappe.db.commit()


def update_item_classification_codes(response: dict) -> None:
    code_list = response["data"]["itemClsList"]
    existing_classifications = {
        classification["name"]: classification
        for classification in frappe.get_all("ZRA Item Classification", ["*"])
    }

    for item_classification in code_list:
        if item_classification["itemClsCd"] in existing_classifications:
            update_query = f"""
                UPDATE `tab{"ZRA Item Classification"}`
                SET item_classification_code = '{item_classification["itemClsCd"]}',
                    item_classification_level = '{item_classification["itemClsLvl"]}',
                    item_classification_name = '{item_classification["itemClsNm"].replace("'", " ")}',
                    taxation_type_code = '{item_classification["taxTyCd"]}',
                    is_used = '{1 if item_classification["useYn"] == "Y" else 0}',
                    is_major_target  = '{1 if item_classification["mjrTgYn"] == "Y" else 0}',
                    modified = SYSDATE()
                WHERE name = '{item_classification["itemClsCd"]}';
            """

            frappe.db.sql(update_query)

        else:
            insert_query = f"""
                INSERT INTO `tab{"ZRA Item Classification"}`
                    (name, item_classification_code, item_classification_level, item_classification_name, taxation_type_code, is_used, is_major_target, creation)
                VALUES
                    ('{item_classification["itemClsCd"]}',
                     '{item_classification["itemClsCd"]}',
                     '{item_classification["itemClsLvl"]}',
                     '{item_classification["itemClsNm"].replace("'", " ")}',
                     '{item_classification["taxTyCd"]}',
                     '{1 if item_classification["useYn"] == "Y" else 0}',
                     '{1 if item_classification["mjrTgYn"] == "Y" else 0}',
                     SYSDATE());
            """

            frappe.db.sql(insert_query)

    frappe.db.commit()
