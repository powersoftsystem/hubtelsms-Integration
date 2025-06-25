# Copyright (c) 2025, Frappe Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class HubtelSMSRecipient(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		delivery_time: DF.Datetime | None
		error_message: DF.SmallText | None
		parent: DF.Data
		parentfield: DF.Data
		parenttype: DF.Data
		recipient: DF.Data
		status: DF.Literal["Pending", "Sent", "Delivered", "Failed"]
	# end: auto-generated types

	pass 