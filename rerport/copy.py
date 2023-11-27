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
            'get_statement_details': self._get_statement_details(data),
            'vendor_bills': self._get_vendor_bill_details(data),
            'check_journal_entries': self._get_journal_entries_details(data),
            'data': data,
            'partner_details': partner_details,
            'company': company_id,
            'grand_total': self._get_total(data),
            'entry_total': self._get_entry_total(data),
            'check_status': self._get_status(data),
            'check_entries_ret': self._get_entries_ret(data),
            'get_cash_details': self._get_cash_details(data),
            'invoice_balance':self._invoice_balance(data),
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

    def _get_cash_details(self, data):
        rec_data = self.env['account.move'].search(
            [('company_id', '=', self.env.company.id),
             ('partner_id', '=', data['partner_id']),
             ('move_type', '=', 'out_invoice'),
             ('invoice_date', '<=', data['end_date']),
             ('invoice_date','>=', data['start_date']),
             ('state', '=', 'posted'),
             ],
            order="invoice_date asc")

        data_dict = {}
        for rec in rec_data:
            #edited
            ppch_ids = rec.env['account.payment'].search(
                [('partner_id', '=', rec.partner_id.id),
                 ('date', '<=', data['end_date']),
                 ('date', '>=', data['start_date']),
                 ],
                order="date asc"
            )
            for ppch in ppch_ids:
                key =ppch.date.strftime('%d/%m/%Y')


                if key in data_dict:

                    data_dict[key].append({
                        'name': ppch.name,
                        'date': ppch.date.strftime('%d/%m/%Y'),
                        'amount': ppch.amount,
                        'invoice_number': ppch.name,
                    })

                else:

                    data_dict[key] = [({
                        'name': ppch.name,
                        'date': ppch.date.strftime('%d/%m/%Y'),
                        'amount': ppch.amount,
                        'invoice_number': ppch.name,
                    })]

        new_data_dict = []
        for new_rec in data_dict:
            new_data_dict.append(data_dict[new_rec][0])

        # print('cash details',new_data_dict)
        return new_data_dict


    def _get_statement_details(self, data):
        parms = data
        rec_data = self.env['account.move'].search([('company_id', '=', self.env.company.id),
                                                    ('partner_id', '=', data['partner_id']),
                                                    ('move_type', '=', 'out_invoice'),
                                                    ('invoice_date', '<=', data['end_date']),
                                                    ('invoice_date', '>=', data['start_date']),
                                                    ('state', '=', 'posted'),
                                                    ],
                                                   order="invoice_date asc")
        pdc_records = self.env['pdc.wizard'].search(
                            [('company_id', '=', self.env.company.id),
                             ('partner_id', '=', data['partner_id']),
                             ('payment_date', '<=', data['end_date']),
                             ('payment_date', '>=', data['start_date']),
                             ('state', 'in',['registered', 'deposited']),
                             ],
                            )

        data_dict = {}
        val=0
        records=self._invoice_balance(data)
        itm=0
        for rec in rec_data:
            inital_blnc=float(format(records[itm], ".2f"))
            itm+=1
            if rec.show_del_order == False:
                del_num = rec.delivery_order
            elif rec.show_del_order == True:
                del_num = rec.related_del_id.name
            pdc_ids = rec.pdc_payment_ids.filtered(lambda x: x.state in ['registered', 'deposited'])
            if not pdc_ids:
                    key = rec.invoice_date.strftime("%B-%Y")
                    if key in data_dict:
                        data_dict[key].append({
                            'invoice_date': rec.invoice_date.strftime('%d/%m/%Y'),
                            'invoice_no': rec.name,
                            'order_no': rec.related_sale_id.name if rec.related_sale_id.name else None,
                            'do_no': del_num,
                            'due_date': rec.invoice_date_due.strftime('%d/%m/%Y'),
                            'total_amount':rec.amount_total_signed,
                            'due_amount': rec.amount_residual_signed,
                            'invoice_amt':inital_blnc
                        })


                    else:
                        data_dict[key] = [
                            {
                                'invoice_date': rec.invoice_date.strftime('%d/%m/%Y'),
                                'invoice_no': rec.name,
                                'order_no': rec.related_sale_id.name if rec.related_sale_id.name else None,
                                'do_no': del_num,
                                'due_date': rec.invoice_date_due.strftime('%d/%m/%Y'),
                                'total_amount': rec.amount_total_signed,
                                'due_amount': rec.amount_residual_signed,
                                'invoice_amt': inital_blnc

                            }
                        ]


            else:
                    key = rec.invoice_date.strftime("%B-%Y")
                    if key in data_dict:
                        data_dict[key].append({
                            'invoice_date': rec.invoice_date.strftime('%d/%m/%Y'),
                            'invoice_no': rec.name,
                            'order_no': rec.related_sale_id.name if rec.related_sale_id.name else None,
                            'do_no': del_num,
                            'due_date': rec.invoice_date_due.strftime('%d/%m/%Y'),
                            'total_amount': rec.amount_total_signed,
                            'due_amount':  rec.amount_residual_signed,
                            'invoice_amt': inital_blnc
                        })

                    else:
                        data_dict[key] = [
                            {
                                'invoice_date': rec.invoice_date.strftime(
                                    '%d/%m/%Y'),
                                'invoice_no': rec.name,
                                'order_no': rec.related_sale_id.name if rec.related_sale_id.name else None,
                                'do_no': del_num,
                                'due_date': rec.invoice_date_due.strftime(
                                    '%d/%m/%Y'),
                                'total_amount': rec.amount_total_signed,
                                'due_amount':  rec.amount_residual_signed,
                                'invoice_amt': inital_blnc

                            }
                        ]


        total_amount = 0
        total_sum = 0
        for data in data_dict:
            sl = 1
            for list in data_dict[data]:
                list['sl'] = sl
                sl += 1
                total_amount += list['due_amount']
                total_sum  += list['total_amount']
        data_dict['total_amount'] = total_amount
        data_dict['total_sum'] = total_sum
        entry = self._get_entries_ret(parms)
        if entry == 'true':
            jrnls = self._get_journal_entries_details(parms)
            total = 0
            for rec in jrnls:
                total += rec['entry_amount']
            data_dict['total_amount'] += total
        # print('statement ',data_dict)
        return data_dict

    def _get_vendor_bill_details(self, data):
        rec_data = self.env['account.move'].search([('company_id', '=', self.env.company.id),
                                                    ('partner_id', '=', data['partner_id']),
                                                    ('invoice_date', '<=', data['end_date']),
                                                    ('invoice_date', '>=', data['start_date']),
                                                    ('move_type', '=', 'in_invoice'),
                                                    ('state', '=', 'posted'),
                                                    ('payment_state', 'in', ['not_paid', 'partial'])],
                                                   order="invoice_date asc")
        data_dict = {}

        for rec in rec_data:
            if rec.show_del_order == False:
                del_num = rec.delivery_order
            elif rec.show_del_order == True:
                del_num = rec.related_del_id.name

            key = rec.invoice_date.strftime("%B-%Y")
            if key in data_dict:
                data_dict[key].append({
                    'invoice_date': rec.invoice_date.strftime('%d/%m/%Y'),
                    'invoice_no': rec.name,
                    'order_no': rec.invoice_origin,
                    'do_no': del_num,
                    'due_date': rec.invoice_date_due.strftime('%d/%m/%Y'),
                    'due_amount':  rec.amount_total_signed-rec.amount,

                })
            else:
                data_dict[key] = [
                    {
                        'invoice_date': rec.invoice_date.strftime('%d/%m/%Y'),
                        'invoice_no': rec.name,
                        'order_no': rec.invoice_origin,
                        'do_no': del_num,
                        'due_date': rec.invoice_date_due.strftime('%d/%m/%Y'),
                        'due_amount':  rec.amount_total_signed-rec.amount,

                    }
                ]

        total_amount = 0
        for data in data_dict:
            sl = 1
            for list in data_dict[data]:
                list['sl'] = sl
                sl += 1
                total_amount += list['due_amount']
        data_dict['total_amount'] = total_amount
        return data_dict

    def _get_entry_total(self, data):

        entri_data = self.env['account.move.line'].search(
            [('partner_id', '=', data['partner_id']), ('move_id.move_type', '=', 'entry'),
             ('move_id.journal_id.type', 'in', ['general', 'sale']),
             ])
        vendor_data = self.env['account.move'].search(
            [('company_id', '=', self.env.company.id), ('partner_id', '=', data['partner_id']),
             ('invoice_date', '<=', data['end_date']),
             ('invoice_date', '>=', data['start_date']),
             ('move_type', '=', 'in_invoice'), ('state', '=', 'posted'),
             ('payment_state', 'in', ['not_paid', 'partial'])],
            order="invoice_date asc")

        customer_data = self.env['account.move'].search(
            [('company_id', '=', self.env.company.id), ('partner_id', '=', data['partner_id']),
             ('move_type', '=', 'out_invoice'), ('invoice_date', '<=', data['end_date']),
             ('invoice_date', '>=', data['start_date']), ('state', '=', 'posted'),
            ],
            order="invoice_date asc")

        entry_tot = 0
        vendor_tot = 0
        customer_tot = 0
        ppc_tot = 0
        pdc_tot = 0
        ppch_dtls = self._get_cash_details(data)
        pdc_dtls = self._get_pdc_details(data)


        for ppc in ppch_dtls:

            ppc_tot += ppc['amount']


        for pdc in pdc_dtls:
            pdc_tot += pdc['amount']

        jrnls = self._get_journal_entries_details(data)
        total = 0

        for rec in entri_data:
            if rec.account_id.account_type == 'asset_receivable':
                if rec.credit:
                    total =0 - rec.credit
                if rec.debit:
                    total =  rec.debit
            entry_tot = total


        for rec in customer_data:
            customer_tot += rec.amount_total_signed


        for rec in vendor_data:
            vendor_tot += rec.amount_residual
        total_without_payment = customer_tot - vendor_tot + entry_tot + pdc_tot
        grand_tot = total_without_payment - ppc_tot
        return grand_tot

    def _get_total(self, data):
        vendor_data = self.env['account.move'].search(
            [('company_id', '=', self.env.company.id), ('partner_id', '=', data['partner_id']),
             ('invoice_date', '<=', data['end_date']),
             ('invoice_date','>=', data['start_date']),
             ('move_type', '=', 'in_invoice'), ('state', '=', 'posted'),
             ('payment_state', 'in', ['not_paid', 'partial'])],
            order="invoice_date asc")
        customer_data = self.env['account.move'].search(
            [('company_id', '=', self.env.company.id), ('partner_id', '=', data['partner_id']),
             ('move_type', '=', 'out_invoice'), ('invoice_date', '<=', data['end_date']),
             ('state', '=', 'posted'), ('invoice_date', '>=', data['start_date']),
           ],
            order="invoice_date asc")

        vendor_tot = 0
        customer_tot = 0
        pdc_tot = 0
        ppc_tot = 0

        pdc_dtls = self._get_pdc_details(data)
        ppch_dtls = self._get_cash_details(data)

        inv_dtls = self._get_statement_details(data)
        for rec in customer_data:
            customer_tot += rec.amount_total_signed

        for pdc in pdc_dtls:
            pdc_tot += pdc['amount']

        for ppc in ppch_dtls:
            ppc_tot += ppc['amount']





        for rec in vendor_data:
            vendor_tot += rec.amount_residual

        grand_tot = customer_tot - vendor_tot


        total=pdc_tot+ppc_tot
        gr_total = pdc_tot + grand_tot
        grand_total = gr_total - ppc_tot

        return grand_total

    def _get_status(self, data):
        vendor_data = self.env['account.move'].search(
            [('company_id', '=', self.env.company.id), ('partner_id', '=', data['partner_id']),
             ('invoice_date', '<=', data['end_date']),
             ('invoice_date', '>=', data['start_date']),
             ('move_type', '=', 'in_invoice'), ('state', '=', 'posted'),
             ('payment_state', 'in', ['not_paid', 'partial'])],
            order="invoice_date asc")

        if vendor_data:
            return 'true'
        else:
            return 'false'

    def _get_journal_entries_details(self, data):

        rec_data = self.env['account.move.line'].search(
            [('partner_id', '=', data['partner_id']),
             ('move_id.move_type', '=', 'entry'),
             ('move_id.journal_id.type', 'in', ['general', 'sale']),
             ('date', '<=', data['end_date']),
             ('date', '>=', data['start_date']),
             ])
        data_dict = {}
        total_value = 0

        lst=[]
        for record in rec_data:
                rec_data.move_id.print_initial = True
                if record.account_id.account_type == 'asset_receivable':
                    amount=0
                    if record.credit:
                        total_value += record.credit
                        initial_amt=1
                        amount=record.credit

                    elif record.debit:
                        total_value += record.debit
                        initial_amt=2
                        amount=record.debit

                    data_dict = {
                        'entry_date': record.move_id.date.strftime('%d/%m/%Y'),
                        'entry_no': record.move_id.name,
                        'entry_amount': amount,
                        'initial_value':initial_amt,
                        'ref': record.move_id.ref

                    }
                    lst.append(data_dict)
                elif record.account_id.account_type == 'asset_payable':


                    data_dict = {
                            'entry_date': record.move_id.date.strftime('%d/%m/%Y'),
                            'entry_no': record.move_id.name,
                            'entry_amount': record.credit,
                            'ref':record.move_id.ref
                        }
                    lst.append(data_dict)
        # print('jurnl entry',lst)
        return lst

    def _get_entries_ret(self, data):
        entri_data = self.env['account.move.line'].search(
            [('partner_id', '=', data['partner_id']), ('move_id.move_type', '=', 'entry'),
             ('move_id.journal_id.type', '=', 'general'),
             ])
        if entri_data:
            return 'true'
        else:
            return 'false'



    def _invoice_balance(self,data):
        rec_data = self.env['account.move.line'].search(
            [('partner_id', '=', data['partner_id']),
             ('move_id.move_type', '=', 'entry'),
             ('move_id.journal_id.type', 'in', ['general', 'sale']),
             ('date', '<=', data['end_date']),
             ('date', '>=', data['start_date']),
             ])
        record_datas = self.env['account.move'].search([('company_id', '=', self.env.company.id),
                                                    ('partner_id', '=', data['partner_id']),
                                                    ('move_type', '=', 'out_invoice'),
                                                    ('invoice_date', '<=', data['end_date']),
                                                    ('invoice_date', '>=', data['start_date']),
                                                    ('state', '=', 'posted'),
                                                    ],
                                                   order="invoice_date asc")
        lst = []
        val = 0
        initial_amount=self._get_journal_entries_details(data)
        amt=0
        incmnt=0
        for rec in record_datas:
            value=rec.amount_total_signed
            amount_crdt = 0
            amount_dbt = 0
            for record in rec_data:
                total_value = 0
                if not record.initial:
                    rec_data.move_id.print_initial = True
                    if record.account_id.account_type == 'asset_receivable':
                        if record.credit:
                            amount_crdt = record.credit
                            amt=1
                        elif record.debit:
                            amount_dbt = record.debit
                            if amt>=1:
                                amt+=1

                if amount_dbt:
                    if amount_dbt > val:
                        val =  value + amount_dbt
                        lst.append(val)
                    elif amount_dbt < val:
                        val += value
                        lst.append(val)
                elif amount_crdt:
                    if not val:
                         val = -(amount_crdt) + value
                         lst.append(val)
                    elif val:
                        val +=  value
                        lst.append(val)
                if amt>1:
                    intl_amt=amount_dbt-amount_crdt
                    if incmnt<1:
                        frst=lst[incmnt]=intl_amt+value
                    else:
                        frst+=value
                        lst[incmnt]=frst
                    incmnt+=1
            if not amount_dbt and not amount_crdt:
                val+=value
                lst.append(val)

        return lst

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



