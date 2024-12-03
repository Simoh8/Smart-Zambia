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
                if (response.message) {
                    // Success response
                    frappe.msgprint(__('Device initialization has been successful.'));
                }
            },
            error: function (err) {
                // Error response handling
                console.error('Device initialization failed:', err); // Log the error for debugging

                if (err.responseJSON && err.responseJSON._server_messages) {
                    // If the server returned a specific error message
                    const errorMessage = JSON.parse(err.responseJSON._server_messages).join('\n');
                    frappe.msgprint({
                        title: __('Error'),
                        message: __('Failed to initialize device. ') + errorMessage,
                        indicator: 'red'
                    });
                } else {
                    // If the error does not contain specific details, show a generic error
                    frappe.msgprint({
                        title: __('Error'),
                        message: __('Failed to initialize device. Check server logs for more details.'),
                        indicator: 'red'
                    });
                }
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
