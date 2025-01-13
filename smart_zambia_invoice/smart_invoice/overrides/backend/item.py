import json

import deprecation

import frappe
import frappe.defaults
from frappe.model.document import Document

from .... import __version__
from ...api.zra_api import make_zra_item_registration
from ...utilities import split_user_mail,generate_next_item_code


@deprecation.deprecated(
    deprecated_in="0.6.2",
    removed_in="1.0.0",
    current_version=__version__,
    details="Use the Register Item button in Item record",
)




def before_insert(doc: Document, method: str) -> None:
    """Item doctype before insertion hook"""
    
    # Generate a unique item code if not provided
    if not doc.custom_zra_item_code:
        # Retrieve required fields for generating the item code
        country_code = doc.custom_zra_country_origin_code or "ZZ"  # Default to "ZZ" if missing
        product_type = doc.custom_zra_product_type_code or "0"     # Default to "0" if missing
        packaging_unit = doc.custom_zra_packaging_unit_code or "XX"  # Default to "XX" if missing
        quantity_unit = doc.custom_zra_unit_quantity_code or "YY"   # Default to "YY" if missing
        
        # Generate the next item code
        doc.custom_zra_item_code = generate_next_item_code(
            country_code, product_type, packaging_unit, quantity_unit
        )
    
    # Prepare the registration data
    item_registration_data = {
        "name": doc.name,
        "company_name": frappe.defaults.get_user_default("Company"),
        "itemCd": "hello",
        "itemClsCd": doc.custom_zra_item_classification_code,
        "itemTyCd": doc.custom_zra_product_type_code,
        "itemNm": doc.item_name,
        "temStdNm": None,
        "orgnNatCd": doc.custom_zra_country_origin_code,
        "pkgUnitCd": doc.custom_zra_packaging_unit_code,
        "qtyUnitCd": doc.custom_zra_unit_quantity_code,
        "taxTyCd": "B" if not doc.custom_zra_tax_type else doc.custom_zra_tax_type,
        "btchNo": None,
        "bcd": None,
        "dftPrc": doc.valuation_rate,
        "grpPrcL1": None,
        "grpPrcL2": None,
        "grpPrcL3": None,
        "grpPrcL4": None,
        "grpPrcL5": None,
        "addInfo": None,
        "sftyQty": "demo",
        "isrcAplcbYn": "Y",
        "useYn": "Y",
        "regrId": split_user_mail(doc.owner),
        "regrNm": doc.owner,
        "modrId": split_user_mail(doc.modified_by),
        "modrNm": doc.modified_by,
    }

    # Make the ZRA item registration request
    make_zra_item_registration(json.dumps(item_registration_data))



def validate(doc: Document, method: str) -> None:
    """
    Generates a unique item code for the CIS compliance.
    Format: {Country of Origin}{Product Type}{Packaging Unit}{Quantity Unit}{Incremented Number}
    Example: ZM2NTBA0000012
    """
    # Step 1: Validate required fields for prefix generation
    required_fields = {
        "Country of Origin Code": doc.custom_zra_country_of_origin,
        "Product Type Code": doc.custom_zra_product_type_code,
        "Packaging Unit Code": doc.custom_zra_packaging_unit,
        "Quantity Unit Code": doc.custom_zras_unit_of_quantity,
    }

    missing_fields = [key for key, value in required_fields.items() if not value]
    if missing_fields:
        frappe.throw(f"Missing required fields for item code generation: {', '.join(missing_fields)}")

    # Step 2: Generate the prefix
    prefix = (
        f"{doc.custom_zra_country_origin_code}"
        f"{doc.custom_product_code}"
        f"{doc.custom_zra_packaging_unit}"
        f"{doc.custom_zras_unit_of_quantity}"
    )

    # Step 3: Check if the item already has a code and extract suffix if present
    if doc.custom_zra_item_code and doc.custom_zra_item_code.startswith(prefix):
        # Extract the numeric suffix
        suffix = doc.custom_zra_item_code[-7:]
    else:
        # Query the last item code with the same prefix
        last_code = frappe.db.sql(
            """
            SELECT custom_zra_item_code
            FROM `tabItem`
            WHERE custom_zra_item_code LIKE %s
            ORDER BY CAST(SUBSTRING(custom_zra_item_code, -7) AS UNSIGNED) DESC
            LIMIT 1
            """,
            (f"{prefix}%",),
            as_dict=True,
        )

        # Increment the suffix or start from '0000001'
        if last_code:
            last_suffix = int(last_code[0]["custom_zra_item_code"][-7:])
            suffix = str(last_suffix + 1).zfill(7)
        else:
            suffix = "0000001"

    # Step 4: Combine the prefix and suffix to form the complete item code
    doc.custom_zra_item_code = f"{prefix}{suffix}"

    # Optional: Log the generated code for audit
    frappe.logger().info(
        f"Generated item code {doc.custom_zra_item_code} for item {doc.name}"
    )
