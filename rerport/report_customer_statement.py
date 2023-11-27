from odoo import models, fields, api
from datetime import date
from datetime import datetime
from collections import defaultdict




class CollectionSaleReportPdf(models.AbstractModel):
    _name = 'report.new_pdf_report.report_statement_pdf'

    def _get_report_values(self, docids, data=None):

        partner_id = self.env['res.partner'].browse(data['partner_id'])
        company_id = self.env.company

        partner_details = {
            'name': partner_id.name,
            'street': partner_id.street,
            'street2': partner_id.street2,
            'city': partner_id.city,
            'state': partner_id.state_id.name,
            'country': partner_id.country_id.name,
            'zip': partner_id.zip,
            'contact1': partner_id.phone,
            'contact2': partner_id.mobile,
        }

        statements_of_customer_template = {
            'get_pdc_details': self._get_pdc_details(data),
            # 'get_statement_details': self._get_statement_details(data),
            # 'vendor_bills': self._get_vendor_bill_details(data),
            # 'check_journal_entries': self._get_journal_entries_details(data),
            'data': data,
            'partner_details': partner_details,
            'company': company_id,
            # 'grand_total': self._get_total(data),
            # 'entry_total': self._get_entry_total(data),
            # 'check_status': self._get_status(data),
            # 'check_entries_ret': self._get_entries_ret(data),
            # 'get_cash_details': self._get_cash_details(data),
            # 'invoice_balance':self._invoice_balance(data),
            'combined_data_set':self._get_invoice_details_amt(data)

        }
        return statements_of_customer_template

    def _get_pdc_details(self, data):
        rec_data = self.env['account.move'].search(
            [('company_id', '=', self.env.company.id),
             ('partner_id', '=', data['partner_id']),
             ('move_type', '=', 'out_invoice'),
             # ('pdc_payment_ids.payment_date', '<=', data['end_date']),
             # ('pdc_payment_ids.payment_date', '>=', data['start_date']),
             ('state', '=', 'posted'),
            ],
            order="invoice_date asc")

        vendor_data = self.env['account.move'].search(
            [('company_id', '=', self.env.company.id),
             ('partner_id', '=', data['partner_id']),
             ('move_type', '=', 'in_invoice'),
             ('invoice_date', '<=', data['end_date']),
             ('invoice_date','>=', data['start_date']),
             ('state', '=', 'posted'),
             ('payment_state', 'in', ['not_paid', 'partial'])],
            order="invoice_date asc")

        pdc_data= self.env['pdc.wizard'].search(
            [('company_id', '=', self.env.company.id),
             ('partner_id', '=', data['partner_id']),
             ('payment_date', '<=', data['end_date']),
             ('payment_date', '>=', data['start_date']),
             ('state', 'in',['done']),
             ],
            )

        data_dict = {}
        if rec_data :
            for rec in rec_data:
                pdc_ids = rec.pdc_payment_ids.filtered(
                    lambda x: x.state in ['done']and
                              x.payment_date >= datetime.strptime(data['start_date'], "%Y-%m-%d").date() and
                              x.payment_date <= datetime.strptime(data['end_date'], "%Y-%m-%d").date() )


                for pdc in pdc_ids:

                    key = pdc.id
                    inv_numbres = ''

                    for inv in pdc.invoice_ids:


                        inv_numbres += inv.name
                        inv_numbres += ','

                    if key in data_dict:
                        data_dict[key].append({
                            'name': pdc.name,
                            'reference': pdc.reference,
                            'date': pdc.payment_date.strftime('%d/%m/%Y'),
                            'amount': pdc.payment_amount,
                            'invoice_number': inv_numbres,
                        })

                    else:
                        data_dict[key] = [({
                            'name': pdc.name,
                            'reference': pdc.reference,
                            'date': pdc.payment_date.strftime('%d/%m/%Y'),
                            'amount': pdc.payment_amount,
                            'invoice_number': inv_numbres,
                        })]

        vend_dict = {}
        if vendor_data:
            for rec in vendor_data:
                pdc_ids = rec.pdc_payment_ids.filtered(
                    lambda x: x.state in ['draft','registered', 'deposited','done'])
                for pdc in pdc_ids:
                    key = pdc.id
                    inv_numbres = ''

                    for inv in pdc.invoice_ids:
                        inv_numbres += inv.name
                        inv_numbres += ','

                    if key in data_dict:
                        data_dict[key].append({
                            'name': pdc.name,
                            'reference': pdc.reference,
                            'date': pdc.payment_date.strftime('%d/%m/%Y'),
                            'amount': pdc.payment_amount,
                            'invoice_number': inv_numbres,
                        })

                    else:
                        data_dict[key] = [({
                            'name': pdc.name,
                            'reference': pdc.reference,
                            'date': pdc.payment_date.strftime('%d/%m/%Y'),
                            'amount': pdc.payment_amount,
                            'invoice_number': inv_numbres,
                        })]

        # pdc_dict = {}
        # if pdc_data:
        #     for data in pdc_data:
        #         for rec in data.rec_data:
        #             key = data.id
        #             inv_numbres = ''
        #             inv_numbres += rec.move_name
        #             if key in pdc_dict:
        #                 pdc_dict[key].append({
        #                     'move_name': rec.name,
        #                     'amount': data.payment_amount,
        #                     'date': rec.date.strftime('%d/%m/%Y'),
        #                     'reference': data.reference,
        #                     'invoice_number': rec.move_name,
        #                 })
        #             else:
        #                 pdc_dict[key] = [({
        #                     'move_name': rec.name,
        #                     'amount': data.payment_amount,
        #                     'reference': data.reference,
        #                     'invoice_number': rec.move_name,
        #                     'date': rec.date.strftime('%d/%m/%Y'),
        #                 })]

        new_data_dict = []
        for new_rec in data_dict:
            new_data_dict.append(data_dict[new_rec][0])
        # if pdc_data:
        #     for pdc_rec in pdc_dict:
        #         new_data_dict.append(pdc_dict[pdc_rec][0])
        #         print(new_data_dict,'new_data_dict')


        return new_data_dict


    def _get_invoice_details_amt(self, data):
        rec_data = self.env['account.move'].search(
            [('company_id', '=', self.env.company.id),
             ('partner_id', '=', data['partner_id']),
             ('move_type', '=', 'out_invoice'),
             ('invoice_date', '<=', data['end_date']),
             ('invoice_date', '>=', data['start_date']),
             ('state', '=', 'posted'),
             ],
            order="invoice_date asc")

        data_dict = {}
        length = 1
        for rec in rec_data:
            # edited
            ppch_ids = rec.env['account.payment'].search(
                [('partner_id', '=', rec.partner_id.id),
                 ('date', '<=', data['end_date']),
                 ('date', '>=', data['start_date']),
                 ],
                order="date asc"
            )


            for ppch in ppch_ids:
                if length > len(ppch_ids):
                    break
                length += 1
                key = ppch.date.strftime('%d/%m/%Y')

                if key in data_dict:

                    data_dict[key].append({
                        'name': ppch.name,
                        'date': ppch.date.strftime('%d/%m/%Y'),
                        'amount': ppch.amount,
                        'invoice_number': ppch.name,
                        'cash_payment':'CSH'

                    })

                else:

                    data_dict[key] = [({
                        'name': ppch.name,
                        'date': ppch.date.strftime('%d/%m/%Y'),
                        'amount': ppch.amount,
                        'invoice_number': ppch.name,
                        'cash_payment': 'CSH'
                    })]




        parms = data
        rec_data = self.env['account.move'].search([('company_id', '=', self.env.company.id),
                                                    ('partner_id', '=', data['partner_id']),
                                                    ('move_type', '=', 'out_invoice'),
                                                    ('invoice_date', '<=', data['end_date']),
                                                    ('invoice_date', '>=', data['start_date']),
                                                    ('state', '=', 'posted'),
                                                    ],
                                                   order="invoice_date asc")


        data_dicts = {}
        val = 0
        # records = self._invoice_balance(data)
        # itm = 0
        for rec in rec_data:
            # inital_blnc = float(format(records[itm], ".2f"))
            # itm += 1
            if rec.show_del_order == False:
                del_num = rec.delivery_order
            elif rec.show_del_order == True:
                del_num = rec.related_del_id.name
            pdc_ids = rec.pdc_payment_ids.filtered(lambda x: x.state in ['registered', 'deposited'])
            if not pdc_ids:
                key = rec.invoice_date.strftime('%d/%m/%Y')
                if key in data_dicts:
                    data_dicts[key].append({
                        'name': rec.name,
                            'date': rec.invoice_date.strftime('%d/%m/%Y'),
                            'amount': rec.amount_total_signed,
                            'order_no': rec.related_sale_id.name if rec.related_sale_id.name else None,
                            'do_no': del_num,
                            'due_date': rec.invoice_date_due.strftime('%d/%m/%Y'),
                            'due_amount': rec.amount_residual_signed,
                            'cash_payment': 'INV'
                            # 'invoice_amt': inital_blnc
                    })


                else:
                    data_dicts[key] = [
                        {
                            'name': rec.name,
                            'date': rec.invoice_date.strftime('%d/%m/%Y'),
                            'amount': rec.amount_total_signed,
                            'order_no': rec.related_sale_id.name if rec.related_sale_id.name else None,
                            'do_no': del_num,
                            'due_date': rec.invoice_date_due.strftime('%d/%m/%Y'),
                            'due_amount': rec.amount_residual_signed,
                            'cash_payment': 'INV'
                            # 'invoice_amt': inital_blnc

                        }
                    ]


            else:
                key =  rec.invoice_date.strftime('%d/%m/%Y')
                if key in data_dicts:
                    data_dicts[key].append({
                        'name': rec.name,
                            'date': rec.invoice_date.strftime('%d/%m/%Y'),
                            'amount': rec.amount_total_signed,
                            'order_no': rec.related_sale_id.name if rec.related_sale_id.name else None,
                            'do_no': del_num,
                            'due_date': rec.invoice_date_due.strftime('%d/%m/%Y'),
                            'due_amount': rec.amount_residual_signed,
                            'cash_payment': 'INV'
                            # 'invoice_amt': inital_blnc
                    })

                else:
                    data_dicts[key] = [
                        {
                            'name': rec.name,
                            'date': rec.invoice_date.strftime('%d/%m/%Y'),
                            'amount': rec.amount_total_signed,
                            'order_no': rec.related_sale_id.name if rec.related_sale_id.name else None,
                            'do_no': del_num,
                            'due_date': rec.invoice_date_due.strftime('%d/%m/%Y'),
                            'due_amount': rec.amount_residual_signed,
                            'cash_payment': 'INV'
                            # 'invoice_amt': inital_blnc

                        }
                    ]
        #first staring
        record_datas = self.env['account.move.line'].search(
            [('partner_id', '=', data['partner_id']),
             ('move_id.move_type', '=', 'entry'),
             ('move_id.journal_id.type', 'in', ['general', 'sale']),
             ('date', '<=', data['end_date']),
             ('date', '>=', data['start_date']),
             ])
        total_value = 0
        for rd in record_datas:
                record_datas.move_id.print_initial = True
                if rd.account_id.account_type == 'asset_receivable':
                    amount=0
                    if rd.credit:
                        total_value += rd.credit
                        initial_amt='CSH'
                        amount=rd.credit

                    elif rd.debit:
                        total_value += rd.debit
                        initial_amt='INV'
                        amount=rd.debit
                    key = rd.move_id.date.strftime('%d/%m/%Y')
                    if key in data_dict:
                        data_dict[key].append({
                            'name':rd.move_id.name,
                            'date':rd.move_id.date.strftime('%d/%m/%Y'),
                            'amount': amount,
                            'cash_payment':initial_amt
                            # 'due_amount': rcrd.amount_residual_signed,
                        })
                    else:
                        data_dict[key] = [
                            {
                                'name':rd.move_id.name,
                                'date':rd.move_id.date.strftime('%d/%m/%Y'),
                                'amount': amount,
                                'cash_payment': initial_amt
                                # 'due_amount': rcrd.amount_residual_signed,
                            }
                        ]



        #last starting


        for date, records in data_dicts.items():
            date_obj = datetime.strptime(date, '%d/%m/%Y')
            key = date_obj.strftime('%d/%m/%Y')
            for record in records:
                if key in data_dict:
                    data_dict[key].append({
                                'name': record['name'],
                                'date':date_obj.strftime('%d/%m/%Y'),
                                'amount': record['amount'],
                                'cash_payment':record['cash_payment']


                                # 'due_amount': rcrd.amount_residual_signed,
                            })
                else:
                    data_dict[key] = [
                        {
                            'name': record['name'],
                            'date': date_obj.strftime('%d/%m/%Y'),
                            'amount': record['amount'],
                            'cash_payment': record['cash_payment']
                            # 'due_amount': rcrd.amount_residual_signed,
                        }
                    ]

        sorted_data = {k: sorted(v, key=lambda x: datetime.strptime(x['date'], '%d/%m/%Y')) for k, v in data_dict.items()}

        # Sort the main dictionary based on dates
        sorted_data = dict(sorted(sorted_data.items(), key=lambda x: datetime.strptime(x[0], '%d/%m/%Y')))

        return sorted_data



