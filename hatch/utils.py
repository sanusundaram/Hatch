import frappe


@frappe.whitelist()
def rename_member(old_name, new_name):
    frappe.rename_doc(
        "Member",
        old_name,
        new_name,
        merge=False
    )

    return new_name