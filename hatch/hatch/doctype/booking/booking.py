# Copyright (c) 2026, sanu and contributors
# For license information, please see license.txt
import frappe
from frappe.model.document import Document
# ----------------------------group E-------------------------------------------------
class Booking(Document):
    def validate(self):
        self.validate_time()
        self.calculate_amounts()
        self.check_capacity()

    def validate_time(self):
        if self.end_time <= self.start_time:
            frappe.throw("End Time must be after Start Time")

    def calculate_amounts(self):
        resource = frappe.db.get_value("Resource", self.resource, ["hourly_rate"], as_dict=True)

        start = frappe.utils.get_datetime(f"{self.booking_date} {self.start_time}")
        end = frappe.utils.get_datetime(f"{self.booking_date} {self.end_time}")
        duration_hours = (end - start).total_seconds() / 3600

        base_precision = self.precision("base_amount") or 2
        self.base_amount = frappe.utils.flt(resource.hourly_rate * duration_hours, base_precision)

        self.addons_total = 0
        for row in self.addons or []:
            amount_precision = row.precision("amount") or 2
            row.amount = frappe.utils.flt(row.rate * row.quantity, amount_precision)
            self.addons_total += row.amount

        addons_precision = self.precision("addons_total") or 2
        self.addons_total = frappe.utils.flt(self.addons_total, addons_precision)

        total_precision = self.precision("total_amount") or 2
        self.total_amount = frappe.utils.flt(self.base_amount + self.addons_total, total_precision)

    def check_capacity(self):
        capacity = frappe.db.get_value("Resource", self.resource, "capacity")

        existing_headcount = frappe.db.sql("""
            SELECT COALESCE(SUM(headcount), 0)
            FROM `tabBooking`
            WHERE resource = %s
              AND booking_date = %s
              AND start_time < %s
              AND end_time > %s
              AND status IN ('Pending Confirmation', 'Confirmed', 'Checked-In')
              AND name != %s
        """, (
            self.resource,
            self.booking_date,
            self.end_time,
            self.start_time,
            self.name or ""
        ))[0][0]

        existing_headcount = existing_headcount or 0
        total_headcount = existing_headcount + self.headcount

        if total_headcount > capacity:
            free_seats = capacity - existing_headcount
            frappe.throw(
                f"Only {free_seats} seat(s) are available for this time slot. "
                f"Requested: {self.headcount}, Capacity: {capacity}."
            )

    def before_submit(self):
        if self.status != "Pending Confirmation":
            frappe.throw(
                "Booking can only be submitted when status is Pending Confirmation."
            )

    def on_submit(self):
        self.status = "Confirmed"
        frappe.enqueue(
            "hatch.hatch.doctype.booking.booking.send_confirmation_email",
            booking_name=self.name,
            queue="short",
            enqueue_after_commit=True
        )

    def on_cancel(self):
        self.status = "Cancelled"
        self.db_set("status", "Cancelled", update_modified=False)

    def on_trash(self):
        if self.status not in ["Cancelled", "Draft"]:
            frappe.throw("Only Draft or Cancelled bookings can be deleted.")

def send_confirmation_email(booking_name):
    booking = frappe.get_doc("Booking", booking_name)
    email = frappe.db.get_value("Member", booking.member, "email")

    if not email:
        return

    frappe.sendmail(
        recipients=[email],
        subject="Booking Confirmed",
        message=f"""
Your booking {booking.name} has been confirmed.

Resource: {booking.resource}
Date: {booking.booking_date}
Start Time: {booking.start_time}
End Time: {booking.end_time}
Total Amount: {booking.total_amount}
"""
    )
# -----------------------group J---------------------
def before_print(doc, method=None, print_settings=None):
    doc.print_summary = f"{doc.member} - {doc.resource} on {doc.booking_date}"