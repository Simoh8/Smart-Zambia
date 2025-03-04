frappe.listview_settings['Purchase Invoice'] = {
    onload: function (listview) {
        listview.page.add_inner_button(__('Fetch Purchase Invoices'), function () {
            frappe.call({
                method: "smart_zambia_invoice.smart_invoice.api.zra_api.perform_purchases_search_on_zra",
                args: {
                    request_data: { company_name: frappe.boot.sysdefaults.company },
                },
                freeze: true,
                freeze_message: __("Fetching Purchase Invoices..."),
                callback: (response) => {
                    frappe.msgprint(__('Purchase invoices fetched successfully!'));
                    listview.refresh();
                }
            });
        });
    }
};

async function fetch_purchase_invoices() {
    const { message } = await frappe.call({
        method: 'smart_zambia_invoice.smart_invoice.api.zra_api.perform_purchases_search_on_zra',
        freeze: true,
        freeze_message: __("Fetching Purchase Invoices..."),
    });

    if (message) {
        frappe.msgprint(__('Purchase invoices fetched successfully!'));
        frappe.listview.refresh();
    }
}
