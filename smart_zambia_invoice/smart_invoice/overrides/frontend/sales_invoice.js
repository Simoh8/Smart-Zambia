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
    if (!frm.is_new() && frm.doc.docstatus === 0) {
      frm.add_custom_button(__('Submit Invoice'), function () {
        // Call the custom method to handle invoice submission
        frappe.call({
          method: 'smart_zambia_invoice.smart_invoice.api.zra_api.perform_sales_invoice_registration',
          args: {
            request_data :{
              name: frm.doc.name,
              invoice_name: frm.doc.name,
              company_name: companyName

            },
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
  validate: function (frm) {
    frappe.db.get_value(
      settingsDoctypeName,
      {
        is_active: 1,
        bhfid: frm.doc.branch,
        company: frappe.defaults.get_user_default('Company'),
      },
      [
        'name',
        'company',
        'bhfid',
        'sales_payment_type',
        'sales_transaction_progress',
      ],
      (response) => {
        if (!frm.doc.custom_payment_type) {
          frm.set_value('custom_zra_payment_type', response.sales_payment_type);
        }
        if (!frm.doc.custom_zra_transaction_progress_status) {
          frm.set_value(
            'custom_zra_transaction_progress_status',
            response.sales_transaction_progress,
          );
        }
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
