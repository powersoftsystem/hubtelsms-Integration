# Copyright (c) 2025, powersoft and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class SMSNotificationCondition(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		field_name: DF.Data
		operator: DF.Literal["=", "!=", ">", ">=", "<", "<=", "contains", "not contains", "in", "not in", "is set", "is not set"]
		value: DF.Data | None
		value_type: DF.Literal["Static", "Field", "Current User", "Current Date", "Current Time"]
	# end: auto-generated types

	pass 