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
      if (
        !frm.doc.custom_zra_item_registered_ &&
        !frm.doc.custom_has_a_recommended_retail_price_rrp_
      ) {
        frm.add_custom_button(
          __("Register/Update Item"),
          function () {
            let taxType = frm.doc.custom_zra_tax_type || null;
            let vatCatCd = null;
            let iplCatCd = null;
            let tlCatCd = null;
            let exciseTxCatCd = null;

            // VAT Category Mapping
            if (
              ["A", "B", "C1", "C2", "C3", "D", "E", "RVAT"].includes(taxType)
            ) {
              vatCatCd = taxType;
            }

            // Insurance Premium Levy Mapping
            if (["IPL1", "IPL2"].includes(taxType)) {
              iplCatCd = taxType;
            }

            if (taxType === "TOT") {
              tlCatCd = taxType;
            }

            // Tourism Levy Mapping
            if (["TL", "F"].includes(taxType)) {
              tlCatCd = taxType;
            }

            // Excise Tax Mapping
            if (["ECM", "EXEEG"].includes(taxType)) {
              exciseTxCatCd = taxType;
            }

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
                  itemStdNm: frm.doc.item_name,
                  orgnNatCd: frm.doc.custom_zra_country_origin_code,
                  pkgUnitCd: frm.doc.custom_zra_packaging_unit_code,
                  qtyUnitCd: frm.doc.custom_zra_unit_quantity_code,
                  vatCatCd: vatCatCd,
                  iplCatCd: iplCatCd,
                  tlCatCd: tlCatCd,
                  exciseTxCatCd: exciseTxCatCd,
                  btchNo: null,
                  bcd: null,
                  dftPrc: frm.doc.valuation_rate.toFixed(2),
                  addInfo: null,
                  sftyQty: "0",
                  manufactuterTpin: "1000000000",
                  manufacturerItemCd: "ZM2EA1234",
                  rrp: frm.doc.custom_recommended_retail_price,
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
                // Error Handling is Deferred to the Server
              },
            });
          },
          __("ZRA Actions")
        );
      }
      if (frm.doc.is_stock_item) {
        frm.add_custom_button(
          __("ZRA Item Inventory Submission"),
          function () {
            frappe.call({
              method:
                "smart_zambia_invoice.smart_invoice.api.zra_api.save_stock_inventory",
              args: {
                request_data: {
                  company_name: companyName,
                  name: frm.doc.name,
                  itemName: frm.doc.item_code,
                  remainq: frm.doc.stock_levels,
                  itemCd: frm.doc.custom_zra_item_classification_code,
                  registered_by: frm.doc.owner,
                  modified_by: frm.doc.modified_by,
                },
              },
              callback: (response) => {},
              error: (error) => {
                // Error Handling is Defered to the Server
              },
            });
          },
          __("ZRA Actions")
        );
      }
      if (
        frm.doc.custom_has_a_recommended_retail_price_rrp_ &&
        !frm.doc.custom_zra_item_registered_
      ) {
        frm.add_custom_button(
          __("Submit RRP Item"),
          function () {
            let originalItemName = frm.doc.item_name || "";

            // Ensure item name is a valid string and trim if necessary
            let shortenedItemName = originalItemName.substring(0, 200);

            frappe.call({
              method:
                "smart_zambia_invoice.smart_invoice.api.zra_api.make_rrp_item_registration",
              args: {
                request_data: {
                  name: frm.doc.name,
                  company_name: companyName,
                  itemCd: frm.doc.custom_zra_item_code,
                  itemClsCd: frm.doc.custom_zra_item_classification_code,
                  itemTyCd: frm.doc.custom_product_code,
                  itemNm: shortenedItemName, 
                  taxTyCd: frm.doc.custom_zra_tax_type,
                  orgnNatCd: frm.doc.custom_zra_country_origin_code,
                  pkgUnitCd: frm.doc.custom_zra_packaging_unit_code,
                  qtyUnitCd: frm.doc.custom_zra_unit_quantity_code,
                  rrp: frm.doc.standard_rate,
                  useYn: "Y",
                  regrId: frm.doc.owner,
                  regrNm: frm.doc.owner,
                  modrId: frm.doc.modified_by,
                  modrNm: frm.doc.modified_by,
                },
              },
              callback: (response) => {
                frappe.msgprint("Request queued. Please Refresh your tab");
              },
              error: (error) => {
                console.error("Error:", error);
              },
            });
          },
          __("ZRA Actions")
        );
      }

      // if (!frm.doc.custom_zra_item_registered_) {
      //   frm.add_custom_button(
      //     __("Submit Imported Item"),
      //     function () {
      //       frappe.call({
      //         method:
      //           "smart_zambia_invoice.smart_invoice.api.zra_api.make_zra_item_registration",
      //         args: {
      //           request_data: {
      //             company_name: companyName,
      //             name: frm.doc.name,
      //             item_sequence: frm.doc.idx,
      //             item_code: frm.doc.custom_zra_item_code,
      //             task_code: frm.doc.custom_zra_imported_item_task_code,
      //             item_classification_code:frm.doc.custom_zra_item_classification_code,
      //             import_item_status:frm.doc.custom_zra_imported_item_status_code,
      //             hs_code: frm.doc.custom_zra_hs_code,
      //             modified_by: frm.doc.modified_by,
      //             declaration_date: frm.doc.creation,
      //           },
      //         },
      //         callback: (response) => {
      //           frappe.msgprint("Request queued. Check later.");
      //         },
      //         error: (error) => {
      //           // Error Handling is Defered to the Server
      //         },
      //       });
      //     },
      //     __("ZRA Actions")
      //   );
      // }
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
