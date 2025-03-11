const doctypeName = 'Item';

frappe.listview_settings[doctypeName].onload = function (listview) {
  const companyName = frappe.boot.sysdefaults.company;

  listview.page.add_inner_button(__('Get Imported Items'), function (listview) {
    frappe.call({
      method:
      "smart_zambia_invoice.smart_invoice.api.zra_api.perform_import_item_search",
      args: {
        request_data: {
          company_name: companyName,
        },
      },
      callback: (response) => {},
      error: (r) => {
        // Error Handling is Defered to the Server
      },
    });
  });
  // listview.page.add_inner_button(__('Fetch Registered Products'), function (listview) {
  //   frappe.call({
  //     method:
  //     "smart_zambia_invoice.smart_invoice.api.zra_api.fetch_Previous_registered_zra_items",
  //     args: {
  //       request_data: {
  //         company_name: companyName,
  //       },
  //     },
  //     callback: (response) => {},
  //     error: (r) => {
  //       // Error Handling is Defered to the Server
  //     },
  //   });
  // });


  listview.page.add_action_item(__('Bulk Register Items'), function () {
    const itemsToRegister = listview
      .get_checked_items()
      .map((item) => item.name);

    frappe.call({
      method: 'smart_zambia_invoice.smart_zambia.api.zra_api.bulk_register_item',
      args: {
        docs_list: itemsToRegister,
      },
      callback: (response) => {
        frappe.msgprint('Bulk submission queued.');
      },
      error: (r) => {
        // Error Handling is Defered to the Server
      },
    });
  });
};
