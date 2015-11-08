# -*- coding: utf-8 -*-
{
    "name" : "Internal Vouchers",
    "version" : "0.1", 
    "category" : "Accounting", 
    "sequence": 40,
    "complexity" : "normal", 
    "author" : "ColourCog.com", 
    "website" : "http://colourcog.com", 
    "depends" : [
        "base", 
        "account",
        "account_voucher",
    ], 
    "summary" : "Enable internal fund transfers", 
    "description" : """
Internal Vouchers
=================
This module adds internal payments and transfer capabilities to OpenERP.
It is able to generate a voucher on the chosen side of the transaction.
    """,
    "data" : [ 
      "security/ir.model.access.csv",
      'internal_voucher_view.xml', 
      'internal_voucher_workflow.xml', 
      'res_config_view.xml', 
    ], 
    'installable': True,
    'auto_install': False,
    'application': False,
}
