# Copyright (c) 2026, sanu and contributors
# For license information, please see license.txt

# import frappe
from frappe import _


def execute(filters: dict | None = None):
	"""Return columns and data for the report.

	This is the main entry point for the report. It accepts the filters as a
	dictionary and should return columns and data. It is called by the framework
	every time the report is refreshed or a filter is updated.
	"""
	columns = get_columns()
	data = get_data()

	return columns, data

def execute_snapshot_report(filters: dict | None = None):
	"""Return columns and data for the report.

	This is the main entry point for snapshot report. When 'Synced
	Report' is enabled in report, framework will call this method
	every time the report is refreshed or a filter is updated. It
	accepts the same filters as normal execute. But a utility method -
	get_latest_sync, is also imported.

	"""
	from frappe.database.duckdb.database import get_latest_sync

	columns = get_columns()
	data = get_data()

	return columns, data

def get_columns() -> list[dict]:
	"""Return columns for the report.

	One field definition per column, just like a DocType field definition.
	"""
	return [
		{
			"label": _("Column 1"),
			"fieldname": "column_1",
			"fieldtype": "Data",
		},
		{
			"label": _("Column 2"),
			"fieldname": "column_2",
			"fieldtype": "Int",
		},
	]


def get_data() -> list[list]:
	"""Return data for the report.

	The report data is a list of rows, with each row being a list of cell values.
	"""
	return [
		["Row 1", 1],
		["Row 2", 2],
	]



# --------------------group I2-------------------------
def execute(filters=None):
    if not filters:
        filters={}
    from_date=frappe.utils.getdate(filters.get("from_date"))
    to_date=frappe.utils.getdate(filters.get("to_date"))
    if not from_date or not to_date:
        frappe.throw("From Date and To Date are required.")
    if from_date>to_date:
        frappe.throw("From Date cannot be after To Date.")
    booking_filters={
        "booking_date":["between",[from_date,to_date]],
        "status":["in",["Pending Confirmation","Confirmed","Checked-In","Completed"]]
    }
    if filters.get("resource"):
        booking_filters["resource"]=filters.get("resource")
    bookings=frappe.get_list(
        "Booking",
        filters=booking_filters,
        fields=["name","resource","booking_date","start_time","end_time","total_amount","status"],
        order_by="booking_date asc,start_time asc",
        limit_page_length=0
    )
    resource_data={}
    for booking in bookings:
        resource=booking.resource
        if resource not in resource_data:
            resource_data[resource]={
                "total_bookings":0,
                "total_hours":0,
                "revenue":0
            }
        resource_data[resource]["total_bookings"]+=1
        start=frappe.utils.get_datetime(f"{booking.booking_date} {booking.start_time}")
        end=frappe.utils.get_datetime(f"{booking.booking_date} {booking.end_time}")
        hours=(end-start).total_seconds()/3600
        resource_data[resource]["total_hours"]+=hours
        resource_data[resource]["revenue"]+=frappe.utils.flt(booking.total_amount or 0)
    number_of_days=(to_date-from_date).days+1
    available_hours=number_of_days*24
    data=[]
    total_bookings=0
    total_revenue=0
    busiest_resource=None
    busiest_booking_count=0
    for resource,values in resource_data.items():
        total_bookings_for_resource=values["total_bookings"]
        total_hours=values["total_hours"]
        revenue=values["revenue"]
        if available_hours:
            utilization=(total_hours/available_hours)*100
        else:
            utilization=0
        data.append({
            "resource":resource,
            "total_bookings":total_bookings_for_resource,
            "total_hours":round(total_hours,2),
            "utilization":round(utilization,2),
            "revenue":revenue
        })
        total_bookings+=total_bookings_for_resource
        total_revenue+=revenue
        if total_bookings_for_resource>busiest_booking_count:
            busiest_booking_count=total_bookings_for_resource
            busiest_resource=resource
    columns=[
        {
            "fieldname":"resource",
            "label":"Resource",
            "fieldtype":"Link",
            "options":"Resource",
            "width":200
        },
        {
            "fieldname":"total_bookings",
            "label":"Total Bookings",
            "fieldtype":"Int",
            "width":150
        },
        {
            "fieldname":"total_hours",
            "label":"Total Hours Booked",
            "fieldtype":"Float",
            "precision":2,
            "width":180
        },
        {
            "fieldname":"utilization",
            "label":"Utilization %",
            "fieldtype":"Percent",
            "width":150
        },
        {
            "fieldname":"revenue",
            "label":"Revenue",
            "fieldtype":"Currency",
            "options":"INR",
            "width":150
        }
    ]
    labels=[row["resource"] for row in data]
    booking_counts=[row["total_bookings"] for row in data]
    chart={
        "type":"bar",
        "data":{
            "labels":labels,
            "datasets":[
                {
                    "name":"Bookings",
                    "values":booking_counts
                }
            ]
        }
    }
    report_summary=[
        {
            "label":"Total Bookings",
            "value":total_bookings,
            "indicator":"Blue",
            "datatype":"Int"
        },
        {
            "label":"Total Revenue",
            "value":total_revenue,
            "indicator":"Green",
            "datatype":"Currency",
            "currency":"INR"
        },
        {
            "label":"Busiest Resource",
            "value":busiest_resource or "None",
            "indicator":"Orange",
            "datatype":"Data"
        }
    ]
    return columns,data,None,chart,report_summary