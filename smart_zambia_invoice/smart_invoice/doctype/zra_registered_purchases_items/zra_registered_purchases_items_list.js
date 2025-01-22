// Copyright (c) 2024, simon muturi and contributors
// For license information, please see license.txt

// frappe.ui.form.on("ZRA Registered Purchases Items", {
// 	refresh(frm) {

// 	},
// });
const doctypeName = "ZRA Registered Purchases";

frappe.listview_settings[doctypeName] = {
  onload: function (listview) {
    const companyName = frappe.boot.sysdefaults.company;

    listview.page.add_inner_button(
      __("Get Raised Purchases"),
      function (listview) {
        frappe.call({
          method:
            "smart_zambia_invoice.smart_invoice.api.zra_api.perform_purchases_search_on_zra",
          args: {
            request_data: {
              company_name: companyName,
            },
          },
          callback: (response) => { },
          error: (error) => {
            // Error Handling is Defered to the Server
          },
        });
      }
    );
  },
};
