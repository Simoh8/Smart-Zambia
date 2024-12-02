// Copyright (c) 2024, simon muturi and contributors
// For license information, please see license.txt

frappe.ui.form.on("ZRA Smart Invoice Settings", {
    refresh(frm) {
        ensure_only_one_checkbox(frm);

    },

    sandboxtest_environment_: function (frm) {
        if (frm.doc.sandboxtest_environment_) {
            frm.set_value('server_url', 'http://localhost:8080/zrasandboxvsdc');
            frm.set_value('environment', 'sandbox');
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
            frm.set_value('environment', 'SandBox');
        }
    }

});


function ensure_only_one_checkbox(frm) {
    if (frm.doc.sandboxtest_environment_ && frm.doc.production_environment_) {
        frm.set_value('production_environment_', 0);
    }
}

