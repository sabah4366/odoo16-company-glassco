from odoo import models, fields, api, _

class AccountPaymentInherit(models.Model):
    _inherit = 'account.payment'

    def button_open_journal_entry(self):
        ''' Redirect the user to this payment journal.
        :return:    An action on account.move.
        '''
        result = super(AccountPaymentInherit, self).button_open_journal_entry()
        record = self.env['account.move'].browse(self.move_id.id)
        record.write({
            'cheque_number': self.cheque_num ,
        })
        return {
            'name': _("Journal Entry"),
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'context': {'create': False},
            'view_mode': 'form',
            'res_id': self.move_id.id,
        }
