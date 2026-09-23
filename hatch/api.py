# -----------------group D------------------------

import frappe

@frappe.whitelist()
def share_booking(booking_name, user_email):
    frappe.share.add(
        "Booking",
        booking_name,
        user_email,
        read=1
    )

    return {
        "message": "Booking shared successfully"
    }




@frappe.whitelist()
def unsafe_booking_query():
    return frappe.get_all(
        "Booking",
        fields="*"
    )


@frappe.whitelist()
def safe_booking_query():

    roles = frappe.get_roles()
    is_staff = "Front Desk Staff" in roles or "Space Manager" in roles

    bookings = frappe.get_list(
        "Booking",
        fields=[
            "name",
            "member",
            "resource",
            "booking_date",
            "start_time",
            "end_time",
            "headcount",
            "status"
        ]
    )

    if not is_staff:
        return bookings

    for booking in bookings:
        booking["member_email"] = frappe.db.get_value(
            "Member", booking.member, "email"
        )
        booking["member_phone"] = frappe.db.get_value(
            "Member", booking.member, "phone"
        )

    return bookings

# ---------------------group B-------------------------
from frappe.query_builder import DocType


@frappe.whitelist()
def get_upcoming_bookings():

    BK = DocType("Booking")

    result = (
        frappe.qb
        .from_(BK)
        .select(
            BK.name,
            BK.member,
            BK.resource,
            BK.booking_date,
            BK.start_time
        )
        .where(
            (BK.booking_date >= frappe.utils.getdate())
            & BK.status.isin([
                "Pending Confirmation",
                "Confirmed"
            ])
        )
        .orderby(BK.booking_date)
        .run(as_dict=True)
    )

    return result


@frappe.whitelist()
def reassign_bookings(from_member, to_member):

    try:

        frappe.db.sql(
            """
            UPDATE `tabBooking`
            SET member = %s
            WHERE member = %s
              AND booking_date >= CURDATE()
              AND status != 'Cancelled'
            """,
            (
                to_member,
                from_member
            )
        )

        frappe.db.commit()

    except Exception:

        frappe.db.rollback()

        frappe.log_error(
            title="Booking Reassignment Failed",
            message=frappe.get_traceback()
        )

        raise

    return True



# ---------------group D------------------------




@frappe.whitelist()
def get_allowed_resources(
    doctype,
    txt,
    searchfield,
    start,
    page_len,
    filters
):

    member = filters.get("member")

    if not member:
        return []

    plan = frappe.db.get_value(
        "Member",
        member,
        "membership_plan"
    )

    if not plan:
        return []

    allowed_types = frappe.get_all(
        "Allowed Resource Types",
        filters={
            "parent": plan
        },
        pluck="resource_type"
    )

    if not allowed_types:
        return []

    placeholders = ", ".join(
        ["%s"] * len(allowed_types)
    )

    return frappe.db.sql(
        f"""
        SELECT name, resource_name
        FROM `tabResource`
        WHERE is_active = 1
          AND resource_type IN ({placeholders})
          AND resource_name LIKE %s
        ORDER BY resource_name
        LIMIT %s, %s
        """,
        tuple(allowed_types) + (
            f"%{txt}%",
            start,
            page_len
        )
    )

@frappe.whitelist()
def check_booking_availability(
    resource,
    booking_date,
    start_time,
    end_time,
    booking_name=None
):

    capacity = frappe.db.get_value(
        "Resource",
        resource,
        "capacity"
    )

    booked = frappe.db.sql(
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
            resource,
            booking_date,
            booking_name or "",
            end_time,
            start_time
        )
    )[0][0]

    booked = booked or 0

    free = capacity - booked

    return {
        "capacity": capacity,
        "booked": booked,
        "free": max(free, 0)
    }



@frappe.whitelist()
def check_in_booking(booking_name):

    booking = frappe.get_doc(
        "Booking",
        booking_name
    )

    if booking.status != "Confirmed":
        frappe.throw(
            "Only Confirmed bookings can be checked in."
        )

    if booking.docstatus != 1:
        frappe.throw(
            "Booking must be submitted before check-in."
        )

    if booking.booking_date != frappe.utils.getdate():
        frappe.throw(
            "Check-in is allowed only on the booking date."
        )

    booking.db_set(
        "status",
        "Checked-In"
    )

    return True


