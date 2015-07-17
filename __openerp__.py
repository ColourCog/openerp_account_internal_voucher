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
    "summary" : "Enable internal payments and transfers", 
    "description" : """
Internal Vouchers
========================
This module adds internal payments and transfer capabilities to OpenERP.
    """,
    "data" : [ 
      'account_voucher_view.xml', 
      'res_config_view.xml', 
    ], 
    'installable': True,
    'auto_install': False,
    'application': False,
}

