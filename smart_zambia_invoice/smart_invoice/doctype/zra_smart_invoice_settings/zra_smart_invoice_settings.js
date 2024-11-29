// Copyright (c) 2024, simon muturi and contributors
// For license information, please see license.txt

frappe.ui.form.on("ZRA Smart Invoice Settings", {
	refresh(frm) {
        const Company =frm.doc.Company;


        if (!frm.is_new() && doc.is_active){
            frm.add_custom_button(
                ('Fetch Notices'),
            )





        }








	},
});
