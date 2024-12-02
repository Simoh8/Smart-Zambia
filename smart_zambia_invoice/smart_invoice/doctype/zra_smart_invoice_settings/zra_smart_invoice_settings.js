// Copyright (c) 2024, simon muturi and contributors
// For license information, please see license.txt

frappe.ui.form.on("ZRA Smart Invoice Settings", {
    refresh(frm) {
        ensure_only_one_checkbox(frm);

    },

    sandboxtest_environment_: function (frm) {
        if (frm.doc.sandboxtest_environment_) {
            frm.set_value('server_url', 'http://localhost:8080/zrasandboxvsdc');
            frm.set_value('environment', 'Sandbox');
            frm.set_value('production_environment_', 0);

        }
        else if (!frm.doc.sandboxtest_environment_) {
            frm.set_value('environment', 'Production');
            frm.set_value('server_url', 'http://kindatech.group:8080/zrasandboxvsdc');
        }
    },


    production_environment_: function (frm) {

        if (frm.doc.production_environment_) {
            frm.set_value('server_url', 'http://kindatech.group:8080/zrasandboxvsdcs');
            frm.set_value('environment', 'Production');
            frm.set_value('sandboxtest_environment_', 0);
        }
        else if (!frm.doc.production_environment_) {
            frm.set_value('server_url', 'http://localhost:8080/zrasandboxvsdc');
            frm.set_value('environment', 'Sandbox');
        }
    },
    after_save: async function (frm) {
        frappe.call({
            method: "smart_zambia_invoice.smart_invoice.utilities.initialize_device",
            args: {
                settings_doc_name: frm.doc.name,
            },
            callback: function (response) {
                if (response.message) {
                    // Success response
                    frappe.msgprint(__('Device initialization successful.'));
                }
            },
            error: function (err) {
                // Error response handling
                if (err.responseJSON && err.responseJSON._server_messages) {
                    // If the server returned a specific error message
                    const errorMessage = err.responseJSON._server_messages.join('\n');
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







frappe.ui.form.on("ZRA Smart Invoice Settings", {

});
