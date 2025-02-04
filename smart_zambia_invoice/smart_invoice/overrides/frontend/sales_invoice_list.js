const doctypeName = "Sales Invoice";

frappe.listview_settings[doctypeName].onload = function (listview) {
  listview.page.add_action_item(__("Bulk Submit to ZRA"), function () {
    bulkSubmitInvoices(listview, doctypeName);
  });
};

function bulkSubmitInvoices(listview, doctype) {
  const itemsToSubmit = listview.get_checked_items().map((item) => item.name);

  frappe.call({
    method:
      "smart_zambia_invoice.smart_invoice.api.zra_api.submit_bulk_sales_invoices",
    args: {
      docs_list: itemsToSubmit,
    },
    callback: (response) => {
      frappe.msgprint("Bulk submission queued.");
    },
    error: (r) => {
      // Error Handling is Defered to the Server
    },
  });
}
