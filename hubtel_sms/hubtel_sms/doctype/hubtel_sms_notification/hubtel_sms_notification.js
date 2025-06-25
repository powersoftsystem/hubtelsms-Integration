// Copyright (c) 2025, powersoft and contributors
// For license information, please see license.txt

// frappe.ui.form.on("Hubtel SMS Notification", {
// 	refresh(frm) {

// 	},
// });

frappe.ui.form.on("Hubtel SMS Notification", {
	refresh: function(frm) {
		// Add custom buttons and styling
		if (!frm.doc.__islocal) {
			frm.add_custom_button(__("Test SMS"), function() {
				test_sms_notification(frm);
			}, __("Actions"));
			
			frm.add_custom_button(__("View Logs"), function() {
				frappe.route_options = {"reference_doctype": frm.doc.name};
				frappe.set_route("List", "SMS Log");
			}, __("Actions"));
		}
		
		// Set help text for message template
		update_message_help(frm);
		
		// Set field requirements based on send_to_field
		set_recipient_field_requirements(frm);
	},

	document_type: function(frm) {
		if (frm.doc.document_type) {
			// Clear existing options
			frm.set_df_property('recipient_fieldname', 'options', []);
			
			// Call the Python function to get field options
			frm.call({
				method: 'get_phone_fields',
				args: {
					doctype: frm.doc.document_type
				},
				callback: function(r) {
					if (r.message) {
						// Set the options for the recipient_fieldname field
						frm.set_df_property('recipient_fieldname', 'options', r.message);
						frm.refresh_field('recipient_fieldname');
					}
				}
			});
			
			// Update condition field options
			update_condition_field_options(frm);
		} else {
			// Clear options if no document type is selected
			frm.set_df_property('recipient_fieldname', 'options', []);
			frm.refresh_field('recipient_fieldname');
		}
	},

	send_to_field: function(frm) {
		// Set field requirements based on send_to_field selection
		set_recipient_field_requirements(frm);
	},

	event: function(frm) {
		// Show relevant help text based on selected event
		show_event_help(frm);
	},

	enable_conditions: function(frm) {
		// Refresh conditions table when enabling/disabling
		frm.refresh_field('conditions');
	}
});

// Child table events for conditions
frappe.ui.form.on("SMS Notification Condition", {
	field_name: function(frm, cdt, cdn) {
		// Validate field name exists in the selected document type
		let row = locals[cdt][cdn];
		if (row.field_name && frm.doc.document_type) {
			validate_field_name(frm, row);
		}
	},

	operator: function(frm, cdt, cdn) {
		// Show/hide value field based on operator
		let row = locals[cdt][cdn];
		if (['is set', 'is not set'].includes(row.operator)) {
			frappe.model.set_value(cdt, cdn, 'value', '');
		}
		frm.refresh_field('conditions');
	}
});

function set_recipient_field_requirements(frm) {
	// Set field requirements based on send_to_field selection
	if (frm.doc.send_to_field === 'Field') {
		frm.set_df_property('recipient_fieldname', 'reqd', 1);
		frm.set_df_property('fixed_number', 'reqd', 0);
	} else if (frm.doc.send_to_field === 'Fixed Number') {
		frm.set_df_property('recipient_fieldname', 'reqd', 0);
		frm.set_df_property('fixed_number', 'reqd', 1);
		// Clear recipient field if switching to fixed number
		if (frm.doc.recipient_fieldname) {
			frm.set_value('recipient_fieldname', '');
		}
	} else {
		frm.set_df_property('recipient_fieldname', 'reqd', 0);
		frm.set_df_property('fixed_number', 'reqd', 0);
	}
	
	frm.refresh_field('recipient_fieldname');
	frm.refresh_field('fixed_number');
}

function update_message_help(frm) {
	if (frm.doc.document_type) {
		frm.call({
			method: 'get_available_fields',
			args: {
				doctype: frm.doc.document_type
			},
			callback: function(r) {
				if (r.message) {
					let help_html = build_help_html(r.message);
					frm.set_df_property('message_variables_help', 'options', help_html);
				}
			}
		});
	}
}

function build_help_html(fields) {
	let field_list = fields.map(field => `<code>{${field}}</code>`).join(', ');
	
	return `<div class="text-muted small">
		<p><strong>Variable Usage:</strong></p>
		<ul>
			<li>Use <code>{field_name}</code> to insert field values</li>
			<li>Common variables: <code>{name}</code>, <code>{owner}</code>, <code>{creation}</code></li>
		</ul>
		<p><strong>Available Fields:</strong><br>
		${field_list}</p>
		<p><strong>Example:</strong><br>
		"Hello {customer_name}, your order {name} has been {status}. Total: {grand_total}"</p>
	</div>`;
}

function update_condition_field_options(frm) {
	if (frm.doc.document_type) {
		frm.call({
			method: 'get_available_fields',
			args: {
				doctype: frm.doc.document_type
			},
			callback: function(r) {
				if (r.message) {
					// Update field options for all condition rows
					frm.doc.conditions = frm.doc.conditions || [];
					frm.doc.conditions.forEach(function(row) {
						frm.fields_dict.conditions.grid.grid_rows_by_docname[row.name].docfields[0].options = r.message;
					});
					frm.refresh_field('conditions');
				}
			}
		});
	}
}

function validate_field_name(frm, row) {
	frm.call({
		method: 'validate_field_exists',
		args: {
			doctype: frm.doc.document_type,
			fieldname: row.field_name
		},
		callback: function(r) {
			if (!r.message) {
				frappe.msgprint({
					title: __('Invalid Field'),
					message: __('Field "{0}" does not exist in {1}', [row.field_name, frm.doc.document_type]),
					indicator: 'red'
				});
			}
		}
	});
}

function show_event_help(frm) {
	const event_help = {
		'Before Save': 'Triggered before document is saved (create or update)',
		'After Insert': 'Triggered after new document is created',
		'Before Submit': 'Triggered before submittable document is submitted',
		'On Submit': 'Triggered after submittable document is submitted',
		'Before Cancel': 'Triggered before submitted document is cancelled',
		'On Cancel': 'Triggered after submitted document is cancelled',
		'On Update After Submit': 'Triggered when submitted document is updated',
		'Before Delete': 'Triggered before document is deleted',
		'After Delete': 'Triggered after document is deleted',
		'On Change': 'Triggered when any field value changes'
	};
	
	if (frm.doc.event && event_help[frm.doc.event]) {
		frm.set_df_property('event', 'description', event_help[frm.doc.event]);
	}
}

function test_sms_notification(frm) {
	let d = new frappe.ui.Dialog({
		title: __('Test SMS Notification'),
		fields: [
			{
				fieldname: 'test_phone',
				fieldtype: 'Data',
				label: __('Test Phone Number'),
				reqd: 1,
				description: __('Phone number to send test SMS to'),
				depends_on: 'eval:doc.send_to_field != "Fixed Number"'
			},
			{
				fieldname: 'test_document',
				fieldtype: 'Link',
				label: __('Test Document'),
				options: frm.doc.document_type,
				description: __('Document to use for testing variables')
			}
		],
		primary_action_label: __('Send Test SMS'),
		primary_action: function() {
			let values = d.get_values();
			
			// Use fixed number if that's the selected option
			let phone_number = values.test_phone;
			if (frm.doc.send_to_field === 'Fixed Number') {
				phone_number = frm.doc.fixed_number;
			}
			
			if (!phone_number) {
				frappe.msgprint({
					title: __('Missing Phone Number'),
					message: __('Please provide a phone number to send the test SMS'),
					indicator: 'red'
				});
				return;
			}
			
			frm.call({
				method: 'send_test_sms',
				args: {
					phone_number: phone_number,
					test_doc: values.test_document
				},
				callback: function(r) {
					if (r.message && r.message.success) {
						frappe.msgprint({
							title: __('Success'),
							message: __('Test SMS sent successfully to {0}', [phone_number]),
							indicator: 'green'
						});
						d.hide();
					} else {
						frappe.msgprint({
							title: __('Error'),
							message: r.message && r.message.error || __('Failed to send test SMS'),
							indicator: 'red'
						});
					}
				}
			});
		}
	});
	
	// Hide test phone field if using fixed number
	if (frm.doc.send_to_field === 'Fixed Number') {
		d.fields_dict.test_phone.df.hidden = 1;
		d.refresh();
	}
	
	d.show();
}
