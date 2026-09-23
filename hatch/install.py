import frappe


def after_install():
    create_default_resources()
    create_default_settings()

    frappe.msgprint(
        "Hatch installed successfully. Default resources and settings created."
    )


def create_default_resources():

    resources = [
        {
            "name": "Room A",
            "resource_name": "Room A",
            "resource_type": "Meeting Room",
            "capacity": 6,
            "hourly_rate": 1000,
            "floor_location": "4th Floor",
            "is_active": 1,
        },
        {
            "name": "Room B",
            "resource_name": "Room B",
            "resource_type": "Meeting Room",
            "capacity": 3,
            "hourly_rate": 700,
            "floor_location": "4th Floor",
            "is_active": 1,
        },
        {
            "name": "Hot Desk Zone",
            "resource_name": "Hot Desk Zone",
            "resource_type": "Hot Desk Zone",
            "capacity": 12,
            "hourly_rate": 400,
            "floor_location": "4th Floor",
            "is_active": 1,
        },
    ]

    for data in resources:

        if not frappe.db.exists("Resource", data["name"]):

            frappe.get_doc({
                "doctype": "Resource",
                **data
            }).insert(ignore_permissions=True)


def create_default_settings():

    if not frappe.db.exists("Hatch Settings", "Hatch Settings"):

        frappe.get_doc({
            "doctype": "Hatch Settings",
            "manager_email": "manager@example.com",
            "pending_confirmation_expiry_hours": 2,
            "cancellation_window_hours": 4,
            "waitlist_enabled": 1,
        }).insert(ignore_permissions=True)