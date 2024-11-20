import frappe

def cleanup_custom_fields():
    doctypes = [
        "Item",
        "Sales Invoice",
        "Sales Invoice Item",
        "Purchase Invoice",
        "Stock Ledger Entry",
        "Customer",
        "Item Tax Template",
        "Warehouse",
        "Branch",
        "Purchase Invoice Item",
        "Customer Group",
        "Supplier",
    ]
    custom_fields = frappe.get_all("Custom Field", filters= {"dt":["in",doctypes]}, fields=["name"])

    for field in custom_fields:
        frappe.delete_doc("Custom Field", field["name"], ignore_missing=True)


    frappe.db.commit()