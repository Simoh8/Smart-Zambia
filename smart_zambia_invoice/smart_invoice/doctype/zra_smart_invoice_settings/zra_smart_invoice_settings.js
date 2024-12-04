// Copyright (c) 2024, Simon Muturi and contributors
// For license information, please see license.txt

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

frappe.ui.form.on("ZRA Smart Invoice Settings", {
    refresh(frm) {
        ensure_only_one_checkbox(frm);
    },

    sandboxtest_environment_: function (frm) {
        if (frm.doc.sandboxtest_environment_) {
            switch_environment(frm, 'sandbox');
        }
    },

    production_environment_: function (frm) {
        if (frm.doc.production_environment_) {
            switch_environment(frm, 'production');
        }
    },

    after_save: async function (frm) {
        // Show an alert indicating the initialization is in progress
        frappe.show_alert({
            message: __('Device initialization is in progress...'),
            indicator: 'blue'
        }, 5); // Timeout in seconds

        // Make the API call to initialize the device
        frappe.call({
            method: "smart_zambia_invoice.smart_invoice.utilities.initialize_device_sync",
            args: {
                settings_doc_name: frm.doc.name,
            },
            callback: function (response) {
                if (response.message && response.message.success) {
                    // Success case
                    frappe.msgprint(__('Device initialization has been successful.'));
                } else {
                    // Error case
                    frappe.msgprint({
                        title: __('Error'),
                        message: response.message.message || __('Device initialization failed.'),
                        indicator: 'red'
                    });
                }
            },
            error: function (err) {
                // Network or server error
                console.error('Device initialization failed:', err);
                frappe.msgprint({
                    title: __('Error'),
                    message: __('An unexpected error occurred during device initialization. Check the server logs for details.'),
                    indicator: 'red'
                });
            }
        });
        
    }
});

// Function to switch between Sandbox and Production environments
function switch_environment(frm, env) {
    if (env === 'sandbox') {
        frm.set_value('server_url', 'http://localhost:8080/zrasandboxvsdc');
        frm.set_value('environment', 'Sandbox');
        frm.set_value('production_environment_', 0);
    } else if (env === 'production') {
        frm.set_value('server_url', 'http://kindatech.group:8080/zrasandboxvsdcs');
        frm.set_value('environment', 'Production');
        frm.set_value('sandboxtest_environment_', 0);
    }
}
