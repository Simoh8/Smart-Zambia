const doctype = "Branch";

frappe.ui.form.on(doctype, {
  refresh: function (frm) {
    const companyName = frappe.boot.sysdefaults.company;

    frm.add_custom_button(
      __("Fetch Imported Items"),
      function () {
        frappe.call({
          method:
            "smart_zambia_invoice.smart_invoice.api.zra_api.perform_import_item_search",
          args: {
            request_data: {
              company_name: companyName,
              branch_code: frm.doc.custom_branch_code,
            },
          },
          callback: (response) => {},
          error: (error) => {
            // Error Handling is Defered to the Server
          },
        });
      },
      __("ZRA Actions")
    );
  },
});
