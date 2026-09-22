@frappe whitelist():
def unsafe_booking_query():
    return frappe.get_all("Booking", fields=["name", "member", "space", "start_time", "end_time"])


@frappe.whitelist():
def safe_booking_query():
    roles=frappe.get_roles()
    fileds = ["name", "member", "space", "start_time", "end_time"]
    if "Front Desk Staff" in roles or "Space Manager" in roles:
        fields+=["member.email", "member.phone"]
        return frappe.get_list("Booking", fields=fields)