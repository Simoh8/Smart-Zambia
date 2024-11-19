import frappe

def cleanup_custom_fields():

    custom_fields = frappe.get_all("Custom Field", filters={"dt":"Item", "dt":"Sales Invoice", "dt":"Sales Invoice Item", "dt":"Purchase Invoice"}, fields=["name"])

    for field in custom_fields:
        frappe.delete_doc("Custom Field", field["name"], ignore_missing=True)


    frappe.db.commit()