import frappe

# -----------------group D------------------------
AUDIT_DOCTYPES=["Booking","Member","Resource","Membership Plan","Hatch Settings"]

def log_change(doc,method):
    if doc.doctype not in AUDIT_DOCTYPES:
        return
    if doc.doctype=="Audit Log":
        return
    action_map={"on_update":"Save","on_submit":"Submit","on_cancel":"Cancel"}
    action=action_map.get(method)
    if not action:
        return
    frappe.get_doc({
        "doctype":"Audit Log",
        "doctype_name":doc.doctype,
        "document_name":doc.name,
        "action":action,
        "user":frappe.session.user,
        "timestamp":doc.modified
    }).insert(ignore_permissions=True)