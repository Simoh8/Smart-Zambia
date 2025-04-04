// Copyright (c) 2024, Simon Muturi and contributors
// For license information, please see license.txt

frappe.ui.form.on("ZRA Smart Invoice Settings", {
  refresh(frm) {
    ensure_only_one_checkbox(frm);

    if (!frm.is_new() && frm.doc.is_active_) {
      const actions = [
        {
          label: __("Get Latest Notices"),
          method:
            "smart_zambia_invoice.smart_invoice.api.zra_api.perform_zra_notice_search",
          args: { 
            name: frm.doc.name,
            company_name: frm.doc.company_name },
        },
        {
          label: __("Update Codes"),
          method:
            "smart_zambia_invoice.smart_invoice.api.zra_api.perform_zra_item_code_classification_search",
          args: { name: frm.doc.name, company_name: frm.doc.company_name },
        },
  
      ];

      actions.forEach((action) => {
        frm.add_custom_button(
          action.label,
          () => {
            frappe.call({
              method: action.method,
              args: { request_data: action.args },
              callback: (response) => {
                // Handle callback
              },
              error: (error) => {
                // Error handling deferred to server
              },
            });
          },
          __("ZRA Actions")
        );
      });
    }


    frm.add_custom_button(
      __("Get Standard Codes"),
      () => {
        frappe.call({
          method:
            "smart_zambia_invoice.smart_invoice.background_jobs.jobs.refresh_code_lists",
          args: {},

          callback: (response) => {
            // Handle callback
          },
        });
      },
      __("ZRA Actions")
    );

    frm.add_custom_button(
        __("Get Item Codes"),
        () => {
          frappe.call({
            method:
              "smart_zambia_invoice.smart_invoice.background_jobs.jobs.get_item_classification_codes",
            args: {},
  
            callback: (response) => {
              // Handle callback
            },
          });
        },
        __("ZRA Actions")
      );

    frm.add_custom_button(
      __("Ping ZRA Server"),
      () => {
        frappe.call({
          method:
            "smart_zambia_invoice.smart_invoice.api.zra_api.ping_zra_server",
          args: { request_data: { server_url: frm.doc.server_url } },
          callback: (response) => {
            // Handle callback
          },
        });
      },
      __("ZRA Actions")
    );
  },

  sandbox(frm) {
    const sandboxFieldValue = parseInt(frm.doc.sandbox);
    const serverUrl =
      sandboxFieldValue === 1
        ? "http://localhost:8080/zrasandboxvsdc"
        : "http://kindatech.group:8080/zrasandboxvsdcs";
    frm.set_value("env", sandboxFieldValue === 1 ? "Sandbox" : "Production");
    frm.set_value("server_url", serverUrl);
  },

  sandboxtest_environment_: function (frm) {
    if (frm.doc.sandboxtest_environment_) {
      switch_environment(frm, "sandbox");
    }
  },

  production_environment_: function (frm) {
    if (frm.doc.production_environment_) {
      switch_environment(frm, "production");
    }
  },
});

// Ensure only one checkbox can be selected at a time
function ensure_only_one_checkbox(frm) {
  const checkboxes = ["sandboxtest_environment_", "production_environment_"];
  checkboxes.forEach((field) => {
    frm.set_df_property(field, "onchange", () => {
      checkboxes.forEach((cb) => {
        if (cb !== field) {
          frm.set_value(cb, 0); // Uncheck other checkboxes
        }
      });
    });
  });
}

// Function to switch between Sandbox and Production environments
function switch_environment(frm, env) {
  const isSandbox = env === "sandbox";
  frm.set_value(
    "server_url",
    isSandbox
      ? "http://localhost:8080/zrasandboxvsdc"
      : "http://kindatech.group:8080/zrasandboxvsdcs"
  );
  frm.set_value("environment", isSandbox ? "Sandbox" : "Production");
  frm.set_value(
    isSandbox ? "production_environment_" : "sandboxtest_environment_",
    0
  );
}
