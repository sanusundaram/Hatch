// Copyright (c) 2026, sanu and contributors
// For license information, please see license.txt

// -----------------group H------------------------------
frappe.ui.form.on("Booking",{
    setup(frm){
        frm.set_query("resource",function(){
            if(!frm.doc.member){
                return {};
            }
            return{
                query:"hatch.api.get_allowed_resources",
                filters:{member:frm.doc.member}
            };
        });
    },
    refresh(frm){
        let colors={
            "Draft":"grey",
            "Pending Confirmation":"orange",
            "Confirmed":"green",
            "Checked-In":"blue",
            "Completed":"green",
            "Cancelled":"red"
        };
        if(frm.doc.status){
            frm.dashboard.add_indicator(frm.doc.status,colors[frm.doc.status]||"grey");
        }
        if(frm.doc.status==="Confirmed"&&Number(frm.doc.docstatus)===1&&frm.doc.booking_date===frappe.datetime.get_today()){
            frm.add_custom_button("Check In",function(){
                frm.set_value("status","Checked-In");
                frm.save();
            });
        }
        if(Number(frm.doc.docstatus)===1&&frm.doc.status!=="Cancelled"){
            frm.add_custom_button("Cancel Booking",function(){
                let dialog=new frappe.ui.Dialog({
                    title:"Cancel Booking",
                    fields:[
                        {
                            label:"Cancellation Reason",
                            fieldname:"cancellation_reason",
                            fieldtype:"Small Text",
                            reqd:1
                        }
                    ],
                    primary_action_label:"Cancel Booking",
                    primary_action(values){
                        frappe.call({
                            method:"hatch.api.cancel_booking",
                            args:{
                                booking_name:frm.doc.name,
                                reason:values.cancellation_reason
                            },
                            callback:function(r){
                                if(r.message){
                                    dialog.hide();
                                    frappe.show_alert({
                                        message:"Booking cancelled successfully",
                                        indicator:"green"
                                    });
                                    frm.reload_doc();
                                    frm.trigger("resource");
                                }
                            }
                        });
                    }
                });
                dialog.show();
            });
        }

        if(!frm.is_new()&&(frm.doc.status==="Pending Confirmation"||frm.doc.status==="Confirmed")){
            frm.add_custom_button("Reassign to Another Member",function(){
                frappe.prompt(
                    [
                        {
                            label:"New Member",
                            fieldname:"new_member",
                            fieldtype:"Link",
                            options:"Member",
                            reqd:1
                        }
                    ],
                    function(values){
                        if(values.new_member===frm.doc.member){
                            frappe.msgprint("Please select a different member.");
                            return;
                        }

                        frappe.confirm(
                            `Are you sure you want to reassign this booking to ${values.new_member}?`,
                            function(){
                                frappe.call({
                                    method:"hatch.api.reassign_booking",
                                    args:{
                                        booking_name:frm.doc.name,
                                        new_member:values.new_member
                                    },
                                    callback:function(r){
                                        if(r.message){
                                            frappe.show_alert({
                                                message:"Booking reassigned successfully",
                                                indicator:"green"
                                            });
                                            frm.reload_doc();
                                            frm.trigger("resource");
                                        }
                                    }
                                });
                            }
                        );
                    },
                    "Reassign Booking",
                    "Continue"
                );
            });
        }
    },
    resource(frm){
        show_live_availability(frm);
    },
    booking_date(frm){
        show_live_availability(frm);
    },
    start_time(frm){
        show_live_availability(frm);
    },
    end_time(frm){
        show_live_availability(frm);
    }
});

function show_live_availability(frm){
    if(!frm.doc.resource||!frm.doc.booking_date||!frm.doc.start_time||!frm.doc.end_time){
        frm.set_intro("");
        return;
    }

    frappe.call({
        method:"hatch.api.get_live_availability",
        args:{
            resource:frm.doc.resource,
            booking_date:frm.doc.booking_date,
            start_time:frm.doc.start_time,
            end_time:frm.doc.end_time,
            booking_name:frm.doc.name
        },
        callback:function(r){
            if(!r.message){
                return;
            }

            let free_seats=r.message.free_seats;
            let capacity=r.message.capacity;

            frm.set_intro(`${free_seats} of ${capacity} seats free in this slot`);
        }
    });
}