// Copyright (c) 2024, simon muturi and contributors
// For license information, please see license.txt

// frappe.ui.form.on("ZRA Smart Invoice User", {
// 	refresh(frm) {


const doctypeName = "ZRA Smart Invoice User";

frappe.ui.form.on(doctypeName, {
  refresh: async function (frm) {
    const companyName = frappe.boot.sysdefaults.company;
    const getUserID = (email) => email.includes("@") ? email.split("@")[0] : email.substring(0, 20);


    if (!frm.is_new() && !frm.doc.registered_on_smart_invoice) {
      frm.add_custom_button(
        __("Submit Branch User Details"),
        function () {
          frappe.call({
            method:
              "smart_zambia_invoice.smart_invoice.api.zra_api.submit_zra_branch_user_details",
            args: {
              request_data: {
                name: frm.doc.name,
                company_name: companyName,
                user_id: frm.doc.system_user,
                full_names: frm.doc.full_name,
                branch_id: frm.doc.branch_id,
                registration_id: getUserID(frm.doc.owner),
                modifier_id: getUserID(frm.doc.modified_by),
              },
            },
            callback: (response) => {
              frappe.msgprint("Request queued. Please refresh the tab.");
            },
            error: (r) => {
              // Error Handling is Defered to the Server
            },
          });
        },
        __("ZRA Actions")
      );
    }
  },
});
