const parentDoctype = 'Sales Invoice';
const childDoctype = `${parentDoctype} Item`;
const packagingUnitDoctypeName = 'ZRA Packaging Unit';
const unitOfQuantityDoctypeName = 'ZRA Unit of Quantity';
const taxationTypeDoctypeName = 'ZRA Tax Type';
const settingsDoctypeName = 'ZRA Smart Invoice Settings';

// frappe.ui.form.on(parentDoctype, {
//   refresh: function (frm) {
//     const companyName = frappe.boot.sysdefaults.company;

//     frm.set_value('update_stock', 1);

//     if (frm.doc.update_stock === 1) {
//       frm.toggle_reqd('set_warehouse', true);
//     }

//     // Add "Submit Invoice" button
//     if (!frm.is_new() && frm.doc.docstatus === 1 && !frm.doc.custom_has_it_been_successfully_submitted) {
//       frm.add_custom_button(__('ZRA Submit Invoice'), function () {
//         // Call the custom method to handle invoice submission
//         let sales_trans_code = frm.doc.is_return;
//         let debit_note_code = frm.doc.is_debit_note;
//         let is_refund=frm.doc.custom_funds_refunded_
//         let postingDateTime = frappe.datetime.str_to_user(frm.doc.posting_date); // Convert to user format
//         let formattedPostingDate = formatToDateOnly(postingDateTime); // "yyyyMMdd"
//         let formattedPostingDateTime = formatToFullTimestamp(postingDateTime); // "

//         // Convert to required formats
//         function formatToFullTimestamp(dateStr) {
//             return dateStr.replace(/[-:\s]/g, ""); // Converts "2024-02-03 15:30:45" → "20240203153045"
//         }
//         function formatToDateOnly(dateStr) {
//             return dateStr.replace(/[-]/g, "");    // Converts "2024-02-03" → "20240203"
//         }

//         let formattedNow = formatToFullTimestamp(now);
//         let formattedToday = formatToDateOnly(today);


//         frappe.call({
//           method: 'smart_zambia_invoice.smart_invoice.api.zra_api.perform_sales_invoice_registration',
//           args: {
//             request_data: {

//               name: frm.doc.name,
//               orgInvcNo: "0",
//               company_name: companyName,
//               cisInvcNo: frm.doc.name,
//               custTpin: frm.doc.tax_id,
//               custNm: frm.doc.customer,
//               salesTyCd: "N",
              
//               rcptTyCd: debit_note_code ? "D" : sales_trans_code ? "R" : "S",
//               pmtTyCd: frm.doc.custom_zra_payment_code,
//               salesSttsCd: frm.doc.custom_progress_status_code,
//               cfmDt: frm.doc.status === "Cancelled" ? frm.doc.posting_date : formattedNow,
//               salesDt: formattedPostingDate,
//               stockRlsDt: formattedPostingDateTime,
//               cnclReqDt: frm.doc.status === "Cancelled" ? formattedNow : formattedNow,
//               cnclDt: frm.doc.status === "Cancelled" ? formattedNow : formattedNow,
//               rfdDt: is_refund ? formattedNow : formattedNow,
//               rfdRsnCd: frm.doc.custom_zra_credit_note_reason,
//               totItemCnt: frm.doc.items.length,
//               "taxblAmtA": 86.2069,
//               "taxblAmtB": 0.0,
//               "taxblAmtC1": 0.0,
//               "taxblAmtC2": 0.0,
//               "taxblAmtC3": 0.0,
//               "taxblAmtD": 0.0,
//               "taxblAmtRvat": 0.0,
//               "taxblAmtE": 0.0,
//               "taxblAmtF": 0.0,
//               "taxblAmtIpl1": 0.0,
//               "taxblAmtIpl2": 100,
//               "taxblAmtTl": 0.0,
//               "taxblAmtEcm": 0,
//               "taxblAmtExeeg": 0.0,
//               "taxblAmtTot": 0.0,
//               "taxRtA": 16,
//               "taxRtB": 16,
//               "taxRtC1": 0,
//               "taxRtC2": 0,
//               "taxRtC3": 0,
//               "taxRtD": 0,
//               "tlAmt": 0.0,
//               "taxRtRvat": 16,
//               "taxRtE": 0,
//               "taxRtF": 10,
//               "taxRtIpl1": 5,
//               "taxRtIpl2": 0,
//               "taxRtTl": 1.5,
//               "taxRtEcm": 5,
//               "taxRtExeeg": 3,
//               "taxRtTot": 0,
//               "taxAmtA": 13.7931,
//               "taxAmtB": 0.0,
//               "taxAmtC1": 0.0,
//               "taxAmtC2": 0.0,
//               "taxAmtC3": 0.0,
//               "taxAmtD": 0.0,
//               "taxAmtRvat": 0.0,
//               "taxAmtE": 0.0,
//               "taxAmtF": 0.0,
//               "taxAmtIpl1": 0.0,
//               "taxAmtIpl2": 0.0,
//               "taxAmtTl": 0.0,
//               "taxAmtEcm": 0.0,
//               "taxAmtExeeg": 0.0,
//               "taxAmtTot": 0.0,
//               "totTaxblAmt": 186.2069,
//               "totTaxAmt": 13.7931,
//               "cashDcRt": 25,
//               "cashDcAmt": 50,
//               "totAmt": 150,
//               "prchrAcptcYn": "N",
//               "remark": null,
//               regrId: split_user_mail(data["owner"]),
//               regrNm: data["owner"],
//               modrId: split_user_mail(data["owner"]),
//               modrNm: data["owner"],
//               "saleCtyCd": "2",
//               "lpoNumber": null,
//               "currencyTyCd": "ZMW",
//               // "exchangeRt": "1", its a mandatory item in the sale invoice 
//               "destnCountryCd": null,
//               "dbtRsnCd": null,
//               "invcAdjustReason": null,
//               itemList: frm.doc.items.map(item => ({
//                 itemSeq: item.idx,
//                 itemCd: item.item_code,
//                 itemClsCd: item.item_class_code,
//                 itemNm: item.item_name,
//                 bcd: item.barcode || "",
//                 pkgUnitCd: item.pkg_unit_code,
//                 pkg: item.pkg || 0.0,
//                 qtyUnitCd: item.qty_unit_code,
//                 qty: item.qty || 1.0,
//                 prc: item.price || 0.0,
//                 splyAmt: item.supply_amount || 0.0,
//                 dcRt: item.discount_rate || 0.0,
//                 dcAmt: item.discount_amount || 0.0,
//                 isrccCd: item.isrc_code || "",
//                 isrccNm: item.isrc_name || "",
//                 isrcRt: item.isrc_rate || 0.0,
//                 isrcAmt: item.isrc_amount || 0.0,
//                 vatCatCd: item.vat_category_code || "A",
//                 exciseTxCatCd: item.excise_tx_category_code || null,
//                 tlCatCd: item.tl_category_code || null,
//                 iplCatCd: item.ipl_category_code || null,
//                 vatTaxblAmt: item.vat_taxable_amount || 0.0,
//                 vatAmt: item.vat_amount || 0.0,
//                 exciseTaxblAmt: item.excise_taxable_amount || 0.0,
//                 tlTaxblAmt: item.tl_taxable_amount || 0.0,
//                 iplTaxblAmt: item.ipl_taxable_amount || 0.0,
//                 iplAmt: item.ipl_amount || 0.0,
//                 tlAmt: item.tl_amount || 0.0,
//                 exciseTxAmt: item.excise_tax_amount || 0.0,
//                 totAmt: item.total_amount || 0.0
//             }))
//             }
//           },
//           callback: function (response) {
//             if (response.message) {
//               frappe.msgprint(__('Invoice submitted successfully: ') + response.message);
//               frm.reload_doc(); // Reload the document after submission
//             }
//           },
//           error: function (error) {
//             frappe.msgprint(__('An error occurred while submitting the invoice.'));
//             console.error(error);
//           },
//         });


//       }).addClass('btn-primary'); // Add a primary button style
//     }
//   },

// });

frappe.ui.form.on(parentDoctype, {
  refresh: function (frm) {
    frm.set_value('update_stock', 1);
    if (frm.doc.update_stock === 1) {
      frm.toggle_reqd('set_warehouse', true);
    }
  },
  validate: function (frm) {
    frappe.db.get_value(
      settingsDoctypeName,
      {
        is_active_: 1,
        bhfid: frm.doc.branch,
        company_name: frappe.defaults.get_user_default('Company'),
      },
      [
        'name',
        'company_name',
        'branch_id',
      ],
      (response) => {
       
      },
    );
  },
});



frappe.ui.form.on(childDoctype, {
  item_code: function (frm, cdt, cdn) {
    const item = locals[cdt][cdn].item_code;
    const taxationType = locals[cdt][cdn].custom_zra_tax_type;

    if (!taxationType) {
      frappe.db.get_value(
        'Item',
        { item_code: item },
        ['custom_zra_tax_type'],
        (response) => {
          locals[cdt][cdn].custom_zra_tax_type = response.custom_zra_tax_type;
          locals[cdt][cdn].custom_taxation_type_code =
            response.custom_zra_tax_type;
        },
      );
    }
  },
  custom_packaging_unit: async function (frm, cdt, cdn) {
    const packagingUnit = locals[cdt][cdn].custom_packaging_unit;

    if (packagingUnit) {
      frappe.db.get_value(
        packagingUnitDoctypeName,
        {
          name: packagingUnit,
        },
        ['code'],
        (response) => {
          const code = response.code;
          locals[cdt][cdn].custom_packaging_unit_code = code;
          frm.refresh_field('custom_packaging_unit_code');
        },
      );
    }
  },
  custom_unit_of_quantity: function (frm, cdt, cdn) {
    const unitOfQuantity = locals[cdt][cdn].custom_unit_of_quantity;

    if (unitOfQuantity) {
      frappe.db.get_value(
        unitOfQuantityDoctypeName,
        {
          name: unitOfQuantity,
        },
        ['code'],
        (response) => {
          const code = response.code;
          locals[cdt][cdn].custom_unit_of_quantity_code = code;
          frm.refresh_field('custom_unit_of_quantity_code');
        },
      );
    }
  },
});
