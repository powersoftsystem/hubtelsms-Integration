# Copyright (c) 2025, powersoft and contributors
# For license information, please see license.txt

import frappe
from hubtel_sms.utils import send_sms
from frappe.model.document import Document


class HubtelSMS(Document):
	def on_submit(self):
		for recipient in self.recipients:
			send_sms(recipient.recipient, self.message)
