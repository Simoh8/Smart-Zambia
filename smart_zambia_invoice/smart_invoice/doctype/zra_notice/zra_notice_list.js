const doctypeName = 'ZRA Notice';

frappe.listview_settings[doctypeName] = {
  onload: function (listview) {
    const companyName = frappe.boot.sysdefaults.company;

    listview.page.add_inner_button(__('Get Latest Notices'), function (listview) {
      frappe.call({
        method:
          'smart_zambia_invoice.smart_invoice.api.zra_api.perform_zra_notice_search',
        args: {
          request_data: {
            company_name: companyName,
            
          },
        },
        callback: (response) => {},
        error: (error) => {
          // Error Handling is Defered to the Server
        },
      });
    });
  },
};
