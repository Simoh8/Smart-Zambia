const itemDoctypName = 'Item';

frappe.ui.form.on(itemDoctypName, {
  refresh: function (frm) {
    const companyName = frappe.boot.sysdefaults.company;

    if (frm.doc.custom_zra_item_registered_) {
      frm.toggle_enable('custom_zra_item_classification_code', false);
      frm.toggle_enable('custom_zra_country_of_origin', false);
      frm.toggle_enable('custom_zra_tax_type', false);
      frm.toggle_enable('custom_zra_packaging_unit', false);
      frm.toggle_enable('custom_zras_unit_of_quantity', false);
      frm.toggle_enable('custom_zra_product_type_code', false);
    }

    if (frm.doc.custom_zra_imported_item_submitted_) {
      frm.toggle_enable('custom_zra_referenced_imported_item', false);
      frm.toggle_enable('custom_zra_imported_item_status', false);
    }

    if (!frm.is_new()) {
      if (
        !frm.doc.custom_zra_item_registered_ 
        // frm.doc.custom_item_classification &&
        // frm.doc.custom_taxation_type
      ) {
        frm.add_custom_button(
          __('Register Item'),
          function () {
            // call with all options
            frappe.call({
              method:
                'smart_zambia_invoice.smart_invoice.api.zra_api.make_zra_item_registration',
              args: {
                request_data: {
                  name: frm.doc.name,
                  company_name: companyName,
                  // itemCd: frm.doc.custom_zra_item_code,
                  itemCd: "ZM2NTBA0000012" ,

                  itemClsCd: frm.doc.custom_item_classification,
                  itemTyCd: frm.doc.custom_zra_product_type_code,
                  itemNm: frm.doc.item_name,
                  temStdNm: null,
                  orgnNatCd: frm.doc.custom_zra_country_origin_code,
                  pkgUnitCd: frm.doc.custom_zra_packaging_unit_code,
                  qtyUnitCd: frm.doc.custom_zra_unit_quantity_code,
                  taxTyCd: frm.doc.custom_zra_tax_type || 'B',
                  btchNo: null,
                  bcd: null,
                  dftPrc: frm.doc.valuation_rate.toFixed(2),
                  grpPrcL1: null,
                  grpPrcL2: null,
                  grpPrcL3: null,
                  grpPrcL4: null,
                  grpPrcL5: null,
                  addInfo: null,
                  sftyQty: null,
                  isrcAplcbYn: 'Y',
                  useYn: 'Y',
                  regrId: frm.doc.owner,
                  regrNm: frm.doc.owner,
                  modrId: frm.doc.modified_by,
                  modrNm: frm.doc.modified_by,
                },
              },
              callback: (response) => {
                frappe.msgprint(
                  'Item Registration Queued. Please check in later.',
                );
              },
              error: (error) => {
                // Error Handling is Defered to the Server
              },
            });
          },
          __('ZRA Actions'),
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

      if (
        frm.doc.custom_referenced_imported_item &&
        !frm.doc.custom_imported_item_submitted &&
        frm.doc.custom_item_classification &&
        frm.doc.custom_taxation_type
      ) {
        frm.add_custom_button(
          __('Submit Imported Item'),
          function () {
            frappe.call({
              method:
                'kenya_compliance.kenya_compliance.apis.apis.send_imported_item_request',
              args: {
                request_data: {
                  company_name: companyName,
                  name: frm.doc.name,
                  item_sequence: frm.doc.idx,
                  item_code: frm.doc.custom_zra_item_code,
                  task_code: frm.doc.custom_zra_imported_item_task_code,
                  item_classification_code: frm.doc.custom_zra_item_classification_code,
                  import_item_status: frm.doc.custom_zra_imported_item_status_code,
                  hs_code: frm.doc.custom_zra_hs_code,
                  modified_by: frm.doc.modified_by,
                  declaration_date: frm.doc.creation,
                },
              },
              callback: (response) => {
                frappe.msgprint('Request queued. Check later.');
              },
              error: (error) => {
                // Error Handling is Defered to the Server
              },
            });
          },
          __('ZRA Actions'),
        );
      }
    }
  },
  custom_product_type_name: function (frm) {
    if (frm.doc.custom_product_type_name === 'Service') {
      frm.set_value('is_stock_item', 0);
    } else {
      frm.set_value('is_stock_item', 1);
    }
  },
});
