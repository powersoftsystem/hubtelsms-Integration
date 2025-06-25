# Copyright (c) 2025, powersoft and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _
import json
from datetime import datetime


class HubtelSMSNotification(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF
		from hubtel_sms.hubtel_sms.doctype.sms_notification_condition.sms_notification_condition import SMSNotificationCondition

		condition: DF.Literal["All conditions must be true (AND)", "Any condition can be true (OR)"]
		conditions: DF.Table[SMSNotificationCondition]
		delay_in_minutes: DF.Int
		description: DF.SmallText | None
		document_type: DF.Link
		enabled: DF.Check
		enable_conditions: DF.Check
		event: DF.Literal["Before Save", "After Insert", "Before Submit", "On Submit", "Before Cancel", "On Cancel", "On Update After Submit", "Before Delete", "After Delete", "On Change"]
		fixed_number: DF.Data | None
		priority: DF.Literal["Low", "Medium", "High", "Critical"]
		recipient_fieldname: DF.Select | None
		retry_attempts: DF.Int
		retry_interval: DF.Int
		send_immediately: DF.Check
		send_to_field: DF.Literal["Field", "Fixed Number"]
		sms_message_template: DF.LongText
		title: DF.Data
	# end: auto-generated types

	def validate(self):
		"""Validate the notification settings"""
		self.validate_message_template()
		self.validate_recipient_settings()
		self.validate_retry_settings()
		
	def validate_message_template(self):
		"""Validate the SMS message template"""
		if not self.sms_message_template:
			frappe.throw(_("SMS Message Template is required"))
			
		# Check message length (160 characters for single SMS)
		if len(self.sms_message_template) > 160:
			frappe.msgprint(_("Warning: Message template exceeds 160 characters and may be sent as multiple SMS"), 
							indicator="yellow")
	
	def validate_recipient_settings(self):
		"""Validate recipient field configuration"""
		if self.send_to_field == "Field":
			if not self.recipient_fieldname:
				frappe.throw(_("Recipient Phone Field is required when Send To is set to 'Field'"))
			# Clear fixed number if using field
			self.fixed_number = None
			
		elif self.send_to_field == "Fixed Number":
			if not self.fixed_number:
				frappe.throw(_("Fixed Phone Number is required when Send To is set to 'Fixed Number'"))
			# Validate phone number format (basic validation)
			self.validate_phone_number_format()
			# Clear recipient field if using fixed number
			self.recipient_fieldname = None
			
	def validate_phone_number_format(self):
		"""Basic validation for phone number format"""
		if self.fixed_number:
			# Remove spaces and special characters for validation
			clean_number = ''.join(filter(str.isdigit, self.fixed_number.replace('+', '')))
			if len(clean_number) < 10 or len(clean_number) > 15:
				frappe.throw(_("Invalid phone number format. Please use international format (e.g., +233201234567)"))
			
	def validate_retry_settings(self):
		"""Validate retry settings"""
		if self.retry_attempts < 0 or self.retry_attempts > 10:
			frappe.throw(_("Retry Attempts must be between 0 and 10"))
			
		if self.retry_interval < 1 or self.retry_interval > 60:
			frappe.throw(_("Retry Interval must be between 1 and 60 minutes"))

	def get_recipient_number(self, doc_data):
		"""Get the recipient phone number based on configuration"""
		if self.send_to_field == "Fixed Number":
			return self.fixed_number
		elif self.send_to_field == "Field" and self.recipient_fieldname:
			return doc_data.get(self.recipient_fieldname)
		return None

	@frappe.whitelist()
	def send_test_sms(self, phone_number, test_doc=None):
		"""Send a test SMS to verify the notification setup"""
		try:
			# Get test document if provided
			doc_data = {}
			if test_doc and self.document_type:
				doc_data = frappe.get_doc(self.document_type, test_doc).as_dict()
			
			# Use the recipient number from configuration if not provided
			if not phone_number and self.send_to_field == "Fixed Number":
				phone_number = self.fixed_number
			
			if not phone_number:
				return {"success": False, "error": "No phone number provided"}
			
			# Process message template
			message = self.process_message_template(doc_data)
			
			# Here you would integrate with your SMS service (Hubtel)
			# For now, we'll just log it
			frappe.log_error(f"Test SMS to {phone_number}: {message}", "Test SMS Notification")
			
			return {"success": True, "message": message, "phone_number": phone_number}
			
		except Exception as e:
			frappe.log_error(f"Test SMS Error: {str(e)}", "Test SMS Error")
			return {"success": False, "error": str(e)}
	
	def process_message_template(self, doc_data):
		"""Process the message template with document data"""
		message = self.sms_message_template
		
		# Replace field variables
		for key, value in doc_data.items():
			if value is not None:
				# Handle datetime formatting
				if isinstance(value, datetime):
					value = value.strftime("%d/%m/%Y %H:%M")
				message = message.replace(f"{{{key}}}", str(value))
				message = message.replace(f"{{doc.{key}}}", str(value))
		
		return message


@frappe.whitelist()
def get_phone_fields(doctype):
	"""Get phone/mobile fields from the specified doctype"""
	try:
		meta = frappe.get_meta(doctype)
		phone_fields = []
		
		for field in meta.fields:
			if field.fieldtype in ["Data", "Phone"] and (
				"phone" in field.fieldname.lower() or 
				"mobile" in field.fieldname.lower() or
				"contact" in field.fieldname.lower()
			):
				phone_fields.append(field.fieldname)
		
		# Add common phone fields if they exist
		common_phone_fields = ["phone", "mobile", "mobile_no", "contact_no", "phone_number"]
		for field_name in common_phone_fields:
			if frappe.db.has_column(doctype, field_name) and field_name not in phone_fields:
				phone_fields.append(field_name)
		
		return phone_fields
		
	except Exception as e:
		frappe.log_error(f"Error getting phone fields for {doctype}: {str(e)}", "Get Phone Fields Error")
		return []


@frappe.whitelist()
def get_available_fields(doctype):
	"""Get all available fields from the specified doctype for use in templates"""
	try:
		meta = frappe.get_meta(doctype)
		fields = []
		
		# Add standard fields
		standard_fields = ["name", "owner", "creation", "modified", "modified_by", "docstatus"]
		fields.extend(standard_fields)
		
		# Add custom fields
		for field in meta.fields:
			if field.fieldtype not in ["Table", "HTML", "Button", "Section Break", "Column Break"]:
				fields.append(field.fieldname)
		
		return sorted(list(set(fields)))
		
	except Exception as e:
		frappe.log_error(f"Error getting available fields for {doctype}: {str(e)}", "Get Available Fields Error")
		return []


@frappe.whitelist()
def validate_field_exists(doctype, fieldname):
	"""Validate if a field exists in the specified doctype"""
	try:
		meta = frappe.get_meta(doctype)
		
		# Check standard fields
		standard_fields = ["name", "owner", "creation", "modified", "modified_by", "docstatus"]
		if fieldname in standard_fields:
			return True
		
		# Check custom fields
		for field in meta.fields:
			if field.fieldname == fieldname:
				return True
		
		return False
		
	except Exception as e:
		frappe.log_error(f"Error validating field {fieldname} in {doctype}: {str(e)}", "Validate Field Error")
		return False


@frappe.whitelist(allow_guest=True)
def get_met_fields(doctype):
	"""Legacy method - redirects to get_phone_fields"""
	return get_phone_fields(doctype)


