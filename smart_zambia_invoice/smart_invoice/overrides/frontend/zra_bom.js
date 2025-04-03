const doctype = "BOM";

frappe.ui.form.on(doctype, {
  refresh: function (frm) {
    const companyName = frappe.boot.sysdefaults.company;

    let itemCode;

    frappe.db.get_value("Item", { name: frm.doc.item }, ["*"], (response) => {
      itemCode = response.custom_zra_item_code;
    });

    if (
      !frm.is_new() &&
      frm.doc.docstatus === 1 &&
      frm.doc.custom_has_item_composition_been_submitted_successfully != 1
    ) {
      frm.add_custom_button(
        __("Submit Item Composition"),
        function () {
          frappe.call({
            method:
              "smart_zambia_invoice.smart_invoice.api.zra_api.save_item_composition",
            args: {
              request_data: {
                name: frm.doc.name,
                company_name: companyName,
                item_name: frm.doc.item,
                quantity: frm.doc.quantity,
                registration_id: getUserID(frm.doc.owner),
                item_code: itemCode,
                items: frm.doc.items,
              },
            },
            callback: (response) => {
              frappe.msgprint("Request sent please refresh your browser")
            },
            error: (r) => {
              // Error Handling is Defered to the Server
            },
          });
        },
        __("ZRA VSDC Actions")
      );
    }
  },
});
