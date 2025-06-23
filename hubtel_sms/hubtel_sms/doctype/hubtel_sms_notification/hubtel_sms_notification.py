# Copyright (c) 2025, powersoft and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class HubtelSMSNotification(Document):
	pass

@frappe.whitelist(allow_guest=True)
def get_met_fields(doctype):
	fields = frappe.get_meta(doctype).fields
	fields = [field.fieldname for field in fields if field.fieldtype in ["Data", "Phone"]]
	return fields


