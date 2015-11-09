# -*- coding: utf-8 -*-
from openerp import netsvc
from openerp.osv import fields, osv
import openerp.addons.decimal_precision as dp
from openerp.tools.translate import _


class account_voucher_internal(osv.osv):

    _name = 'account.voucher.internal'
    
    def _default_transfer_account(self, cr, uid, context=None):
        user = self.pool.get('res.users').browse(cr, uid, uid, context=context)
        if user.company_id.default_internal_transfer_account_id:
            return user.company_id.default_internal_transfer_account_id.id
        return False

    _columns = {
        'name': fields.char(
            'Memo',
            size=256,
            readonly=True,
            states={'draft': [('readonly', False)]}),
        'period_id': fields.many2one(
            'account.period', 
            'Period', 
            readonly=True),
        'date': fields.date(
            'Date',
            readonly=True,
            select=True,
            required=True,
            states={'draft': [('readonly', False)]},
            help="Effective date for accounting entries"),
        'partner_id': fields.many2one(
            'res.partner',
            'Partner',
            change_default=1,
            required=True,
            readonly=True,
            states={'draft': [('readonly', False)]}),
        'user_id': fields.many2one('res.users', 'User', required=True),
        'company_id': fields.many2one('res.company', 'Company', required=True),
        'reference': fields.char(
            'Ref #', 
            size=64, 
            readonly=True, 
            states={'draft':[('readonly',False)]}, 
            help="Transaction reference number."),
        'credit_account_id': fields.many2one(
            'account.account',
            'Origin account',
            required=True,
            readonly=True,
            states={'draft': [('readonly', False)]}),
        'credit_journal_id': fields.many2one(
            'account.journal',
            'Register in',
            required=True,
            readonly=True,
            states={'draft': [('readonly', False)]}),
        'credit_voucher_id': fields.many2one(
            'account.voucher',
            'Credit Voucher',
            readonly=True),
        'credit_move_id': fields.many2one(
            'account.move', 
            'Credit Journal Entry',
            readonly=True),
        'debit_account_id': fields.many2one(
            'account.account',
            'Destination account',
            required=True,
            readonly=True,
            states={'draft': [('readonly', False)]}),
        'debit_journal_id': fields.many2one(
            'account.journal',
            'Register in',
            required=True,
            readonly=True,
            states={'draft': [('readonly', False)]}),
        'debit_voucher_id': fields.many2one(
            'account.voucher',
            'Debit Voucher',
            readonly=True),
        'debit_move_id': fields.many2one(
            'account.move', 
            'Debit Journal Entry',
            readonly=True),
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
             ('posted', 'Posted'),
             ('cancel', 'Cancelled')],
            'Status',
            readonly=True),
        'transfer_type': fields.selection(
            [('account', 'Pure Accounting'),
             ('outbound', 'Voucher on Origin'),
             ('inbound', 'Voucher on Destination')],
            'Transfer Type',
            readonly=True,
            states={'draft': [('readonly', False)]}),
    }
    
    _defaults = {
        'company_id': lambda s, cr, uid, c: s.pool.get('res.company')._company_default_get(cr, uid, 'account.voucher.internal', context=c),
        'user_id': lambda cr, uid, id, c={}: id,
        'transfer_account_id': _default_transfer_account,
        'state': 'draft',
        'transfer_type': 'account',
    }
    
    # Tools
    def _create_move(self, cr, uid, transfer_id, reference, credit_id, 
                    debit_id, journal_id, date, amount, context=None):
        """return a move, given the variables."""
        ctx = dict(context or {}, account_period_prefer_normal=True)
        move_obj = self.pool.get('account.move')
        journal_obj = self.pool.get('account.journal')
        period_obj = self.pool.get('account.period')
        period_id = period_obj.find(cr, uid, date, context=ctx)[0]
        transfer = self.browse(cr, uid, transfer_id, context=ctx)
        journal = journal_obj.browse(cr, uid, journal_id, context=ctx)
        company_id = transfer.company_id.id

        move_id =  move_obj.create(
            cr, 
            uid, 
            move_obj.account_move_prepare(
                cr, 
                uid, 
                journal_id,
                date=date, 
                ref=reference, 
                company_id=company_id, 
                context=ctx),
            context=ctx)

        lml = []
        # common values
        vals = { 
        }
        # create the credit move line
        lml.append({
            'partner_id': transfer.partner_id.id,
            'name': transfer.name,
            'date_maturity': date,
            'period_id': period_id,
            'credit': amount,
            'account_id': credit_id,
            })
        # create the debit move line
        lml.append({
            'partner_id': transfer.partner_id.id,
            'name': transfer.name,
            'date_maturity': date,
            'period_id': period_id,
            'debit': amount,
            'account_id': debit_id,
            })
        # convert eml into an osv-valid format
        lines = [(0, 0, x) for x in lml]
        move_obj.write(cr, uid, [move_id], {'line_id': lines}, context=ctx)
        # post the journal entry if 'Skip 'Draft' State for Manual Entries' is checked
        if journal.entry_posted:
            move_obj.button_validate(cr, uid, [move_id], ctx)
        return move_id

    def _create_voucher(self, cr, uid, transfer_id, move_id, journal_id, 
                        name, vtype, reference, date, amount, 
                        context=None):
        ctx = dict(context or {}, account_period_prefer_normal=True)
        CRDIR = {'in': 'cr', 'out':'dr'}
        TRDIR = {'in': 'receipt', 'out':'payment'}
        period_obj = self.pool.get('account.period')
        voucher_obj = self.pool.get('account.voucher')
        journal_obj = self.pool.get('account.journal')
        move_obj = self.pool.get('account.move')
        move = move_obj.browse(cr, uid, move_id, context=ctx)
        transfer = self.browse(cr, uid, transfer_id, context=ctx)
        journal = journal_obj.browse(cr, uid, journal_id, context=ctx)
        company_id = transfer.company_id.id
        period_id = period_obj.find(cr, uid, date, context=ctx)[0]
        partner_id = transfer.partner_id.id
        account_id = journal.default_debit_account_id.id
        if vtype == 'in':
            account_id = journal.default_credit_account_id.id
        # prepare the voucher
        voucher = {
            'journal_id': journal_id,
            'company_id': company_id,
            'partner_id': partner_id,
            'type': TRDIR.get(vtype),
            'name': name,
            'account_id': account_id,
            'reference': reference,
            'amount': amount > 0.0 and amount or 0.0,
            'date': date,
            'date_due': date,
            'period_id': period_id,
            }

        # Define the voucher line
        lml = []
        # Create voucher_lines
        for line_id in move.line_id:
            if vtype == 'in' and line_id.credit:
                continue
            if vtype == 'out' and line_id.debit:
                continue
            account_id = line_id.account_id.id
            lml.append({
                'name': line_id.name,
                'move_line_id': line_id.id,
                'reconcile': True,
                'amount': amount > 0.0 and amount or 0.0,
                'account_id': line_id.account_id.id,
                'type': CRDIR.get(vtype)
                })
        lines = [(0, 0, x) for x in lml]
        
                
        voucher['line_ids'] = lines
        voucher_id = voucher_obj.create(cr, uid, voucher, context=ctx)
        # validate now
        # this may be dangerous, but it is convenient
        voucher_obj.button_proforma_voucher(cr, uid, [voucher_id], context)
        return voucher_id
    
    def _pure_move(self, cr, uid, transfer_id, context=None):
        """Simply create the moves using the transfer account"""
        transfer = self.browse(cr, uid, transfer_id, context=context)
        res = {}
        res['credit_move_id'] = self._create_move(
            cr, 
            uid, 
            transfer.id,
            transfer.reference,
            transfer.credit_account_id.id, 
            transfer.transfer_account_id.id, 
            transfer.credit_journal_id.id,
            transfer.date,
            transfer.amount,
            context)
        res['debit_move_id'] = self._create_move(
            cr, 
            uid, 
            transfer.id,
            transfer.reference,
            transfer.transfer_account_id.id, 
            transfer.debit_account_id.id, 
            transfer.debit_journal_id.id,
            transfer.date,
            transfer.amount,
            context)
        #TODO: reconcile these two
        return res
    
    def _outbound_voucher(self, cr, uid, transfer_id, context=None):
        """Voucher on Origin"""
        transfer = self.browse(cr, uid, transfer_id, context=context)
        if transfer.credit_journal_id.type not in ['cash', 'bank']:
            raise osv.except_osv(
                _('Cannot create voucher!'),
                _('The origin journal must be of type "bank" or "cash".'))
        res = {}
        res['debit_move_id'] = self._create_move(
            cr, 
            uid, 
            transfer.id,
            transfer.reference,
            transfer.transfer_account_id.id, 
            transfer.debit_account_id.id, 
            transfer.debit_journal_id.id,
            transfer.date,
            transfer.amount,
            context)
        res['credit_voucher_id'] = self._create_voucher(
            cr, 
            uid, 
            transfer.id,
            res['debit_move_id'],
            transfer.credit_journal_id.id,
            transfer.name,
            'out',
            transfer.reference,
            transfer.date,
            transfer.amount,
            context)
        return res

    def _inbound_voucher(self, cr, uid, transfer_id, context=None):
        """Voucher on Destination"""
        transfer = self.browse(cr, uid, transfer_id, context=context)
        if transfer.debit_journal_id.type not in ['cash', 'bank']:
            raise osv.except_osv(
                _('Cannot create voucher!'),
                _('The destination journal must be of type "bank" or "cash".'))
        res = {}
        res['credit_move_id'] = self._create_move(
            cr, 
            uid, 
            transfer.id,
            transfer.reference,
            transfer.transfer_account_id.id, 
            transfer.credit_account_id.id, 
            transfer.credit_journal_id.id,
            transfer.date,
            transfer.amount,
            context)
        res['debit_voucher_id'] = self._create_voucher(
            cr, 
            uid, 
            transfer.id,
            res['credit_move_id'],
            transfer.debit_journal_id.id,
            transfer.name,
            'out',
            transfer.reference,
            transfer.date,
            transfer.amount,
            context)
        return res
        
    # CRUD
    def create(self, cr, uid, vals, context=None):
        period_obj = self.pool.get('account.period')
        vals['period_id'] = period_obj.find(cr, uid, vals['date'], context=context)[0]
        return super(account_voucher_internal, self).create(cr, uid, vals, context=context)
    
    def unlink(self, cr, uid, ids, context=None):
        for rec in self.browse(cr, uid, ids, context=context):
            if rec.amount and rec.state not in ['draft', 'cancel']:
                raise osv.except_osv(
                    _('Warning!'),
                    _('You must cancel the Transfer before you can delete it.'))
        return super(account_voucher_internal, self).unlink(cr, uid, ids, context)

    # UI
    def onchange_date(self, cr, uid, ids, date, context=None):
        period_obj = self.pool.get('account.period')
        return {'value': {'period_id': period_obj.find(cr, uid, date, context=context)[0]}}
    

    # Workflow
    def internal_draft(self, cr, uid, ids, context=None):
        wf_service = netsvc.LocalService("workflow")
        for transfer in self.browse(cr, uid, ids):
            wf_service.trg_delete(uid, 'account.voucher.internal', transfer.id, cr)
            wf_service.trg_create(uid, 'account.voucher.internal', transfer.id, cr)
        return self.write(cr, uid, ids, {'state': 'draft'}, context=context)
    
    def internal_validate(self, cr, uid, ids, context=None):
        """Create all moves and vouchers"""
        tx = {
            'account': self._pure_move,
            'outbound': self._outbound_voucher,
            'inbound': self._inbound_voucher,
        }
        for transfer in self.browse(cr, uid, ids):
            res = {'state': 'posted'}
            # read the transfer type and decide what to do from there
            res.update(tx.get(transfer.transfer_type)(cr, uid, transfer.id, context))
            # We're done, let's post it!
            self.write(cr, uid, [transfer.id], res, context=context)
        return True
        
    def internal_cancel(self, cr, uid, ids, context=None):
        """Cancel/Delete all moves and vouchers"""
        move_obj = self.pool.get('account.move')
        voucher_obj = self.pool.get('account.voucher')
        res = {
            'credit_move_id': False,
            'credit_voucher_id': False,
            'debit_move_id': False,
            'debit_voucher_id': False,
            'state': 'cancel',
        }
        for transfer in self.browse(cr, uid, ids):
            moves = [
                transfer.credit_move_id.id,
                transfer.debit_move_id.id,
            ]
            # unreconcile, then cancel/(delete?) vouchers
            if transfer.credit_voucher_id:
                voucher_obj.cancel_voucher(
                    cr,
                    uid,
                    [transfer.credit_voucher_id.id],
                    context=context)
                voucher_obj.unlink(cr, uid, [transfer.credit_voucher_id.id], context=context)
            if transfer.debit_voucher_id:
                voucher_obj.cancel_voucher(
                    cr,
                    uid,
                    [transfer.debit_voucher_id.id],
                    context=context)
                voucher_obj.unlink(cr, uid, [transfer.debit_voucher_id.id], context=context)
            # unpost, then delete moves
            if transfer.credit_move_id:
                move_obj.button_cancel(
                    cr,
                    uid,
                    [transfer.credit_move_id.id],
                    context=context)
                move_obj.unlink(cr, uid, [transfer.credit_move_id.id], context=context)
            if transfer.debit_move_id:
                move_obj.button_cancel(
                    cr,
                    uid,
                    [transfer.debit_move_id.id],
                    context=context)
                move_obj.unlink(cr, uid, [transfer.debit_move_id.id], context=context)
        return self.write(cr, uid, ids, res, context=context)
    
account_voucher_internal()
