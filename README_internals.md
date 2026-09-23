def validate(self):
    self.total_amount = sum(r.amount for r in self.addons) + self.base_amount
    self.save()
    resource = frappe.get_doc("Resource", self.resource)
    resource.times_booked += 1
    resource.save()


correct-----------------
def validate(self):
    self.total_amount = sum(r.amount for r in self.addons) + self.base_amount