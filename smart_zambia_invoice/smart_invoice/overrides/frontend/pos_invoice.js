const doctypeName = "POS Invoice";
const childDoctypeName = `${doctypeName} Item`;
const packagingUnitDoctypeName = 'ZRA Packaging Unit';
const unitOfQuantityDoctypeName = 'ZRA Unit of Quantity';
const taxationTypeDoctypeName = 'ZRA Tax Type';
const settingsDoctypeName = 'ZRA Smart Invoice Settings';



frappe.ui.form.on(doctypeName, {
  refresh: function (frm) {
    frappe.db.get_value(
      settingsDoctypeName,
      {
        is_active: 1,
        bhfid: frm.doc.branch,
        company: frappe.defaults.get_user_default("Company"),
      },
      [
        'name',
        'company_name',
        'branch_id',
      ],
      (response) => {

      }
    );
  },
});

frappe.ui.form.on(childDoctypeName, {
  custom_packaging_unit: async function (frm, cdt, cdn) {
    const packagingUnit = locals[cdt][cdn].custom_packaging_unit;

    if (packagingUnit) {
      const response = await frappe.db.get_value(
        packagingUnitDoctypeName,
        {
          name: packagingUnit,
        },
        ["code"]
      );

      const code = response.message?.code;
      locals[cdt][cdn].custom_packaging_unit_code = code;
      frm.refresh_field("custom_packaging_unit_code");
    }
  },
  custom_unit_of_quantity: async function (frm, cdt, cdn) {
    const unitOfQuantity = locals[cdt][cdn].custom_unit_of_quantity;

    if (unitOfQuantity) {
      const response = await frappe.db.get_value(
        unitOfQuantityDoctypeName,
        {
          name: unitOfQuantity,
        },
        ["code"]
      );

      const code = response.message?.code;
      locals[cdt][cdn].custom_unit_of_quantity_code = code;
      frm.refresh_field("custom_unit_of_quantity_code");
    }
  },
  custom_taxation_type: async function (frm, cdt, cdn) {
    const taxationType = locals[cdt][cdn].custom_taxation_type;

    if (taxationType) {
      const response = await frappe.db.get_value(
        taxationTypeDoctypeName,
        {
          name: taxationType,
        },
        ["cd"]
      );

      const code = response.message?.cd;
      locals[cdt][cdn].custom_taxation_type_code = code;
      frm.refresh_field("custom_zra_tax_type");
    }
  },
});
