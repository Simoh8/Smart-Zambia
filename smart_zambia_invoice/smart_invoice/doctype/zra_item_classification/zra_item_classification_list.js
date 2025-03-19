// const doctypeName = "ZRA Item Classification";

// frappe.listview_settings[doctypeName] = {
//   onload: function (listview) {
//     const companyName = frappe.boot.sysdefaults.company;

//     listview.page.add_inner_button(__(" Search Codes"), function (listview) {
//       frappe.call({
//         method:
//           "smart_zambia_invoice.smart_invoice.api.zra_api.perform_zra_item_code_classification_search",
//         args: {
//           request_data: {
//             company_name: companyName,
//           },
//         },
//         callback: (response) => {
//           frappe.msgprint("The request Has been Queued by the system please wait and refresh the tab")
//         },
//         error: (error) => {
//           // Error Handling is Defered to the Server
//         },
//       });
//     });
//   },
// };
