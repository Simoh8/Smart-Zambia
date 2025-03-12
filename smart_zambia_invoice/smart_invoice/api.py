import frappe

@frappe.whitelist()
def get_tableau_url(docname):
    """Fetch the Tableau URL for the given document."""
    try:
        tableau_url = frappe.db.get_value("Tableau", {"name": docname}, "tableau_url")
        return {"tableau_url": tableau_url} if tableau_url else {"error": "No URL found"}
    except Exception as e:
        return {"error": str(e)}
