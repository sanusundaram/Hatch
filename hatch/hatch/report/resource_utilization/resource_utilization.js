// Copyright (c) 2026, sanu and contributors
// For license information, please see license.txt

// -----------------group I2------------------------------
frappe.query_reports["Resource Utilization"]={
    filters:[
        {
            fieldname:"from_date",
            label:"From Date",
            fieldtype:"Date",
            reqd:1,
            default:frappe.datetime.get_today()
        },
        {
            fieldname:"to_date",
            label:"To Date",
            fieldtype:"Date",
            reqd:1,
            default:frappe.datetime.get_today()
        },
        {
            fieldname:"resource",
            label:"Resource",
            fieldtype:"Link",
            options:"Resource"
        }
    ],
    formatter:function(value,row,column,data){
        if(column.fieldname==="utilization"){
            let utilization=parseFloat(value)||0;
            if(utilization>95){
                return `<span style="color: red;">${utilization.toFixed(2)}%</span>`;
            }
            if(utilization>=40&&utilization<=85){
                return `<span style="color: green;">${utilization.toFixed(2)}%</span>`;
            }
            return `${utilization.toFixed(2)}%`;
        }
        return value;
    }
};