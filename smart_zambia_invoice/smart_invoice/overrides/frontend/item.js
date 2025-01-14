const itemDoctypName = "Item";

frappe.ui.form.on(itemDoctypName, {
  refresh: function (frm) {
    const companyName = frappe.boot.sysdefaults.company;

    // if (frm.doc.custom_zra_item_registered_) {
    //   frm.toggle_enable("custom_zra_item_classification_code", false);
    //   frm.toggle_enable("custom_zra_country_of_origin", false);
    //   frm.toggle_enable("custom_zra_tax_type", false);
    //   frm.toggle_enable("custom_zra_packaging_unit", false);
    //   frm.toggle_enable("custom_zras_unit_of_quantity", false);
    //   frm.toggle_enable("custom_zra_product_type_code", false);
    // }

    // if (frm.doc.custom_zra_imported_item_submitted_) {
    //   frm.toggle_enable("custom_zra_referenced_imported_item", false);
    //   frm.toggle_enable("custom_zra_imported_item_status", false);
    // }

    if (!frm.is_new()) {
      if (!frm.doc.custom_zra_item_registered_) {


        frm.add_custom_button(
          __("Register/Update Item"),
          function () {
            // call with all options
            frappe.call({
              method:
                "smart_zambia_invoice.smart_invoice.api.zra_api.make_zra_item_registration",
              args: {
                request_data: {
                  name: frm.doc.name,
                  company_name: companyName,
                  itemCd: frm.doc.custom_zra_item_code,
                  itemClsCd: frm.doc.custom_zra_item_classification_code,
                  itemTyCd: frm.doc.custom_product_code,
                  itemNm: frm.doc.item_name,
                  temStdNm: frm.doc.item_name,
                  orgnNatCd: frm.doc.custom_zra_country_origin_code,
                  pkgUnitCd: frm.doc.custom_zra_packaging_unit_code,
                  qtyUnitCd: frm.doc.custom_zra_unit_quantity_code,
                  vatCatCd: frm.doc.custom_zra_tax_type,
                  iplCatCd: null,
                  tlCatCd: null,
                  exciseTxCatCd: null,
                  btchNo: null,
                  bcd: null,
                  dftPrc: frm.doc.valuation_rate.toFixed(2),
                  addInfo: null,
                  sftyQty: "0",
                  manufactuterTpin: "1000000000",
                  manufacturerItemCd: "ZM2EA1234",
                  rrp: "1000.0",
                  svcChargeYn: "Y",
                  rentalYn: "N",
                  useYn: "Y",
                  regrId: frm.doc.owner,
                  regrNm: frm.doc.owner,
                  modrId: frm.doc.modified_by,
                  modrNm: frm.doc.modified_by,
                },
              },
              callback: (response) => {
                frappe.msgprint(
                  "Item Registration Queued. Please refresh the browser tab."
                );
              },
              error: (error) => {
                // Error Handling is Defered to the Server
              },
            });
          },
          __("ZRA Actions")
        );
      }
      // if (frm.doc.is_stock_item) {
      //   frm.add_custom_button(
      //     __('Submit Item Inventory'),
      //     function () {
      //       frappe.call({
      //         method:
      //           'kenya_compliance.kenya_compliance.apis.apis.submit_inventory',
      //         args: {
      //           request_data: {
      //             company_name: companyName,
      //             name: frm.doc.name,
      //             itemName: frm.doc.item_code,
      //             itemCd: frm.doc.custom_item_code_etims,
      //             registered_by: frm.doc.owner,
      //             modified_by: frm.doc.modified_by,
      //             // TODO: Fix the branch id below
      //             branch_id: '00',
      //           },
      //         },
      //         callback: (response) => {
      //           frappe.msgprint('Inventory submission queued.');
      //         },
      //         error: (error) => {
      //           // Error Handling is Defered to the Server
      //         },
      //       });
      //     },
      //     __('ZRA Actions'),
      //   );
      // }

      if (!frm.doc.custom_zra_item_registered_) {
        frm.add_custom_button(
          __("Submit Imported Item"),
          function () {
            frappe.call({
              method:
                "smart_zambia_invoice.smart_invoice.api.zra_api.make_zra_item_registration",
              args: {
                request_data: {
                  company_name: companyName,
                  name: frm.doc.name,
                  item_sequence: frm.doc.idx,
                  item_code: frm.doc.custom_zra_item_code,
                  task_code: frm.doc.custom_zra_imported_item_task_code,
                  item_classification_code:
                    frm.doc.custom_zra_item_classification_code,
                  import_item_status:
                    frm.doc.custom_zra_imported_item_status_code,
                  hs_code: frm.doc.custom_zra_hs_code,
                  modified_by: frm.doc.modified_by,
                  declaration_date: frm.doc.creation,
                },
              },
              callback: (response) => {
                frappe.msgprint("Request queued. Check later.");
              },
              error: (error) => {
                // Error Handling is Defered to the Server
              },
            });
          },
          __("ZRA Actions")
        );
      }
    }
  },
  custom_product_type_name: function (frm) {
    if (frm.doc.custom_product_type_name === "Service") {
      frm.set_value("is_stock_item", 0);
    } else {
      frm.set_value("is_stock_item", 1);
    }
  },
});
