const parentDoctype = 'Purchase Invoice';
const settingsDoctypeName = 'ZRA Smart Invoice Settings';

frappe.ui.form.on(parentDoctype, {
  refresh: function (frm) {
    frm.set_value('update_stock', 1);
    if (frm.doc.update_stock === 1) {
      frm.toggle_reqd('set_warehouse', true);
    }

    if (frm.doc.is_return && frm.doc.docstatus < 2) {
      frm.add_custom_button(__('Submit to ZRA'), function () {
        frappe.call({
          method: 'your_app.your_module.doctype.your_method.submit_to_zra', // 🔁 update with real method path
          args: {
            docname: frm.doc.name
          },
          callback: function (r) {
            if (r.message) {
              frappe.msgprint(__('Successfully submitted to ZRA'));
            }
          }
        });
      });
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
