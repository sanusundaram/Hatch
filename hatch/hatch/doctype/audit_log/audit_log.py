# Copyright (c) 2026, sanu and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class AuditLog(Document):
	pass


def log_change(doc, method=None):

    if doc.doctype == "Audit Log":
        return

    frappe.get_doc({
        "doctype": "Audit Log",
        "doctype_name": doc.doctype,
        "document_name": doc.name,
        "action": method,
        "user": frappe.session.user,
        "timestamp": frappe.utils.now_datetime(),
    }).insert(ignore_permissions=True)