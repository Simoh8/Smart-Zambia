import datetime
import frappe
from smart_zambia_invoice.smart_invoice.utilities import duplicate, fetch_qr_code, get_real_name, requote_current_url, show_success_message, success
from ..error_handlers import handle_errors





def notices_search_on_success(response: dict) -> None:
    notices_list = response["data"]["noticeList"]
    success_codes = []  # To store successfully inserted notice numbers
    duplicate_codes = []  # To store duplicate notice numbers

    for notice in notices_list:
        doc = frappe.new_doc("ZRA Notice")
        doc.notice_number = notice["noticeNo"]
        doc.notice_title = notice["title"]
        doc.registration_name = notice["regrNm"]
        doc.notice_url = notice["dtlUrl"]
        doc.notice_registration_datetime = notice["regDt"]
        doc.notice_contents = notice["cont"]

        try:
            doc.submit()
            success_codes.append(notice["noticeNo"])
        except frappe.exceptions.DuplicateEntryError:
            duplicate_codes.append(notice["noticeNo"])

    # Use the success and duplicate functions to generate messages
    success_message = success(success_codes)
    duplicate_message = duplicate(duplicate_codes)

    # Display the combined message
    frappe.msgprint(f"{success_message}<br>{duplicate_message}", title="Notice Import Summary")





def item_composition_submission_succes(response: dict, document_name: str) -> None:
    frappe.db.set_value(
        "BOM", document_name, {"custom_item_composition_submitted_successfully": 1}
    )




def on_success_customer_branch_details_submission(response: dict, document_name: str) -> None:
    try:
        # Update the document to indicate success
        frappe.db.set_value("Customer", document_name, {"custom_details_submitted_successfully": 1})

        show_success_message("Customer Details Submitted Succesfully on ZRA Portal")
    
    except Exception as e:
        frappe.log_error(f"Error updating customer document {document_name}: {str(e)}")
        frappe.msgprint(frappe._("An error occurred while registering the user. Please try again."))




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




def on_success_item_registration(response: dict, document_name: str) -> None:
    frappe.db.set_value("Item", document_name, {"custom_zra_item_registered_": 1})
    show_success_message("Item registration succesful")





def on_success_user_details_submission(response:dict, document_name:str)-> None:
    
    frappe.db.set_value("ZRA Smart Invoice User", document_name,{"registered_on_smart_invoice":1})
    show_success_message("The user has been succesfully registered on the ZRA Portal")





def on_success_customer_search(
    response: dict,
    document_name: str,
) -> None:
        # Extract customer data
    customer_data = response.get('data', {}).get('custList', [{}])[0]
    customer_name = customer_data.get('custNm', 'Unknown')
    custom_phone_number = customer_data.get('telNo', 'Unknown')
    custom_email_address = customer_data.get('email', 'Unknown')
    tax_id = customer_data.get('custTpin', 'Unknown')
    custom_tax_payers_status = "Active" if customer_data.get('useYn') == 'Y' else "Inactive"
    custom_province_name = customer_data.get('adrs', 'Unknown')  # Extract address

# Include additional information from the zra server when need be but for now work with the name and tpin
    frappe.db.set_value(
        "Customer",
        document_name,
        {
            "customer_name": customer_name,
            "custom_tax_payers_name":customer_name,
            "custom_phone_number": custom_phone_number,
            "custom_email_address": custom_email_address,
            "custom_tax_payers_status":custom_tax_payers_status,
            "custom__province_name": custom_province_name,  

            "tax_id": tax_id,
            "custom_is_validated": 1,
        },
    )
    show_success_message("Customer details updated successfully")





def on_successful_fetch_latest_items(frm, response):

    if frm is None:
        frm = {} 

    for item in response.get('data', {}).get('itemList', []):

        item_code = item.get("itemCd") or item.get("itemNm") or frm.get("custom_zra_item_code") or "DEFAULT_ITEM_CODE"

        existing_item = frappe.get_all("Item", filters={"item_code": item_code}, limit=1)

        if existing_item:
            item_code = f"{item_code}_"
            doc = frappe.get_doc("Item", existing_item[0].get("name"))
            doc.item_code = item_code  
        else:
            doc = frappe.new_doc("Item")

            country_code = item.get("orgnNatCd")
            packaging_unit= item.get("pkgUnitCd")
            unit_quantity= item.get("qtyUnitCd")
            product_type= item.get("itemTyCd")
            
            # Corrected: Pass the target_field parameter explicitly
            # unit_quantity_name=get_real_name("ZRA Unit of Quantity", "code", unit_quantity, "code_name" )
            code_name = get_real_name("Smart Zambia Country", "code", country_code, "code_name")
            # packaging_unit_name =get_real_name("ZRA Packaging Unit", "code", packaging_unit, "code_name" )
            # product_type_name=get_real_name("ZRA Product Type", "code",product_type,"code_name"            
            doc.custom_zra_item_classification_code = item.get("itemClsCd")
            doc.item_group = "All Item Groups"
            doc.custom_zra_item_code="item.get(itemCd)"
            doc.item_code = item.get("itemNm", frm.get("item_name", "DefaultItemName"))
            doc.item_name = item.get("itemNm", frm.get("item_name", "DefaultItemName"))
            doc.company = item.get("company_name", frm.get("company_name", "DefaultCompany"))
            doc.standard_rate = float(item.get("dftPrc", frm.get("valuation_rate", 0)))
            doc.custom_zra_country_of_origin = code_name
            doc.custom_zra_packaging_unit = item.get("pkgUnitCd")
            doc.custom_zra_unit_quantity_code = item.get("qtyUnitCd")
            doc.custom_zra_tax_type = item.get("vatCatCd", frm.get("custom_zra_tax_type", "DefaultTax"))
            doc.batch_no = item.get("btchNo")
            doc.custom_zra_product_type_code = item.get("itemTyCd")
            doc.custom_zras_unit_of_quantity = "Pair"
            doc.additional_info = item.get("addInfo")
            doc.safety_quantity = item.get("sftyQty", "0")
            doc.manufacturer_tpin = item.get("manufactuterTpin", "1000000000")
            doc.manufacturer_item_code = item.get("manufacturerItemCd", "ZM2EA1234")
            doc.rrp = float(item.get("rrp", 0))
            doc.service_charge_applicable = item.get("svcChargeYn", "N") == "Y"
            doc.rental_applicable = item.get("rentalYn", "N") == "Y"
            doc.is_active = item.get("useYn", "Y") == "Y"
            doc.custom_zra_item_registered_="0"
            doc.owner = item.get("regrId", frm.get("owner", "DefaultOwner"))
            doc.custom_zra_item_registered_="1"
            doc.modified_by = item.get("modrId", frm.get("modified_by", "DefaultModifier"))

        try:
            # Save the document (either create a new item or update the existing one)
            doc.insert()
        except Exception as e:
            pass




def on_success_item_composition_submission(response: dict, document_name: str) -> None:
    frappe.db.set_value(
        "BOM", document_name, {"custom_has_item_composition_been_submitted_successfully": 1}
    )



def on_success_rrp_item_registration(response: dict, document_name: str) -> None:
    frappe.db.set_value("Item", document_name, {"custom_zra_item_registered_": 1})
    show_success_message(" RRP Item registration succesful")

import base64
from io import BytesIO

def convert_qr_code_to_base64(qr_code_data):
    """Convert QR code binary data from BytesIO to a base64 string."""
    if isinstance(qr_code_data, BytesIO):
        qr_code_data = qr_code_data.read()  # Read the content from BytesIO
    return base64.b64encode(qr_code_data).decode('utf-8')

def on_success_sales_information_submission(
    response: dict,
    invoice_type: str,
    document_name: str,
    company_name: str,
    invoice_number: int | str,
    tpin: str,
    branch_id: str = "00",
) -> None:
    try:
        response_data = response["data"]

        # Extracting the relevant fields from the response data
        receipt_signature = response_data["rcptSign"]
        receipt_number = response_data["rcptNo"]
        internal_data = response_data["intrlData"]
        control_unit_time = response_data["vsdcRcptPbctDate"]  # Make sure this is correct field
        # qr_code_url = response_data["qrCodeUrl"]

        # Encoding the URL for the QR Code generation
        encoded_url = requote_current_url(
            f"https://sandboxportal.zra.org.zm/common/link/ebm/receipt/indexEbmReceiptData?Data={tpin}{branch_id}{receipt_signature}"
        )

        # Fetch the QR code
        qr_code_data = fetch_qr_code(encoded_url)

        # If qr_code_data is in BytesIO format, convert to base64
        # qr_code = convert_qr_code_to_base64(qr_code_data)

        # Setting values in the database
        frappe.db.set_value(
            invoice_type,
            document_name,
            {
                "custom_receipt_number": receipt_number,
                "custom_zra_internal_data": internal_data,
                "custom_zra_receipt_signature": receipt_signature,
                "custom_zra_control_unit_time": control_unit_time,
                "custom_has_it_been_successfully_submitted": 1,
                "custom_zra_submission_sequence_number": invoice_number,
                "custom_zra_sales_invoice_qr_code": qr_code_data,
            },
        )
        show_success_message("The Sales Invoice has been succesfully registered on the ZRA Portal")


    except KeyError as e:
        # Handle missing fields from the response data
        frappe.throw(f"Missing expected field in the response: {str(e)}")
    except Exception as e:
        # Handle any other exceptions
        frappe.throw(f"An error occurred while processing the submission: {str(e)}")





def on_success_item_classification_search(response: dict) -> None:
    classification_codes = response.get("data", {}).get("itemClsList", [])
    success_codes = []  # To store successfully inserted item codes
    duplicate_codes = []  # To store duplicate item codes

    for classification_code in classification_codes:
        doc = frappe.new_doc("ZRA Item Classification")
        doc.item_classification_code = classification_code.get("itemClsCd")
        doc.item_classification_name = classification_code.get("itemClsNm")
        doc.item_classification_level = classification_code.get("itemClsLvl")
        doc.taxation_type_code = classification_code.get("taxTyCd")
        doc.is_major_target = classification_code.get("mjrTgYn") == "Y"
        doc.is_used = classification_code.get("useYn") == "Y"
        try:
            doc.insert(ignore_permissions=True)
            success_codes.append(classification_code.get("itemClsCd"))
        except frappe.exceptions.DuplicateEntryError:
            duplicate_codes.append(classification_code.get("itemClsCd"))

    # Generate messages using the modular functions
    success_message = success(success_codes)
    duplicate_message = duplicate(duplicate_codes)

    # Display the combined message
    frappe.msgprint(f"{success_message}<br>{duplicate_message}", title="ZRA Data Import Summary")




def on_succesfull_purchase_search_zra(response: dict) -> None:
    sales_list = response["data"]["saleList"]

    for sale in sales_list:
        created_record = create_purchase_from_search_details(sale)

        for item in sale["itemList"]:
            create_and_link_purchase_item(item, created_record)




def create_and_link_purchase_item(item: dict, parent_record: str) -> None:
    '''There is an issue with the way its creating items from fetched purchases. Need some fix.
    KRA is down and am very annoyed because its really wasting my whole time.'''
    item_cls_code = item["itemClsCd"]

    if not frappe.db.exists("ZRA Item Classification", item_cls_code):
        doc = frappe.new_doc("ZRA Item Classification")
        doc.itemclscd = item_cls_code
        doc.taxtycd = item["taxTyCd"]
        doc.save()

        item_cls_code = doc.name

    registered_item = frappe.new_doc("ZRA Registered Purchases")

    registered_item.parent = parent_record
    registered_item.parentfield = "items"
    registered_item.parenttype = "ZRA Registered Purchases"

    registered_item.item_name = item["itemNm"]
    registered_item.item_code = item["itemCd"]
    registered_item.item_sequence = item["itemSeq"]
    registered_item.item_classification_code = item_cls_code
    registered_item.barcode = item["bcd"]
    registered_item.package = item["pkg"]
    registered_item.packaging_unit_code = item["pkgUnitCd"]
    registered_item.quantity = item["qty"]
    registered_item.quantity_unit_code = item["qtyUnitCd"]
    registered_item.unit_price = item["prc"]
    registered_item.supply_amount = item["splyAmt"]
    registered_item.discount_rate = item["dcRt"]
    registered_item.discount_amount = item["dcAmt"]
    registered_item.taxation_type_code = item["taxTyCd"]
    registered_item.taxable_amount = item["taxblAmt"]
    registered_item.tax_amount = item["taxAmt"]
    registered_item.total_amount = item["totAmt"]

    registered_item.save()








def create_purchase_from_search_details(fetched_purchase: dict) -> str:
    existing_unique_id = check_duplicate_registered_purchase(fetched_purchase)
    if existing_unique_id:
        return existing_unique_id
    doc = frappe.new_doc("ZRA Registered Purchases")

    doc.supplier_name = fetched_purchase["spplrNm"]
    doc.supplier_pin = fetched_purchase["spplrTin"]
    doc.supplier_branch_id = fetched_purchase["spplrBhfId"]
    doc.supplier_invoice_number = fetched_purchase["spplrInvcNo"]

    doc.receipt_type_code = fetched_purchase["rcptTyCd"]
    doc.payment_type_code = frappe.get_doc(
        "ZRA Payment Method", {"code": fetched_purchase["pmtTyCd"]}, ["name"]
    ).name
    doc.remarks = fetched_purchase["remark"]
    doc.validated_date = fetched_purchase["cfmDt"]
    doc.sales_date = fetched_purchase["salesDt"]
    doc.stock_released_date = fetched_purchase["stockRlsDt"]
    doc.total_item_count = fetched_purchase["totItemCnt"]
    doc.taxable_amount_a = fetched_purchase["taxblAmtA"]
    doc.taxable_amount_b = fetched_purchase["taxblAmtB"]
    doc.taxable_amount_c = fetched_purchase["taxblAmtC"]
    doc.taxable_amount_d = fetched_purchase["taxblAmtD"]
    doc.taxable_amount_e = fetched_purchase["taxblAmtE"]

    doc.tax_rate_a = fetched_purchase["taxRtA"]
    doc.tax_rate_b = fetched_purchase["taxRtB"]
    doc.tax_rate_c = fetched_purchase["taxRtC"]
    doc.tax_rate_d = fetched_purchase["taxRtD"]
    doc.tax_rate_e = fetched_purchase["taxRtE"]

    doc.tax_amount_a = fetched_purchase["taxAmtA"]
    doc.tax_amount_b = fetched_purchase["taxAmtB"]
    doc.tax_amount_c = fetched_purchase["taxAmtC"]
    doc.tax_amount_d = fetched_purchase["taxAmtD"]
    doc.tax_amount_e = fetched_purchase["taxAmtE"]

    doc.total_taxable_amount = fetched_purchase["totTaxblAmt"]
    doc.total_tax_amount = fetched_purchase["totTaxAmt"]
    doc.total_amount = fetched_purchase["totAmt"]

    try:
        doc.submit()

    except frappe.exceptions.DuplicateEntryError:
        frappe.log_error(title="Duplicate entries")

    return doc.name



def check_duplicate_registered_purchase(fetched_purchase: dict) -> str:
    """
    Check if a Registered Purchase already exists based on a unique ID.

    Args:
        fetched_purchase (dict): The purchase details fetched from the source.

    Returns:
        str: The unique ID if the Registered Purchase exists, else None.
    """
   
    unique_id = f"{fetched_purchase['spplrTin']}-{fetched_purchase['spplrInvcNo']}"

    if frappe.db.exists("ZRA Registered Purchases", unique_id):
        frappe.log_error(
            title="Duplicate Registered Purchase",
            message=f"Purchase with ID {unique_id} already exists. Skipping creation."
        )
        return unique_id
    
    return None
