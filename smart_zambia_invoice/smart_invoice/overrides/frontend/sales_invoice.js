const parentDoctype = 'Sales Invoice';
const childDoctype = `${parentDoctype} Item`;
const packagingUnitDoctypeName = 'ZRA Packaging Unit';
const unitOfQuantityDoctypeName = 'ZRA Unit of Quantity';
const taxationTypeDoctypeName = 'ZRA Tax Type';
const settingsDoctypeName = 'ZRA Smart Invoice Settings';

frappe.ui.form.on(parentDoctype, {
  refresh: function (frm) {
    const companyName = frappe.boot.sysdefaults.company;

    frm.set_value('update_stock', 1);

    if (frm.doc.update_stock === 1) {
      frm.toggle_reqd('set_warehouse', true);
    }

    // Add "Submit Invoice" button
    if (!frm.is_new() && frm.doc.docstatus === 1 && !frm.doc.custom_has_it_been_successfully_submitted) {
      frm.add_custom_button(__('ZRA Submit Invoice'), function () {
        // Call the custom method to handle invoice submission
        let sales_trans_code = frm.doc.is_return;
        let debit_note_code = frm.doc.is_debit_note;
        let is_refund=frm.doc.custom_funds_refunded_
        frappe.call({
          method: 'smart_zambia_invoice.smart_invoice.api.zra_api.perform_sales_invoice_registration',
          args: {
            request_data: {

              name: frm.doc.name,
              orgInvcNo: "0",
              company_name: companyName,
              cisInvcNo: frm.doc.name,
              custTpin: frm.doc.tax_id,
              custNm: frm.doc.customer,
              salesTyCd: "N",
              rcptTyCd: debit_note_code ? "D" : sales_trans_code ? "R" : "S",
              pmtTyCd: frm.doc.custom_zra_payment_code,
              salesSttsCd: frm.doc.custom_progress_status_code,
              cfmDt: frm.doc.status === "Cancelled" ? frappe.datetime.get_today() : "",  
              "salesDt": frm.doc.posting_time,
              "stockRlsDt": null,
              "cnclReqDt": frm.doc.status === "Cancelled" ? frappe.datetime.get_today() : "",
              "cnclDt": frm.doc.status === "Cancelled" ? frappe.datetime.get_today() : "",
              "rfdDt": is_refund ? frappe.datetime.get_today() : "",
              "rfdRsnCd": frm.doc.custom_zra_credit_note_reason,
              "totItemCnt": 2,
              "taxblAmtA": 86.2069,
              "taxblAmtB": 0.0,
              "taxblAmtC1": 0.0,
              "taxblAmtC2": 0.0,
              "taxblAmtC3": 0.0,
              "taxblAmtD": 0.0,
              "taxblAmtRvat": 0.0,
              "taxblAmtE": 0.0,
              "taxblAmtF": 0.0,
              "taxblAmtIpl1": 0.0,
              "taxblAmtIpl2": 100,
              "taxblAmtTl": 0.0,
              "taxblAmtEcm": 0,
              "taxblAmtExeeg": 0.0,
              "taxblAmtTot": 0.0,
              "taxRtA": 16,
              "taxRtB": 16,
              "taxRtC1": 0,
              "taxRtC2": 0,
              "taxRtC3": 0,
              "taxRtD": 0,
              "tlAmt": 0.0,
              "taxRtRvat": 16,
              "taxRtE": 0,
              "taxRtF": 10,
              "taxRtIpl1": 5,
              "taxRtIpl2": 0,
              "taxRtTl": 1.5,
              "taxRtEcm": 5,
              "taxRtExeeg": 3,
              "taxRtTot": 0,
              "taxAmtA": 13.7931,
              "taxAmtB": 0.0,
              "taxAmtC1": 0.0,
              "taxAmtC2": 0.0,
              "taxAmtC3": 0.0,
              "taxAmtD": 0.0,
              "taxAmtRvat": 0.0,
              "taxAmtE": 0.0,
              "taxAmtF": 0.0,
              "taxAmtIpl1": 0.0,
              "taxAmtIpl2": 0.0,
              "taxAmtTl": 0.0,
              "taxAmtEcm": 0.0,
              "taxAmtExeeg": 0.0,
              "taxAmtTot": 0.0,
              "totTaxblAmt": 186.2069,
              "totTaxAmt": 13.7931,
              "cashDcRt": 25,
              "cashDcAmt": 50,
              "totAmt": 150,
              "prchrAcptcYn": "N",
              "remark": "",
              "regrId": "admin",
              "regrNm": "admin",
              "modrId": "admin",
              "modrNm": "admin",
              "saleCtyCd": "1",
              "lpoNumber": null,
              "currencyTyCd": "ZMW",
              "exchangeRt": "1",
              "destnCountryCd": "",
              "dbtRsnCd": "",
              "invcAdjustReason": "",
              "itemList": [
                {
                  "itemSeq": 1,
                  "itemCd": "20056",
                  "itemClsCd": "50102518",
                  "itemNm": "Bread",
                  "bcd": "",
                  "pkgUnitCd": "BA",
                  "pkg": 0.0,
                  "qtyUnitCd": "BE",
                  "qty": 1.0,
                  "prc": 125,
                  "splyAmt": 125,
                  "dcRt": 20,
                  "dcAmt": 25,
                  "isrccCd": "",
                  "isrccNm": "",
                  "isrcRt": 0.0,
                  "isrcAmt": 0.0,
                  "vatCatCd": "A",
                  "exciseTxCatCd": null,
                  "tlCatCd": null,
                  "iplCatCd": null,
                  "vatTaxblAmt": 86.2069,
                  "vatAmt": 13.7931,
                  "exciseTaxblAmt": 0,
                  "tlTaxblAmt": 0.0,
                  "iplTaxblAmt": 0.0,
                  "iplAmt": 0.0,
                  "tlAmt": 0.0,
                  "exciseTxAmt": 0,
                  "totAmt": 100
                },
                {
                  "itemSeq": 2,
                  "itemCd": "20056",
                  "itemClsCd": "50102518",
                  "itemNm": "Reinsurance",
                  "bcd": "",
                  "pkgUnitCd": "BA",
                  "pkg": 0.0,
                  "qtyUnitCd": "BE",
                  "qty": 1.0,
                  "prc": 100,
                  "splyAmt": 100,
                  "dcRt": 0.0,
                  "dcAmt": 0.0,
                  "isrccCd": "",
                  "isrccNm": "",
                  "isrcRt": 0.0,
                  "isrcAmt": 0.0,
                  "vatCatCd": null,
                  "exciseTxCatCd": null,
                  "vatTaxblAmt": 0.0,
                  "exciseTaxblAmt": 0,
                  "tlTaxblAmt": 0.0,
                  "tlCatCd": null,
                  "tlAmt": 0.0,
                  "iplCatCd": "IPL2",
                  "iplAmt": 0.0,
                  "iplTaxblAmt": 100,
                  "vatAmt": 0.0,
                  "exciseTxAmt": 0,
                  "totAmt": 100
                }
              ]
            }
          },
          callback: function (response) {
            if (response.message) {
              frappe.msgprint(__('Invoice submitted successfully: ') + response.message);
              frm.reload_doc(); // Reload the document after submission
            }
          },
          error: function (error) {
            frappe.msgprint(__('An error occurred while submitting the invoice.'));
            console.error(error);
          },
        });
      }).addClass('btn-primary'); // Add a primary button style
    }
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
