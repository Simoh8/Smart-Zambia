const parentDoctype = 'Sales Invoice';
const childDoctype = `${parentDoctype} Item`;
const packagingUnitDoctypeName = 'ZRA Packaging Unit';
const unitOfQuantityDoctypeName = 'ZRA Unit of Quantity';
const taxationTypeDoctypeName = 'ZRA Tax Type';
const settingsDoctypeName = 'ZRA Smart Invoice Settings';



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
        branch_id: frm.doc.branch,
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
