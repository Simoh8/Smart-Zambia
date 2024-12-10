
frappe.ui.form.on('ZRA Smart Invoice Settings', {
    refresh: function (frm) {
      const companyName = frm.doc.company;
  
      if (!frm.is_new() && frm.doc.is_active) {
        frm.add_custom_button(
          __('Get Latest Notices'),
          function () {
            frappe.call({
                method: 'smart_zambia_invoice.smart_invoice.api.zra_api.perform_zra_notice_search',

              args: {
                request_data: {
                  name: frm.doc.name,
                  company_name: companyName,
                },
              },
              callback: (response) => {},
              error: (error) => {
                // Error Handling is Defered to the Server
              },
            });
          },
          __('ZRA Actions'),
        );
  
        frm.add_custom_button(
          __('Update Codes'),
          function () {
            frappe.call({
                method: 'smart_zambia_invoice.smart_invoice.api.zra_api.ping_zra_server',

              args: {
                request_data: {
                  name: frm.doc.name,
                  company_name: companyName,
                },
              },
              callback: (response) => {},
              error: (error) => {
                // Error Handling is Defered to the Server
              },
            });
          },
          __('ZRA Actions'),
        );
  
        frm.add_custom_button(
          __('Get Item Classification Codes'),
          function () {
            frappe.call({
                method: 'smart_zambia_invoice.smart_invoice.api.zra_api.ping_zra_server',

              args: {},
              callback: (response) => {},
              error: (error) => {
                // Error Handling is Defered to the Server
              },
            });
          },
          __('ZRA Actions'),
        );
  
        frm.add_custom_button(
          __('Update Stock Movements'),
          function () {
            frappe.call({
              method: 'smart_zambia_invoice.smart_invoice.api.zra_api.ping_zra_server',
              args: {
                request_data: {
                  name: frm.doc.name,
                  company_name: companyName,
                  branch_id: frm.doc.bhfid,
                },
              },
              callback: (response) => {},
              error: (error) => {
                // Error Handling is Defered to the Server
              },
            });
          },
          __('ZRA Actions'),
        );
      }
  
      frm.add_custom_button(
        __('Ping ZRA Server'),
        function () {
          frappe.call({
            method: 'smart_zambia_invoice.smart_invoice.api.zra_api.ping_zra_server',
            
            args: {
              request_data: {
                server_url: frm.doc.server_url,
              },
            },
          });
        },
        __('ZRA Actions'),
      );
  
      frm.set_query('bhfid', function () {
        return {
          filters: [['Branch', 'custom_is_etims_branch', '=', 1]],
        };
      });
    },
    sandbox: function (frm) {
      const sandboxFieldValue = parseInt(frm.doc.sandbox);
      const sandboxServerUrl = 'http://localhost:8080/zrasandboxvsdc'
      const productionServerUrl ='http://kindatech.group:8080/zrasandboxvsdcs';
  
      if (sandboxFieldValue === 1) {
        frm.set_value('env', 'Sandbox');
        frm.set_value('server_url', sandboxServerUrl);
      } else {
        frm.set_value('env', 'Production');
        frm.set_value('server_url', productionServerUrl);
      }
    },
  });
  