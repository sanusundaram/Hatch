# Copyright (c) 2026, sanu and contributors
# For license information, please see license.txt
import frappe
from frappe.model.document import Document


class Booking(Document):
    def validate(self):
        self.validate_time()
        self.calculate_amounts()
        self.check_capacity()

    def validate_time(self):
        if self.end_time <= self.start_time:
            frappe.throw("End Time must be after Start Time")

    # def calculate_amounts(self):

    #     resource = frappe.db.get_value(
    #         "Resource",
    #         self.resource,
    #         ["hourly_rate"],
    #         as_dict=True
    #     )

    #     start = frappe.utils.get_datetime(
    #         f"{self.booking_date} {self.start_time}"
    #     )

    #     end = frappe.utils.get_datetime(
    #         f"{self.booking_date} {self.end_time}"
    #     )

    #     duration_hours = (
    #         end - start
    #     ).total_seconds() / 3600

    #     self.base_amount = (
    #         resource.hourly_rate * duration_hours
    #     )

    #     addons_total = 0

    #     for row in self.addons:
    #         row.amount = row.rate * row.quantity
    #         addons_total += row.amount

    #     self.addons_total = addons_total

    #     self.total_amount = (
    #         self.base_amount + self.addons_total
    #     )

    def check_capacity(self):

        capacity = frappe.db.get_value(
            "Resource",
            self.resource,
            "capacity"
        )

        total = frappe.db.sql(
            """
            SELECT COALESCE(SUM(headcount), 0)
            FROM `tabBooking`
            WHERE resource = %s
              AND booking_date = %s
              AND name != %s
              AND status IN (
                  'Pending Confirmation',
                  'Confirmed',
                  'Checked-In'
              )
              AND start_time < %s
              AND end_time > %s
            """,
            (
                self.resource,
                self.booking_date,
                self.name or "",
                self.end_time,
                self.start_time
            )
        )[0][0]

        total = total or 0

        requested = total + self.headcount

        if requested > capacity:

            free = capacity - total

            frappe.throw(
                f"Only {free} seat(s) are available "
                f"for this time slot. "
                f"Requested: {self.headcount}, "
                f"Capacity: {capacity}."
            )

    def before_submit(self):

        if self.status != "Pending Confirmation":
            frappe.throw(
                "Booking can only be submitted "
                "when status is Pending Confirmation."
            )

    def on_submit(self):

        self.status = "Confirmed"

        frappe.enqueue(
            "hatch.hatch.doctype.booking.booking.send_confirmation_email",
            booking_name=self.name,
            queue="short"
        )

    def on_cancel(self):

        self.status = "Cancelled"

    def on_trash(self):

        if self.status not in ["Cancelled", "Draft"]:
            frappe.throw(
                "Only Draft or Cancelled bookings "
                "can be deleted."
            )

    def calculate_amounts(self):
        resource = frappe.db.get_value(
            "Resource",
            self.resource,
            ["hourly_rate"],
            as_dict=True
        )

        start = frappe.utils.get_datetime(
            f"{self.booking_date} {self.start_time}"
        )

        end = frappe.utils.get_datetime(
            f"{self.booking_date} {self.end_time}"
        )

        duration_hours = (end - start).total_seconds() / 3600

        self.base_amount = resource.hourly_rate * duration_hours

        addons_total = 0

        for row in self.addons or []:
            row.amount = row.rate * row.quantity
            addons_total += row.amount

        self.addons_total = addons_total
        self.total_amount = self.base_amount + self.addons_total

def send_confirmation_email(booking_name):

    booking = frappe.get_doc(
        "Booking",
        booking_name
    )

    email = frappe.db.get_value(
        "Member",
        booking.member,
        "email"
    )

    if not email:
        return

    frappe.sendmail(
        recipients=[email],
        subject="Booking Confirmed",
        message=f"Your booking {booking.name} has been confirmed."
    )

    

# import frappe
# from frappe.model.document import Document
# from frappe.utils import time_diff_in_hours


# class Booking(Document):

#     def validate(self):
#         # 1. Time validation
#         if self.end_time <= self.start_time:
#             frappe.throw("End time must be after start time")

#         # 2. Get resource
#         resource = frappe.get_doc("Resource", self.resource)

#         # 3. Calculate duration
#         duration = time_diff_in_hours(
#             self.end_time,
#             self.start_time
#         )

#         # 4. Calculate base amount
#         self.base_amount = resource.hourly_rate * duration

#         # 5. Calculate add-ons
#         self.addons_total = 0

#         for row in self.addons:
#             row.amount = row.rate * row.quantity
#             self.addons_total += row.amount

#         # 6. Calculate total
#         self.total_amount = (
#             self.base_amount + self.addons_total
#         )

#         # 7. Check capacity
#         self.check_capacity()

#     def check_capacity(self):

#         total_headcount = frappe.db.sql(
#             """
#             SELECT COALESCE(SUM(headcount), 0)
#             FROM `tabBooking`
#             WHERE resource = %s
#               AND booking_date = %s
#               AND start_time < %s
#               AND end_time > %s
#               AND status IN (
#                   'Pending Confirmation',
#                   'Confirmed',
#                   'Checked-In'
#               )
#               AND name != %s
#             """,
#             (
#                 self.resource,
#                 self.booking_date,
#                 self.end_time,
#                 self.start_time,
#                 self.name
#             )
#         )[0][0]

#         total_headcount += self.headcount

#         resource_capacity = frappe.db.get_value(
#             "Resource",
#             self.resource,
#             "capacity"
#         )

#         if total_headcount > resource_capacity:

#             available = resource_capacity - (
#                 total_headcount - self.headcount
#             )

#             frappe.throw(
#                 f"Only {available} seats are available "
#                 f"for this time slot."
#             )

#     def before_submit(self):

#         if self.status != "Pending Confirmation":
#             frappe.throw(
#                 "Only Pending Confirmation bookings "
#                 "can be submitted."
#             )

#     def on_submit(self):

#         self.status = "Confirmed"

#         frappe.enqueue(
#             "hatch.api.send_booking_confirmation",
#             booking_name=self.name
#         )

#     def on_cancel(self):

#         self.status = "Cancelled"

#     def on_trash(self):

#         if self.status not in ["Cancelled", "Draft"]:
#             frappe.throw(
#                 "Only Draft or Cancelled bookings can be deleted."
#             )