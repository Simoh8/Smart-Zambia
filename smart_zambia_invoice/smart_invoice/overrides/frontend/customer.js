// Copyright (c) 2024, simon muturi and contributors
// For license information, please see license.txt


const doctypeName = "Customer";

frappe.ui.form.on(doctypeName, {
  refresh: async function (frm) {
    const companyName = frappe.boot.sysdefaults.company;
    const getUserID = (email) => email.includes("@") ? email.split("@")[0] : email.substring(0, 20);


    // Only show the "Fetch Customer Details" button if custom_details_submitted_successfully is false
    if (!frm.is_new() && frm.doc.tax_id && frm.doc.custom_details_submitted_successfully) {
      frm.add_custom_button(
        __("Fetch Customer Details"),
        function () {
          frappe.call({
            method: "smart_zambia_invoice.smart_invoice.api.zra_api.fetch_customer_info",
            args: {
              request_data: {
                name: frm.doc.name,
                tax_id: frm.doc.tax_id,
                company_name: companyName,
              },
            },
            callback: (response) => {
              frappe.msgprint("Search queued. Please refresh the tab");
            },
            error: (r) => {
              // Error Handling is Deferred to the Server
            },
          });
        },
        __("ZRA Actions")
      );
    } else if (!frm.doc.custom_details_submitted_successfully) {
      // Only show the "Submit Customer Details" button if custom_details_submitted_successfully is false
      frm.add_custom_button(
        __("Submit Customer Details"),
        function () {
          frappe.call({
            method:
              "smart_zambia_invoice.smart_invoice.api.zra_api.submit_branch_customer_details",
            args: {
              request_data: {
                name: frm.doc.name,
                customer_pin: frm.doc.tax_id,
                customer_name: frm.doc.customer_name,
                company_name: companyName,
                registration_id: getUserID(frm.doc.owner),
                modifier_id: getUserID(frm.doc.modified_by),
                customer_remarks: frm.doc.customer_details || "",
                customer_address: frm.doc.custom_location_address || "", // Default empty string if missing
                customer_phone: frm.doc.custom_phone_number || "",  // Default empty string if missing
                customer_email: frm.doc.custom_email_address || ""  // Default empty string if missing
              },
            },
            callback: (response) => {
              frappe.msgprint("The request has been queud. Please referesh the tab")

            },
            error: (r) => {
              // Error Handling is Deferred to the Server
            },
          });
        },
        __("ZRA Actions")
      );
    }

    // Additional conditions (for insurance-related buttons, etc.) go here...
  },

  customer_group: function (frm) {
    frappe.db.get_value(
      "Customer Group",
      {
        name: frm.doc.customer_group,
      },
      ["custom_insurance_applicable"],
      (response) => {
        const customerGroupInsuranceApplicable =
          response.custom_insurance_applicable;

        if (customerGroupInsuranceApplicable) {
          frappe.msgprint(
            `The Customer Group ${frm.doc.customer_group} has Insurance Applicable on. Please fill the relevant insurance fields under Tax tab`
          );
          frm.toggle_reqd("custom_insurance_code", true);
          frm.toggle_reqd("custom_insurance_name", true);
          frm.toggle_reqd("custom_premium_rate", true);

          frm.set_value("custom_insurance_applicable", 1);
        } else {
          frm.toggle_reqd("custom_insurance_code", false);
          frm.toggle_reqd("custom_insurance_name", false);
          frm.toggle_reqd("custom_premium_rate", false);

          frm.set_value("custom_insurance_applicable", 0);
        }
      }
    );
  },
});
