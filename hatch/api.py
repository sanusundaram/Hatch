# -----------------group D------------------------
import frappe

@frappe.whitelist()
def share_booking(booking_name,user_email):
    frappe.share.add("Booking",booking_name,user_email,read=1)
    return{"message":"Booking shared successfully"}

@frappe.whitelist()
def unsafe_booking_query():
    return frappe.get_all("Booking",fields="*")

@frappe.whitelist()
def safe_booking_query():
    roles=frappe.get_roles()
    is_staff="Front Desk Staff" in roles or "Space Manager" in roles
    bookings=frappe.get_list("Booking",fields=["name","member","resource","booking_date","start_time","end_time","headcount","status"])
    if not is_staff:
        return bookings
    for booking in bookings:
        booking["member_email"]=frappe.db.get_value("Member",booking.member,"email")
        booking["member_phone"]=frappe.db.get_value("Member",booking.member,"phone")

    return bookings

# ---------------------group B-------------------------
from frappe.query_builder import DocType

@frappe.whitelist()
def get_upcoming_bookings():
    BK=DocType("Booking")
    result=(
        frappe.qb
        .from_(BK)
        .select(BK.name,BK.member,BK.resource,BK.booking_date,BK.start_time)
        .where(
            (BK.booking_date>=frappe.utils.getdate())
            & BK.status.isin(["Pending Confirmation","Confirmed"])
        )
        .orderby(BK.booking_date)
        .run(as_dict=True)
    )
    return result

@frappe.whitelist()
def reassign_bookings(from_member,to_member):
    try:
        frappe.db.sql("""
            UPDATE `tabBooking`
            SET member=%s
            WHERE member=%s
              AND booking_date>=CURDATE()
              AND status!='Cancelled'
        """,(to_member,from_member))
        frappe.db.commit()
    except Exception:
        frappe.db.rollback()
        frappe.log_error(title="Booking Reassignment Failed",message=frappe.get_traceback())
        raise
    return True

# ---------------group H------------------------
@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def get_allowed_resources(doctype,txt,searchfield,start,page_len,filters):
    filters=frappe.parse_json(filters)
    member_name=filters.get("member")
    if not member_name:
        return []
    membership_plan=frappe.db.get_value("Member",member_name,"membership_plan")
    if not membership_plan:
        return []
    plan=frappe.get_doc("Membership Plan",membership_plan)
    allowed_types=[row.resource_type for row in plan.allowed_resource_types]
    if not allowed_types:
        return []

    return frappe.db.sql("""
        SELECT name,resource_name,resource_type
        FROM `tabResource`
        WHERE resource_type IN %(allowed_types)s
          AND is_active=1
          AND resource_name LIKE %(txt)s
        ORDER BY resource_name
        LIMIT %(start)s,%(page_len)s
    """,{
        "allowed_types":tuple(allowed_types),
        "txt":f"%{txt}%",
        "start":start,
        "page_len":page_len
    })

# --------------------group H--------------------------------
@frappe.whitelist()
def get_live_availability(resource,booking_date,start_time,end_time,booking_name=None):
    if not resource or not booking_date or not start_time or not end_time:
        return None
    capacity=frappe.db.get_value("Resource",resource,"capacity")
    if not capacity:
        return None
    existing_headcount=frappe.db.sql("""
        SELECT COALESCE(SUM(headcount),0)
        FROM `tabBooking`
        WHERE resource=%s
          AND booking_date=%s
          AND start_time<%s
          AND end_time>%s
          AND status IN ('Pending Confirmation','Confirmed','Checked-In')
          AND name!=%s
    """,(resource,booking_date,end_time,start_time,booking_name or ""))[0][0]

    existing_headcount=existing_headcount or 0
    free_seats=max(0,capacity-existing_headcount)

    return{
        "free_seats":free_seats,
        "capacity":capacity
    }

# ------------------group H2---------------------------
@frappe.whitelist()
def cancel_booking(booking_name,reason):
    booking=frappe.get_doc("Booking",booking_name)
    booking.cancellation_reason=reason
    booking.cancel()
    return True

@frappe.whitelist()
def reassign_booking(booking_name,new_member):
    booking=frappe.get_doc("Booking",booking_name)
    if booking.status not in ["Pending Confirmation","Confirmed"]:
        frappe.throw("This booking cannot be reassigned at this stage.")
    if booking.member==new_member:
        frappe.throw("Booking is already assigned to this member.")
    member=frappe.get_doc("Member",new_member)
    if member.status!="Active":
        frappe.throw("Only Active members can be assigned.")
    if not member.membership_plan:
        frappe.throw("The new member does not have a Membership Plan.")
    plan=frappe.get_doc("Membership Plan",member.membership_plan)
    allowed_types=[row.resource_type for row in plan.allowed_resource_types]
    resource_type=frappe.db.get_value("Resource",booking.resource,"resource_type")
    if resource_type not in allowed_types:
        frappe.throw(
            f"Resource type '{resource_type}' is not allowed for the new member's Membership Plan."
        )
    if booking.docstatus==0:
        booking.member=new_member
        booking.save()
    elif booking.docstatus==1:
        booking.db_set("member",new_member)
    else:
        frappe.throw("Invalid booking state.")

    return True