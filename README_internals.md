B2c — Dangerous Patterns - document lifecycle bugs
def validate(self):
    self.total_amount=sum(r.amount for r in self.addons)+self.base_amount
    self.save()
    resource=frappe.get_doc("Resource",self.resource)
    resource.times_booked+=1
    resource.save()

ANSWER
There are two problems here. First, self.save() inside validate() can call validate again and cause recursion. Second, updating and saving another document inside validate is not a good pattern because validate should mainly be used for validation and calculations.

Correct way:
def validate(self):
    self.total_amount=sum(r.amount for r in self.addons)+self.base_amount

def on_submit(self):
    resource=frappe.get_doc("Resource",self.resource)
    resource.times_booked+=1
    resource.save()
B2d — Concurrency, One Question - optimistic locking
In README_internals.md: why would you see a "Document has been modified after you have opened it" error, and how does Frappe prevent concurrent overwrites?
ANSWER

This error comes when two front-desk staff open the same Booking and one of them saves it first. Frappe checks the modified time when saving. If the Booking was changed by someone else, the modified time will be different, so Frappe stops the second save. This prevents one user's changes from overwriting the other user's changes. Frappe does not lock the Booking while it is open, it checks the change when saving.

C3 — Booking Add-on Entry & Child Table Internals
What is the DB table name for Booking Add-on Entry? When you append a row and save, what 4 columns does Frappe set automatically on the child row? If you delete the row at idx=2 and re-save, what happens to the idx values of the remaining rows?
ANSWER

The DB table name is tabBooking Add-on Entry. When a row is added and saved, Frappe sets name, parent, parenttype and parentfield automatically. The idx value is used to keep the child rows in order. If the row at idx=2 is deleted and the document is saved, the remaining rows are re-numbered and the idx values stay in order.

E1 — Complete Lifecycle
on_update()
Call self.save() inside on_update and observe what breaks. Explain it and correct the pattern in README_internals.md.
ANSWER

When self.save() is used inside on_update(), save triggers the update again and on_update() gets called again. This keeps repeating and causes recursive calls. So self.save() should not be used inside on_update().

E2 — autoname & Renaming
Call frappe.rename_doc("Member", old, new, merge=False) in a utility function and show linked fields update automatically. Explain when merge=True would be dangerous.
ANSWER

When frappe.rename_doc() is called, it changes the Member name and also updates the Link fields in other documents. So the member field in existing Bookings will also get the new Member name automatically.

When merge=True and the new name already exists, the two documents can be merged. This can be dangerous because the old Member record will not remain separately and some data can get combined.

E3 — One Performance Judgment Call
frappe.db.get_value vs get_doc
In the Resource controller's on_update, which pattern would you use to read a single settings value, and why?
doc=frappe.get_doc("Hatch Settings","Hatch Settings")
hours=doc.pending_confirmation_expiry_hours
hours=frappe.db.get_value("Hatch Settings",None,"pending_confirmation_expiry_hours")
ANSWER

I would use frappe.db.get_value("Hatch Settings",None,"pending_confirmation_expiry_hours") because I only need one value from Hatch Settings. get_doc() loads the full document, but get_value() directly gets the required field, so it is simpler for this case.

H1 — Booking Form Script
ANSWER

The live availability check should not be done inside the client validate event as a synchronous call. frappe.call() is asynchronous, so the response comes later and cannot be used immediately for the validation result. That is why the availability check is done when the resource, booking date, start time or end time changes. The final capacity check is still done on the server.

I1 — Query Report: Upcoming Bookings by Resource
SQL parameterization
Selects name, member, resource, booking_date, start_time, end_time, headcount, status. Filter: booking_date >= today, optional resource filter using %(resource)s. In README_internals.md: show the f-string version side by side with the parameterized version, and explain why the latter is always preferred.
ANSWER

In an f-string, the Resource value entered by the user is directly added into the SQL query. In the parameterized version using %(resource)s, the query and the value are passed separately. This is safer because the user input is not directly added into the SQL query.

K2 — Spot the N+1 - bulk fetch vs per-row query
The snippet below has an N+1 query problem. Identify it and rewrite it:
N+1 PROBLEM - fix this

bookings=frappe.get_all("Booking",fields=["name","member"])
for bk in bookings:
mem=frappe.get_doc("Member",bk.member)
print(mem.member_name,mem.email)

ANSWER

The problem is frappe.get_doc() is used inside the loop. So every Booking makes another query to get the Member. I fixed it by getting all the Members together and using a dictionary for lookup.
  
bookings=frappe.get_all("Booking",fields=["name","member"])
member_names=list({bk.member for bk in bookings if bk.member})
members=frappe.get_all(
    "Member",
    filters={"name":["in",member_names]},
    fields=["name","member_name","email"]
)
member_lookup={m.name:m for m in members}

for bk in bookings:
    member=member_lookup.get(bk.member)
    if member:
        print(member.member_name,member.email)

Here only two database queries are used, one for Bookings and one for Members. The loop uses the dictionary, so there is no extra query for every Booking.

N1 — ignore_permissions Audit & JS-Hiding Pitfall
List every place using ignore_permissions=True; one-sentence justification each.
ANSWER
In after_install(), the default Resource records are inserted with ignore_permissions=True because they need to be created automatically when Hatch is installed.
In after_install(), the Hatch Settings record is inserted with ignore_permissions=True because the default settings should be created during installation.
In log_change(), the Audit Log is inserted with ignore_permissions=True because audit entries should be created even if the current user does not have normal create permission for Audit Log.
JS field hiding

For non-staff users, the Member email and phone can be hidden in the Booking form:

frappe.ui.form.on("Booking",{
    refresh(frm){
        let is_staff=frappe.user.has_role("Front Desk Staff")||frappe.user.has_role("Space Manager");
        frm.toggle_display("member_email",is_staff);
        frm.toggle_display("member_phone",is_staff);
    }
});