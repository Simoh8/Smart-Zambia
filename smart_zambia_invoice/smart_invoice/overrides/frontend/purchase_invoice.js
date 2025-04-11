const parentDoctype = 'Purchase Invoice';
const settingsDoctypeName = 'ZRA Smart Invoice Settings';

frappe.ui.form.on(parentDoctype, {
  refresh: function (frm) {
    frm.set_value('update_stock', 1);
    if (frm.doc.update_stock === 1) {
      frm.toggle_reqd('set_warehouse', true);
    }

    if (frm.doc.docstatus === 1 && frm.doc.is_return) {
      frm.add_custom_button(__('Submit to ZRA'), function () {
        frappe.call({
          method: 'smart_zambia_invoice.smart_invoice.overrides.backend.purchase_invoice.perform_debit_invoice_registration', // 🔁 replace with actual method path
          args: {
            document_name: frm.doc.name,
            company_name: frm.doc.company

          },
          callback: function (r) {
            if (r.message) {
              frappe.msgprint(__('Successfully submitted to ZRA'));
            }
          }
        });
      }, __('ZRA Actions')); // 👉 This groups the button under "ZRA Actions"
    }
  },

  validate: function (frm) {
    frappe.db.get_value(
      settingsDoctypeName,
      {
        is_active: 1,
        branch_id: frm.doc.branch ?? '00',
        company: frappe.defaults.get_user_default('Company'),
      },
      [
        'name',
        'company',
        'branch_id',
        'purchases_purchase_type',
        'purchases_receipt_type',
        'purchases_payment_type',
        'purchases_purchase_status',
      ],
      (response) => {
        if (!frm.doc.custom_purchase_type) {
          frm.set_value('custom_purchase_type', response.purchases_purchase_type);
        }
        if (!frm.doc.custom_receipt_type) {
          frm.set_value('custom_receipt_type', response.purchases_receipt_type);
        }
        if (!frm.doc.custom_purchase_status) {
          frm.set_value('custom_purchase_status', response.purchases_purchase_status);
        }
        if (!frm.doc.custom_payment_type) {
          frm.set_value('custom_payment_type', response.purchases_payment_type);
        }
      },
    );
  },
});
