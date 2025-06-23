// Copyright (c) 2025, powersoft and contributors
// For license information, please see license.txt

// frappe.ui.form.on("Hubtel SMS Notification", {
// 	refresh(frm) {

// 	},
// });

frappe.ui.form.on("Hubtel SMS Notification", {
	document_type: function(frm) {
		if (frm.doc.document_type) {
			// Clear existing options
			frm.set_df_property('recipient_fieldname', 'options', []);
			
			// Call the Python function to get field options
			frm.call({
				method: 'get_met_fields',
				args: {
					doctype: frm.doc.document_type
				},
				callback: function(r) {
                    console.log(r);
					if (r.message) {
						// Set the options for the recipient_fieldname field
						let options = r.message.map(field => ({
							label: field,
							value: field
						}));
						frm.set_df_property('recipient_fieldname', 'options', options);
						frm.refresh_field('recipient_fieldname');
					}
				}
			});
		} else {
			// Clear options if no document type is selected
			frm.set_df_property('recipient_fieldname', 'options', []);
			frm.refresh_field('recipient_fieldname');
		}
	}
});
