// Copyright (c) 2026, sanu and contributors
// For license information, please see license.txt

// frappe.ui.form.on("Booking", {
// 	refresh(frm) {

// 	},
// });
frappe.ui.form.on("Booking", {

    // --------------------------------
    // 1. Setup - Resource filtering
    // --------------------------------
    setup(frm) {

        frm.set_query("resource", function () {

            if (!frm.doc.member) {
                return {};
            }

            return {
                query: "hatch.api.get_allowed_resources",
                filters: {
                    member: frm.doc.member
                }
            };
        });
    },


    // --------------------------------
    // 2. Refresh - Status + Check In
    // --------------------------------
    refresh(frm) {

        // Status indicator
        if (frm.doc.status === "Confirmed") {

            frm.dashboard.add_indicator(
                "Confirmed",
                "green"
            );

        } else if (frm.doc.status === "Pending Confirmation") {

            frm.dashboard.add_indicator(
                "Pending Confirmation",
                "orange"
            );

        } else if (frm.doc.status === "Checked-In") {

            frm.dashboard.add_indicator(
                "Checked-In",
                "blue"
            );

        } else if (frm.doc.status === "Cancelled") {

            frm.dashboard.add_indicator(
                "Cancelled",
                "red"
            );
        }


        // Check In button
        if (
            frm.doc.status === "Confirmed" &&
            frm.doc.docstatus === 1 &&
            frm.doc.booking_date === frappe.datetime.get_today()
        ) {

            frm.add_custom_button(
                "Check In",
                function () {

                    frappe.call({
                        method: "hatch.api.check_in_booking",
                        args: {
                            booking_name: frm.doc.name
                        },

                        callback: function (r) {

                            if (!r.exc) {

                                frappe.show_alert({
                                    message: "Booking checked in successfully",
                                    indicator: "green"
                                });

                                frm.reload_doc();
                            }
                        }
                    });

                }
            );
        }
    },


    // --------------------------------
    // 3. Resource changed
    // --------------------------------
    resource(frm) {
        frm.trigger("check_availability");
    },


    // --------------------------------
    // 4. Booking date changed
    // --------------------------------
    booking_date(frm) {
        frm.trigger("check_availability");
    },


    // --------------------------------
    // 5. Start time changed
    // --------------------------------
    start_time(frm) {
        frm.trigger("check_availability");
    },


    // --------------------------------
    // 6. End time changed
    // --------------------------------
    end_time(frm) {
        frm.trigger("check_availability");
    },


    // --------------------------------
    // 7. Live availability
    // --------------------------------
    check_availability(frm) {

        if (
            !frm.doc.resource ||
            !frm.doc.booking_date ||
            !frm.doc.start_time ||
            !frm.doc.end_time
        ) {
            return;
        }

        frappe.call({

            method: "hatch.api.check_booking_availability",

            args: {
                resource: frm.doc.resource,
                booking_date: frm.doc.booking_date,
                start_time: frm.doc.start_time,
                end_time: frm.doc.end_time,
                booking_name: frm.doc.name
            },

            callback: function (r) {

                if (r.exc) {
                    return;
                }

                if (!r.message) {
                    return;
                }

                const data = r.message;

                frm.dashboard.set_headline(
                    `${data.free} of ${data.capacity} seats free in this slot`
                );
            }
        });
    }

});