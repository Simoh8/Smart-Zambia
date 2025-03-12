// frappe.listview_settings['Tableau'] = {
//     onload: function (listview) {
//         let tableau_url = "https://public.tableau.com/views/MojoesSchoolFile_Revamped/AcademicDashboard?:showVizHome=no&:embed=true";
//         let iframe = `<iframe width="100%" height="800px" style="width:100%; border:none;" src="${tableau_url}" allowfullscreen></iframe>`;

//         // Ensure it does not duplicate on refresh
//         if (!$(".tableau-dashboard").length) {
//             setTimeout(() => {
//                 $(".layout-main-section").html(`<div class="tableau-dashboard">${iframe}</div>`);
//             }, 500);
//         }
//     }
// };



frappe.listview_settings['Tableau'] = {
    onload: function (listview) {
        // Add the "Open Dashboard" button at the top
        if (!$(".open-dashboard-btn").length) {
            listview.page.add_inner_button('Open Dashboard', function () {
                let selected = listview.get_checked_items();
                if (selected.length > 0) {
                    frappe.call({
                        method: "smart_zambia_invoice.smart_invoice.api.get_tableau_url",
                        args: { docname: selected[0].name },
                        callback: function (response) {
                            console.log("API Response:", response);
                            if (response.message && response.message.tableau_url) {
                                let tableau_url = response.message.tableau_url;
                                let iframe = `<iframe width="100%" height="800px" style="width:100%; border:none;" src="${tableau_url}" allowfullscreen></iframe>`;

                                // Ensure it does not duplicate on refresh
                                if (!$(".tableau-dashboard").length) {
                                    setTimeout(() => {
                                        $(".layout-main-section").html(`
                                            <div class="tableau-dashboard">
                                                <button class="btn btn-danger close-dashboard" style="margin-bottom: 10px;">Close Dashboard</button>
                                                ${iframe}
                                            </div>
                                        `);
                                        
                                        // Add close button functionality
                                        $(".close-dashboard").click(function () {
                                            $(".tableau-dashboard").remove();
                                            
                                            // Redirect back to the list view
                                            frappe.set_route("List", "Tableau");
                                        });
                                    }, 500);
                                }
                            } else {
                                frappe.msgprint("No valid Tableau URL found for this entry.");
                            }
                        }
                    });
                } else {
                    frappe.msgprint("Please select an entry to view the dashboard.");
                }
            }).addClass("open-dashboard-btn");
        }
    }
};
