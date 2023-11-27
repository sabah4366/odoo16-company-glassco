from odoo import models, fields, api, _
from datetime import datetime




class CustomerReportWizard(models.TransientModel):
    _name = 'customer.pdf.report.wizard'

    def get_todat(self):
        to_day = datetime.today()
        return to_day

    to_date = fields.Date(string="To Date", default=get_todat)
    from_date = fields.Date(string="From Date")
    partner_id = fields.Many2one('res.partner', string="Customer")

    def print_report_pdf(self):
        data = {
            'end_date': self.to_date,
            'partner_id': self.partner_id.id,
            'start_date': self.from_date
        }
        return self.env.ref(
            'new_pdf_report.action_report_print_statement_pdf').report_action(
            self, data=data)

