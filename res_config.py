# -*- coding: utf-8 -*-
from openerp.osv import fields, osv

class res_company(osv.osv):
    _inherit = "res.company"

    _columns = {
        'default_internal_transfer_account_id': fields.many2one('account.account',
            'The transfer account for internal vouchers'),
    }

class account_config_settings(osv.osv_memory):
    _inherit = 'account.config.settings'
    _columns = {
        'default_internal_transfer_account_id': fields.related(
            'company_id',
            'default_internal_transfer_account_id',
            type='many2one',
            relation='account.account',
            string="Internal Transfer Account"),
    }

    def onchange_company_id(self, cr, uid, ids, company_id, context=None):
        res = super(account_config_settings, self).onchange_company_id(cr, uid, ids, company_id, context=None)
        # update related fields
        res['value'].update({
            'default_internal_transfer_account_id': False,
        })
        if company_id:
            company = self.pool.get('res.company').browse(cr, uid, company_id, context=context)
            res['value'].update({
                'default_internal_transfer_account_id': company.default_internal_transfer_account_id and company.default_internal_transfer_account_id.id or False,
            })
        return res
