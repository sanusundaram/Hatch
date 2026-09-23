# Copyright (c) 2026, sanu and contributors
# For license information, please see license.txt
import frappe
from frappe.model.document import Document


class Resource(Document):
    pass

    # def on_update(self):

    #     hours = frappe.db.get_value(
    #         "Hatch Settings",
    #         None,
    #         "pending_confirmation_expiry_hours"
    #     )

    #     frappe.logger().info(
    #         f"Pending confirmation expiry: {hours} hours"
    #     )