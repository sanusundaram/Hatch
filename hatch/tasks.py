import frappe
from datetime import timedelta

# -----------------group K1------------------------
def release_expired_holds():
    run_key=f"release_holds:{frappe.utils.now_datetime().strftime('%Y%m%d%H')}"
    if frappe.cache().get_value(run_key):
        return
    frappe.cache().set_value(run_key,True,expires_in_sec=3500)
    expiry_hours=frappe.db.get_single_value("Hatch Settings","pending_confirmation_expiry_hours")
    if not expiry_hours:
        return
    expiry_time=frappe.utils.now_datetime()-timedelta(hours=expiry_hours)
    bookings=frappe.get_list(
        "Booking",
        filters={
            "status":"Pending Confirmation",
            "creation":["<",expiry_time],
            "docstatus":0
        },
        fields=["name"],
        limit_page_length=0
    )
    for booking in bookings:
        doc=frappe.get_doc("Booking",booking.name)
        if doc.status=="Pending Confirmation":
            doc.db_set("status","Cancelled",update_modified=False)