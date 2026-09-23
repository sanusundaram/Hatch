# import frappe
# def booking_query(user):
#     if not user:
#         user = frappe.session.user
#         roles=frappe.get_roles(user)
#         if "Front Desk Staff" in roles or "Space Manager" in roles:
#             return ""
#         if "Hatch Member" in roles:
#             return "1=0"
#         member = frappe.db.get_value("Member", {"user": user},"name")
#         if not member:
#             return "1=0"
#         return f"`tabBooking`.member = '{frappe.db.escape(member)}'"


import frappe


def booking_query(user):
    if not user:
        user = frappe.session.user

    if "Front Desk Staff" in frappe.get_roles(user):
        return ""

    if "Space Manager" in frappe.get_roles(user):
        return ""

    return """
        `tabBooking`.`member` IN (
            SELECT `name`
            FROM `tabMember`
            WHERE `user` = {user}
        )
    """.format(
        user=frappe.db.escape(user)
    )