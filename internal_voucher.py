from openerp.osv import fields, osv
import openerp.addons.decimal_precision as dp
from openerp.tools.translate import _


class account_voucher_transfer(osv.osv):

    _name = 'account.voucher.transfer'

    _columns = {
        'name': fields.char(
            'Memo',
            size=256,
            readonly=True,
            states={'draft': [('readonly', False)]}),
        'date': fields.date(
            'Date',
            readonly=True,
            select=True,
            states={'draft': [('readonly', False)]},
            help="Effective date for accounting entries"),
        'period_id': fields.many2one(
            'account.period',
            'Period',
            required=True,
            readonly=True,
            states={'draft': [('readonly', False)]}),
        'partner_id': fields.many2one(
            'res.partner',
            'Partner',
            change_default=1,
            readonly=True,
            states={'draft': [('readonly', False)]}),
        'journal_id': fields.many2one(
            'account.journal',
            'Payment method',
            required=True,
            readonly=True,
            states={'draft': [('readonly', False)]}),
        'credit_account_id': fields.many2one(
            'account.account',
            'Take from',
            required=True,
            readonly=True,
            states={'draft': [('readonly', False)]}),
        'debit_account_id': fields.many2one(
            'account.account',
            'Transfer to',
            required=True,
            readonly=True,
            states={'draft': [('readonly', False)]}),
        'transfer_account_id': fields.many2one(
            'account.account',
            'Transfer Account',
            required=True,
            readonly=True,
            states={'draft': [('readonly', False)]}),
        'amount': fields.float(
            'Total',
            digits_compute=dp.get_precision('Account'),
            required=True,
            readonly=True,
            states={'draft': [('readonly', False)]}),
        'state': fields.selection(
            [('draft', 'Draft'),
             ('cancel', 'Cancelled'),
             ('posted', 'Posted')],
            'Status',
            readonly=True),
    }


account_voucher_transfer()
